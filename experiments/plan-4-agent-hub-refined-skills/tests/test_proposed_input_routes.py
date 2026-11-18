import copy
from pathlib import Path
import sys
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'python'), str(Path(__file__).resolve().parent)]
from input_router import InputRouter, RoutingPolicy
from test_input_router import ScriptedClient


class ProposedInputRoutesTests(unittest.TestCase):
    def test_shared_identity_context_does_not_need_a_separate_business_goal_route(self):
        snapshot = self.snapshot(content='My name is Sofia. I do not know my user ID; can you look it up?')
        snapshot['goals'].append({'goal_id': 'g2', 'episode_id': 'episode', 'description': 'request credit increase', 'state': 'active', 'waiting_for': ''})
        snapshot['route_proposals'] = []
        snapshot['context_quote'] = snapshot['content']
        snapshot['last_assistant_message'] = 'Please provide your user ID or identifying details.'
        result = self.router(context_supported=.99).interpret(snapshot)
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['context_only'])
        self.assertEqual(result['targets'], [])
        self.assertEqual(len([name for name in result['request']['questions'] if name.startswith('context')]), 1)

    def test_closed_goal_outcome_is_available_for_status_query(self):
        snapshot = self.snapshot('query', 'What happened to the replacement?')
        snapshot['goals'][0].update(state='closed', outcome='cancelled')
        result = self.router().interpret(snapshot)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['targets'], [{'goal_id': 'g1', 'action': 'query'}])
        self.assertEqual(result['request']['state']['goals'][0]['outcome'], 'cancelled')

    def test_continue_already_active_goal_is_an_idempotent_context_update(self):
        result = self.router().interpret(self.snapshot('resume', 'Please continue the replacement.'))
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['context_only'])
        self.assertEqual(result['targets'], [])

    def snapshot(self, action='context', content='I still need a replacement card.'):
        return {'episode_id': 'episode', 'message_id': 'm', 'based_on_revision': 5,
            'source': 'official-user', 'kind': 'free_text', 'content': content,
            'last_question': '', 'context_complete': True,
            'goals': [{'goal_id': 'g1', 'episode_id': 'episode', 'description': 'replace card',
                       'state': 'active', 'waiting_for': ''}], 'new_goal_proposals': [],
            'route_proposals': [{'goal_id': 'g1', 'action': action, 'quote': content}]}

    def router(self, **values):
        client = ScriptedClient({'covered': .99, 'route0_supported': .99, **values})
        return InputRouter(client, RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'))

    def test_narrow_context_proposal_does_not_ask_unrelated_actions(self):
        router = self.router()
        snapshot = self.snapshot()
        self.assertNotIn('g0_modify', router.request(snapshot)['questions'])
        result = router.interpret(snapshot)
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['context_only'])
        self.assertEqual(result['targets'], [])

    def test_rejected_action_or_missing_coverage_never_progresses(self):
        for values in ({'route0_supported': .01}, {'route0_supported': .5}, {'covered': .01}):
            with self.subTest(values=values):
                self.assertEqual(self.router(**values).interpret(self.snapshot('cancel', 'Cancel the card replacement.'))['status'], 'clarify')

    def test_modify_preserves_the_specific_validated_goal_description(self):
        snapshot = self.snapshot('modify', 'Use the new address instead.')
        snapshot['route_proposals'][0]['description'] = 'Replace card using the newly supplied address.'
        result = self.router().interpret(snapshot)
        self.assertEqual(result['targets'], [{'goal_id': 'g1', 'action': 'modify',
            'description': 'Replace card using the newly supplied address.'}])

    def test_fabricated_quotes_and_foreign_targets_fail_before_inference(self):
        for key, value in (('quote', 'never said'), ('goal_id', 'foreign')):
            snapshot = self.snapshot(); snapshot['route_proposals'][0][key] = value
            router = self.router()
            with self.assertRaises(ValueError): router.interpret(snapshot)
            self.assertEqual(router.client.calls, [])
