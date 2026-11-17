"""Real Java process, scripted inference: cross-process integration acceptance."""
from pathlib import Path
import sys
import tempfile
import unittest

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM / 'python'), str(Path(__file__).resolve().parent)]
from test_input_router import ScriptedClient
from input_router import InputRouter, RoutingPolicy
from task_session import JavaTask, TaskSession


class TaskSessionTests(unittest.TestCase):
    def test_context_only_reply_preserves_goal_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            router = self.router()
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                session.handle('m1', 'check balance', [{'description': 'check balance', 'quote': 'check balance'}], now=900)
                original = task.call('status', now=900)['goals']
                router.client.values = {'covered': .99, 'g0_reaffirm': .69}
                result = session.handle('m2', 'I still need that balance.', [], now=900)
                self.assertTrue(result['context_only'])
                self.assertEqual(task.call('status', now=900)['goals'], original)
                session.handle('m2', 'I still need that balance.', [], now=900)
                self.assertEqual(len(router.client.calls), 2)
                self.assertTrue(task.call('status', now=900)['can_dispatch'])

    def router(self):
        client = ScriptedClient({'covered': .99, 'has_new': .99, 'new0_supported': .99})
        return InputRouter(client, RoutingPolicy('synthetic-only', .3, .7, 'jev-latest', 'jev-1.14.0'))

    def test_real_java_receive_judge_commit_and_duplicate_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            router = self.router()
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                result = session.handle('m1', 'check my balance', [{'description': 'check balance', 'quote': 'check my balance'}], now=900)
                self.assertEqual(result['status'], 'ready')
                self.assertEqual(task.call('status', now=900)['calls'], 1)
                self.assertTrue(task.call('status', now=900)['can_dispatch'])
            with JavaTask(Path(directory), 'episode', 5000, 50) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                again = session.handle('m1', 'check my balance', [], now=900)
                self.assertEqual(again['input_hash'], result['input_hash'])
                self.assertEqual(len(router.client.calls), 1)
                self.assertEqual(task.call('status', now=900)['deadline'], 1000)

    def test_failed_provider_keeps_task_blocked_and_no_blind_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            router = self.router()
            def fail(request): raise RuntimeError('synthetic transport failure')
            router.client.ask = fail
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                with self.assertRaises(RuntimeError):
                    session.handle('m1', 'check balance', [], now=900)
                with self.assertRaises(RuntimeError):
                    session.handle('m1', 'check balance', [], now=900)
                state = task.call('status', now=900)
                self.assertFalse(state['can_dispatch'])
                self.assertEqual(state['calls'], 1)

    def test_foreign_message_and_bad_revision_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                with self.assertRaises(RuntimeError):
                    task.call('receive', episode='other', message='m', content='hello')
                task.call('receive', episode='episode', message='m', content='hello')
                with self.assertRaises(RuntimeError):
                    task.call('apply', message='m', revision=0, actions=[])

    def test_audit_response_can_be_committed_after_coordinator_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            router = self.router()
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                original = session.commit
                def interrupted(*args): raise RuntimeError('synthetic interruption before commit')
                session.commit = interrupted
                with self.assertRaises(RuntimeError):
                    session.handle('m', 'check balance', [{'description': 'check balance', 'quote': 'check balance'}], now=900)
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                self.assertEqual(session.handle('m', 'check balance', [], now=900)['status'], 'ready')
                self.assertEqual(len(router.client.calls), 1)

    def test_clarification_is_resolved_by_explicit_new_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            router = self.router(); router.client.values = {'covered': .99, 'ambiguous': .99}
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                self.assertEqual(session.handle('m1', 'do that', [], now=900)['status'], 'clarify')
                router.client.values = {'covered': .99, 'has_new': .99, 'new0_supported': .99, 'clarify0_resolved': .99}
                result = session.handle('m2', 'check balance', [{'description': 'check balance', 'quote': 'check balance'}], now=900)
                self.assertEqual(result['resolved_messages'], ['m1'])
                self.assertTrue(task.call('status', now=900)['can_dispatch'])

    def test_pause_new_goal_then_resume_original_goal(self):
        with tempfile.TemporaryDirectory() as directory:
            router = self.router()
            with JavaTask(Path(directory), 'episode', 1000, 12) as task:
                session = TaskSession(task, router, Path(directory)/'audit')
                session.handle('m1', 'replace card', [{'description': 'replace card', 'quote': 'replace card'}], now=900)
                first = task.call('status', now=900)['goals'][0]['goal_id']
                router.client.values = {'covered': .99, 'g0_pause': .99, 'has_new': .99, 'new0_supported': .99}
                session.handle('m2', 'pause card replacement; check balance', [{'description': 'check balance', 'quote': 'check balance'}], now=900)
                self.assertEqual(task.call('status', now=900)['goals'][0]['state'], 'waiting')
                router.client.values = {'covered': .99, 'g0_resume': .99}
                session.handle('m3', 'resume card replacement', [], now=900)
                goals = task.call('status', now=900)['goals']
                self.assertEqual(goals[0]['goal_id'], first)
                self.assertEqual(goals[0]['state'], 'active')
                self.assertEqual(len(goals), 2)

    def test_killed_java_process_restores_persisted_pending_input_and_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            task = JavaTask(Path(directory), 'episode', 1000, 8)
            task.call('receive', episode='episode', message='m1', content='check balance')
            task.call('charge', now=900)
            task.process.kill(); task.process.wait(timeout=5); task.close()
            with JavaTask(Path(directory), 'episode', 5000, 80) as restored:
                state = restored.call('status', now=900)
                self.assertEqual(state['input_status'], 'pending')
                self.assertFalse(state['can_dispatch'])
                self.assertEqual(state['calls'], 1)
                self.assertEqual(state['deadline'], 1000)

    def test_audit_failure_never_commits_input_route(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            with JavaTask(Path(directory), 'episode', 1000, 8) as task:
                router = self.router()
                session = TaskSession(task, router, Path(directory)/'audit')
                with patch('task_session.durable_json', side_effect=OSError('synthetic disk error')):
                    with self.assertRaises(OSError):
                        session.handle('m', 'check balance', [], now=900)
                self.assertFalse(task.call('status', now=900)['can_dispatch'])
                self.assertEqual(router.client.calls, [])
