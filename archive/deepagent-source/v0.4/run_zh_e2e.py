"""Pinned official Chinese banking text E2E; planning is offline by default."""
import argparse
import getpass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
UPSTREAM = ROOT / '.deps/tau2-bench-v2-zh'
UPSTREAM_COMMIT = 'c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4'
EXPERIMENT = 'deepagent-todo-skill-mcp-v0.4'
CANONICAL_TASKS = ('task_003', 'task_054')
SKILL_VERSION = 'banking-evidence-guides'
SKILL_VERSIONS = ('banking-evidence-guides', '3.1.0', '3.2.0', '3.3.0')
PROMPT_VERSIONS = ('baseline-v1', 'evidence-todo-v1')
DEFAULT_PROMPT_VERSION = 'evidence-todo-v1'
sys.path.insert(0, str(ROOT / 'python'))
from eval_config import configure, GATEWAY, MODEL
from skill_assets import skill_release_identity, pin_manifest_skill


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def usage_event(response):
    # New SDK usage objects contain nested wrapper classes; only meter scalar totals.
    usage = response.get('usage') or {}
    return {'time': time.time(), 'model': response.get('model'),
            **{key: usage.get(key) for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}}


def configure_environment():
    os.environ.update(TAU2_DATA_DIR=str(UPSTREAM / 'data'),
                      LITELLM_LOCAL_MODEL_COST_MAP='True',
                      JAVA_AGENT_COMMAND='bash ' + str(ROOT / 'java/run-deepagent.sh'),
                      JAVA_AGENT_EVENT_TIMEOUT='1500',
                      JAVA_AGENT_COMPLETION_TIMEOUT='1200',
                      TAU3_SKILL_VERSION=SKILL_VERSION)
    model, base = configure()
    if (model, base) != (MODEL, GATEWAY):
        raise ValueError('This experiment requires the approved model and gateway')
    import tau2
    if not Path(tau2.__file__).resolve().is_relative_to(UPSTREAM):
        raise ValueError('Use .venv-tau2-v2/bin/python with the isolated upstream checkout')
    revision = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != UPSTREAM_COMMIT:
        raise ValueError('Upstream revision differs from the pinned Chinese experiment')
    subprocess.run(['git', '-C', str(UPSTREAM), 'diff', '--quiet', 'HEAD', '--', 'src', 'data'], check=True)


def config_and_tasks(saved=None, canonical_tasks=None, allowed_tasks=CANONICAL_TASKS):
    from tau2.data_model.simulation import TextRunConfig
    from tau2.multilingual.runtime import pin_language_artifacts
    from tau2.runner.helpers import select_run_tasks
    if saved:
        config = TextRunConfig.model_validate(saved)
    else:
        config = TextRunConfig(
            domain='banking_knowledge', language='zh', localize_db=True,
            pack_extension='banking-dates-v1', agent='tau3_java_zh', user='user_simulator',
            llm_agent='openai/' + MODEL, llm_user='openai/' + MODEL,
            llm_args_agent={'temperature': 0.0},
            llm_args_user={'temperature': 0.0, 'api_base': GATEWAY, 'timeout': 120, 'num_retries': 0},
            retrieval_config='bm25', seed=300, num_trials=1, max_steps=200, max_errors=10)
    loaded = pin_language_artifacts(config)
    mapping = {}
    for task_id, metadata in loaded.metadata.items():
        if metadata.canonical_task_id in allowed_tasks:
            if metadata.canonical_task_id in mapping:
                raise ValueError('Ambiguous official canonical task mapping')
            mapping[metadata.canonical_task_id] = task_id
    if set(mapping) != set(allowed_tasks):
        raise ValueError('Official language binding lacks a selected task')
    if saved:
        reverse = {value: key for key, value in mapping.items()}
        if not config.task_ids or any(key not in reverse for key in config.task_ids):
            raise ValueError('Frozen localized task selection differs')
        selected = tuple(reverse[key] for key in config.task_ids)
        if canonical_tasks is not None and tuple(canonical_tasks) != selected:
            raise ValueError('Frozen localized task selection differs')
    else:
        selected = tuple(CANONICAL_TASKS if canonical_tasks is None else canonical_tasks)
    if not selected or len(set(selected)) != len(selected) or any(key not in mapping for key in selected):
        raise ValueError('Choose unique canonical tasks from the declared diagnostic scope')
    expected = [mapping[key] for key in selected]
    config.task_ids = expected
    by_id = {task.id: task for task in select_run_tasks(config, loaded)}
    tasks = [by_id[key] for key in expected]
    return config, tasks


