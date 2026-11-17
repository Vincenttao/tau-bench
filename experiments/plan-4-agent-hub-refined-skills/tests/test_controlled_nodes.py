from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from task_session import JavaTask, ARM
from hub_gate import HubGate
from controlled_nodes import ControlledNodes


class ControlledNodeTests(unittest.TestCase):
    def test_fixed_workflow_and_wait_resume_use_actual_adopted_nodes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                task.call('receive', episode='episode', message='m', content='compare products')
                task.call('apply', message='m', revision=task.call('status', now=900)['revision'],
                          actions=[{'kind': 'new_goal', 'description': 'compare products'}])
                goal = task.call('status', now=900)['goals'][0]['goal_id']
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl', ARM.parents[1].parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                nodes = ControlledNodes(task, hub, root/'nodes')
                proof = {'status': 'allow', 'model': 'fixture', 'observation_ref': 'fixture-judgment'}
                ref = nodes.start('candidate-comparison', goal, {'fee': 0}, proof, now=900)
                nodes.finish(ref)
                waiting = nodes.start('await-user', goal, {'question': 'Which card?'}, proof, now=900)
                nodes.wait(waiting)
                task.call('wait_goal', goal=goal, revision=task.call('status', now=900)['revision'], question='Which card?')
                nodes.resume_waits(now=900)
                self.assertEqual(next(n['status'] for n in task.call('status', now=900)['nodes'] if n['node_id'] == waiting), 'waiting')
                task.call('receive', episode='episode', message='reply', content='Card A')
                task.call('apply', message='reply', revision=task.call('status', now=900)['revision'],
                          actions=[{'kind': 'respond', 'goal_id': goal}])
                nodes.resume_waits(now=900)
                nodes.resume_waits(now=900)
                self.assertEqual({node['status'] for node in task.call('status', now=900)['nodes']}, {'completed'})
                with self.assertRaises(PermissionError): nodes.start('unregistered', goal, {}, proof, now=900)
                with self.assertRaises(PermissionError): nodes.start('candidate-comparison', goal, {}, dict(proof, status='unknown'), now=900)
