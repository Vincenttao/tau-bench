from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from model_proxy import inspect_response


class ModelProxyTests(unittest.TestCase):
    def test_sse_actual_model_and_usage_are_preserved(self):
        body=b'data: {"model":"actual-model","choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2}}\n\ndata: [DONE]\n\n'
        result=inspect_response(body, 'text/event-stream')
        self.assertEqual(result['actual_model'],'actual-model')
        self.assertEqual(result['usage']['prompt_tokens'],3)

    def test_model_drift_within_stream_and_missing_model_are_refused(self):
        for body in [b'data: {"model":"one"}\n\ndata: {"model":"two"}\n\n',b'{"choices":[]}']:
            with self.assertRaises(ValueError): inspect_response(body,'text/event-stream' if body.startswith(b'data:') else 'application/json')
