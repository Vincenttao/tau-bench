from pathlib import Path
import sys
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'python'), str(Path(__file__).resolve().parent)]
import test_input_router
from replay_input_routes import replay


class InputReplayTests(unittest.TestCase):
    def captured(self):
        case = test_input_router.InputRouterTests()
        router, _ = case.router({'g0_respond': .99, 'has_new': .99, 'new0_supported': .99})
        return router.interpret(case.snapshot())

    def test_replays_recorded_observations_without_network(self):
        self.assertEqual(replay(self.captured())['status'], 'passed')

    def test_changed_input_and_missing_response_refuse(self):
        record = self.captured()
        record['input_snapshot']['content'] += ' Cancel everything.'
        with self.assertRaises(ValueError): replay(record)
        record = self.captured(); record['raw_response'] = None
        with self.assertRaises(ValueError): replay(record)
