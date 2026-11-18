"""Seven synthetic input turns with real S2/Jev; no bank tools or benchmark tasks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from episode_controller import EpisodeController
from input_router import RoutingPolicy
from jev_provider import JevClient
from planner_client import PlannerClient
from task_session import ARM, ROOT, JavaTask, durable_json
import sys
sys.path.insert(0, str(ROOT/'shared/python'))
from eval_config import GATEWAY


def run(output):
    observations = []
    summary = {'scope': 'synthetic input routing; no native executor or bank operations',
               'official_episodes': 0, 'formal_comparison': False, 'automatic_retries': 0,
               'observations': observations, 'status': 'failed'}
    with JavaTask(output/'task', 'synthetic-input-probe', int(time.time())+1200, 64) as task:
        planner = PlannerClient(task, output/'planner', os.environ['OPENAI_API_KEY'], GATEWAY,
                                'volcengine/deepseek-v4.1-flash')
        controller = EpisodeController(task, None, planner,
            JevClient(os.environ['TYPESAFE_API_KEY'], timeout=120, long_context=True),
            RoutingPolicy('synthetic-proposed-input-check', .3, .7, 'jev-latest', 'jev-1.14.0'),
            output/'controller', {}, 'Synthetic input-routing exercise only. No banking action can be executed.')
        turns = [
            'Please replace my debit card.',
            'Also check the balance of my checking account.',
            'My name is Sofia. I do not know my user ID; can you locate my account with my name?',
            'Pause the debit card replacement for now; please continue the balance check.',
            'Resume the debit card replacement.',
            'Cancel the balance check. Keep the debit card replacement request open.',
            'What is the status of my balance request?',
        ]
        first = None
        try:
            for index, content in enumerate(turns):
                if index == 2:
                    controller.remember_assistant('To continue your existing services, please provide your user ID or identifying details.', kind='controller_clarification')
                route = controller.user('m'+str(index), content, now=int(time.time()))
                state = controller.state(int(time.time()))
                if index in (0, 1): first = [goal['goal_id'] for goal in state['goals']]
                passed = route['status'] == 'ready' and len(state['goals']) == (1 if index == 0 else 2)
                if first is not None: passed &= [goal['goal_id'] for goal in state['goals']] == first
                if index == 3: passed &= state['goals'][0]['state'] == 'waiting' and state['goals'][1]['state'] == 'active'
                if index == 4: passed &= all(g['state'] == 'active' for g in state['goals'])
                if index == 5: passed &= state['goals'][1]['outcome'] == 'cancelled' and state['goals'][0]['state'] == 'active'
                if index == 6: passed &= route['targets'] == [{'goal_id': first[1], 'action': 'query'}]
                observations.append({'turn': index+1, 'passed': bool(passed), 'status': route['status'],
                    'reason': route['reason'], 'targets': route['targets'],
                    'shared_context_used': bool(route['input_snapshot'].get('context_quote'))})
                if not passed: break
            if len(observations) == len(turns) and all(item['passed'] for item in observations): summary['status'] = 'passed'
        except Exception as error:
            summary['error_type'] = type(error).__name__
        summary['task'] = task.call('status', now=int(time.time()))
        summary['actual_s2_model'] = planner.actual_model
    durable_json(output/'result.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    durable_json(args.output/'manifest.json', {'scope': 'synthetic-proposed-input-check',
        'formal_comparison': False, 'planned_s2_requests': 7, 'planned_jev_requests': 7,
        'source_hashes': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in ARM.joinpath('python').glob('*.py')}})
    result = run(args.output)
    print(json.dumps({'status': result['status'], 'completed_turns': len(result['observations'])}))
    raise SystemExit(0 if result['status'] == 'passed' else 1)
