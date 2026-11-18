from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from output_claims import ClaimGate


class Judge:
    class Policy: low=.3; high=.7
    policy = Policy()
    def __init__(self, values=None): self.values = values or {}; self.calls = 0
    def ask(self, state, questions, now=None):
        self.calls += 1
        return {key: self.values.get(key, .01 if key.endswith('_violated') else .99) for key in questions}, 'observation://fixture'


class OutputClaimTests(unittest.TestCase):
    def test_unsupported_completion_is_an_explicit_counterexample_not_a_task_finished_question(self):
        for value, expected in ((.01, 'allow'), (.5, 'unknown'), (.99, 'deny')):
            result = ClaimGate(Judge({'completion_violated': value}), lambda refs: refs).check(
                'Could you provide your name?', [], self.state(), now=900)
            self.assertEqual(result['status'], expected)

    def state(self):
        return {'task': {'goals': []}, 'evidence': {
            'receipt': {'source': 'official-tool', 'content': 'Dispute filed. Review pending.'},
            'user': {'source': 'official-user', 'content': 'Please approve my dispute.'}}}

    def test_supported_submission_can_pass_without_claiming_approval(self):
        gate = ClaimGate(Judge(), lambda refs: refs)
        self.assertEqual(gate.check('Your dispute was submitted.', [{'quote': 'Your dispute was submitted.',
            'kind': 'operation', 'evidence_refs': ['receipt']}], self.state(), now=900)['status'], 'allow')

    def test_claim_hidden_in_question_is_not_bypassed_by_empty_extraction(self):
        gate = ClaimGate(Judge({'claim_coverage': .01}), lambda refs: refs)
        self.assertEqual(gate.check('Your card was approved; what is your address?', [], self.state(), now=900)['status'], 'deny')

    def test_customer_text_or_task_state_cannot_prove_a_bank_operation(self):
        judge = Judge(); gate = ClaimGate(judge, lambda refs: refs)
        for ref in ('user', 'controller-state'):
            result = gate.check('Approved.', [{'quote': 'Approved.', 'kind': 'operation', 'evidence_refs': [ref]}], self.state(), now=900)
            self.assertNotEqual(result['status'], 'allow')
        self.assertEqual(judge.calls, 0)

    def test_missing_source_identifies_the_specific_unsupported_claim(self):
        gate = ClaimGate(Judge(), lambda refs: refs)
        result = gate.check('Delivery takes 7 days.', [{'quote': '7 days', 'kind': 'policy', 'evidence_refs': []}], self.state(), now=900)
        self.assertNotEqual(result['status'], 'allow')
        self.assertEqual(result['claim_failures'][0]['quote'], '7 days')
