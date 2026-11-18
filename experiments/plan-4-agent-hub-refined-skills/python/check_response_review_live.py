"""Fixed synthetic response classification/numeric checks; no bank tools or retries."""
import argparse
import json
import os
from pathlib import Path
import time
from input_router import RoutingPolicy
from jev_provider import JevClient
from planner_client import PlannerClient
from response_review import ResponseReview
from runtime_guards import JudgmentService
from task_session import durable_json


class Budget:
    def __init__(self): self.calls = 0
    def call(self, method, **values):
        if method != 'charge' or self.calls >= 24: raise RuntimeError('Synthetic request budget reached')
        self.calls += 1
        return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    task = Budget()
    planner = PlannerClient(task, args.output/'planner', os.environ['OPENAI_API_KEY'],
        os.environ['OPENAI_BASE_URL'], 'volcengine/deepseek-v4.1-flash')
    policy = RoutingPolicy('synthetic-response-surface', .3, .7, 'jev-latest', 'jev-1.14.0')
    review = ResponseReview(planner, JudgmentService(JevClient(os.environ['TYPESAFE_API_KEY']), task,
        args.output/'judgments', policy))
    goals = [{'goal_id': name, 'description': description, 'state': 'active', 'outcome': 'undetermined'} for name, description in [
        ('dispute', 'Refund the unauthorized charge.'), ('replace', 'Replace the card with a new number.'),
        ('limit', 'Increase the credit limit by $4000.')]]
    state = {'task': {'goals': goals}, 'evidence': {'guide': {'source': 'official-policy',
        'content': 'Unrelated product table: A has maximum limit $100000 and $0 annual fee; B has maximum limit $200000 and $50 annual fee. Prefer the lowest annual fee when the required possible limit is met.'}},
        'last_question': '', 'last_assistant_message': ''}
    recommendation = {'task': {'goals': [{'goal_id': 'recommend', 'description':
        'Recommend the lowest annual fee card whose possible maximum credit limit is at least $100000.',
        'state': 'closed', 'outcome': 'success'}]}, 'evidence': state['evidence']}
    cases = [('identity-question-with-numeric-policy',
        'To verify your identity, please provide your full name plus any two of your date of birth, email, phone number or mailing address.', state, True),
        ('unfinished-question', 'Your requests are not yet complete. What is your full name?', state, True),
        ('false-all-complete', 'All three requests have been completed successfully.', state, False),
        ('correct-low-fee', 'I recommend A: its possible maximum limit is $100000 and annual fee is $0. B has a $200000 maximum and $50 annual fee. Both meet your required possible limit, and A has the lowest annual fee.', recommendation, True),
        ('incorrect-high-fee', 'I recommend B for its higher $200000 maximum credit limit despite its $50 annual fee. A offers $100000 and charges $0, so both meet your required possible limit.', recommendation, False)]
    rows = []
    for label, content, visible, expected in cases:
        try:
            result = review.check(content, visible, now=int(time.time()))
            rows.append({'case': label, 'passed': (result['status'] == 'allow') == expected,
                'status': result['status'], 'reason': result['reason']})
            durable_json(args.output/(label+'.json'), {'content': content, 'visible_state': visible, 'result': result})
        except Exception as error:
            rows.append({'case': label, 'passed': False, 'error_type': type(error).__name__})
    summary = {'status': 'passed' if all(row['passed'] for row in rows) else 'failed',
        'scope': 'five synthetic response-surface and numeric checks only', 'formal_comparison': False,
        'inference_calls': task.calls, 'bank_calls': 0, 'automatic_retries': 0, 'results': rows}
    durable_json(args.output/'result.json', summary); print(json.dumps(summary))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__': raise SystemExit(main())
