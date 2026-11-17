"""Prepare and execute an immutable full-control diagnostic; never a formal trial."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil

from task_session import ARM, ROOT, durable_json
sys.path.insert(0, str(ROOT/'shared/python'))
from diagnostic_run import build_manifest as baseline_manifest
from process_tree import terminate_tree


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_manifest(task, model=None):
    manifest = baseline_manifest(4, task, runtime_pilot=True)
    manifest.update(driver='hub-evidence-control', revision_id='llm-evidence-control',
                    formal_comparison=False, full_architecture_ready=False, automatic_episode_retries=0,
                    acceptance_scope='single full-control diagnostic; not all-39-contract release')
    if model is not None:
        if model not in ('deepseek-v4-flash', 'volcengine/deepseek-v4.1-flash'):
            raise ValueError('Unapproved diagnostic model route')
        manifest['baseline_requested_model'] = manifest['model']
        manifest['model'] = model
        manifest['diagnostic_model_override'] = model != manifest['baseline_requested_model']
    return manifest


def prepare(task, output, model=None):
    manifest = build_manifest(task, model)
    output = Path(output).resolve(); manifest['output'] = str(output)
    files = [*ARM.joinpath('python').glob('*.py'), *ARM.joinpath('java/src').rglob('*.java'),
             *ARM.joinpath('java/target').rglob('*.class'), *ARM.joinpath('go').rglob('*.go'),
             ARM/'go/target/banking-gate', ARM/'go/source-pin.json',
             *ROOT.joinpath('shared/python').glob('*.py'), *ROOT.joinpath('shared/java/target/classes').rglob('*.class')]
    manifest['implementation_files'] = {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}
    manifest['dependencies'] = {path: sha(path) for path in (ROOT/'shared/java/classpath.txt').read_text().strip().split(os.pathsep)}
    manifest['runtime_bindings'] = {'jev_request_model': 'jev-latest', 'jev_expected_model': 'jev-1.14.0',
                                   'input_policy': 'banking-evidence-input-policy', 'node_version': 'banking-evidence-control',
                                   'proposal_thinking': 'disabled', 'proposal_max_tokens': 4096,
                                   'actual_model_identity': 'pin-first-response-per-layer; reject-drift',
                                   'native_transport': 'private-loopback-buffered-sse',
                                   'native_ttft_comparable': False}
    manifest['runtime_bindings']['jev_context_policy'] = 'long-context-header-at-65536-json-bytes; no-truncation-or-retry'
    output.mkdir(parents=True, exist_ok=False)
    for name, expected in manifest['implementation_files'].items():
        source = ROOT/name
        if sha(source) != expected: raise RuntimeError('Implementation drift during freeze')
        target = output/'freeze-sources'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    durable_json(output/'manifest.json', manifest)
    return manifest


def inspect(manifest):
    episode = Path(manifest['output'])/'episodes'/manifest['episodes'][0]['key']
    control = episode/'hub-control'
    checks = {}
    try:
        task = json.loads((control/'final-task.json').read_text())
        bindings_path = control/'controller/call-bindings.json'
        bindings = json.loads(bindings_path.read_text()) if bindings_path.exists() else {}
        official = [json.loads(line) for line in (episode/'official-trajectory.jsonl').read_text().splitlines()]
        calls = {call['id']: call for msg in official if msg.get('role') == 'assistant' for call in msg.get('tool_calls') or []}
        receipts = {msg['id'] for msg in official if msg.get('role') == 'tool'}
        ledger = [json.loads(line) for line in (control/'ledger.jsonl').read_text().splitlines()]
        dispatched = {event['identity']['operation_id'] for event in ledger if event['outcome']['status'] == 'dispatched'}
        checks['actual_go_dispatch'] = bool(dispatched)
        checks['no_official_tool_bypass'] = set(calls) == set(bindings)
        checks['official_receipts_bound'] = set(calls) <= receipts
        checks['go_and_final_payload_binding'] = all(
            binding['operation'] in dispatched
            and (lambda record: record['payload']['operation'] == calls[call_id]['name']
                 and record['payload']['arguments'] == calls[call_id]['arguments'])(
                     json.loads((control/'controller/effects'/(binding['operation']+'.json')).read_text()))
            for call_id, binding in bindings.items())
        checks['persistent_native_checkpoint'] = bool(list((control/'deepagent').glob('*/checkpoints')))
        checks['native_model_reservations'] = bool(list(control.glob('native-model-*.json')))
        inputs = list((control/'controller/inputs').glob('*.proposal.json'))
        from tau2.user.user_simulator import UserSimulator
        from tau2.data_model.message import UserMessage
        checks['user_input_interpretation'] = len(inputs) == sum(
            msg.get('role') == 'user' and not UserSimulator.is_stop(UserMessage.model_validate(msg)) for msg in official)
        checks['independent_output_check'] = bool(list((control/'controller').glob('output-*.json')))
        checks['registered_task_nodes'] = bool(task['nodes']) and all(node['decision_ref'] in dispatched for node in task['nodes'])
        status = json.loads((episode/'status.json').read_text())
        result = json.loads((episode/'result.json').read_text())
        checks['official_score_preserved'] = status['status'] == 'scored' and status['reward'] == result['simulations'][0]['reward_info']['reward']
    except (OSError, ValueError, KeyError, TypeError) as error:
        checks['complete_evidence'] = False
        error_type = type(error).__name__
    else: error_type = None
    return {'status': 'passed' if checks and all(checks.values()) else 'failed',
            'scope': manifest['acceptance_scope'], 'checks': checks, 'error_type': error_type,
            'all_39_contracts_passed': False, 'business_reward_is_separate': True}


def execute(manifest):
    for key in ('OPENAI_API_KEY', 'TYPESAFE_API_KEY'):
        if not os.environ.get(key): raise RuntimeError('Runtime credential missing: '+key)
    for path, expected in manifest['implementation_files'].items():
        if sha(ROOT/path) != expected: raise RuntimeError('Frozen implementation changed: '+path)
    for path, expected in manifest['dependencies'].items():
        if sha(path) != expected: raise RuntimeError('Frozen dependency changed')
    output = Path(manifest['output'])
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT/'shared/python'), str(ARM/'python')])
    with (output/'supervisor.log').open('w') as log:
        proc = subprocess.Popen([str(ROOT/'.venv312/bin/python'), str(ARM/'python/run_full_episode.py'),
                                 '--manifest', str(output/'manifest.json')], cwd=ROOT, env=env,
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try: proc.wait(timeout=manifest['limits']['episode_timeout_seconds'])
        except BaseException:
            terminate_tree(proc)
            durable_json(output/'supervisor-status.json', {'status': 'interrupted-or-deadline'})
            raise
    acceptance = inspect(manifest)
    durable_json(output/'architecture-acceptance.json', acceptance)
    status_path = output/'episodes'/manifest['episodes'][0]['key']/'status.json'
    status = json.loads(status_path.read_text()) if status_path.exists() else {'status': 'execution_error', 'returncode': proc.returncode}
    summary = {**status, 'architecture_acceptance': acceptance['status'],
               'all_39_contracts_passed': False, 'formal_comparison': False}
    durable_json(output/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--model', choices=['deepseek-v4-flash', 'volcengine/deepseek-v4.1-flash'])
    args = parser.parse_args()
    manifest = prepare(args.task, args.output, args.model)
    if args.execute:
        result = execute(manifest); print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(0 if result['architecture_acceptance'] == 'passed' else 1)
    print(json.dumps({'execution_started': False, 'output': manifest['output']}))


if __name__ == '__main__': main()
