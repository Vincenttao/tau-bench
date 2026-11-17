import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from analyze_latency import extract, quantile, union_seconds


class LatencyAnalysisTest(unittest.TestCase):
    def test_overlapping_spans_are_not_added_as_wall_time(self):
        self.assertEqual(union_seconds([(1, 5), (2, 4), (4, 7), (10, 11)]), 7)

    def test_empty_and_single_sample(self):
        self.assertIsNone(quantile([], .95))
        self.assertEqual(quantile([12], .95), 12)
        self.assertEqual(union_seconds([]), 0)

    def fixture(self, root):
        folder = Path(root) / 'P07-task_001-r00-a00'
        episode = folder / 'episodes/test'
        (episode / 'java').mkdir(parents=True)
        result = {'simulations': [{'task_id': 'task_001', 'duration': 5,
                  'reward_info': {'reward': 0}, 'termination_reason': 'user_stop',
                  'messages': [
                      {'role': 'assistant', 'tool_calls': [
                          {'id': 'a', 'name': 'KB_search', 'arguments': {'query': 'q'}}]},
                      {'role': 'tool', 'id': 'a', 'content': 'ID: doc_x\nID: doc_y'},
                      {'role': 'assistant', 'tool_calls': [
                          {'id': 'b', 'name': 'KB_search', 'arguments': {'query': 'q'}}]},
                      {'role': 'tool', 'id': 'b', 'content': 'ID: doc_x'}]}]}
        (episode / 'result.json').write_text(json.dumps(result))
        (episode / 'java/log.stderr.log').write_text(
            '23:59:59.000 INFO event=react_model_call_completed status=success '
            'model_duration_ms=1000 prompt_tokens=100 completion_tokens=10 total_tokens=110\n'
            '00:00:02.000 INFO event=react_model_call_completed status=success '
            'model_duration_ms=2000 prompt_tokens=200 completion_tokens=20 total_tokens=220\n')
        return folder, episode

    def test_midnight_is_unfolded_and_token_counts_are_not_unique_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = self.fixture(tmp)
            row = extract(folder)
            self.assertEqual(row['java_model_interval_union_seconds'], 3)
            self.assertEqual(row['java_prompt_tokens']['sum'], 300)
            self.assertEqual(row['java_model_interval_union_fraction'], .6)

    def test_repeated_documents_and_queries_are_counted_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = self.fixture(tmp)
            row = extract(folder)
            self.assertEqual(row['KB_exact_repeated_query_count'], 1)
            self.assertEqual(row['KB_document_occurrences'], 3)
            self.assertEqual(row['KB_distinct_document_ids'], 2)
            self.assertEqual(row['KB_repeat_document_occurrences'], 1)

    def test_extraction_preserves_source_and_missing_result_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, episode = self.fixture(tmp)
            path = episode / 'result.json'
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            row = extract(folder)
            self.assertEqual(before, row['source_result_sha256'])
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertIsNone(extract(Path(tmp) / 'unstarted'))
