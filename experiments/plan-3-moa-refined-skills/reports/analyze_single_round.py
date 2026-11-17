"""Offline official DB replay and evidence extraction, with all network disabled."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'


def no_network(*args, **kwargs):
    raise RuntimeError('Network disabled for offline review')


socket.create_connection = no_network
socket.socket.connect = no_network
from loguru import logger
logger.remove()
from tau2.data_model.simulation import Results
from tau2.domains.banking_knowledge.environment import get_environment
from tau2.runner.build import _derive_read_log_allowlist


def differences(actual, expected, path=''):
    if isinstance(actual, dict) and isinstance(expected, dict):
        rows = []
        for key in sorted(actual.keys() | expected.keys()):
            if key not in actual or key not in expected:
                rows.append({'path': path + '/' + key, 'actual': actual.get(key), 'expected': expected.get(key)})
            else:
                rows.extend(differences(actual[key], expected[key], path + '/' + key))
        return rows
    return [] if actual == expected else [{'path': path, 'actual': actual, 'expected': expected}]


def inspect(run, task_id):
    episode = run / task_id / 'episodes' / task_id
    path = episode / 'result.json'
    summary = run / task_id / 'summary.json'
    evidence = {'task_id': task_id, 'summary': json.loads(summary.read_text()) if summary.exists() else None}
    if not path.exists() or (evidence['summary'] or {}).get('status') != 'scored':
        error = episode / 'exception.txt'
        evidence['exception'] = error.read_text() if error.exists() else None
        journal = episode / 'official-trajectory.jsonl'
        evidence['messages'] = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        return evidence
    results = Results.model_validate_json(path.read_text())
    task, sim = results.tasks[0], results.simulations[0]
    evidence.update(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    reward_info=sim.reward_info.model_dump(mode='json'),
                    task_purpose=task.description.model_dump(mode='json'),
                    reference_actions=[x.model_dump(mode='json') for x in task.evaluation_criteria.actions or []],
                    messages=[x.model_dump(mode='json') for x in sim.messages])
    try:
        kw = dict(retrieval_variant='bm25', task=task, read_log_allowlist=_derive_read_log_allowlist(task))
        actual, expected = get_environment(**kw), get_environment(**kw)
        initial = task.initial_state
        init = dict(initialization_data=initial.initialization_data if initial else None,
                    initialization_actions=initial.initialization_actions if initial else None)
        actual.set_state(**init, message_history=sim.messages, strict=True)
        expected.set_state(**init, message_history=(initial.message_history or []) if initial else [], strict=True)
        for action in task.evaluation_criteria.actions or []:
            expected.make_tool_call(tool_name=action.name, requestor=action.requestor, **action.arguments)
        evidence['replay'] = {'strict': True, 'agent_db_match': actual.get_db_hash() == expected.get_db_hash(),
                              'user_db_match': actual.get_user_db_hash() == expected.get_user_db_hash(),
                              'differences': differences(actual.tools.db.model_dump(), expected.tools.db.model_dump())}
    except Exception as error:
        evidence['replay'] = {'error_type': type(error).__name__, 'error': str(error)}
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    progress = json.loads((args.run / 'progress.json').read_text())
    index = []
    for row in progress['cases']:
        if row['status'] in ('planned', 'started'):
            continue
        task = row['task_id']
        data = inspect(args.run, task)
        messages = data.pop('messages', [])
        (args.output / (task + '-evidence.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        trace = [f'# {task} visible trace', '', 'Offline extraction; M numbers identify official message indices.', '']
        for i, message in enumerate(messages):
            trace += [f'## M{i:03d} {message["role"]}', '', message.get('content') or '', '']
            if message.get('tool_calls'):
                trace += ['```json', json.dumps(message['tool_calls'], ensure_ascii=False, indent=2), '```', '']
        (args.output / (task + '-trace.md')).write_text('\n'.join(trace))
        index.append({'task_id': task, 'summary': data['summary'], 'replay': data.get('replay')})
        print(task, 'reward', (data['summary'] or {}).get('reward'), 'diffs',
              len(data.get('replay', {}).get('differences', [])), flush=True)
    (args.output / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