def register_agent(prompt_version=DEFAULT_PROMPT_VERSION):
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError('Unsupported system prompt version')
    from tau2.registry import registry
    from deepagent_java_agent import DeepAgentJavaAgent

    class ChineseJavaAgent(DeepAgentJavaAgent):
        def _init_extra(self):
            return {**super()._init_extra(), 'language': 'zh', 'system_prompt_version': prompt_version}

    # Upstream passes a policy with its official language guidance. Never forward task/answers.
    def factory(*, tools, domain_policy, llm, llm_args, **ignored):
        return ChineseJavaAgent(tools=tools, domain_policy=domain_policy, llm=llm, llm_args=llm_args)
    registry.register_agent_factory(factory, 'tau3_java_zh')


def prepare(output, canonical_tasks=CANONICAL_TASKS, prompt_version=DEFAULT_PROMPT_VERSION,
            skill_version=SKILL_VERSION, run_plan=None, plan_path=None, runner_path=None):
    if output.exists():
        raise ValueError('Planning requires a fresh output directory')
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError('Unsupported system prompt version')
    if skill_version not in SKILL_VERSIONS:
        raise ValueError('Unsupported Skill version for the Chinese diagnostic')
    skill_identity = skill_release_identity(skill_version)
    config, tasks = config_and_tasks(canonical_tasks=canonical_tasks, allowed_tasks=canonical_tasks)
    output.mkdir(parents=True)
    manifest = {
        'schema_version': 1, 'experiment_id': EXPERIMENT,
        'validation_kind': 'official-zh-banking-text-diagnostic-e2e-not-paired',
        'implementation': 'deepagent-todo-skill-mcp', 'language': 'zh',
        'model': MODEL, 'api_base': GATEWAY, 'api_protocol': 'chat_completions',
        'benchmark_commit': UPSTREAM_COMMIT, 'benchmark_version': '2.0.0',
        'skill_release': skill_identity,
        'system_prompt_version': prompt_version,
        'run_config': config.model_dump(mode='json'), 'seed': 300,
        'concurrency': 1, 'trials': 1, 'token_limit': None,
        'episode_timeout': 2400, 'max_hours': 1.5 if run_plan is None else 16,
        'output': str(output),
        'episodes': [{'task_id': task.id, 'canonical_task_id': canonical, 'key': task.id,
                      'domain': config.domain, 'trial': 0, 'seed': 300}
                     for canonical, task in zip(canonical_tasks, tasks)],
    }
    if run_plan is not None:
        manifest['plan_id'] = run_plan['plan_id']
        manifest['plan_sha256'] = sha(plan_path)
        manifest['batch_wall_time_seconds'] = run_plan['conditions']['batch_wall_time_seconds']
        manifest['episode_timeout'] = run_plan['conditions']['episode_timeout_seconds']
        manifest['validation_kind'] = f'official-zh-banking-text-{len(tasks)}-case-single-round'
        for item, planned in zip(manifest['episodes'], run_plan['cases']):
            item['order'] = planned['order']
            item['wave'] = planned['wave']
            item['category'] = planned['category']
            item['task_sha256'] = planned['task_sha256']
    write(output / 'manifest.json', manifest)
    write(output / 'resolved-tasks.json', [task.model_dump(mode='json') for task in tasks])
    packages = sorted({distribution.metadata['Name'] + '==' + distribution.version
                       for distribution in importlib.metadata.distributions()})
    (output / 'python-packages.txt').write_text('\n'.join(packages) + '\n')
    files = {}
    roots = (ROOT / 'python', ROOT / 'experiments/deepagent-todo-skill-mcp/python',
             ROOT / 'java/src', ROOT / 'java/target/classes',
             ROOT / 'experiments/deepagent-todo-skill-mcp/skills/releases' / skill_version,
             UPSTREAM / 'src', UPSTREAM / 'data')
    for folder in roots:
        for path in folder.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                files[str(path)] = sha(path)
    paths = [Path(__file__), ROOT / 'java/classpath.txt', ROOT / 'java/run-deepagent.sh',
             output / 'manifest.json', output / 'resolved-tasks.json', output / 'python-packages.txt']
    if run_plan is not None:
        paths.extend((plan_path, runner_path, ROOT / run_plan['source_selection']['path']))
    paths += [Path(p) for p in (ROOT / 'java/classpath.txt').read_text().strip().split(os.pathsep)]
    for path in paths:
        files[str(path)] = sha(path)
    for path in (ROOT / 'experiments/deepagent-todo-skill-mcp/v0.4/tests').glob('*.py'):
        files[str(path)] = sha(path)
    write(output / 'freeze.json', {'files': files, 'benchmark_commit': UPSTREAM_COMMIT})
    snapshot = output / 'freeze-sources'
    for name in files:
        path = Path(name)
        if path.is_relative_to(ROOT) and not path.is_relative_to(UPSTREAM) and path.suffix in ('.py', '.java', '.md', '.json') and not path.is_relative_to(output):
            target = snapshot / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    write(output / 'prepared.json', {'freeze_sha256': sha(output / 'freeze.json')})
    print(json.dumps({'status': 'prepared', 'tasks': [t.id for t in tasks], 'frozen_files': len(files)}, ensure_ascii=False), flush=True)


