"""One English banking baseline attempt; no agent-hub enforcement is installed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New evidence directory under v1.0/runs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    version = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve()
    if not output.is_relative_to(version / 'runs'):
        parser.error('Output must be under this experiment v1.0/runs')
    if not os.environ.get('OPENAI_API_KEY'):
        parser.error('Inject OPENAI_API_KEY into the process environment before execution')
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', TAU3_SKILL_VERSION='3.2.0',
               OPENAI_MODEL='deepseek-v4-flash',
               OPENAI_API_BASE='https://st8tp3ajl0df3n8b8l8qu.apigateway-cn-beijing.volceapi.com/v1',
               OPENAI_BASE_URL='https://st8tp3ajl0df3n8b8l8qu.apigateway-cn-beijing.volceapi.com/v1',
               TAU2_REPO=str(root / '.deps/tau2-bench'),
               TAU2_DATA_DIR=str(root / '.deps/tau2-bench/data'),
               JAVA_AGENT_EVENT_TIMEOUT='1500', JAVA_AGENT_COMPLETION_TIMEOUT='1200',
               LITELLM_LOCAL_MODEL_COST_MAP='True')
    env['PYTHONPATH'] = os.pathsep.join([str(root / '.deps/tau2-bench/src'), str(root / 'python')])
    python = str(root / '.venv312/bin/python')
    commit = subprocess.check_output(['git', '-C', env['TAU2_REPO'], 'rev-parse', 'HEAD'], text=True).strip()
    if commit != 'fc0055dc4e0a316c3f83133267fbd6faaa770992':
        parser.error('Unexpected official benchmark commit')
    subprocess.run(['git', '-C', env['TAU2_REPO'], 'diff', '--quiet', 'HEAD', '--', 'src', 'data'], check=True)
    output.mkdir(parents=True, exist_ok=False)
    state = {'started_at': datetime.now(timezone.utc).isoformat(), 'task_id': 'task_054',
             'language': 'en', 'skill_version': '3.2.0', 'system_prompt_version': 'evidence-todo-v1',
             'benchmark_commit': commit, 'control_arm': 'existing-baseline',
             'agent_hub_enforcement': False, 'trials': 1, 'concurrency': 1,
             'seed': 300, 'token_limit': None, 'phases': [],
             'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

    def save():
        (output / 'execution.json').write_text(json.dumps(state, indent=2) + '\n')

    def run(label, command, credential=False):
        phase = {'name': label, 'command': command, 'started_at': datetime.now(timezone.utc).isoformat()}
        state['phases'].append(phase)
        save()
        child_env = dict(env)
        if not credential:
            child_env.pop('OPENAI_API_KEY', None)
        print('START ' + label, flush=True)
        with (output / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=root, env=child_env, stdout=log, stderr=subprocess.STDOUT)
        phase.update(returncode=result.returncode, finished_at=datetime.now(timezone.utc).isoformat())
        save()
        if result.returncode:
            raise RuntimeError(label + ' failed; inspect its evidence log')
        print('DONE ' + label, flush=True)

    try:
        run('build', ['mvn', '-B', '-ntp', '-f', 'java/pom.xml', '-DskipTests',
                      'package', 'dependency:build-classpath', '-Dmdep.outputFile=classpath.txt'])
        run('protocol', [python, str(root / 'experiments/deepagent-todo-skill-mcp/python/check_deepagent_protocol.py'),
                         '--output', str(output / 'protocol'), '--skill-version', '3.2.0',
                         '--language', 'en', '--prompt-version', 'evidence-todo-v1'])
        run('gateway', [python, str(root / 'python/check_gateway.py')], credential=True)
        gateway = json.loads((output / 'gateway.log').read_text())
        if not gateway.get('has_content'):
            raise RuntimeError('Gateway returned no content; official episode was not started')
        run('banking', [python, str(root / 'experiments/deepagent-todo-skill-mcp/python/run_deepagent.py'),
                        '--output', str(output / 'banking'), '--task-ids', 'task_054',
                        '--skill-version', '3.2.0', '--execute'], credential=True)
        run('analysis', [python, str(root / 'python/analyze_v2.py'), str(output / 'banking')])
        statuses = [json.loads(p.read_text()) for p in (output / 'banking/episodes').glob('*/status.json')]
        state['official_statuses'] = statuses
        if len(statuses) != 1 or statuses[0]['status'] != 'scored':
            raise RuntimeError('Official episode is unscored; retain the attempt without retry')
        state['status'] = 'scored_pass' if statuses[0]['reward'] == 1 else 'scored_failure'
    except Exception as exc:
        state['status'] = 'incomplete_or_unscored'
        state['error'] = str(exc)
        raise
    finally:
        state['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()


if __name__ == '__main__':
    main()
