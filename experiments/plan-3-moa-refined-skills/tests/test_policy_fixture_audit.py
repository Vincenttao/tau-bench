from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reports'))
from audit_policy_fixture import check_review


class PolicyFixtureAuditTest(unittest.TestCase):
    def test_coverage_exceptions_both_directions_and_missing_policy(self):
        policy = {'product-a': {'base_rate': '0.02', 'merchant_rates': {'merchant-b': '0.03'},
                                'source': 'fixture-policy-a'}}
        items = [
            {'id': 'x1', 'merchant': 'merchant-a', 'product': 'product-a', 'purchase': 1000,
             'credited': 15, 'submission_receipt': 'fixture-ack'},
            {'id': 'x2', 'merchant': 'merchant-b', 'product': 'product-a', 'purchase': 4000, 'credited': 125},
            {'id': 'x3', 'merchant': 'merchant-c', 'product': 'product-b', 'purchase': 7000, 'credited': 80},
        ]
        observed = [{'id': 'x1', 'policy': 'fixture-policy-a', 'difference': 5, 'status': 'submitted'},
                    {'id': 'x2', 'policy': 'fixture-policy-a', 'difference': -5, 'status': 'reviewed'},
                    {'id': 'x3', 'status': 'unresolved'}]
        self.assertEqual(check_review(items, policy, observed), [])
        self.assertEqual(check_review(items[::-1], policy, observed), [])
        changed = [dict(items[0], purchase=1500), *items[1:]]
        self.assertIn(('x1', 'policy or signed difference mismatch'), check_review(changed, policy, observed))
        missing = [observed[0], observed[0], dict(observed[2], difference=0)]
        self.assertCountEqual(check_review(items, policy, missing), [
            ('x1', 'duplicate or unknown item'), ('x2', 'missing item'), ('x3', 'no applicable policy')])
        self.assertIn(('x2', 'no submission receipt'), check_review(
            items, policy, [observed[0], dict(observed[1], status='submitted'), observed[2]]))
