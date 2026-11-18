from pathlib import Path
import queue
import sys
import tempfile
import unittest
from unittest.mock import patch

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM/'python'), str(Path(__file__).resolve().parent)]
from episode_controller import EpisodeController
from input_router import RoutingPolicy
from task_session import JavaTask
from hub_gate import HubGate
from test_input_router import ScriptedClient


class Planner:
    def complete(self, purpose, state, schema):
        if purpose == 'dispatch-policy':
            doc = next(doc for doc in state['documents'].values() if doc['source'] == 'official-policy')
            return {'fragment_numbers': [doc['fragments'][-1]['number']]}
        if purpose == 'response-review': return {'completed_goal_ids': [g['goal_id'] for g in state['visible_state']['task']['goals']]
            if 'Your balance' in state['candidate_response'] else [], 'comparison': None}
        if purpose == 'new-goals': return {'goals': [{'description': 'read balance', 'quote': state['content']}]}
        if purpose == 'tool-step':
            return {'goal_id': state['task']['goals'][0]['goal_id'], 'status': 'proposed',
                    'policy_refs': [ref for ref, record in state['evidence'].items() if record['source'] == 'official-policy'],
                    'argument_bindings': [{'parameter': key, 'mode': 'literal', 'sources': [
                        {'ref': ref, 'quote': record['content']} for ref, record in state['evidence'].items()
                        if record['source'] == 'official-user' and str(value) in record['content']]}
                        for key,value in state.get('effective_operation', {}).get('arguments', {}).items()],
                    'conditions': [{'clause_ids': list(state['dispatch_clauses']), 'id': 'authorized_request', 'statement': 'Customer requested this balance query.',
                                    'evidence_refs': list(state['evidence'])}]}
        if purpose == 'goal-completion':
            return {'goal_id': state['goal']['goal_id'], 'status': 'proposed',
                    'policy_refs': [ref for ref, record in state['evidence'].items() if record['source'] == 'official-policy'],
                    'conditions': [{'id': 'result', 'statement': 'Balance was read and the accurate amount is reported.',
                                    'evidence_refs': list(state['evidence'])}]}
        raise AssertionError(purpose)


class AllSupported(ScriptedClient):
    def ask(self, request):
        result = super().ask(request)
        if 'has_new' not in request['questions']:
            for name, answer in result['answers'].items():
                answer['noul'] = .01 if name.endswith('_violated') or name == 'comparison_needed' else .99
        return result


