"""Real Java/Go end-to-end control tests; synthetic business service only."""
from pathlib import Path
import queue
import sys
import tempfile
import unittest

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM/'python'), str(Path(__file__).resolve().parent)]
from task_session import JavaTask, TaskSession
from input_router import InputRouter, RoutingPolicy
from test_input_router import ScriptedClient
from hub_gate import HubGate
from controlled_effects import ControlledEffects, digest


class ControlledEffectsTests(unittest.TestCase):
    def test_stable_step_cannot_silently_reuse_a_different_payload(self):
        class Task:
            episode = 'episode'
            def call(self, method, **arguments):
                return {'can_dispatch': True, 'revision': 1, 'goals': [{'goal_id': 'goal', 'state': 'active'}]}
        class Hub:
            def call(self, method, **arguments): return {'ok': True}
        with tempfile.TemporaryDirectory() as directory:
            effects = ControlledEffects(Task(), Hub(), Path(directory), {'write': {'access': 'write'}})
            def judgment(amount):
                return {'episode_id': 'episode', 'goal_id': 'goal', 'status': 'allow',
                        'payload_hash': digest({'episode': 'episode', 'operation': 'write', 'arguments': {'amount': amount}}),
                        'evidence_refs': ['fixture'], 'rule_version': 'fixture', 'model': 'fixture', 'conditions': {'valid': 'satisfied'}}
            effects.adopt('goal', 'same-step', 'write', {'amount': 5}, judgment(5), now=900)
            with self.assertRaises(PermissionError):
                effects.adopt('goal', 'same-step', 'write', {'amount': 6}, judgment(6), now=900)

    def test_queue_failure_is_not_blindly_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root, 'episode', 1000, 8) as task:
                client = ScriptedClient({'covered': .99, 'has_new': .99, 'new0_supported': .99})
                TaskSession(task, InputRouter(client, RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0')), root/'audit').handle(
                    'm', 'submit dispute', [{'description': 'submit dispute', 'quote': 'submit dispute'}], now=900)
                goal = task.call('status', now=900)['goals'][0]['goal_id']
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                effects = ControlledEffects(task, hub, root/'effects', {'synthetic_submit': {'access': 'write'}})
                payload = {'episode': 'episode', 'operation': 'synthetic_submit', 'arguments': {}}
                judgment = {'episode_id': 'episode', 'goal_id': goal, 'status': 'allow', 'payload_hash': digest(payload),
                            'evidence_refs': ['synthetic:policy'], 'rule_version': 'fixture', 'model': 'scripted', 'conditions': {'valid': 'satisfied'}}
                operation = effects.adopt(goal, 'submit', 'synthetic_submit', {}, judgment, now=900)
                class BrokenQueue:
                    def put(self, event): raise RuntimeError('synthetic crash before enqueue')
                with self.assertRaises(RuntimeError): effects.dispatch(operation, 'call-one', BrokenQueue(), now=900)
                reopened = ControlledEffects(task, hub, root/'effects', {'synthetic_submit': {'access': 'write'}})
                with self.assertRaises(PermissionError): reopened.dispatch(operation, 'call-two', queue.Queue(), now=900)
                # Authoritative late observation can still close the operation after task stop.
                task.call('stop', reason='official-stop')
                reopened.receipt(operation, 'call-one', {'status': 'succeeded'}, error=False)
                self.assertEqual(reopened.status(operation)['phase'], 'completed')

    def test_adopt_dispatch_receipt_and_new_call_id_cannot_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root, 'episode', 1000, 8) as task:
                client = ScriptedClient({'covered': .99, 'has_new': .99, 'new0_supported': .99})
                session = TaskSession(task, InputRouter(client, RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0')), root/'audit')
                session.handle('m1', 'submit dispute', [{'description': 'submit dispute', 'quote': 'submit dispute'}], now=900)
                goal = task.call('status', now=900)['goals'][0]['goal_id']
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                effects = ControlledEffects(task, hub, root/'effects', {'synthetic_submit': {'access': 'write'}})
                evidence = {'episode_id': 'episode', 'goal_id': goal, 'rule_version': 'fixture-rule',
                            'payload_hash': digest({'episode': 'episode', 'operation': 'synthetic_submit', 'arguments': {'amount': 5}}),
                            'evidence_refs': ['synthetic-policy:one'], 'conditions': {'identity': 'satisfied', 'consent': 'satisfied'},
                            'model': 'scripted-fixture', 'status': 'allow'}
                operation = effects.adopt(goal, 'submit', 'synthetic_submit', {'amount': 5}, evidence, now=900)
                output = queue.Queue()
                effects.dispatch(operation, 'call-one', output, now=900)
                self.assertEqual(output.qsize(), 1)
                with self.assertRaises(PermissionError): effects.dispatch(operation, 'call-two', output, now=900)
                effects.receipt(operation, 'call-one', {'status': 'accepted', 'request_id': 'one'}, error=False)
                self.assertEqual(effects.status(operation)['business_status'], 'accepted')
                self.assertEqual(effects.status(operation)['goal_outcome'], 'undetermined')
                # Duplicate accepted receipt is idempotent, conflicting receipt is not.
                effects.receipt(operation, 'call-one', {'status': 'accepted', 'request_id': 'one'}, error=False)
                with self.assertRaises(PermissionError): effects.receipt(operation, 'wrong', {'status': 'succeeded'}, error=False)
                original_call = hub.call
                def fail_completion(method, **arguments):
                    if method == 'complete': raise RuntimeError('synthetic receipt transport loss')
                    return original_call(method, **arguments)
                hub.call = fail_completion
                with self.assertRaises(RuntimeError):
                    effects.receipt(operation, 'call-one', {'status': 'succeeded'}, error=False)
                self.assertEqual(effects.status(operation)['phase'], 'dispatched')
                hub.call = original_call
                effects.receipt(operation, 'call-one', {'status': 'succeeded'}, error=False)
                self.assertEqual(effects.status(operation)['phase'], 'completed')
                task.call('receive', episode='episode', message='m2', content='cancel')
                with self.assertRaises(PermissionError):
                    effects.adopt(goal, 'another', 'synthetic_submit', {}, evidence, now=900)

    def test_missing_evidence_never_adopts_and_task_stop_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                effects = ControlledEffects(task, None, Path(directory)/'effects', {'synthetic_submit': {'access': 'write'}})
                with self.assertRaises(PermissionError): effects.adopt('unknown', 'step', 'synthetic_submit', {}, {}, now=900)
                task.call('stop', reason='official-stop')
                with self.assertRaises(PermissionError): effects.adopt('unknown', 'step', 'synthetic_submit', {}, {}, now=900)
