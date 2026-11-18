from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from model_proxy import inspect_response, public_request


class ModelProxyTests(unittest.TestCase):
    def test_episode_paths_are_virtualized_without_changing_business_text_or_input(self):
        root = '/repo/logs/diagnostic/episodes/task_003'
        request = {'model': 'fixture', 'messages': [{'role': 'system', 'content': root+'/skills'},
            {'role': 'tool', 'content': [{'type': 'text', 'text': root+'/evidence'}]},
            {'role': 'user', 'content': 'Please dispute $487.50. Do not cancel the card.'}]}
        result = public_request(request, {root: '/workspace/episode'})
        self.assertNotIn('task_003', str(result))
        self.assertEqual(result['messages'][2], request['messages'][2])
        self.assertEqual(request['messages'][0]['content'], root+'/skills')
        self.assertEqual(result['messages'][0]['content'], '/workspace/episode/skills')

    def test_sse_actual_model_and_usage_are_preserved(self):
        body=b'data: {"model":"actual-model","choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2}}\n\ndata: [DONE]\n\n'
        result=inspect_response(body, 'text/event-stream')
        self.assertEqual(result['actual_model'],'actual-model')
        self.assertEqual(result['usage']['prompt_tokens'],3)

    def test_model_drift_within_stream_and_missing_model_are_refused(self):
        for body in [b'data: {"model":"one"}\n\ndata: {"model":"two"}\n\n',b'{"choices":[]}']:
            with self.assertRaises(ValueError): inspect_response(body,'text/event-stream' if body.startswith(b'data:') else 'application/json')
