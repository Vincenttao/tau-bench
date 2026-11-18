"""Reexecute captured Python/Java/Go control logic with no inference or bank effects.

Native executor outputs and official receipts are recorded inputs, not reexecuted.
Only serial sealed captures with matching implementation/dependency hashes qualify.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import sys
import time
from unittest.mock import patch

# A newer replay driver may inspect an older capture without replacing that
# capture's controller implementation. Verify bytes before importing its code.
if __name__ == '__main__' and '--frozen-code' in sys.argv:
    capture_arg = Path(sys.argv[sys.argv.index('--capture')+1]).resolve()
    frozen_seal = json.loads((capture_arg/'seal.json').read_text())
    for relative, expected in frozen_seal['files'].items():
        path = (capture_arg/relative).resolve()
        if not path.is_relative_to(capture_arg) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen capture integrity mismatch')
    sys.path.insert(0, str(capture_arg/'freeze-sources/experiments/plan-4-agent-hub-refined-skills/python'))

from control_recording import ReplayClock, ReplayTape, ReplayPlanner, ReplayJev, ReplayHub, logical_task
from controlled_effects import digest
from episode_controller import EpisodeController
from hub_gate import HubGate
from input_router import RoutingPolicy
from task_session import ARM, ROOT, JavaTask, durable_json


def verify_capture(capture):
    capture = Path(capture).resolve()
    seal = json.loads((capture/'seal.json').read_text())
    metadata = json.loads((capture/'metadata.json').read_text())
    for relative, expected in seal['files'].items():
        path = (capture/relative).resolve()
        if not path.is_relative_to(capture) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Capture integrity mismatch: '+relative)
    for relative, expected in metadata['implementation_files'].items():
        path = (ROOT/relative).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Implementation changed; use the frozen checkout: '+relative)
    for name, expected in metadata['dependencies'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError('Replay dependency changed')
    events = [json.loads(p.read_text()) for p in sorted((capture/'events').glob('*.json'))]
    def correlated_tool_receipt(x, y):
        # Both actual actions use EpisodeController._operation_lock. The next
        # receipt may take its read-only audit snapshot before the preceding
        # tool event finishes its snapshot. Permit only this causal edge, and
        # still require exact before/after states during actual reexecution.
        return (x['kind'] == 'tool' and y['kind'] == 'receipt'
            and x['arguments']['call']['id'] == y['arguments']['call_id'])
    if (len(events) != seal['events']
            or any((y['before_clock']['monotonic'] < x['after_clock']['monotonic'] and not correlated_tool_receipt(x, y))
                   or x['after'] != y['before'] for x, y in zip(events, events[1:]))):
        raise ValueError('Concurrent control actions or state gaps require a scheduler trace; serial replay refused')
    # Old captures conservatively marked overlapping record fsync as concurrent.
    # Reclassify only if the action intervals and state boundaries above prove
    # serial order. Preserve the source seal and report its original flag.
    metadata['correlated_tool_receipt_audit_overlaps'] = sum(
        y['before_clock']['monotonic'] < x['after_clock']['monotonic'] and correlated_tool_receipt(x, y)
        for x, y in zip(events, events[1:]))
    return capture, metadata, seal


def replay(capture, output, *, mutate_first_input=False, omit_first_receipt=False):
    capture, metadata, seal = verify_capture(capture)
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=False)
    task_dir = output/'task'; task_dir.mkdir()
    shutil.copyfile(capture/'initial-task.properties', task_dir/'task.properties')
    clock = ReplayClock(); clock.set(metadata['clocks'])
    tape = ReplayTape(capture/'providers', clock)
    task = JavaTask(task_dir, metadata['episode'], metadata['initial']['task']['deadline'], metadata['call_limit'],
                    replay_goal_ids=seal['goal_ids'], offline_replay=True)
    binary = output/'banking-gate'
    shutil.copyfile(ARM/'go/target/banking-gate', binary); binary.chmod(0o700)
    hub = HubGate(binary, output/'ledger.jsonl', capture/'frozen-schema')
    actual_queue = queue.Queue()
    def no_network(*args, **kwargs): raise RuntimeError('Network disabled during control replay')
    controller = None
    try:
        with patch('time.time', clock.time), patch('time.monotonic', clock.monotonic), patch.object(socket.socket, 'connect', no_network):
            controller = EpisodeController(task, ReplayHub(hub, tape), ReplayPlanner(task, tape), ReplayJev(tape),
                RoutingPolicy(**metadata['policy']), output/'controller', metadata['catalog'], metadata['domain_policy'])
            def snapshot():
                return {'task': logical_task(controller.task.call('status', now=int(time.time()))),
                    'evidence_refs': sorted(controller.evidence.visible()), 'last_question': controller.last_question,
                    'last_assistant_message': controller.last_assistant_message,
                    'bindings': controller.bindings,
                    'effects': {p.stem: json.loads(p.read_text()) for p in sorted(controller.effects.directory.glob('*.json'))}}
            if digest(snapshot()) != digest(metadata['initial']): raise ValueError('Initial replay state differs')
            events = sorted((capture/'events').glob('*.json'))
            if len(events) != seal['events']: raise ValueError('Missing control events')
            for index, path in enumerate(events):
                row = json.loads(path.read_text()); clock.set(row['before_clock'])
                if digest(snapshot()) != digest(row['before']): raise ValueError('Before-state differs at event '+str(index))
                arguments = row['arguments']; kind = row['kind']
                if omit_first_receipt and kind == 'receipt':
                    omit_first_receipt = False
                    continue  # Counterfactual: no observation may be invented to fill this gap.
                if mutate_first_input and kind == 'user':
                    arguments = {**arguments, 'content': arguments['content']+' changed'}
                    mutate_first_input = False
                if kind == 'restart_controls':
                    task.close(); hub.close()
                    task = JavaTask(task_dir, metadata['episode'], metadata['initial']['task']['deadline'], metadata['call_limit'],
                        replay_goal_ids=seal['goal_ids'], offline_replay=True)
                    hub = HubGate(binary, output/'ledger.jsonl', capture/'frozen-schema')
                    if not hub.call('health')['ok']: raise RuntimeError('Recovery health check refused')
                    controller.rebind_controls(task, ReplayHub(hub, tape))
                    result = None
                    clock.set(row['after_clock'])
                    if row['status'] != 'completed' or row['result'] is not None or digest(snapshot()) != digest(row['after']):
                        raise ValueError('Control recovery diverged')
                    continue
                if kind not in ('user', 'tool', 'receipt', 'response', 'remember_assistant',
                                'reserve_model', 'add_published_evidence', 'stop'):
                    raise ValueError('Unsupported replay event: '+kind)
                if kind == 'tool': arguments = {**arguments, 'official_queue': actual_queue}
                try:
                    result = getattr(controller, kind)(**arguments)
                except Exception as error:
                    if row['status'] != 'error' or type(error).__name__ != row['error_type']: raise
                else:
                    if row['status'] != 'completed' or digest(result) != digest(row['result']):
                        raise ValueError('Control result differs at event '+str(index))
                clock.set(row['after_clock'])
                if digest(snapshot()) != digest(row['after']): raise ValueError('After-state differs at event '+str(index))
            tape.assert_consumed()
            if digest(snapshot()) != digest(seal['final']): raise ValueError('Final task differs')
            result = {'status': 'passed', 'events': len(events), 'provider_calls': tape.cursor,
                'external_inference_calls': 0, 'official_bank_calls': 0, 'suppressed_tool_dispatches': actual_queue.qsize(),
                'source_serial_flag': seal['serial'], 'serial_action_boundaries_verified': True,
                'correlated_tool_receipt_audit_overlaps': metadata['correlated_tool_receipt_audit_overlaps'],
                'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'scope': metadata['replay_scope'], 'final': snapshot(), 'formal_comparison': False}
            durable_json(output/'result.json', result)
            return result
    except Exception as error:
        durable_json(output/'result.json', {'status': 'failed', 'error_type': type(error).__name__,
            'reason': str(error), 'external_inference_calls': 0, 'official_bank_calls': 0})
        raise
    finally:
        task.close(); hub.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True); parser.add_argument('--output', required=True)
    parser.add_argument('--mutate-first-input', action='store_true')
    parser.add_argument('--frozen-code', action='store_true', help='Import the verified captured controller implementation')
    parser.add_argument('--omit-first-receipt', action='store_true')
    args = parser.parse_args()
    replay(args.capture, args.output, mutate_first_input=args.mutate_first_input, omit_first_receipt=args.omit_first_receipt)
    print(json.dumps({'status': 'passed', 'output': args.output}))
