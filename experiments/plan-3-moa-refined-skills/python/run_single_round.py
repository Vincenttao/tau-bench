"""Run a frozen MOA cohort serially. A started episode may never be replayed."""
import argparse
from datetime import datetime, timezone
import fcntl
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'shared/python'))
from diagnostic_run import prepare, execute, summarize, verify_inputs
from experiment_plan import sha

COHORT = ROOT / 'studies/banking-architecture-comparison/cohort.json'
SAMPLE = ARM / 'plans/remediation-sample.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def selection(sample):
    cohort = [case['task_id'] for case in read(COHORT)['cases']]
    if not sample:
        if len(set(cohort)) != 22 or len(cohort) != 22:
            raise ValueError('Invalid full cohort')
        return cohort
    config = read(SAMPLE)
    ids = config['task_ids']
    if (len(ids) != 3 or len(set(ids)) != 3 or not set(ids) <= set(cohort)
            or (config['trial'], config['seed'], config['max_starts_per_task']) != (0, 300, 1)):
        raise ValueError('Invalid sampled cohort')
    return ids


def prepare_batch(output, sample):
    ids = selection(sample)
    config_files = [COHORT, ROOT / 'studies/banking-architecture-comparison/contracts/business-ownership.json',
                    ARM / 'plan.json', ARM / 'moa-single-round-implementation-plan-20261118.md']
    if sample:
        config_files.extend([SAMPLE, ARM / 'moa-remediation-implementation-plan.md'])
    frozen = {}
    for source in config_files:
        name = source.relative_to(ROOT)
        destination = output / 'batch-freeze' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        frozen[str(name)] = sha(destination)
    rows = []
    for task in ids:
        prepare(3, task, output / task, True, 'deepseek-flash', 'https://api.deepseek.com')
        rows.append({'task_id': task, 'status': 'planned', 'starts': 0,
                     'manifest_sha256': sha(output / task / 'manifest.json')})
    state = {'schema_version': 2, 'batch_id': output.name, 'started_at': now(),
             'sample': sample, 'formal_comparison': False, 'owner': 'MOA evaluation',
             'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             'frozen_inputs': frozen, 'status': 'prepared', 'cases': rows}
    save(output / 'progress.json', state)
    (output / 'worktree-status.txt').write_text(subprocess.check_output(
        ['git', 'status', '--short'], cwd=ROOT, text=True))
    return state


def connection_cause(detail):
    # Classify only observed transport causes, never a wrapper named InternalServerError alone.
    text = detail.lower()
    for label, signatures in [('dns', ('unresolvedaddressexception', 'name resolution', 'getaddrinfo failed')),
                              ('tls', ('handshake operation timed out', 'sslhandshakeexception')),
                              ('stream_idle', ('stream_idle timeout',)),
                              ('connection', ('connecttimeout', 'connectexception', 'apiconnectionerror'))]:
        if any(marker in text for marker in signatures):
            return label
    return None


def infrastructure(directory, result):
    if result.get('status') != 'execution_error':
        return None
    episode = directory / 'episodes' / directory.name
    # Read exception causes only; no model content or credential-bearing messages go into the ledger.
    for path in [episode / 'exception.txt', *sorted((episode / 'moa').glob('*.stderr.log'))]:
        if path.is_file():
            trace = path.read_text(errors='replace')
            lines = (line for line in trace.splitlines()
                     if any(word in line.lower() for word in ('caused by:', 'exception:', 'error:', 'timeout:')))
            cause = connection_cause('\n'.join(lines))
            if cause:
                component = 'user_simulator' if 'user_simulator' in trace else path.name
                return {'component_log': path.name, 'component': component, 'cause': cause}
    cause = connection_cause(result.get('error_type', ''))
    return {'component_log': 'summary', 'cause': cause} if cause else None


def reconcile(output, row):
    directory = output / row['task_id']
    # Java hosts run in the episode workspace and may outlive the official worker.
    for process in Path('/proc').glob('[0-9]*'):
        try:
            cwd = (process / 'cwd').readlink()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if cwd.is_relative_to(directory):
            raise RuntimeError('An episode process still owns this workspace: ' + row['task_id'])
    summary = directory / 'summary.json'
    status = directory / 'episodes' / row['task_id'] / 'status.json'
    if summary.is_file():
        result = read(summary)
    elif status.is_file():
        result = summarize(read(status))
        save(summary, result)
    else:
        # An existing final Results file requires review if the official status write was interrupted.
        record = status.with_name('result.json')
        if record.is_file():
            sim, = read(record)['simulations']
            scored = (sim.get('reward_info') or {}).get('reward')
            if (scored is None or sim.get('task_id') != row['task_id'] or sim.get('trial') != 0
                    or not sim.get('termination_reason')):
                raise ValueError('Interrupted result has no verified terminal score; manual review required')
            result = summarize({'status': 'scored', 'task_id': row['task_id'], 'trial': sim['trial'],
                                'reward': scored, 'termination_reason': sim['termination_reason'],
                                'duration': sim.get('duration')})
        else:
            result = summarize({'status': 'execution_error', 'error_type': 'InterruptedEpisode'})
        save(summary, result)
    if result.get('task_id', row['task_id']) != row['task_id'] or result.get('trial', 0) != 0:
        raise ValueError('Terminal result identity mismatch')
    row.update(status=result['status'], result=result, infrastructure=infrastructure(directory, result), ended_at=now())


def run_locked(output, state, lock_fd, key):
    rows = state['cases']
    if state.get('schema_version') != 2:
        raise ValueError('Historical ledger has no resume lock provenance')
    if [r['task_id'] for r in rows] != selection(state['sample']):
        raise ValueError('Frozen selection changed')
    for name, digest in state['frozen_inputs'].items():
        if sha(ROOT / name) != digest or sha(output / 'batch-freeze' / name) != digest:
            raise ValueError('Frozen configuration changed: ' + name)
    manifests = []
    for row in rows:
        path = output / row['task_id'] / 'manifest.json'
        if sha(path) != row['manifest_sha256']:
            raise ValueError('Frozen manifest changed')
        manifest = read(path)
        if Path(manifest['output']) != path.parent or manifest['episodes'][0]['task_id'] != row['task_id']:
            raise ValueError('Manifest identity mismatch')
        verify_inputs(manifest)
        manifests.append(manifest)
        if row['status'] == 'started' and row['starts'] == 1:
            reconcile(output, row)
        if row['starts'] != int(row['status'] != 'planned'):
            raise ValueError('Invalid start count')
    # A deliberately resumed stop starts a new connectivity observation window.
    # A crash between recording a result and deciding to stop retains the prior streak.
    consecutive = 0
    previous = [row for row in rows if row['starts']]
    if state['status'] == 'stopped_infrastructure':
        state['connection_window_start'] = len(previous)
    else:
        window = previous[state.get('connection_window_start', 0):]
        for row in reversed(window):
            if not row.get('infrastructure'):
                break
            consecutive += 1
        if window and (consecutive >= 2 or window[-1].get('result', {}).get('error_type') in
                         ('AuthenticationError', 'RateLimitError', 'MemoryError')):
            state.update(status='stopped_infrastructure', ended_at=now())
            save(output / 'progress.json', state)
            return
    state.update(status='running', pid=os.getpid())
    save(output / 'progress.json', state)
    for row, manifest in zip(rows, manifests):
        if row['starts']:
            continue
        directory = Path(manifest['output'])
        for name, digest in state['frozen_inputs'].items():
            if sha(ROOT / name) != digest:
                raise ValueError('Configuration changed before start: ' + name)
        if sha(directory / 'manifest.json') != row['manifest_sha256']:
            raise ValueError('Manifest changed before start')
        verify_inputs(manifest)
        row.update(status='started', starts=1, started_at=now())
        save(output / 'progress.json', state)
        print(json.dumps({'event': 'start', 'task': row['task_id']}), flush=True)
        try:
            result = execute(manifest, key, batch_lock_fd=lock_fd)
        except Exception as error:
            result = summarize({'status': 'execution_error', 'error_type': type(error).__name__})
            save(directory / 'summary.json', result)
        cause = infrastructure(directory, result)
        consecutive = consecutive + 1 if cause else 0
        row.update(status=result['status'], result=result, infrastructure=cause, ended_at=now())
        save(output / 'progress.json', state)
        print(json.dumps({'event': 'end', 'task': row['task_id'], 'status': row['status'],
                          'reward': result.get('reward'), 'infrastructure': cause}), flush=True)
        if result.get('error_type') in ('AuthenticationError', 'RateLimitError', 'MemoryError') or consecutive >= 2:
            state['status'] = 'stopped_infrastructure'
            break
    else:
        state['status'] = 'finished'
    state['ended_at'] = now()
    save(output / 'progress.json', state)
    print(json.dumps({'batch_terminal': state['status']}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--sample', dest='sample', action='store_true', default=True, help='Run the three remediation episodes (default)')
    mode.add_argument('--full-cohort', dest='sample', action='store_false', help='Explicitly request the historical 22-episode cohort')
    mode.add_argument('--resume', action='store_true', help='Continue the frozen cohort at the first unstarted task')
    args = parser.parse_args()
    output = args.output.resolve()
    if not args.resume:
        output.mkdir(parents=True, exist_ok=False)
    with (output / 'batch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        key = os.environ.get('DEEPSEEK_API_KEY') or getpass.getpass('DeepSeek credential: ')
        if not key:
            raise ValueError('Credential required')
        state = read(output / 'progress.json') if args.resume else prepare_batch(output, args.sample)
        run_locked(output, state, lock.fileno(), key)


if __name__ == '__main__':
    main()
