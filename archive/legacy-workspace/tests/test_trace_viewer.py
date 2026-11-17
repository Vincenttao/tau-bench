"""Regression checks for trace evidence boundaries and incomplete journals."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from trace_viewer import catalog, episode_folder, load_episode, run_summary


class TraceViewerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'experiments' / 'demo' / 'runs' / 'round-01'
        self.episode = {'key': 'example', 'task_id': 'task_062', 'trial': 0}
        self.folder = self.run / 'episodes' / 'example'
        self.folder.mkdir(parents=True)
        (self.run / 'manifest.json').write_text(json.dumps({'episodes': [self.episode]}))

    def test_unscored_partial_journal_does_not_become_zero_reward(self):
        (self.folder / 'official-trajectory.jsonl').write_text(
            json.dumps({'role': 'user', 'content': '<script>hello</script>'}) + '\n{"role":')
        item = next(iter(catalog(self.root).items()))
        summary = run_summary(*item)
        self.assertIsNone(summary['episodes'][0]['reward'])
        bundle, raw = load_episode(self.run, self.episode)
        self.assertEqual(bundle['counts']['conversation'], 1)
        self.assertEqual(len(bundle['warnings']), 1)
        self.assertEqual(raw['0']['content'], '<script>hello</script>')
        self.assertEqual(bundle['events'][0]['locator'], '行 1')

    def test_mcp_link_uses_request_id_and_keeps_distinct_streams(self):
        events = self.folder / 'deepagent' / 'session'
        (events / 'mcp').mkdir(parents=True)
        (events / 'deepagent-events.jsonl').write_text(json.dumps({
            'event': 'tool_end', 'time_ms': 1000,
            'data': {'name': 'skill_tool', 'result': {'success': False}}}) + '\n')
        (events / 'mcp' / 'skill.jsonl').write_text(json.dumps({
            'id': 'skill-3', 'mcp_request_id': 'req-3', 'arguments': {'query': 'hello'}}) + '\n')
        (events / 'mcp' / 'mcp.jsonl').write_text(json.dumps({
            'method': 'tools/call', 'request_id': 'req-3', 'tool_name': 'KB_search'}) + '\n')
        bundle, raw = load_episode(self.run, self.episode)
        self.assertEqual(bundle['events'][0]['category'], 'skill')
        self.assertTrue(bundle['events'][0]['error'])
        self.assertEqual(bundle['events'][1]['stream'], 'mcp')
        self.assertEqual(bundle['events'][1]['call_id'], 'skill-3')
        self.assertEqual(raw['1']['skill_record']['arguments'], {'query': 'hello'})

    def test_result_fallback_preserves_message_locator(self):
        (self.folder / 'result.json').write_text(json.dumps({'simulations': [{
            'messages': [{'role': 'assistant', 'content': 'Hello'}]}]}))
        bundle, _ = load_episode(self.run, self.episode)
        self.assertEqual(bundle['events'][0]['locator'], 'messages[0]')
        self.assertTrue(bundle['events'][0]['source'].endswith('result.json'))

    def test_manifest_cannot_escape_episode_directory(self):
        with self.assertRaises(ValueError):
            episode_folder(self.run, {'key': '../../private'})

    def test_archive_move_preserves_run_id_and_deduplicates_alias(self):
        legacy = self.root / 'experiments/deepagent-todo-skill-mcp/runs/batch'
        legacy.mkdir(parents=True)
        (legacy / 'manifest.json').write_text(json.dumps({'episodes': []}))
        before = {k for k, v in catalog(self.root).items() if v[0] == legacy}
        archived = self.root / 'archive/deepagent-history/runs/batch'
        archived.parent.mkdir(parents=True)
        legacy.rename(archived)
        legacy.symlink_to(archived, target_is_directory=True)
        after = {k for k, v in catalog(self.root).items() if v[0] == archived}
        self.assertEqual(len(after), 1)
        self.assertEqual(before, after)

    def test_nested_archived_hub_baseline_is_discovered(self):
        run = self.root / 'archive/agent-hub-history/v1.0/runs/batch/banking'
        run.mkdir(parents=True)
        (run / 'manifest.json').write_text(json.dumps({'episodes': []}))
        self.assertEqual(sum(v[0] == run for v in catalog(self.root).values()), 1)

    def test_empty_episode_is_explicit(self):
        bundle, _ = load_episode(self.run, self.episode)
        self.assertFalse(bundle['events'])
        self.assertTrue(bundle['warnings'])


if __name__ == '__main__':
    unittest.main()
