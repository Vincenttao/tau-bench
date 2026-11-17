"""Run a pinned Chinese case plan, with one attempt per case in this run."""
import argparse
import fcntl
import getpass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import run_zh_e2e as base
from skill_assets import skill_release_identity

PLAN = Path(__file__).resolve().parent / 'plans/skill33-zh-single-round/plan.json'
TAG = 'TAU3_ZH_ROUND_ID'


def checked_plan(plan_path=PLAN):
    plan = json.loads(plan_path.read_text())
    cases = plan['cases']
    canonical = [case['canonical_task_id'] for case in cases]
    if not canonical or len(canonical) != len(set(canonical)) or len(canonical) != plan['task_count']:
        raise ValueError('The round requires the declared unique cases')
    if [case['order'] for case in cases] != sorted({case['order'] for case in cases}):
        raise ValueError('The original case order changed')
    if plan['conditions']['skill_release'] != skill_release_identity(plan['conditions']['skill_release']['version']):
        raise ValueError('Chinese Skill release differs from the round plan')
    if plan['conditions']['system_prompt_version'] != 'evidence-todo-v1':
        raise ValueError('Unexpected system prompt version')
    source = base.ROOT / plan['source_selection']['path']
    if base.sha(source) != plan['source_selection']['sha256']:
        raise ValueError('Original selected cohort changed')
    source_cases = json.loads(source.read_text())['cases']
    if any(case['order'] < 1 or case['order'] > len(source_cases) or
           source_cases[case['order'] - 1]['task_id'] != case['canonical_task_id']
           for case in cases):
        raise ValueError('Selected case order differs from the source')
    recovery = plan.get('recovery_from')
    if recovery:
        previous = base.ROOT / recovery['run_path']
        if base.sha(previous / 'manifest.json') != recovery['manifest_sha256'] or \
                base.sha(previous / 'progress.json') != recovery['progress_sha256']:
            raise ValueError('Original round evidence changed')
        old_manifest = json.loads((previous / 'manifest.json').read_text())
        old_statuses = {item['task_id']: json.loads((previous / 'episodes' / item['key'] / 'status.json').read_text())
                        for item in old_manifest['episodes']}
        if [item['task_id'] for item in old_manifest['episodes'] if old_statuses[item['task_id']]['status'] == 'scored'] != recovery['scored_tasks']:
            raise ValueError('Previously scored case set changed')
        if [item['task_id'] for item in old_manifest['episodes'] if old_statuses[item['task_id']]['status'] == 'process_error'] != [case['task_id'] for case in cases]:
            raise ValueError('Recovery case set differs from the original process errors')
        for case in cases:
            folder = previous / 'episodes' / case['task_id']
            if (folder / 'result.json').exists() or (folder / 'official-trajectory.jsonl').exists():
                raise ValueError('Recovery case already has model or scoring evidence: ' + case['task_id'])
            if 'argument --episode-index: invalid choice:' not in (folder / 'process.log').read_text():
                raise ValueError('Recovery case has a different process error: ' + case['task_id'])
    config, tasks = base.config_and_tasks(canonical_tasks=canonical, allowed_tasks=canonical)
    if config.model_dump(mode='json') != plan['run_config_template']:
        raise ValueError('Official language/run config differs from the plan')
    from tau2.multilingual.runtime import task_digest, pin_language_artifacts
    if pin_language_artifacts(config).artifact_pins.model_dump(mode='json') != plan['language_artifacts']:
        raise ValueError('Official Chinese assets differ from the plan')
    for case, task in zip(cases, tasks):
        if case['task_id'] != task.id or case['task_sha256'] != task_digest(task):
            raise ValueError('Official task binding differs: ' + case['canonical_task_id'])
    return plan


def tagged_processes(run_id):
    found = []
    marker = (TAG + '=' + run_id).encode()
    for folder in Path('/proc').iterdir():
        if not folder.name.isdigit():
            continue
        try:
            if marker in (folder / 'environ').read_bytes().split(b'\0'):
                state = (folder / 'stat').read_text().split(') ', 1)[1][0]
                if state != 'Z':
                    found.append(int(folder.name))
        except (OSError, ValueError, IndexError):
            continue
    return found


def mark_progress(output, manifest):
    statuses = []
    for item in manifest['episodes']:
        folder = output / 'episodes' / item['key']
        if (folder / 'status.json').exists():
            status = json.loads((folder / 'status.json').read_text())
        elif folder.exists():
            status = {'task_id': item['task_id'], 'status': 'started_unscored', 'reward': None}
        else:
            status = {'task_id': item['task_id'], 'status': 'not_started', 'reward': None}
        statuses.append(status)
    base.write(output / 'progress.json', {'planned': len(statuses), 'started': sum(x['status'] != 'not_started' for x in statuses),
        'scored': sum(x['status'] == 'scored' for x in statuses),
        'passed': sum(x['status'] == 'scored' and x['reward'] == 1 for x in statuses),
        'failed': sum(x['status'] == 'scored' and x['reward'] < 1 for x in statuses),
        'unscored_started': sum(x['status'] not in ('scored', 'not_started') for x in statuses),
        'not_started': sum(x['status'] == 'not_started' for x in statuses), 'statuses': statuses})
    return statuses


