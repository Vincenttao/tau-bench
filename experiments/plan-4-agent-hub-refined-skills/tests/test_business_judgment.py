from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from business_judgment import BusinessJudge, parse_credit_dispute_receipt
from controlled_effects import digest
from input_router import RoutingPolicy


class BusinessJudgmentTests(unittest.TestCase):
    def test_source_labels_reach_semantic_judgment_without_becoming_policy(self):
        class Client:
            def ask(self, request):
                self.request = request
                return {'model': 'jev-1.14.0', 'answers': {q: {'type': 'noul', 'noul': .99 if q.endswith('_supported') else .01}
                        for q in request['questions']}, 'usage': {'input_tokens': 1, 'output_tokens': 1}}
        client = Client()
        judge = BusinessJudge(client, RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'))
        judge.judge('episode', 'goal', {'episode': 'episode'}, 'rule',
            [{'id': 'request', 'statement': 'The customer asked for a dispute.', 'evidence_refs': ['user']}],
            [{'ref': 'user', 'episode_id': 'episode', 'goal_id': 'goal', 'source': 'official-user', 'content': 'Please dispute this charge.'}])
        self.assertEqual(client.request['questions']['c0_supported']['instructions']['evidence']['user']['source'], 'official-user')

    def test_supported_condition_allows_missing_evidence_is_unknown(self):
        class Client:
            def ask(self, request):
                return {'model': 'jev-1.14.0', 'answers': {q: {'type': 'noul', 'noul': .99 if q.endswith('_supported') else .01}
                        for q in request['questions']}, 'usage': {'input_tokens': 1, 'output_tokens': 1}}
        judge = BusinessJudge(Client(), RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'))
        payload = {'episode': 'episode', 'operation': 'tool', 'arguments': {}}
        evidence = [{'ref': 'public:policy', 'episode_id': 'episode', 'goal_id': 'goal', 'content': 'Synthetic policy: confirmation is required.'}]
        conditions = [{'id': 'consent', 'statement': 'User explicitly confirmed this operation.', 'evidence_refs': ['public:policy']}]
        result = judge.judge('episode', 'goal', payload, 'fixture-rule', conditions, evidence)
        self.assertEqual(result['status'], 'allow')
        self.assertEqual(result['payload_hash'], digest(payload))
        self.assertEqual(judge.judge('episode', 'goal', payload, 'fixture-rule', conditions, [])['status'], 'unknown')
        evidence[0]['episode_id'] = 'wrong'
        with self.assertRaises(ValueError): judge.judge('episode', 'goal', payload, 'fixture-rule', conditions, evidence)

    def test_official_submission_is_accepted_not_approved_and_errors_not_success(self):
        text = 'Credit card transaction dispute filed successfully. A case has been opened and will be reviewed within 10 business days.\n\nExecuted: file_credit_card_transaction_dispute_4829\nDispute ID: synthetic-id\nTransaction: synthetic-tx'
        result = parse_credit_dispute_receipt(text)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['request_id'], 'synthetic-id')
        self.assertEqual(parse_credit_dispute_receipt('Error: missing')['status'], 'rejected')
        self.assertEqual(parse_credit_dispute_receipt('looks fine')['status'], 'unknown')
