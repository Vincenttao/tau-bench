"""Authoritative acceptance uses published requirements, not Todo completion."""
from pathlib import Path
import sys
import tempfile
import unittest

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM/'python'))
from task_session import JavaTask


class GoalAcceptanceTests(unittest.TestCase):
    def create(self, task, message, description):
        task.call('receive', episode='episode', message=message, content=description)
        state = task.call('status', now=900)
        task.call('apply', message=message, revision=state['revision'], actions=[{'kind': 'new_goal', 'description': description}])
        return task.call('status', now=900)['goals'][-1]['goal_id']

    def test_success_requires_all_conditions_and_dependency_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with JavaTask(Path(directory), 'episode', 1000, 20) as task:
                first = self.create(task, 'm1', 'open account')
                second = self.create(task, 'm2', 'transfer funds')
                for goal, dependencies in [(first, []), (second, [first])]:
                    task.call('configure_goal', goal=goal, revision=task.call('status', now=900)['revision'],
                              requirements=['confirmed_result'], source_ref='public-policy:fixture', dependencies=dependencies)
                with self.assertRaises(RuntimeError): task.call('accept_goal', goal=first, revision=task.call('status', now=900)['revision'])
                task.call('record_condition', goal=second, condition='confirmed_result', value='satisfied',
                          evidence_ref='official-receipt:transfer', revision=task.call('status', now=900)['revision'])
                with self.assertRaises(RuntimeError): task.call('accept_goal', goal=second, revision=task.call('status', now=900)['revision'])
                task.call('record_condition', goal=first, condition='confirmed_result', value='satisfied',
                          evidence_ref='official-receipt:open', revision=task.call('status', now=900)['revision'])
                task.call('accept_goal', goal=first, revision=task.call('status', now=900)['revision'])
                task.call('accept_goal', goal=second, revision=task.call('status', now=900)['revision'])
                state = task.call('status', now=900)
                self.assertEqual(state['outcome'], 'success')
                self.assertTrue(all(goal['outcome'] == 'success' for goal in state['goals']))

    def test_unknown_or_stale_evidence_and_cycles_cannot_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            with JavaTask(Path(directory), 'episode', 1000, 20) as task:
                first = self.create(task, 'm1', 'first'); second = self.create(task, 'm2', 'second')
                revision = task.call('status', now=900)['revision']
                task.call('configure_goal', goal=first, revision=revision, requirements=['result'], source_ref='public:fixture', dependencies=[second])
                with self.assertRaises(RuntimeError):
                    task.call('configure_goal', goal=second, revision=task.call('status', now=900)['revision'], requirements=['result'], source_ref='public:fixture', dependencies=[first])
                with self.assertRaises(RuntimeError):
                    task.call('record_condition', goal=first, revision=revision, condition='result', value='satisfied', evidence_ref='stale')
                task.call('record_condition', goal=first, revision=task.call('status', now=900)['revision'], condition='result', value='unknown', evidence_ref='official:timeout')
                with self.assertRaises(RuntimeError): task.call('accept_goal', goal=first, revision=task.call('status', now=900)['revision'])

    def test_modification_invalidates_old_condition_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            with JavaTask(Path(directory), 'episode', 1000, 20) as task:
                goal = self.create(task, 'm1', 'transfer 10')
                task.call('configure_goal', goal=goal, revision=task.call('status', now=900)['revision'], requirements=['result'], source_ref='policy:fixture', dependencies=[])
                task.call('record_condition', goal=goal, revision=task.call('status', now=900)['revision'], condition='result', value='satisfied', evidence_ref='receipt:10')
                task.call('receive', episode='episode', message='m2', content='transfer 20 instead')
                task.call('apply', message='m2', revision=task.call('status', now=900)['revision'], actions=[{'kind': 'modify', 'goal_id': goal, 'description': 'transfer 20'}])
                with self.assertRaises(RuntimeError): task.call('accept_goal', goal=goal, revision=task.call('status', now=900)['revision'])
