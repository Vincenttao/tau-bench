import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from input_proposals import normalize_context_routes


class InputProposalTests(unittest.TestCase):
    def proposal(self):
        return {'goals': [], 'existing_routes': [
            {'goal_id': 'g', 'action': 'context', 'quote': 'My income is 180000.'},
            {'goal_id': 'g', 'action': 'context', 'quote': 'I already have a subscription.'}]}

    def test_compatible_context_spans_merge_without_changing_the_original_or_granting_an_action(self):
        source = self.proposal(); original = copy.deepcopy(source)
        content = 'My income is 180000. I already have a subscription.'
        result = normalize_context_routes(content, source)
        self.assertEqual(source, original)
        self.assertEqual(result['existing_routes'], [{'goal_id': 'g', 'action': 'context', 'quote': content}])
        self.assertEqual(result['goals'], [])

    def test_fabricated_quote_or_conflicting_action_is_not_discarded(self):
        content = 'My income is 180000. I already have a subscription.'
        for key, value in [('quote', 'Never said'), ('action', 'cancel'), ('action', 'modify')]:
            source = self.proposal(); source['existing_routes'][1][key] = value
            self.assertEqual(normalize_context_routes(content, source), source)

    def test_repeated_confirmations_or_new_requests_are_not_coalesced(self):
        source = self.proposal()
        for route in source['existing_routes']: route['action'] = 'respond'
        self.assertEqual(normalize_context_routes('My income is 180000. I already have a subscription.', source), source)

    def test_candidate_bound_is_not_bypassed_by_coalescing(self):
        source = self.proposal(); source['existing_routes'] = [source['existing_routes'][0]]*33
        self.assertEqual(normalize_context_routes('My income is 180000.', source), source)
