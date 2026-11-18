"""Real local Java/Go control replay; scripted models and synthetic receipts only."""
import json
import hashlib
from pathlib import Path
import queue
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM/'python'))
from episode_controller import EpisodeController
from hub_gate import HubGate
from input_router import RoutingPolicy
from replay_control import replay, verify_capture
from task_session import JavaTask, ROOT, durable_json


class Planner:
    def __init__(self, task): self.task = task
    def complete(self, purpose, state, schema):
        self.task.call('charge', now=int(time.time()), kind='execution')
        if purpose == 'new-goals':
            return {'goals': [{'description': 'write synthetic value 8', 'quote': state['content']}], 'existing_routes': []}
        if purpose == 'response-review':
            return {'completed_goal_ids': [g['goal_id'] for g in state['visible_state']['task']['goals']],
                'comparison': None, 'claims': [{'quote': state['candidate_response'], 'kind': 'operation',
                    'evidence_refs': [r for r, v in state['visible_state']['evidence'].items() if v['source'] == 'official-tool']}]}
        goal = state.get('goal') or state['task']['goals'][0]
        return {'goal_id': goal['goal_id'], 'status': 'proposed',
            'policy_refs': [r for r, v in state['evidence'].items() if v['source'] == 'official-policy'],
            'conditions': [{'id': 'requested', 'statement': 'Customer requested writing synthetic value 8.',
                'evidence_refs': list(state['evidence'])}]}


class Jev:
    def ask(self, request):
        negative = {'no_business', 'ambiguous', 'comparison_needed', 'accepted', 'pending', 'rejected'}
        answers = {name: {'type': 'noul', 'noul': .01 if name in negative or name.endswith('_violated') else .99}
                   for name in request['questions']}
        return {'model': 'jev-1.14.0', 'answers': answers, 'usage': {'input_tokens': 1, 'output_tokens': 1}}


class ControlReplayTests(unittest.TestCase):
    def capture(self, root, *, audit_failure=None):
        now = int(time.time())
        with JavaTask(root/'task', 'synthetic-episode', now+600, 64) as task:
            hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ROOT.parent/'agent-hub-alpha/agent-festival/schema')
            try:
                controller = EpisodeController(task, hub, Planner(task), Jev(),
                    RoutingPolicy('synthetic', .3, .7, 'jev-latest', 'jev-1.14.0'), root/'controller',
                    {'write_fixture': {'access': 'write', 'principal': 'synthetic'}},
                    'Synthetic policy: write the exact requested value after explicit customer request.', capture_replay=True)
                self.assertEqual(controller.user('m', 'Write synthetic value 8.', now=now)['status'], 'ready')
                target = queue.Queue()
                with self.assertRaises(PermissionError):
                    controller.tool({'id': 'bad-call', 'name': 'unregistered', 'arguments': {}}, target, now=now)
                self.assertTrue(controller.state(now)['can_dispatch'], 'A business refusal must not become an audit outage')
                if audit_failure:
                    def fail_event(path, value):
                        if Path(path).parent.name == 'events' and value.get('kind') == 'tool' and value.get('status') == audit_failure:
                            raise OSError('Synthetic audit disk failure')
                        return durable_json(path, value)
                    with patch('control_recording.durable_json', side_effect=fail_event):
                        with self.assertRaises(OSError):
                            controller.tool({'id': 'call-1', 'name': 'write_fixture', 'arguments': {'amount': 8}}, target, now=now)
                    self.assertEqual(target.qsize(), 0 if audit_failure == 'started' else 1)
                    self.assertFalse(controller.state(now)['can_dispatch'])
                    if audit_failure == 'completed':
                        binding = controller.bindings['call-1']
                        self.assertEqual(controller.effects.status(binding['operation'])['business_status'], 'unknown')
                    with self.assertRaises(RuntimeError):
                        controller.tool({'id': 'call-2', 'name': 'write_fixture', 'arguments': {'amount': 8}}, target, now=now)
                    return
                controller.tool({'id': 'call-1', 'name': 'write_fixture', 'arguments': {'amount': 8}}, target, now=now)
                self.assertEqual(target.qsize(), 1)
                controller.receipt('call-1', 'Synthetic value 8 was written successfully.', False, now=now)
                def restart():
                    nonlocal task, hub
                    task.close(); hub.close()
                    task = JavaTask(root/'task', 'synthetic-episode', now+600, 64)
                    hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ROOT.parent/'agent-hub-alpha/agent-festival/schema')
                    self.assertTrue(hub.call('health')['ok'])
                    controller.rebind_controls(task, hub)
                controller.journal.run('restart_controls', {}, restart)
                result = controller.response('Synthetic value 8 was written successfully.', waiting=False, now=now)
                self.assertEqual(result['status'], 'allow')
                self.assertEqual(controller.state(now)['outcome'], 'success')
                controller.stop('fixture-ended'); controller.seal_replay()
                return root/'controller/control-replay'
            finally: hub.close(); task.close()

    def test_audit_failure_before_action_stops_all_future_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            self.capture(Path(directory), audit_failure='started')

    def test_audit_failure_after_enqueue_retains_unknown_and_stops_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            self.capture(Path(directory), audit_failure='completed')

    def test_overlapping_actions_cannot_be_reclassified_as_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            capture = self.capture(Path(directory))
            event0 = json.loads((capture/'events/000000.json').read_text())
            path = capture/'events/000001.json'; event1 = json.loads(path.read_text())
            event1['before_clock']['monotonic'] = event0['after_clock']['monotonic']-1
            durable_json(path, event1)
            seal_path = capture/'seal.json'; seal = json.loads(seal_path.read_text())
            seal['files']['events/000001.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
            durable_json(seal_path, seal)
            with self.assertRaisesRegex(ValueError, 'Concurrent control actions'):
                verify_capture(capture)

    def test_correlated_tool_receipt_audit_window_requires_exact_reexecution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); capture = self.capture(root)
            events = sorted((capture/'events').glob('*.json'))
            for x, path in zip(events, events[1:]):
                previous = json.loads(x.read_text()); current = json.loads(path.read_text())
                if previous['kind'] == 'tool' and current['kind'] == 'receipt': break
            current['before_clock']['monotonic'] = previous['after_clock']['monotonic']-.001
            durable_json(path, current)
            seal_path = capture/'seal.json'; seal = json.loads(seal_path.read_text())
            seal['serial'] = False
            seal['files'][str(path.relative_to(capture))] = hashlib.sha256(path.read_bytes()).hexdigest()
            durable_json(seal_path, seal)
            result = replay(capture, root/'causal')
            self.assertEqual(result['correlated_tool_receipt_audit_overlaps'], 1)
            current['arguments']['call_id'] = 'unrelated-call'
            durable_json(path, current)
            seal['files'][str(path.relative_to(capture))] = hashlib.sha256(path.read_bytes()).hexdigest()
            durable_json(seal_path, seal)
            with self.assertRaisesRegex(ValueError, 'Concurrent control actions'):
                verify_capture(capture)

    def test_whole_control_chain_replays_and_changed_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.capture(root)
            result = replay(capture, root/'replayed')
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['external_inference_calls'], 0)
            self.assertEqual(result['official_bank_calls'], 0)
            self.assertEqual(result['suppressed_tool_dispatches'], 1)
            with self.assertRaises(ValueError): replay(capture, root/'changed', mutate_first_input=True)
            with self.assertRaises(ValueError): replay(capture, root/'missing-receipt', omit_first_receipt=True)
            event = capture/'events/000000.json'
            event.write_text('{}')
            with self.assertRaises(ValueError): replay(capture, root/'tampered')
