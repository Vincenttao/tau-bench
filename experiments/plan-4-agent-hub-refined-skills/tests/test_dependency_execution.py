from pathlib import Path
import queue
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from task_session import JavaTask, ARM
from controlled_effects import ControlledEffects, digest
from hub_gate import HubGate


class DependencyExecutionTests(unittest.TestCase):
    def test_wait_a_complete_b_then_resume_original_a(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                task.call('receive', episode='episode', message='m', content='A requires B first')
                task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                    actions=[{'kind': 'new_goal', 'description': text} for text in ('A', 'B')])
                a, b = [g['goal_id'] for g in task.call('status', now=900)['goals']]
                def configure(goal, deps):
                    task.call('configure_goal', goal=goal, revision=task.call('status', now=900)['revision'],
                        requirements=['result'], source_ref='fixture-policy', dependencies=deps)
                configure(a, [b]); configure(b, [])
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                effects = ControlledEffects(task, hub, root/'effects', {'write': {'access': 'write'}})
                judgment = {'episode_id': 'episode', 'goal_id': a, 'status': 'allow',
                    'payload_hash': digest({'episode': 'episode', 'operation': 'write', 'arguments': {}}),
                    'evidence_refs': ['fixture'], 'rule_version': 'fixture', 'model': 'fixture',
                    'conditions': {'authorized': 'satisfied'}}
                with self.assertRaises(PermissionError): effects.adopt(a, 'write', 'write', {}, judgment, now=900)
                self.assertEqual(task.call('status', now=900)['goals'][0]['state'], 'waiting')
                task.call('record_condition', goal=b, revision=task.call('status', now=900)['revision'],
                    condition='result', value='satisfied', evidence_ref='fixture-receipt')
                task.call('accept_goal', goal=b, revision=task.call('status', now=900)['revision'])
                self.assertEqual(task.call('status', now=900)['goals'][0]['state'], 'active')
                operation = effects.adopt(a, 'write', 'write', {}, judgment, now=900)
                output = queue.Queue(); effects.dispatch(operation, 'one', output, now=900)
                self.assertEqual(output.qsize(), 1)
                self.assertEqual(task.call('status', now=900)['goals'][0]['goal_id'], a)
