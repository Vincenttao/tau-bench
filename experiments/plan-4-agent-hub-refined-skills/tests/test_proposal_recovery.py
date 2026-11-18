"""Exercise input repair against strict JSON decoding, Java input state and the provider tape."""
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from test_control_replay import ARM, EpisodeController, HubGate, JavaTask, Jev, ROOT, RoutingPolicy, replay
from planner_client import PlannerClient

class ProposalRecoveryTests(unittest.TestCase):
    def exercise(self, repaired):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = int(time.time())
            with JavaTask(root/'task', 'synthetic', now+600, 64) as task:
                hub = HubGate(ARM/'go/target/banking-gate', root/'ledger.jsonl',
                              ROOT.parent/'agent-hub-alpha/agent-festival/schema')
                self.addCleanup(hub.close)
                planner = PlannerClient(task, root/'planner', 'fixture', 'https://example.invalid', 'fixture')
                ctl = EpisodeController(task, hub, planner, Jev(), RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'),
                                        root/'control', {}, 'policy', capture_replay=True)
                message = 'Please check delivery.'
                valid = json.dumps({'goals': [{'description': 'Check delivery', 'quote': message}], 'existing_routes': []})
                malformed = valid+'\nWait, reconsider the response.'
                bodies = [malformed, valid if repaired else malformed]
                def answer(req, **kwargs):
                    body = bodies.pop(0)
                    return io.BytesIO(json.dumps({'model':'fixture','usage':{'prompt_tokens':5,'completion_tokens':4},
                        'choices':[{'message':{'content':body}}]}).encode())
                with patch.object(planner.opener, 'open', side_effect=answer) as service:
                    result = ctl.user('m', message, now=now)
                    self.assertEqual(result['status'], 'ready' if repaired else 'clarify')
                    self.assertEqual(ctl.state(now)['can_dispatch'], repaired)
                    self.assertEqual(len(ctl.state(now)['goals']), int(repaired))
                    if not repaired:
                        self.assertEqual(result['reason'], 'input_format_unresolved')
                    self.assertEqual(ctl.user('m', message, now=now), result)
                    self.assertEqual(service.call_count, 2)
                ctl.stop('end'); ctl.seal_replay()
            result = replay(root/'control/control-replay', root/'replay')
            self.assertEqual(result['suppressed_tool_dispatches'], 0)

    def test_restart_after_lost_repair_retains_three_goals_and_never_resends(self):
        from planner_client import ProposalFormatError
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = int(time.time())
            policy = RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0')
            planner = Mock()
            planner.complete.side_effect = [ProposalFormatError('JSON'), KeyboardInterrupt()]
            with JavaTask(root/'task', 'restart', now+600, 64) as task:
                task.call('receive', episode='restart', message='first', content='Three services')
                task.call('apply', message='first', revision=task.call('status', now=now)['revision'],
                          actions=[{'kind': 'new_goal', 'description': goal} for goal in ('delivery','address','fees')])
                ctl = EpisodeController(task, None, planner, Jev(), policy, root/'controller', {}, 'policy')
                goals = ctl.state(now)['goals']
                with self.assertRaises(KeyboardInterrupt):
                    ctl.user('second', 'Continue my requests.', now=now)
            with JavaTask(root/'task', 'restart', now+600, 64) as task:
                ctl = EpisodeController(task, None, planner, Jev(), policy, root/'controller', {}, 'policy')
                route = ctl.user('second', 'Continue my requests.', now=now)
                self.assertEqual(route['status'], 'clarify')
                self.assertEqual(ctl.state(now)['goals'], goals)
                self.assertFalse(ctl.state(now)['can_dispatch'])
                self.assertEqual(planner.complete.call_count, 2)

    def test_provider_integrity_failure_never_enters_format_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            now = int(time.time())
            with JavaTask(Path(directory)/'task', 'integrity', now+600, 64) as task:
                planner = Mock()
                planner.complete.side_effect = ValueError('model identity changed')
                ctl = EpisodeController(task, None, planner, Jev(), RoutingPolicy('fixture', .3, .7, 'jev-latest', 'jev-1.14.0'),
                                        Path(directory)/'ctl', {}, 'policy')
                with self.assertRaisesRegex(ValueError, 'model identity'):
                    ctl.user('m', 'Handle my delivery.', now=now)
                self.assertFalse(ctl.state(now)['can_dispatch'])
                self.assertEqual(planner.complete.call_count, 1)

    def test_malformed_then_valid(self):
        self.exercise(True)

    def test_malformed_twice_remains_pending_for_later_input(self):
        self.exercise(False)
