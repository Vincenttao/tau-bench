"""Policy phase and outward clarification contracts, independent of banking case IDs."""
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from test_episode_controller import EpisodeController, AllSupported, RoutingPolicy

class QuestionAndPhaseTests(TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.ctl = EpisodeController(Mock(episode='fixture'), None, Mock(), AllSupported(),
            RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'), Path(root.name), {},
            'Get consent before submitting. Review the receipt after submission.')
        self.goal = {'goal_id': 'delivery', 'state': 'active', 'description': 'Change delivery.'}
        self.ctl.state = lambda now: {'goals': [self.goal], 'can_dispatch': True}
        self.question = 'Which delivery speed do you prefer?'
        self.draft = self.question + ' The order has shipped.'
        self.candidate = {'question': self.question, 'source_quote': self.question, 'goal_id': 'delivery'}

    def test_reviewed_question_alone_creates_wait_for_selected_goal(self):
        self.ctl.planner.complete.return_value = {'clarification': self.candidate}
        with patch.object(self.ctl, '_wait_for_question') as wait:
            self.ctl.review.extract = Mock(return_value={'claims': [], 'comparison': None, 'completed_goal_ids': []})
            self.ctl.claims.check = Mock(return_value={'status': 'allow'})
            self.assertEqual(self.ctl.repair_question(self.draft, now=900), self.question)
            wait.assert_called_once()
            self.assertEqual(wait.call_args.args[:2], ('delivery', self.question))
            self.assertEqual(self.ctl.last_assistant_message, self.question)
            self.assertEqual(self.ctl.last_question, self.question)
            self.assertFalse(self.ctl.bindings)

    def test_foreign_or_fabricated_question_cannot_create_wait(self):
        for updates in ({'goal_id': 'other'}, {'source_quote': 'Invented question'}):
            self.ctl.planner.complete.return_value = {'clarification': {**self.candidate, **updates}}
            self.assertIsNone(self.ctl.repair_question(self.draft, now=900))
        self.assertEqual(self.ctl.last_question, '')

    def test_unproven_later_phase_never_removes_a_prerequisite(self):
        from dispatch_policy import split_later_clauses
        clauses = {'P1': {'quote': 'Get consent before submitting.'},
                   'P2': {'quote': 'Review the receipt after submission.'}}
        current, later, checks = split_later_clauses(clauses, [{'clause_id':'P2','stage':'receipt'}])
        self.assertEqual(set(current), {'P1'})
        self.assertEqual(later['P2']['quote'], clauses['P2']['quote'])
        self.assertIn('later_P2', checks)
        with self.assertRaises(PermissionError):
            split_later_clauses(clauses, [{'clause_id':'unknown','stage':'receipt'}])

    def test_unreviewed_embedded_claim_is_never_published(self):
        self.ctl.planner.complete.return_value = {'clarification': self.candidate}
        self.ctl.review.extract = Mock(return_value={'claims': [], 'completed_goal_ids': [], 'comparison': None})
        self.ctl.claims.check = Mock(return_value={'status': 'unknown'})
        with patch.object(self.ctl, '_wait_for_question') as wait:
            self.assertIsNone(self.ctl.repair_question(self.draft, now=900))
            wait.assert_not_called()
        self.assertFalse(self.ctl.last_assistant_message)

    def test_later_duty_blocks_completion_without_correlated_receipt(self):
        record = self.ctl.evidence.add('official-user', 'Change my delivery.')
        self.ctl.bindings['operation-call'] = {'goal': 'delivery', 'effective': {'name': 'change_delivery'},
            'later_obligations': {'P2': {'stage':'receipt','quote':'Review the receipt after submission.',
                                         'ref':self.ctl.policy_ref}}}
        proposal = {'status':'proposed','goal_id':'delivery','policy_refs':[self.ctl.policy_ref],
                    'conditions':[{'id':'delivery','statement':'Recorded','evidence_refs':[record]}]}
        with self.assertRaisesRegex(PermissionError, 'Missing correlated receipt'):
            self.ctl._validate_plan('goal-completion', {}, proposal, now=900)

    def test_reply_after_reopening_wait_continues_original_goal(self):
        from contextlib import closing
        from test_question_lifecycle import Judge
        from test_episode_controller import JavaTask, ARM, HubGate
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            planner = Mock()
            def controller(task, hub):
                return EpisodeController(task, hub, planner, Judge(), RoutingPolicy('fixture', .3, .7,
                    'jev-latest', 'jev-1.14.0'), root/'control', {}, 'synthetic delivery policy')
            def gate():
                return closing(HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl',
                                       ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema'))
            with JavaTask(root/'task', 'fixture', 1000, 64) as task, gate() as hub:
                ctl = controller(task, hub)
                planner.complete.return_value = {'goals':[{'description':'delivery','quote':'Change delivery'}],
                                                 'existing_routes':[]}
                ctl.user('m1', 'Change delivery', now=900)
                goal = ctl.state(900)['goals'][0]['goal_id']
                planner.complete.return_value = {'clarification':{**self.candidate,'goal_id':goal}}
                ctl.review.extract = Mock(return_value={'completed_goal_ids':[], 'claims':[], 'comparison':None})
                ctl.review.check = Mock(return_value={'status':'allow'})
                ctl.claims.check = Mock(return_value={'status':'allow'})
                self.assertEqual(ctl.repair_question(self.draft, now=900), self.question)
                self.assertEqual(ctl.state(900)['goals'][0]['state'], 'waiting')
            with JavaTask(root/'task', 'fixture', 1000, 64) as task, gate() as hub:
                ctl = controller(task, hub)
                planner.complete.return_value = {'goals':[], 'existing_routes':[
                    {'goal_id':goal,'action':'respond','quote':'Standard delivery.'}]}
                result = ctl.user('m2', 'Standard delivery.', now=900)
                self.assertEqual(result['status'], 'ready')
                updated, = ctl.state(900)['goals']
                self.assertEqual((updated['goal_id'], updated['state'], updated['outcome']), (goal,'active','undetermined'))
                self.assertFalse(ctl.bindings)

    def test_unresolved_receipt_requires_new_official_facts_before_completion_review(self):
        from controlled_effects import digest
        from task_session import durable_json
        ref = self.ctl.evidence.add('official-tool', 'Receipt: delivery change accepted.')
        self.ctl.bindings['call'] = {'goal': 'delivery', 'effective': {'name':'change_delivery'},
            'later_obligations': {'P2': {'stage':'receipt','quote':'Verify the recorded update.',
                                         'ref':self.ctl.policy_ref}}}
        path = self.ctl.directory/('receipt-'+digest('call')+'.json')
        durable_json(path, {'receipt': {'status':'accepted'}, 'evidence_ref':ref, 'official_facts_at_receipt':[ref],
                            'receipt_obligations': {'conditions':{'P2':'unknown'}}})
        plan = {'status':'proposed','goal_id':'delivery','policy_refs':[self.ctl.policy_ref],
                'conditions':[{'id':'done','statement':'Updated','evidence_refs':[ref]}]}
        self.ctl.evidence.add('official-user', 'I think it is done.')
        with self.assertRaisesRegex(PermissionError, 'lacks a new official observation'):
            self.ctl._validate_plan('goal-completion', {}, plan, now=900)
        proof = self.ctl.evidence.add('official-tool', 'Readback: updated delivery on account A.')
        state = {'evidence':self.ctl.evidence.visible()}
        plan['conditions'][0]['evidence_refs'] = [proof]
        with patch.object(self.ctl.judgments, 'requirements', return_value={'status':'unknown',
                'conditions':{'obligation_0':'unknown'}}) as review:
            with self.assertRaisesRegex(PermissionError, 'obligation_0=unknown'):
                self.ctl._validate_plan('goal-completion', state, plan, now=900)
            self.assertIn('obligation_0', review.call_args.args[1])
        self.assertEqual(self.ctl._validate_plan('goal-completion', state, plan, now=900)['goal_id'], 'delivery')
