from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from control_recording import CallTape, ReplayTape, AuditPlanner, ReplayPlanner, AuditHub, ReplayHub


class Budget:
    def __init__(self): self.calls = 0
    def call(self, method, **values):
        if method == 'charge': self.calls += 1
        return {'calls': self.calls}


class RecordingTests(unittest.TestCase):
    def test_exact_replay_uses_recorded_result_and_preserves_budget(self):
        class Planner:
            def complete(self, purpose, state, schema):
                self.task.call('charge', kind='execution')
                return {'value': 2}
        with tempfile.TemporaryDirectory() as directory:
            task = Budget(); tape = CallTape(Path(directory))
            planner = AuditPlanner(Planner(), task, tape)
            self.assertEqual(planner.complete('fixture', {'value': 1}, {'type': 'object'}), {'value': 2})
            replay_task = Budget()
            replay = ReplayTape(Path(directory))
            result = ReplayPlanner(replay_task, replay).complete('fixture', {'value': 1}, {'type': 'object'})
            self.assertEqual(result, {'value': 2})
            self.assertEqual(replay_task.calls, task.calls)
            replay.assert_consumed()
            with self.assertRaises(ValueError): ReplayPlanner(Budget(), ReplayTape(Path(directory))).complete('fixture', {'value': 3}, {'type': 'object'})

    def test_replay_hub_executes_real_delegate_and_checks_the_result(self):
        class Hub:
            def __init__(self, ok): self.ok = ok; self.calls = 0
            def call(self, method, **values):
                self.calls += 1
                return {'id': str(self.calls), 'component': 'agent-hub/adopt', 'ok': self.ok}
        with tempfile.TemporaryDirectory() as directory:
            tape = CallTape(Path(directory)); AuditHub(Hub(True), tape).call('health')
            actual = Hub(True)
            self.assertTrue(ReplayHub(actual, ReplayTape(Path(directory))).call('health')['ok'])
            self.assertEqual(actual.calls, 1)
            with self.assertRaises(ValueError): ReplayHub(Hub(False), ReplayTape(Path(directory))).call('health')