def run(output, resume, plan_path=PLAN):
    with (output / '.controller.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = base.verify(output)
        plan = checked_plan(plan_path)
        if manifest.get('plan_sha256') != base.sha(plan_path) or manifest['skill_release'] != plan['conditions']['skill_release']:
            raise ValueError('Prepared round differs from immutable plan')
        if len(manifest['episodes']) != plan['task_count']:
            raise ValueError('Prepared round has the wrong task count')
        saved = output / 'execution.json'
        if resume != saved.exists():
            raise ValueError('Use --execute for a new round or --resume for an already started round')
        if not os.getenv('OPENAI_API_KEY'):
            os.environ['OPENAI_API_KEY'] = getpass.getpass('API key (not saved): ')
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError('Missing API credential')
        if resume:
            execution = json.loads(saved.read_text())
        else:
            started = time.time()
            execution = {'started_at': started, 'deadline': started + manifest['batch_wall_time_seconds'],
                'run_id': os.urandom(16).hex(), 'plan_sha256': manifest['plan_sha256']}
            base.write(saved, execution)
        if execution['plan_sha256'] != manifest['plan_sha256']:
            raise ValueError('Started round plan differs')
        run_id = execution['run_id']
        for index, item in enumerate(manifest['episodes']):
            statuses = mark_progress(output, manifest)
            if statuses[index]['status'] != 'not_started':
                continue
            if tagged_processes(run_id):
                raise RuntimeError('Tagged episode processes remain alive; inspect before continuing')
            if time.time() >= execution['deadline']:
                print('STOP: batch deadline; unstarted cases remain', flush=True)
                break
            base.verify(output)
            folder = output / 'episodes' / item['key']
            folder.mkdir(parents=True, exist_ok=False)
            base.write(folder / 'attempt.json', {'task_id': item['task_id'], 'index': index,
                'started_at': time.time(), 'run_id': run_id})
            mark_progress(output, manifest)
            print(f"START {index + 1}/{len(manifest['episodes'])} {item['task_id']}", flush=True)
            worker_env = dict(os.environ, **{TAG: run_id, 'TAU3_ZH_ROUND_TASK': item['task_id']})
            with (folder / 'process.log').open('w') as log:
                proc = subprocess.Popen([sys.executable, str(base.Path(base.__file__)), '--output', str(output),
                    '--episode-index', str(index)], stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, env=worker_env)
                base.write(folder / 'worker.json', {'pid': proc.pid, 'started_at': time.time()})
                remaining = execution['deadline'] - time.time()
                try:
                    proc.wait(timeout=max(0.001, min(manifest['episode_timeout'], remaining)))
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait(timeout=5)
                    base.write(folder / 'status.json', {'task_id': item['task_id'], 'status': 'timeout', 'reward': None})
            for _ in range(5):
                if not tagged_processes(run_id):
                    break
                time.sleep(1)
            if tagged_processes(run_id):
                raise RuntimeError('Episode descendants remain alive; stop before next case')
            if not (folder / 'status.json').exists():
                base.write(folder / 'status.json', {'task_id': item['task_id'], 'status': 'process_error',
                    'reward': None, 'returncode': proc.returncode})
            status = json.loads((folder / 'status.json').read_text())
            mark_progress(output, manifest)
            print(json.dumps(status, ensure_ascii=False), flush=True)
            if status['status'] != 'scored':
                print('UNSCORED: preserve this attempt; continue only after isolated cleanup', flush=True)
        base.verify(output)
        print('ROUND_STATUS ' + json.dumps(mark_progress(output, manifest)[-1], ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--plan', type=Path, default=PLAN)
    args = parser.parse_args()
    if args.resume and not args.execute:
        parser.error('--resume requires --execute')
    base.configure_environment()
    plan_path = args.plan.resolve()
    plan = checked_plan(plan_path)
    output = args.output.resolve()
    if not output.exists():
        if args.resume:
            raise ValueError('Cannot resume a nonexistent run')
        canonical = tuple(case['canonical_task_id'] for case in plan['cases'])
        base.prepare(output, canonical_tasks=canonical, skill_version=plan['conditions']['skill_release']['version'],
            prompt_version='evidence-todo-v1', run_plan=plan, plan_path=plan_path, runner_path=Path(__file__))
    elif not args.execute:
        raise ValueError('Preparation requires a fresh output directory')
    if args.execute:
        run(output, args.resume, plan_path)


if __name__ == '__main__':
    main()
