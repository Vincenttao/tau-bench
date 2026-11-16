"""Resume only the authorized P07 single round; never chain into repetitions."""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', type=Path, required=True)
    args = parser.parse_args()
    suite = args.suite.resolve()
    scope = json.loads((suite / 'single-round-scope.json').read_text())
    if scope.get('mode') != 'single_round' or scope.get('rounds_per_case') != 1:
        raise SystemExit('Explicit single-round scope required')
    freeze = json.loads((suite / 'freeze.json').read_text())
    os.environ['JAVA_AGENT_COMPLETION_TIMEOUT'] = str(freeze['core_completion_timeout_seconds'])
    os.environ['JAVA_AGENT_EVENT_TIMEOUT'] = str(freeze['event_timeout_seconds'])
    os.environ['OPENAI_MODEL'] = freeze['model']
    if freeze['token_limit'] is not None:
        raise SystemExit('Expected no token budget')
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = getpass.getpass('API key (not saved): ')
    if not os.environ['OPENAI_API_KEY']:
        raise SystemExit('Missing API key')
    record = {'pid': os.getpid(), 'started_at': time.time(), 'stage': 'P07',
              'mode': 'single_round', 'state': 'PREFLIGHT', 'child_pid': None,
              'P08': 'CANCELLED_BY_USER', 'goal_complete': False}
    write(suite / 'single-round-execution.json', record)
    # Capture only the gateway helper's sanitized output, never raw credentials/errors.
    check = subprocess.run([sys.executable, str(ROOT / 'python/check_gateway.py')],
                           cwd=ROOT, capture_output=True, text=True)
    (suite / 'single-round-gateway-check.log').write_text(check.stdout + check.stderr)
    if check.returncode:
        record.update(state='PREFLIGHT_FAILED', exit_code=check.returncode, finished_at=time.time())
        write(suite / 'single-round-execution.json', record)
        raise SystemExit('Gateway preflight failed; see sanitized log')
    print('Gateway preflight complete; starting P07 only.', flush=True)
    command = [sys.executable, str(ROOT / 'python/run_plan_stage.py'), '--stage', 'P07',
               '--suite', str(suite), '--resume', '--continue-reviewed-timeouts',
               '--continue-reviewed-core-errors']
    with (suite / 'single-round-controller.log').open('a') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        record.update(state='RUNNING', child_pid=child.pid)
        write(suite / 'single-round-execution.json', record)
        code = child.wait()
    record.update(state='CONTROLLER_COMPLETED' if code == 0 else 'CONTROLLER_ERROR',
                  exit_code=code, finished_at=time.time())
    write(suite / 'single-round-execution.json', record)
    from report_full_suite import report
    result = report(suite)
    pending = [row['case_id'] for row in result['rows']
               if row['status'] in ['NOT_STARTED', 'RUNNING_OR_UNKNOWN']]
    record['pending_primary_cases'] = pending
    record['primary_status_counts'] = result['status_counts']
    record['secondary_status_counts'] = [
        {'case_id': row['case_id'], 'status': row['status']}
        for row in result['retry_rows']]
    # Controller completion is execution evidence; final review remains separate.
    write(suite / 'single-round-execution.json', record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