def verify(output):
    freeze = json.loads((output / 'freeze.json').read_text())
    for name, expected in freeze['files'].items():
        if sha(name) != expected:
            raise ValueError('Frozen file changed: ' + name)
    manifest = json.loads((output / 'manifest.json').read_text())
    pin_manifest_skill(manifest)
    return manifest


def episode(output, index):
    manifest = verify(output)
    allowed = tuple(item['canonical_task_id'] for item in manifest['episodes'])
    if not 0 <= index < len(allowed):
        raise ValueError('Episode index outside frozen plan')
    config, tasks = config_and_tasks(manifest['run_config'], allowed_tasks=allowed)
    task = tasks[index]
    folder = output / 'episodes' / task.id
    os.environ['JAVA_LOG_DIR'] = str(folder / 'java')
    from loguru import logger
    logger.remove()
    logger.add(str(folder / 'runner.log'), level='WARNING')
    register_agent(manifest.get('system_prompt_version', 'baseline-v1'))
    from tau2.utils import llm_utils
    original_completion = llm_utils.completion

    def metered_completion(*args, **kwargs):
        if kwargs.get('model') not in (MODEL, 'openai/' + MODEL):
            raise ValueError('Unexpected model route; do not silently replace an official judge')
        kwargs['api_base'] = GATEWAY
        result = original_completion(*args, **kwargs)
        with (folder / 'user-usage.jsonl').open('a') as stream:
            stream.write(json.dumps(usage_event(result)) + '\n')
        return result
    llm_utils.completion = metered_completion
    from tau2.runner import run_single_task, get_info
    from tau2.runner import batch as batch_module, simulation as simulation_module
    from tau2.data_model.simulation import Results
    from tau2.evaluator.evaluator import EvaluationType
    from java_agent import cleanup
    from deepagent_java_agent import close_facades
    captured = []
    original_evaluate = simulation_module.evaluate_simulation

    def observed_evaluate(*args, **kwargs):
        simulation = kwargs['simulation']
        captured.append(simulation)
        (folder / 'trajectory-unscored.json').write_text(simulation.model_dump_json(indent=2))
        return original_evaluate(*args, **kwargs)
    simulation_module.evaluate_simulation = observed_evaluate
    original_build = batch_module.build_orchestrator

    def observed_build(*args, **kwargs):
        orchestrator = original_build(*args, **kwargs)
        original_step, written = orchestrator.step, [0]
        def observed_step(*a, **kw):
            try:
                return original_step(*a, **kw)
            finally:
                messages = orchestrator.trajectory
                with (folder / 'official-trajectory.jsonl').open('a') as stream:
                    for message in messages[written[0]:]:
                        stream.write(message.model_dump_json() + '\n')
                written[0] = len(messages)
        orchestrator.step = observed_step
        return orchestrator
    batch_module.build_orchestrator = observed_build
    status = {'task_id': task.id, 'canonical_task_id': manifest['episodes'][index]['canonical_task_id'], 'trial': 0}
    try:
        simulation = run_single_task(config, task, seed=300, evaluation_type=EvaluationType.ALL,
                                     save_dir=folder, verbose_logs=True)
        simulation.trial = 0
        result = Results(info=get_info(config, tasks=[task]), tasks=[task], simulations=[simulation])
        result.save(folder / 'result.json')
        status.update(status='scored', reward=simulation.reward_info.reward,
                      duration=simulation.duration, termination_reason=simulation.termination_reason)
    except Exception as error:
        secret = os.getenv('OPENAI_API_KEY', '')
        detail = traceback.format_exc()
        (folder / 'exception.txt').write_text(detail.replace(secret, '[REDACTED]') if secret else detail)
        status.update(status='evaluation_error' if captured else 'execution_error',
                      error_type=type(error).__name__, reward=None)
    finally:
        close_facades()
        cleanup()
    write(folder / 'status.json', status)