class EpisodeControllerTests(unittest.TestCase):
    def test_operation_plan_feedback_and_evidence_boundary(self):
        from unittest.mock import Mock
        client = AllSupported()
        with tempfile.TemporaryDirectory() as directory:
            task = Mock(episode='fixture')
            planner = Mock()
            controller = EpisodeController(task, None, planner, client,
                RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'),
                Path(directory), {}, 'Require consent before updating a preference.')
            consent = controller.evidence.add('official-user', 'Please update the preference.')
            def proposal(refs):
                return {'goal_id': 'g', 'status': 'proposed', 'argument_bindings': [], 'policy_refs': [controller.policy_ref],
                        'conditions': [{'clause_ids': ['P1'], 'id': 'consent', 'statement': 'Customer authorized the update.',
                                        'evidence_refs': refs}]}
            state = {'effective_operation': {'name': 'change_preference'}}
            state['dispatch_clauses'] = {'P1': {'ref': controller.policy_ref, 'quote': 'Require consent before updating a preference.'}}
            for refs, reason in [([], 'consent: empty'), (['invented'], 'consent: unobserved')]:
                planner.complete.return_value = proposal(refs)
                with self.assertRaisesRegex(PermissionError, reason):
                    controller._plan('tool-step', state, now=900)
            self.assertFalse(client.calls)
            planner.complete.return_value = proposal([consent])
            with patch.object(controller.judgments, 'requirements', return_value={
                    'status': 'unknown', 'conditions': {'goal_link': 'satisfied', 'conditions_grounded': 'unknown'}}):
                with self.assertRaisesRegex(PermissionError, 'conditions_grounded=unknown'):
                    controller._plan('tool-step', state, now=900)
            controller.evidence.add('official-user', 'I confirm the update.')
            state['evidence'] = controller.evidence.visible()
            self.assertEqual(controller._plan('tool-step', state, now=900)['conditions'][0]['evidence_refs'], [consent])

    def test_rejected_step_reaches_planner_without_becoming_receipt_evidence(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            planner = Mock()
            controller = EpisodeController(Mock(episode='fixture'), None, planner, AllSupported(),
                RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'),
                Path(directory), {}, 'Record authorization before changing a preference.')
            state = {'effective_operation': {'name': 'record_authorization', 'arguments': {}},
                     'task': {'goals': [{'goal_id': 'language'}]}, 'evidence': controller.evidence.visible()}
            invalid = {'status': 'proposed', 'argument_bindings': [], 'goal_id': 'language', 'policy_refs': [controller.policy_ref],
                       'goal_relation': 'required_prerequisite', 'goal_basis': 'Authorization must be recorded.',
                       'expected_effect': 'Authorization is recorded.',
                       'conditions': [{'id': 'already_recorded', 'statement': 'This record already exists.',
                                       'evidence_refs': [controller.policy_ref]}]}
            state['dispatch_clauses'] = {'P1': {'ref': controller.policy_ref, 'quote': 'Record authorization before changing a preference.'}}
            invalid['conditions'][0].update(clause_ids=['P1'], evidence_refs=[controller.evidence.add('official-user', 'Please proceed.')])
            state['evidence'] = controller.evidence.visible()
            planner.complete.return_value = invalid
            with patch.object(controller.judgments, 'requirements', return_value={
                'status': 'deny', 'conditions': {'pre_already_recorded': 'violated'}}) as review:
                with self.assertRaisesRegex(PermissionError, 'pre_already_recorded=violated'):
                    controller._plan('tool-step', state, now=900)
                with self.assertRaisesRegex(PermissionError, 'unchanged'):
                    controller._plan('tool-step', state, now=900)
                self.assertEqual(review.call_count, 1)
            revision = planner.complete.call_args.args[1]['previous_refusal']
            self.assertEqual(revision['proposal'], invalid)
            self.assertEqual(revision['proposal']['expected_effect'], invalid['expected_effect'])
            self.assertEqual(state['evidence'], controller.evidence.visible())

    def test_prior_receipt_is_correlated_to_object_and_available_before_dispatch(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            controller = EpisodeController(Mock(episode='fixture'), None, Mock(), AllSupported(),
                RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'),
                Path(directory), {}, 'Record consent before applying the change.')
            ref = controller.evidence.add('official-tool', 'Authorization recorded for subject A.')
            condition = {'id': 'consent_record', 'statement': 'Prior authorization was recorded.',
                         'evidence_refs': [ref], 'prior_receipt_call_id': 'earlier'}
            proposal = {'status': 'proposed', 'goal_id': 'language', 'policy_refs': [controller.policy_ref],
                        'conditions': [condition]}
            condition['clause_ids'] = ['P1']
            proposal['argument_bindings'] = [{'parameter': 'customer_id', 'mode': 'literal', 'sources': [{'ref': ref, 'quote': 'subject A.'}]}]
            receipt = {'receipt': {'status': 'succeeded'}, 'operation': {'arguments': {'customer_id': 'A'}},
                       'evidence_ref': ref}
            state = {'prior_receipts': {}, 'effective_operation': {'arguments': {'customer_id': 'A'}}}
            with self.assertRaisesRegex(PermissionError, 'prior receipt missing'):
                controller._validate_plan('tool-step', state, proposal, now=900)
            state['dispatch_clauses'] = {'P1': {'ref': controller.policy_ref, 'quote': 'Record consent before applying the change.'}}
            state['prior_receipts']['earlier'] = receipt
            controller._validate_plan('tool-step', state, proposal, now=900)
            state['effective_operation']['arguments']['customer_id'] = 'B'
            with self.assertRaisesRegex(PermissionError, 'subject mismatch'):
                controller._validate_plan('tool-step', state, proposal, now=900)

    def test_action_basis_cannot_hide_a_missing_approval(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            client = AllSupported()
            ctl = EpisodeController(Mock(episode='fixture'), None, Mock(), client,
                RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), Path(directory), {},
                'Require consent. After supervisor approval, update the setting.')
            fact = ctl.evidence.add('official-user', 'I consent to the update.')
            state = {'effective_operation': {'name': 'update_setting', 'arguments': {}}, 'dispatch_clauses': {
                'P1': {'quote': 'Require consent.', 'ref': ctl.policy_ref},
                'P2': {'quote': 'After supervisor approval, update the setting.', 'ref': ctl.policy_ref}}}
            plan = {'goal_id': 'update', 'goal_basis': 'Perform the update.', 'status': 'proposed',
                    'goal_basis_clause_ids': ['P2'], 'argument_bindings': [],
                    'conditions': [{'id': 'consent', 'statement': 'Customer consented.', 'clause_ids': ['P1'],
                                    'evidence_refs': [fact]}]}
            with patch.object(ctl.judgments, 'requirements', return_value={
                'status': 'deny', 'conditions': {'basis_P2': 'satisfied', 'clause_P2': 'violated'}}) as check:
                with self.assertRaisesRegex(PermissionError, 'clause_P2=violated'):
                    ctl._validate_plan('tool-step', state, plan, now=900)
            snapshot, questions = check.call_args.args
            self.assertEqual(snapshot['proposal']['policy_refs'], [ctl.policy_ref])
            self.assertIn('basis_P2', questions)
            self.assertEqual(questions['clause_P2']['instructions']['mapped_conditions'], [])

    def test_shared_prerequisite_dispatches_once_across_goals(self):
        class SharedPlanner(Planner):
            def complete(self, purpose, state, schema):
                plan = super().complete(purpose, state, schema)
                if purpose == 'tool-step':
                    plan.update(goal_relation='required_prerequisite', goal_basis='Both services require consent.',
                                expected_effect='Consent is recorded.',
                                goal_id=state['task']['goals'][self.index]['goal_id'])
                return plan
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                task.call('receive', episode='episode', message='m', content='two services')
                task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                          actions=[{'kind': 'new_goal', 'description': goal} for goal in ('change language', 'change format')])
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                planner = SharedPlanner()
                ctl = EpisodeController(task, hub, planner, AllSupported(),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'controller',
                    {'record_consent': {'access': 'write', 'principal': 'fixture'}}, 'Record consent first.',
                    {'record_consent': lambda content, args: {'status': 'succeeded'}})
                ctl.evidence.add('official-user', 'Please record consent for customer A.')
                output = queue.Queue()
                action = {'name': 'record_consent', 'arguments': {'customer_id': 'A'}}
                planner.index = 0
                ctl.tool({**action, 'id': 'first'}, output, now=900)
                ctl.receipt('first', 'Consent recorded.', False, now=900)
                planner.index = 1
                with self.assertRaisesRegex(PermissionError, 'Shared prerequisite already adopted'):
                    ctl.tool({**action, 'id': 'second'}, output, now=900)
                self.assertEqual(output.qsize(), 1)

    def test_scope_revision_controls_dispatch_and_refuses_unchanged_retry(self):
        # Exercise the real boundary with scripted observations, including an uncertain exclusion.
        baseline = 'Require consent for changing delivery.'
        for case, expected in [('equivalent', 1), ('missing approval', 0), ('approved', 1),
                               ('wrong subject', 0), ('later', 1), ('conflict', 0)]:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                rule = {'equivalent': 'Obtain customer consent before changing delivery.',
                        'later': 'Review cancellations before cancelling delivery.',
                        'conflict': 'Prohibit delivery changes.'}.get(case, 'Supervisor approval is also required.')
                class ScopePlanner(Planner):
                    revisions = 0

                    def complete(self, purpose, state, schema):
                        if purpose == 'dispatch-policy':
                            return {'fragment_numbers': [1, 2]}
                        plan = super().complete(purpose, state, schema)
                        if purpose == 'tool-step':
                            self.revisions += 1
                            pending, = state['policy_scope']['unresolved']
                            assert state['dispatch_clauses'][pending]['quote'] == rule
                            if case in ('later', 'conflict'):
                                plan['conditions'][0]['clause_ids'].remove(pending)
                                plan['scope_exclusions'] = [{'clause_id': pending, 'scope_quote': rule}]
                            elif case != 'equivalent':
                                plan['conditions'][0]['clause_ids'].remove(pending)
                                plan['conditions'].append({'id': 'approval', 'statement': 'Approval for A.',
                                    'clause_ids': [pending], 'evidence_refs': [proof]})
                        return plan

                class ScopeObservations(AllSupported):
                    def ask(self, request):
                        result = super().ask(request)
                        for key, question in request['questions'].items():
                            score = None
                            if key.startswith('F') and request['state']['candidates'][key]['quote'] == rule:
                                score = .5
                            if key.startswith('scope_'):
                                score = .99 if case == 'later' else .5
                            if key.startswith('clause_') and question['instructions']['clause'] == rule:
                                if case in ('missing approval', 'wrong subject'):
                                    score = .01
                            if score is not None:
                                result['answers'][key]['noul'] = score
                        return result

                with JavaTask(root/'task', 'episode', 1000, 64) as task:
                    task.call('receive', episode='episode', message='m', content='Change delivery for A.')
                    task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                              actions=[{'kind': 'new_goal', 'description': 'Change delivery for A.'}])
                    hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl',
                                  ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                    self.addCleanup(hub.close)
                    planner = ScopePlanner()
                    ctl = EpisodeController(task, hub, planner, ScopeObservations(),
                        RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'controller',
                        {'change_delivery': {'access': 'write', 'principal': 'fixture'}}, baseline)
                    ctl.add_published_evidence('published-skill', rule)
                    ctl.evidence.add('official-user', 'Change delivery for A.')
                    proof = ctl.evidence.add('official-tool', {'approved': 'Approved for A.',
                        'wrong subject': 'Approved for B.'}.get(case, 'No approval recorded.'))
                    action = {'id': 'first', 'name': 'change_delivery', 'arguments': {'customer_id': 'A'}}
                    output = queue.Queue()
                    if expected:
                        ctl.tool(action, output, now=900)
                    else:
                        with self.assertRaisesRegex(PermissionError, 'evidence/coverage'):
                            ctl.tool(action, output, now=900)
                        with self.assertRaisesRegex(PermissionError, 'Same scope and evidence'):
                            ctl.tool({**action, 'id': 'second'}, output, now=900)
                    self.assertEqual(planner.revisions, 1)
                    self.assertEqual(output.qsize(), expected)

    def test_unselected_policy_text_still_requires_independent_coverage(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            controller = EpisodeController(Mock(episode='sample'), None, Mock(), AllSupported(),
                RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'),
                Path(directory), {}, 'Require customer consent. Also require supervisor approval.')
            ref = controller.evidence.add('official-user', 'Please proceed.')
            proposal = {'status': 'proposed', 'goal_id': 'g', 'policy_refs': [controller.policy_ref],
                        'argument_bindings': [], 'conditions': [{'id': 'consent', 'statement': 'Customer consented.',
                        'clause_ids': ['consent'], 'evidence_refs': [ref]}]}
            state = {'effective_operation': {'arguments': {}}, 'policy_scope': {'residual_fragment_count': 1},
                     'dispatch_clauses': {'consent': {'ref': controller.policy_ref, 'quote': 'Require customer consent.'}}}
            with patch.object(controller.judgments, 'requirements', return_value={
                    'status': 'deny', 'conditions': {'conditions_complete': 'violated'}}) as check:
                with self.assertRaisesRegex(PermissionError, 'conditions_complete'):
                    controller._validate_plan('tool-step', state, proposal, now=900)
                snapshot, questions = check.call_args.args
                self.assertIn('conditions_complete', questions)
                self.assertIn('supervisor approval', snapshot['evidence'][controller.policy_ref]['content'])
                self.assertIn('clause_consent', questions)

    def test_fabricated_s2_quote_is_durable_clarification_not_episode_crash(self):
        class InvalidPlanner(Planner):
            def complete(self, purpose, state, schema):
                return {'goals': [], 'existing_routes': [], 'context_quote': 'not in customer message'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = EpisodeController(task, None, InvalidPlanner(), AllSupported({}),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control', {}, 'policy')
                result = controller.user('m', 'Hello', now=900)
                self.assertEqual(result['status'], 'clarify')
                self.assertEqual(task.call('message_status', message='m')['status'], 'clarify')
                self.assertFalse(controller.state(900)['can_dispatch'])
                self.assertEqual(controller.state(900)['goals'], [])

    def test_request_expiring_during_planning_never_adopts_or_enqueues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = EpisodeController(task, None, Planner(),
                    AllSupported({'covered': .99, 'has_new': .99, 'new0_supported': .99}),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control',
                    {'write_fixture': {'access': 'write', 'principal': 'fixture'}}, 'policy')
                controller.user('m', 'Please read balance', now=900)
                output = queue.Queue()
                with patch('episode_controller.time.monotonic', side_effect=[0, 2]):
                    with self.assertRaises(PermissionError):
                        controller.tool({'id': 'late', 'name': 'write_fixture', 'arguments': {}}, output, now=900, request_deadline=1)
                self.assertTrue(output.empty())
                self.assertEqual(list((root/'control/effects').glob('*.json')), [])

    def test_unlock_requires_observed_disclosure_but_not_business_completion(self):
        class MetadataPlanner(Planner):
            def complete(self, purpose, state, schema):
                if purpose == 'tool-step': raise AssertionError('Unlock is metadata, not a bank effect')
                return super().complete(purpose, state, schema)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                client = AllSupported({'covered': .99, 'has_new': .99, 'new0_supported': .99})
                controller = EpisodeController(task, hub, MetadataPlanner(), client,
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control',
                    {'unlock_discoverable_agent_tool': {'access': 'write', 'principal': 'broker'},
                     'special_read': {'access': 'read', 'principal': 'shared-read', 'discoverable': True}}, 'policy')
                controller.user('m', 'Please read balance', now=900)
                output = queue.Queue()
                call = {'id': 'unlock', 'name': 'unlock_discoverable_agent_tool', 'arguments': {'agent_tool_name': 'special_read'}}
                controller.evidence.add('official-user', 'Please enable special_read')
                with self.assertRaises(PermissionError): controller.tool(call, output, now=900)
                self.assertTrue(output.empty())
                controller.evidence.add('official-policy', 'Use the published internal capability special_read to obtain this fact.')
                inference_count = len(client.calls)
                controller.tool(call, output, now=900)
                self.assertEqual(output.qsize(), 1)
                self.assertEqual(len(client.calls), inference_count)
                controller.receipt('unlock', 'Tool unlocked: special_read\nDescription: synthetic reader', False, now=900)
                self.assertIn('special_read', controller.unlocked)

    def test_public_evidence_read_can_support_multiple_active_goals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                task.call('receive', episode='episode', message='m', content='two services')
                task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                    actions=[{'kind': 'new_goal', 'description': text} for text in ('dispute', 'replace card')])
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                # Planner has no read-goal-selection handler: public facts must not need it.
                controller = EpisodeController(task, hub, Planner(), AllSupported(),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control',
                    {'KB_search': {'access': 'read', 'principal': 'shared-read'}}, 'policy')
                output = queue.Queue()
                controller.tool({'id': 'kb', 'name': 'KB_search', 'arguments': {'query': 'card dispute'}}, output, now=900)
                self.assertEqual(output.qsize(), 1)
                self.assertEqual(output.get()['tool_calls'][0]['id'], 'kb')

    def test_customer_text_cannot_be_used_as_policy_authority(self):
        class UserPolicyPlanner(Planner):
            def complete(self, purpose, state, schema):
                result = super().complete(purpose, state, schema)
                if purpose == 'tool-step':
                    result['policy_refs'] = [ref for ref, record in state['evidence'].items()
                                             if record['source'] == 'official-user']
                return result
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = EpisodeController(task, None, UserPolicyPlanner(),
                    AllSupported({'covered': .99, 'has_new': .99, 'new0_supported': .99}),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control', {}, 'policy')
                controller.user('m', 'Please read balance', now=900)
                with self.assertRaises(PermissionError):
                    controller._plan('tool-step', {**controller.visible(900), 'dispatch_clauses': {}}, now=900)

    def test_accepted_operation_does_not_complete_goal(self):
        class PendingEffects:
            def status(self, operation): return {'business_status': 'accepted'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = EpisodeController(task, None, Planner(),
                    AllSupported({'covered': .99, 'has_new': .99, 'new0_supported': .99}),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control', {}, 'policy')
                controller.user('m', 'Please read balance', now=900)
                goal = task.call('status', now=900)['goals'][0]['goal_id']
                controller.bindings['call'] = {'operation': 'op', 'goal': goal}
                controller.effects = PendingEffects()
                result = controller.response('Your balance is 10.', waiting=False, now=900)
                self.assertNotEqual(result['status'], 'allow')
                self.assertEqual(task.call('status', now=900)['outcome'], 'undetermined')

    def test_unknown_customer_scope_never_dispatches(self):
        class UnknownSubject(AllSupported):
            def ask(self, request):
                result = super().ask(request)
                if 'customer_scope' in result['answers']: result['answers']['customer_scope']['noul'] = .5
                return result
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                task.call('receive', episode='episode', message='m', content='two services')
                task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                    actions=[{'kind': 'new_goal', 'goal_id': None, 'description': text}
                             for text in ('balance', 'rates')], resolved_messages=[])
                controller = EpisodeController(task, None, Planner(), UnknownSubject(),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control',
                    {'read_balance': {'access': 'read', 'principal': 'shared-read'}}, 'policy')
                output = queue.Queue()
                with self.assertRaises(PermissionError):
                    controller.tool({'id': 'read', 'name': 'read_balance', 'arguments': {}}, output, now=900)
                self.assertTrue(output.empty())

    def test_information_question_does_not_try_to_complete_all_active_goals(self):
        class QuestionPlanner(Planner):
            def complete(self, purpose, state, schema):
                if purpose == 'goal-completion': raise AssertionError('Question must not complete a goal')
                return super().complete(purpose, state, schema)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = EpisodeController(task, None, QuestionPlanner(),
                    AllSupported({'covered': .99, 'has_new': .99, 'new0_supported': .99}),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control', {}, 'policy')
                controller.user('m', 'Please read balance', now=900)
                self.assertEqual(controller.response('Please provide your name.', waiting=False, now=900)['status'], 'allow')
                self.assertEqual(task.call('status', now=900)['outcome'], 'undetermined')
    def test_full_controller_routes_tool_receipt_and_accepts_goal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                client = AllSupported({'covered': .99, 'has_new': .99, 'new0_supported': .99})
                controller = EpisodeController(task, hub, Planner(), client,
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control',
                    {'read_balance': {'access': 'read', 'principal': 'shared-read'}}, 'Fixture public policy: balance queries are permitted.')
                self.assertEqual(controller.user('m1', 'Please read my balance', now=900)['status'], 'ready')
                output = queue.Queue()
                controller.tool({'id': 'call-one', 'name': 'read_balance', 'arguments': {}}, output, now=900)
                self.assertEqual(output.qsize(), 1)
                controller.receipt('call-one', 'Balance: 10', False, now=900)
                result = controller.response('Your balance is 10.', waiting=False, now=900)
                self.assertEqual(result['status'], 'allow')
                self.assertEqual(task.call('status', now=900)['outcome'], 'success')

    def test_uninterpreted_input_and_unknown_wrapper_never_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = EpisodeController(task, None, Planner(), AllSupported(),
                    RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'control', {}, 'policy')
                output = queue.Queue()
                with self.assertRaises(PermissionError): controller.tool({'id': 'x', 'name': 'unknown', 'arguments': {}}, output, now=900)
                self.assertTrue(output.empty())
