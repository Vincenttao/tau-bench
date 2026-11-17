"""One immutable development episode; never enters the formal comparison cohort."""
import argparse
import getpass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from eval_config import GATEWAY
from experiment_plan import ROOT, read, sha, validate
from process_tree import terminate_tree
from skill_assets import skill_release_identity

ARMS = {
    1: 'plan-1-deepagent-original-skills',
    2: 'plan-2-deepagent-refined-skills',
    3: 'plan-3-moa-refined-skills',
    4: 'plan-4-agent-hub-refined-skills',
}


def build_manifest(arm, task_id, runtime_pilot=False):
    if arm not in ARMS:
        raise ValueError('Unknown arm')
    directory = ROOT / 'experiments' / ARMS[arm]
    preparation = validate(directory)
    plan = read(directory / 'plan.json')
    cohort = read(ROOT / 'studies/banking-architecture-comparison/cohort.json')
    selected = next((c for c in cohort['cases'] if c['task_id'] == task_id), None)
    if selected is None:
        raise ValueError('Task is not in the selected cohort')
    if runtime_pilot and arm not in (3, 4):
        raise ValueError('Runtime pilots are available only for partial MOA/Hub integrations')
    if arm in (3, 4) and not runtime_pilot:
        raise NotImplementedError('Required architecture runtime is not integrated: ' + ARMS[arm])
    return {
        'schema_version': 1, 'purpose': 'development-diagnostic', 'formal_comparison': False,
        'arm_id': ARMS[arm], 'driver': {3: 'moa-pilot', 4: 'hub-read-pilot'}[arm] if runtime_pilot else 'deepagent',
        'full_architecture_ready': False,
        'model': plan['model_profile']['request_model'],
        'api_base': GATEWAY, 'language': plan['comparison_language'],
        'system_prompt_version': plan['system_prompt_version'],
        'limits': plan['limits'], 'skill_release': skill_release_identity(plan['skill_release']),
        'preparation': preparation, 'benchmark_commit': cohort['benchmark_commit'],
        'episodes': [{'key': task_id, 'domain': 'banking_knowledge', 'task_id': task_id,
                      'task_sha256': selected['task_file_sha256'], 'trial': 0, 'seed': selected['seed']}],
    }


def prepare(arm, task_id, output, runtime_pilot=False):
    manifest = build_manifest(arm, task_id, runtime_pilot)
    output = Path(output).resolve()
    manifest['output'] = str(output)
    # Capture source and class identities; never capture environment variables.
    files = list((ROOT / 'shared/python').glob('*.py'))
    files += list((ROOT / 'shared/java/src').rglob('*.java'))
    files += list((ROOT / 'shared/java/target/classes').rglob('*.class'))
    files += [ROOT / 'shared/java/run-deepagent.sh', ROOT / 'shared/java/pom.xml', ROOT / 'shared/java/classpath.txt']
    if runtime_pilot:
        directory = ROOT / 'experiments' / ARMS[arm]
        files += list((directory / 'python').glob('*.py'))
        files += list((directory / 'java/src').rglob('*.java'))
        files += list((directory / 'java/patches').glob('*'))
        files += list((directory / 'java/target/classes').rglob('*.class'))
        files += list((directory / 'go').rglob('*.go'))
        files += [p for p in (directory / 'go').glob('go.*') if p.is_file()]
        files += [p for p in (directory / 'go/target').glob('banking-gate') if p.is_file()]
        files += list((directory / 'go').glob('*.json'))
        files += list((directory / 'go').glob('*.py'))
        files += list((directory / 'go').glob('*.sh'))
    manifest['implementation_files'] = {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}
    classpath = ROOT / 'shared/java/classpath.txt'
    manifest['dependency_files'] = {name: sha(Path(name)) for name in classpath.read_text().strip().split(os.pathsep)}
    output.mkdir(parents=True, exist_ok=False)
    for path in files:
        target = output / 'freeze-sources' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def summarize(status):
    reward = status.get('reward') if status.get('status') == 'scored' else None
    return {**status, 'business_pass': None if reward is None else reward == 1,
            'formal_comparison': False,
            'architecture_acceptance': 'not-yet-evaluated'}


def execution_exit_code(result):
    return 0 if result.get('status') == 'scored' and result.get('architecture_acceptance') == 'passed' else 1


def verify_inputs(manifest, root=ROOT):
    for name, expected in manifest['implementation_files'].items():
        if sha(Path(root) / name) != expected:
            raise ValueError('Prepared implementation changed: ' + name)
    for name, expected in manifest.get('dependency_files', {}).items():
        if sha(Path(name)) != expected:
            raise ValueError('Prepared dependency changed: ' + name)


def execute(manifest, key):
    if not key:
        raise ValueError('OPENAI_API_KEY is required')
    verify_inputs(manifest)
    output = Path(manifest['output'])
    python = ROOT / '.venv312/bin/python'
    command = ROOT / 'shared/java/run-deepagent.sh'
    if not python.exists() or not (command.parent / 'target/classes/eval/DeepAgentBridge.class').exists():
        raise RuntimeError('Build Java bridge and install pinned benchmark environment first')
    env = os.environ.copy()
    env.update(OPENAI_API_KEY=key, JAVA_AGENT_COMMAND='bash ' + shlex.quote(str(command)))
    # No credential appears in argv, manifest, or emitted status.
    with (output / 'supervisor.log').open('w') as log:
        proc = subprocess.Popen([str(python), str(ROOT / 'shared/python/run_episode.py'),
                                 '--manifest', str(output / 'manifest.json')],
                                env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            proc.wait(timeout=manifest['limits']['episode_timeout_seconds'])
        except subprocess.TimeoutExpired:
            terminate_tree(proc)
            (output / 'supervisor-status.json').write_text(json.dumps({'status': 'deadline'}))
        except BaseException:
            terminate_tree(proc)
            (output / 'supervisor-status.json').write_text(json.dumps({'status': 'cancelled'}))
            raise
    status_path = output / 'episodes' / manifest['episodes'][0]['key'] / 'status.json'
    if status_path.exists():
        status = read(status_path)
    elif (output / 'supervisor-status.json').exists():
        status = read(output / 'supervisor-status.json')
    else:
        status = {'status': 'execution_error', 'returncode': proc.returncode}
    result = summarize(status)
    from episode_acceptance import inspect_deepagent
    acceptance = inspect_deepagent(manifest) if manifest['driver'] == 'deepagent' else {
        'status': 'not-yet-evaluated', 'scope': 'Integration pilot; full MOA continuation or Hub write judgment is pending'}
    result['architecture_acceptance'] = acceptance['status']
    result['acceptance_scope'] = acceptance['scope']
    (output / 'architecture-acceptance.json').write_text(json.dumps(acceptance, indent=2) + '\n')
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', type=int, choices=list(ARMS), required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--prompt-key', action='store_true', help='Read secret without terminal echo')
    parser.add_argument('--runtime-pilot', action='store_true', help='Partial MOA/Hub integration diagnostic; cannot pass full architecture acceptance')
    args = parser.parse_args()
    manifest = prepare(args.arm, args.task, args.output, args.runtime_pilot)
    if not args.execute:
        print(json.dumps({'output': manifest['output'], 'execution_started': False}))
        return
    key = getpass.getpass('API credential: ') if args.prompt_key else os.getenv('OPENAI_API_KEY')
    result = execute(manifest, key)
    print(json.dumps(result))
    sys.exit(execution_exit_code(result))


if __name__ == '__main__':
    main()
