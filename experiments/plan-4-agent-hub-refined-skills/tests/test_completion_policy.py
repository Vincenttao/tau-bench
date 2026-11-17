from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from completion_policy import permits_completion


class CompletionPolicyTests(unittest.TestCase):
    def test_acceptance_is_only_enough_for_explicit_submission_boundary(self):
        self.assertTrue(permits_completion(['accepted'], 'submission'))
        self.assertFalse(permits_completion(['accepted'], 'final_effect'))
        self.assertFalse(permits_completion(['accepted'], 'information'))
        for status in ('pending', 'unknown', 'rejected'):
            self.assertFalse(permits_completion([status], 'submission'))

    def test_success_requires_no_remaining_nonterminal_operations(self):
        self.assertTrue(permits_completion(['succeeded'], 'final_effect'))
        self.assertFalse(permits_completion(['succeeded', 'unknown'], 'final_effect'))
        self.assertTrue(permits_completion([], 'information'))
        with self.assertRaises(ValueError): permits_completion(['succeeded'], 'invented')
