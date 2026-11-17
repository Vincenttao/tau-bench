"""Serial, immutable 22-case MOA diagnostic; never rerun a started case."""
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'shared/python'))
from diagnostic_run import prepare, execute, verify_inputs
from experiment_plan import sha


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    key = getpass.getpass('DeepSeek credential (not saved): ')
    if not key:
        raise ValueError('Credential required')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cohort = json.loads((ROOT / 'studies/banking-architecture-comparison/cohort.json').read_text())
    ids = [case['task_id'] for case in cohort['cases']]
    if len(ids) != 22 or len(set(ids)) != 22:
        raise ValueError('Expected exactly 22 distinct tasks')
    manifests = [prepare(3, task, output / task, True, 'deepseek-flash',
                         'https://api.deepseek.com') for task in ids]
    first = manifests[0]
    for manifest in manifests:
        if manifest['implementation_files'] != first['implementation_files']:
            raise ValueError('Implementation drift during preparation')
    paths = ['studies/banking-architecture-comparison/cohort.json',
             'studies/banking-architecture-comparison/contracts/business-ownership.json',
             'experiments/plan-3-moa-refined-skills/plan.json',
             'experiments/plan-3-moa-refined-skills/moa-single-round-implementation-plan-20261118.md']
    frozen = {name: sha(ROOT / name) for name in paths}
    for name in paths:
        target = output / 'batch-freeze' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    rows = [{'task_id': task, 'status': 'planned', 'starts': 0} for task in ids]
    state = {'batch_id': output.name, 'started_at': now(), 'pid': os.getpid(),
             'owner': 'Codex (execution and evidence review)', 'formal_comparison': False,
             'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             'frozen_inputs': frozen, 'status': 'running', 'cases': rows}
    save(output / 'progress.json', state)
    (output / 'worktree-status.txt').write_text(subprocess.check_output(
        ['git', 'status', '--short'], cwd=ROOT, text=True))
    consecutive_connections = 0
    for row, manifest in zip(rows, manifests):
        verify_inputs(manifest)
        if any(sha(ROOT / name) != digest for name, digest in frozen.items()):
            state['status'] = 'stopped_input_drift'
            break
        row.update(status='started', starts=1, started_at=now())
        save(output / 'progress.json', state)
        print(json.dumps({'event': 'start', 'task': row['task_id'], 'time': now()}), flush=True)
        try:
            result = execute(manifest, key)
        except Exception as error:
            # Never store exception messages that could contain credentials.
            result = {'status': 'execution_error', 'error_type': type(error).__name__}
        row.update(result=result, status=result.get('status', 'execution_error'), ended_at=now())
        save(output / 'progress.json', state)
        print(json.dumps({'event': 'end', 'task': row['task_id'], 'result': result}), flush=True)
        error = result.get('error_type', '')
        consecutive_connections = consecutive_connections + 1 if error in (
            'APIConnectionError', 'InternalServerError') else 0
        if error in ('AuthenticationError', 'RateLimitError', 'MemoryError') or consecutive_connections >= 2:
            state['status'] = 'stopped_infrastructure'
            break
    else:
        state['status'] = 'finished'
    state['ended_at'] = now()
    save(output / 'progress.json', state)
    print(json.dumps({'event': 'batch_terminal', 'status': state['status']}), flush=True)


if __name__ == '__main__':
    main()
