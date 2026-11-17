"""Scripted observations test control logic; they do not measure Jev accuracy."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from input_router import InputRouter, RoutingPolicy
from jev_provider import JevError


class ScriptedClient:
    def __init__(self, values=None):
        self.values = values or {}
        self.calls = []
        self.model = 'jev-1.14.0'

    def ask(self, request):
        self.calls.append(copy.deepcopy(request))
        answers = {}
        for q, question in request['questions'].items():
            if question['type'] == 'choice':
                prefix = q.split('_', 1)[0]
                selected = max(('cancel', 'pause', 'resume'), key=lambda action: self.values.get(prefix+'_'+action, .01))
                answers[q] = {'type': 'choice', 'choice': selected,
                              'probabilities': {action: .99 if action == selected else .005 for action in ('cancel', 'pause', 'resume')}}
            else:
                value = self.values.get(q, .01)
                if q.endswith('_lifecycle_requested'):
                    prefix = q.split('_', 1)[0]
                    value = self.values.get(q, max(self.values.get(prefix+'_'+action, .01) for action in ('cancel', 'pause', 'resume')))
                answers[q] = {'type': 'noul', 'noul': value}
        return {'model': self.model,
                'answers': answers,
                'usage': {'input_tokens': 10, 'output_tokens': 2}}


class InputRouterTests(unittest.TestCase):
    def test_restatement_of_active_goal_is_not_a_duplicate_new_goal(self):
        snapshot = self.snapshot('I still need the card replacement.')
        snapshot['goals'][0].update(state='active', waiting_for='')
        snapshot['new_goal_proposals'] = []
        router, _ = self.router({'g0_reaffirm': .99})
        result = router.interpret(snapshot)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['targets'], [{'goal_id': 'g1', 'action': 'respond'}])
        self.assertEqual(result['new_goal_proposals'], [])

    def snapshot(self, content='Yes, use the same address. Also check my balance.'):
        return {'episode_id': 'episode', 'message_id': 'm2', 'based_on_revision': 5,
                'source': 'official-user', 'kind': 'free_text', 'content': content,
                'last_question': 'Use the same address?', 'context_complete': True,
                'goals': [{'goal_id': 'g1', 'episode_id': 'episode', 'description': 'replace card',
                           'state': 'waiting', 'waiting_for': 'address confirmation'}],
                'new_goal_proposals': [{'description': 'check balance', 'quote': 'check my balance'}]}

    def router(self, values=None):
        client = ScriptedClient({'covered': 0.99, **(values or {})})
        return InputRouter(client, RoutingPolicy('synthetic-test-only', 0.3, 0.7,
                                               'jev-latest', 'jev-1.14.0')), client

    def test_response_and_new_goal_both_preserved(self):
        router, client = self.router({'g0_respond': .99, 'has_new': .99, 'new0_supported': .99})
        proposal = router.interpret(self.snapshot())
        self.assertEqual(proposal['status'], 'ready')
        self.assertEqual(proposal['targets'], [{'goal_id': 'g1', 'action': 'respond'}])
        self.assertEqual(proposal['new_goal_proposals'][0]['description'], 'check balance')
        self.assertNotIn('goal_id', proposal['new_goal_proposals'][0])
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(proposal['based_on_revision'], 5)
        self.assertEqual(proposal['evidence_refs'], [{'message_id': 'm2', 'quote': self.snapshot()['content']}])

    def test_cancel_is_not_confirmation_and_conflict_clarifies(self):
        router, _ = self.router({'g0_cancel': .99})
        self.assertEqual(router.interpret(self.snapshot())['targets'][0]['action'], 'cancel')
        router, _ = self.router({'g0_cancel': .99, 'g0_respond': .99})
        self.assertEqual(router.interpret(self.snapshot())['status'], 'clarify')

    def test_uncertain_ambiguous_or_uncovered_never_ready(self):
        for values in ({'g0_cancel': .5}, {'ambiguous': .99}, {'covered': .01},
                       {'has_new': .99}, {'has_new': .99, 'new0_supported': .5}):
            with self.subTest(values=values):
                router, _ = self.router(values)
                self.assertEqual(router.interpret(self.snapshot())['status'], 'clarify')

    def test_closed_goal_query_allowed_but_resume_clarifies(self):
        snapshot = self.snapshot(); snapshot['goals'][0]['state'] = 'closed'
        router, _ = self.router({'g0_query': .99})
        self.assertEqual(router.interpret(snapshot)['targets'][0]['action'], 'query')
        router, _ = self.router({'g0_respond': .99})
        self.assertEqual(router.interpret(snapshot)['status'], 'clarify')

    def test_foreign_goal_and_fabricated_quote_rejected_before_api(self):
        for mutate in (lambda s: s['goals'][0].update(episode_id='other'),
                       lambda s: s['new_goal_proposals'][0].update(quote='not in message'),
                       lambda s: s.update(reference_actions=['hidden']),
                       lambda s: s.update(source='tool')):
            snapshot = self.snapshot(); mutate(snapshot)
            router, client = self.router()
            with self.assertRaises(ValueError): router.interpret(snapshot)
            self.assertEqual(client.calls, [])

    def test_incomplete_context_clarifies_without_inference(self):
        snapshot = self.snapshot(); snapshot['context_complete'] = False
        router, client = self.router()
        self.assertEqual(router.interpret(snapshot)['status'], 'clarify')
        self.assertEqual(client.calls, [])

    def test_model_drift_and_missing_answers_are_provider_errors(self):
        router, client = self.router(); client.model = 'unexpected'
        with self.assertRaises(JevError): router.interpret(self.snapshot())
        class Missing(ScriptedClient):
            def ask(self, request):
                result = super().ask(request); result['answers'].pop('covered'); return result
        router.client = Missing()
        with self.assertRaises(JevError): router.interpret(self.snapshot())

    def test_question_state_preserves_full_input_and_input_not_mutated(self):
        snapshot = self.snapshot(); original = copy.deepcopy(snapshot)
        router, client = self.router({'g0_respond': .99})
        proposal = router.interpret(snapshot)
        self.assertEqual(snapshot, original)
        self.assertEqual(client.calls[0]['state']['content'], snapshot['content'])
        self.assertEqual(proposal['raw_response']['usage']['input_tokens'], 10)
        self.assertEqual(proposal['policy_id'], 'synthetic-test-only')
        snapshot['content'] = 'changed'
        self.assertNotEqual(proposal['input_snapshot']['content'], snapshot['content'])

    def test_no_business_action_is_explicit_and_not_a_goal(self):
        router, _ = self.router({'no_business': .99})
        result = router.interpret(self.snapshot())
        self.assertEqual(result['status'], 'no_business_action')
        self.assertEqual(result['targets'], [])

    def test_policy_requires_ordered_probabilities(self):
        for low, high in ((.7, .3), (-.1, .7), (.3, 1.1), (True, .7)):
            with self.assertRaises(ValueError): RoutingPolicy('test', low, high, 'jev-latest', 'jev-1.14.0')

    def test_pause_is_distinct_from_cancel(self):
        router, _ = self.router({'g0_pause': .99})
        self.assertEqual(router.interpret(self.snapshot())['targets'][0]['action'], 'pause')

    def test_threshold_boundaries_remain_unknown(self):
        for value in (.3, .7):
            router, _ = self.router({'g0_respond': value})
            self.assertEqual(router.interpret(self.snapshot())['status'], 'clarify')

    def test_provider_error_has_no_fallback(self):
        router, client = self.router()
        def broken(request):
            client.calls.append(request)
            raise JevError('synthetic failure')
        client.ask = broken
        with self.assertRaises(JevError): router.interpret(self.snapshot())
        self.assertEqual(len(client.calls), 1)

    def test_malformed_typed_answer_is_provider_error(self):
        router, client = self.router()
        original = client.ask
        def malformed(request):
            response = original(request); response['answers']['covered'] = []
            return response
        client.ask = malformed
        with self.assertRaises(JevError): router.interpret(self.snapshot())

    def test_lifecycle_choice_requires_an_explicit_applicable_request(self):
        router, client = self.router({'g0_respond': .99})
        request = router.request(self.snapshot())
        self.assertEqual(request['questions']['g0_lifecycle_action']['type'], 'choice')
        self.assertEqual(router.interpret(self.snapshot())['targets'][0]['action'], 'respond')
