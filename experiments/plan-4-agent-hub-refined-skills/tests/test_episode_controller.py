from pathlib import Path
import queue
import sys
import tempfile
import unittest

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM/'python'), str(Path(__file__).resolve().parent)]
from episode_controller import EpisodeController
from input_router import RoutingPolicy
from task_session import JavaTask
from hub_gate import HubGate
from test_input_router import ScriptedClient


class Planner:
    def complete(self, purpose, state, schema):
        if purpose == 'response-review': return {'completed_goal_ids': [g['goal_id'] for g in state['visible_state']['task']['goals']]
            if 'Your balance' in state['candidate_response'] else [], 'comparison': None}
        if purpose == 'new-goals': return {'goals': [{'description': 'read balance', 'quote': state['content']}]}
        if purpose == 'tool-step':
            return {'goal_id': state['task']['goals'][0]['goal_id'], 'status': 'proposed',
                    'policy_refs': [ref for ref, record in state['evidence'].items() if record['source'] == 'official-policy'],
                    'conditions': [{'id': 'authorized_request', 'statement': 'Customer requested this balance query.',
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
                    controller._plan('tool-step', controller.visible(900), now=900)

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

    def test_unknown_read_target_never_dispatches(self):
        class UnknownPlanner(Planner):
            def complete(self, purpose, state, schema):
                if purpose == 'read-goal-selection':
                    return {'goal_id': state['task']['goals'][0]['goal_id'], 'status': 'unknown',
                            'policy_refs': [], 'conditions': []}
                return super().complete(purpose, state, schema)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                task.call('receive', episode='episode', message='m', content='two services')
                task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                    actions=[{'kind': 'new_goal', 'goal_id': None, 'description': text}
                             for text in ('balance', 'rates')], resolved_messages=[])
                controller = EpisodeController(task, None, UnknownPlanner(), AllSupported(),
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
