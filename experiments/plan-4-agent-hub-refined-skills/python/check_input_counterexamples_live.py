"""Real Jev rejects synthetic wrong input proposals; no S2 or banking tool calls."""
import argparse
import copy
import json
import os
from pathlib import Path

from input_router import InputRouter, RoutingPolicy
from jev_provider import JevClient
from task_session import durable_json


def cases():
    base = {'episode_id': 'synthetic-negative-probe', 'message_id': 'm', 'based_on_revision': 5,
        'source': 'official-user', 'kind': 'free_text', 'last_question': '', 'context_complete': True,
        'goals': [
            {'goal_id': 'card', 'episode_id': 'synthetic-negative-probe', 'description': 'Replace the debit card.', 'state': 'active', 'waiting_for': '', 'outcome': 'undetermined'},
            {'goal_id': 'balance', 'episode_id': 'synthetic-negative-probe', 'description': 'Check the checking account balance.', 'state': 'active', 'waiting_for': '', 'outcome': 'undetermined'}],
        'new_goal_proposals': []}
    specifications = [
        ('cancel-is-not-confirmation', 'Cancel the card replacement.', 'respond'),
        ('pause-is-not-cancellation', 'Pause the card replacement for now.', 'cancel'),
        ('ambiguous-target', 'Cancel it.', 'cancel'),
        ('wrong-target', 'Cancel the balance check.', 'cancel'),
        ('closed-goal-cannot-resume', 'Resume the card replacement.', 'resume'),
        ('invented-requirement', 'Use the address already on my account.', 'modify'),
        ('shared-context-cannot-cancel', 'Cancel the card replacement.', 'context'),
    ]
    for label, content, action in specifications:
        snapshot = copy.deepcopy(base); snapshot['content'] = content
        route = {'goal_id': 'card', 'action': action, 'quote': content}
        if action == 'respond':
            snapshot['goals'][0].update(state='waiting', waiting_for='May I replace your debit card using your current address?')
            snapshot['last_question'] = snapshot['goals'][0]['waiting_for']
        if label == 'closed-goal-cannot-resume': snapshot['goals'][0].update(state='closed', outcome='cancelled')
        if action == 'modify': route['description'] = 'Replace the debit card and waive all future account fees.'
        snapshot['route_proposals'] = [route]
        if label == 'shared-context-cannot-cancel':
            snapshot['route_proposals'] = []
            snapshot['context_quote'] = content
        yield label, snapshot


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    router = InputRouter(JevClient(os.environ['TYPESAFE_API_KEY'], timeout=120),
                         RoutingPolicy('synthetic-proposed-input-negatives', .3, .7, 'jev-latest', 'jev-1.14.0'))
    rows = []
    for label, snapshot in cases():
        try:
            result = router.interpret(snapshot)
            durable_json(args.output/(label+'.json'), result)
            rows.append({'case': label, 'passed': result['status'] == 'clarify',
                         'status': result['status'], 'reason': result['reason']})
        except Exception as error:
            rows.append({'case': label, 'passed': False, 'error_type': type(error).__name__})
    summary = {'status': 'passed' if all(row['passed'] for row in rows) else 'failed',
        'scope': 'seven synthetic semantic counterexamples only', 'formal_comparison': False,
        's2_calls': 0, 'bank_tool_calls': 0, 'automatic_retries': 0, 'results': rows}
    durable_json(args.output/'result.json', summary)
    print(json.dumps(summary))
    raise SystemExit(0 if summary['status'] == 'passed' else 1)
