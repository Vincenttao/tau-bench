from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from response_review import ResponseReview


class Planner:
    def __init__(self, result): self.result = result
    def complete(self, purpose, context, schema): return self.result


class Judge:
    class Policy: low=.3; high=.7
    policy=Policy()
    def ask(self, state, questions, now=None):
        return {k: (.99 if k != 'comparison_needed' else (.99 if state['proposal']['comparison'] else .01)) for k in questions}, 'synthetic-observation'


class ResponseReviewTests(unittest.TestCase):
    def test_plain_question_needs_no_unused_numeric_extraction_judgment(self):
        class QuestionJudge(Judge):
            def ask(self, state, questions, now=None):
                return {key: {'comparison_needed': .01, 'completion_declarations_complete': .99,
                              'extraction_faithful': .5}[key] for key in questions}, 'synthetic-observation'
        review = ResponseReview(Planner({'completed_goal_ids': [], 'comparison': None}), QuestionJudge())
        self.assertEqual(review.check('What is your name?', {'task': {'goals': []}}, now=900)['status'], 'allow')

    def proposal(self):
        return {'completed_goal_ids': [], 'comparison': {
            'candidates': [{'id': 'A', 'values': {'limit': 100000, 'fee': 0}, 'units': {'limit': 'USD', 'fee': 'USD/year'}},
                           {'id': 'B', 'values': {'limit': 200000, 'fee': 50}, 'units': {'limit': 'USD', 'fee': 'USD/year'}}],
            'requirements': [{'field': 'limit', 'op': 'ge', 'value': 100000, 'unit': 'USD'}],
            'preferences': [{'field': 'fee', 'direction': 'min'}], 'selected_id': 'A'}}

    def test_correct_boundary_and_lowest_fee_are_verified_in_code(self):
        review = ResponseReview(Planner(self.proposal()), Judge())
        self.assertEqual(review.check('Recommend A.', {'task': {'goals': []}}, now=900)['status'], 'allow')
        bad = self.proposal(); bad['comparison']['selected_id'] = 'B'
        self.assertEqual(ResponseReview(Planner(bad), Judge()).check('Recommend B.', {'task': {'goals': []}}, now=900)['status'], 'deny')

    def test_unfinished_goal_and_mismatched_units_cannot_be_declared_complete(self):
        data = {'completed_goal_ids': ['g1'], 'comparison': None}
        state = {'task': {'goals': [{'goal_id': 'g1', 'outcome': 'undetermined'}]}}
        self.assertEqual(ResponseReview(Planner(data), Judge()).check('Done.', state, now=900)['status'], 'deny')
        data = self.proposal(); data['comparison']['candidates'][0]['units']['limit'] = 'EUR'
        self.assertEqual(ResponseReview(Planner(data), Judge()).check('Recommend A.', state, now=900)['status'], 'unknown')
