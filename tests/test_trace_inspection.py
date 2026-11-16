"""Decision rules must preserve scoring and capability evidence boundaries."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from trace_inspection import aggregate, case_verdict, inspection, verdict


class VerdictTest(unittest.TestCase):
    def test_success_requires_scored_state_and_valid_full_reward(self):
        self.assertEqual(verdict({'status': 'scored', 'reward': 1}), 'pass')
        self.assertEqual(verdict({'status': 'scored', 'reward': 0}), 'fail')
        self.assertEqual(verdict({'status': 'scored', 'reward': .5}), 'fail')
        self.assertEqual(verdict({'status': 'execution_error'}), 'unscored')
        for value in (True, '1', -1, 2, float('nan'), None):
            self.assertEqual(verdict({'status': 'scored', 'reward': value}), 'review')
        self.assertEqual(verdict({'status': 'running', 'reward': 1}), 'review')

    def test_round_rule_retains_unscored_denominator(self):
        rows = [{'verdict': v} for v in ('pass', 'fail', 'unscored')]
        summary = aggregate(rows)
        self.assertEqual(summary['decision'], 'fail')
        self.assertEqual(summary['pass_rate_scored'], .5)
        self.assertEqual(summary['unscored'], 1)
        self.assertEqual(aggregate([])['decision'], 'pending')
        self.assertIsNone(aggregate([])['pass_rate_scored'])
        self.assertEqual(aggregate([{'verdict': 'pass'}])['decision'], 'pass')
        self.assertEqual(aggregate([{'verdict': 'pass'}, {'verdict': 'review'}])['decision'], 'pending')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.episode = {'key': 'case', 'task_id': 'task_test', 'trial': 0}
        self.folder = self.root / 'episodes' / 'case'
        self.folder.mkdir(parents=True)

    def write_result(self, reward, **extra):
        result = {'tasks': [{'id': 'task_test', 'evaluation_criteria': {'reward_basis': ['DB']}}],
                  'simulations': [{'task_id': 'task_test', 'trial': 0,
                                   'reward_info': {'reward': reward, **extra}}]}
        (self.folder / 'result.json').write_text(json.dumps(result))
        (self.folder / 'status.json').write_text(json.dumps({'status': 'scored', 'reward': 1}))

    def test_conflicting_result_is_review_for_case_and_round(self):
        self.write_result(0)
        status = {'status': 'scored', 'reward': 1}
        self.assertEqual(case_verdict(self.folder, self.episode, status), 'review')
        info = inspection(self.root, self.episode, [], {})
        self.assertEqual(info['grading']['verdict'], 'review')
        self.assertTrue(info['grading']['conflicts'])

    def test_non_scoring_diagnostics_do_not_override_official_result(self):
        self.write_result(1, reward_breakdown={'DB': 1, 'ACTION': 0})
        info = inspection(self.root, self.episode, [], {})
        self.assertEqual(info['grading']['verdict'], 'pass')
        checks = {c['name']: c for c in info['grading']['checks']}
        self.assertTrue(checks['DB']['participates'])
        self.assertFalse(checks['ACTION']['participates'])

    def test_deployed_catalog_is_distinct_from_observed_mcp_calls(self):
        skill = self.folder / 'deepagent' / 'session' / 'skills' / 'example'
        skill.mkdir(parents=True)
        (skill / 'guides').mkdir()
        (skill / 'guides' / 'business.md').write_text('Business acceptance evidence')
        (skill / 'SKILL.md').write_text('---\nname: example\ndescription: Test skill\n---\nUse example.')
        (skill / 'operations.json').write_text(json.dumps({'unused': {
            'name': 'unused', 'description': 'Deployed but not called', 'parameters': {}}}))
        info = inspection(self.root, self.episode, [], {})
        self.assertEqual(info['skills'][0]['description'], 'Test skill')
        self.assertEqual(info['skills'][0]['guides'][0]['content'], 'Business acceptance evidence')
        self.assertEqual(info['operations'][0]['observed_mcp_records'], 0)
        self.assertEqual(info['agent_tools'], [])
        self.assertEqual(info['mcp']['tools'], {})
        self.assertEqual(info['grading']['verdict'], 'unscored')

    def test_model_schema_keeps_provenance_and_is_not_inferred_from_calls(self):
        events = [{'id': '0', 'source': 'events.jsonl', 'locator': '行 1', 'stream': 'internal'},
                  {'id': '1', 'source': 'events.jsonl', 'locator': '行 2', 'stream': 'internal'}]
        raw = {'0': {'event': 'model_request', 'data': {'tools': [{'name': 'allowed', 'parameters': {}}]}},
               '1': {'event': 'tool_start', 'data': {'name': 'unknown'}}}
        info = inspection(self.root, self.episode, events, raw)
        self.assertEqual([t['name'] for t in info['agent_tools']], ['allowed'])
        self.assertEqual(info['agent_tools'][0]['source']['locator'], '行 1')
        self.assertEqual(info['agent_tools'][0]['tool_start_events'], 0)


if __name__ == '__main__':
    unittest.main()