def execute(output):
    prepared = json.loads((output / 'prepared.json').read_text())
    if sha(output / 'freeze.json') != prepared['freeze_sha256']:
        raise ValueError('Prepared freeze inventory changed')
    manifest = verify(output)
    if (output / 'execution.json').exists():
        raise ValueError('An attempt already started; no implicit retry or deadline reset')
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = getpass.getpass('API key (not saved): ')
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError('Missing API credential')
    started = time.time()
    write(output / 'execution.json', {'started_at': started, 'deadline': started + 5400})
    statuses = []
    for index, item in enumerate(manifest['episodes']):
        verify(output)
        folder = output / 'episodes' / item['key']
        folder.mkdir(parents=True, exist_ok=False)
        print('START ' + item['task_id'], flush=True)
        remaining = started + 5400 - time.time()
        if remaining <= 0:
            break
        with (folder / 'process.log').open('w') as log:
            proc = subprocess.Popen([sys.executable, str(Path(__file__)), '--output', str(output),
                                     '--episode-index', str(index)], stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            try:
                proc.wait(timeout=min(2400, remaining))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)
                write(folder / 'status.json', {'task_id': item['task_id'], 'status': 'timeout', 'reward': None})
        if not (folder / 'status.json').exists():
            write(folder / 'status.json', {'task_id': item['task_id'], 'status': 'process_error',
                                         'returncode': proc.returncode, 'reward': None})
        status = json.loads((folder / 'status.json').read_text())
        statuses.append(status)
        write(output / 'progress.json', {'planned': len(manifest['episodes']), 'finished': len(statuses), 'statuses': statuses})
        print(json.dumps(status, ensure_ascii=False), flush=True)
        if status['status'] != 'scored':
            print('STOP: preserve unscored attempt; no automatic retry or next case', flush=True)
            break
    verify(output)
    print('DONE: ' + str(output), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--episode-index', type=int)
    parser.add_argument('--canonical-tasks', nargs='+', choices=CANONICAL_TASKS)
    parser.add_argument('--prompt-version', choices=PROMPT_VERSIONS)
    parser.add_argument('--skill-version', choices=SKILL_VERSIONS)
    args = parser.parse_args()
    configure_environment()
    output = args.output.resolve()
    if output.exists() and (args.canonical_tasks is not None or args.prompt_version is not None or args.skill_version is not None):
        frozen = json.loads((output / 'manifest.json').read_text())
        if args.canonical_tasks is not None and args.canonical_tasks != [item['canonical_task_id'] for item in frozen['episodes']]:
            raise ValueError('Requested tasks differ from the frozen plan')
        if args.prompt_version is not None and args.prompt_version != frozen.get('system_prompt_version', 'baseline-v1'):
            raise ValueError('Requested prompt differs from the frozen plan')
        if args.skill_version is not None and args.skill_version != frozen['skill_release']['version']:
            raise ValueError('Requested Skill differs from the frozen plan')
    if args.episode_index is not None:
        episode(output, args.episode_index)
    else:
        if not output.exists():
            prepare(output, args.canonical_tasks or CANONICAL_TASKS,
                    args.prompt_version or DEFAULT_PROMPT_VERSION,
                    args.skill_version or SKILL_VERSION)
        elif not args.execute:
            raise ValueError('Use a new output directory for planning')
        if args.execute:
            execute(output)


if __name__ == '__main__':
    main()
