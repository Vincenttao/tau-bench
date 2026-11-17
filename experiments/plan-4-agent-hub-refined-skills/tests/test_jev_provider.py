import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from jev_provider import JevClient, JevError, claim_request, interpret_claim, visible_box


class JevProviderTests(unittest.TestCase):
    def test_long_context_is_explicit_and_only_used_for_large_requests(self):
        client = JevClient('test-secret', long_context=True)
        sent = []
        class Reply:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'model': 'jev-1.14.0', 'answers': {},
                'usage': {'input_tokens': 1, 'output_tokens': 0}}).encode()
        def fake(req, timeout): sent.append(req); return Reply()
        with patch.object(client.opener, 'open', side_effect=fake):
            for size in (1, 70_000): client.ask({'state': 'x'*size, 'questions': {}})
        headers = [{k.lower(): v for k, v in request.header_items()} for request in sent]
        self.assertNotIn('typesafe-danger-zone-long-context', headers[0])
        self.assertEqual(headers[1]['typesafe-danger-zone-long-context'], 'true')

    def response(self, probability):
        return {'model': 'jev-1.14.0', 'answers': {'supported': {'type': 'noul', 'noul': probability},
                'evidence_present': {'type': 'noul', 'noul': 0.99}},
                'usage': {'input_tokens': 10, 'output_tokens': 2}}

    def test_unknown_is_not_permission_and_missing_evidence_blocks(self):
        self.assertEqual(interpret_claim(self.response(0.5)), 'unknown')
        self.assertEqual(interpret_claim(self.response(0.99)), 'supported')
        self.assertEqual(interpret_claim(self.response(0.01)), 'unsupported')
        r = self.response(0.99)
        r['answers']['evidence_present']['noul'] = 0.1
        self.assertEqual(interpret_claim(r), 'unknown')

    def test_malformed_probability_is_error(self):
        for p in [True, float('nan'), -0.1, 1.1, '0.9']:
            with self.assertRaises(JevError):
                interpret_claim(self.response(p))

    def test_image_header_and_no_secret_in_payload(self):
        client = JevClient('test-secret')
        sent = []
        class Reply:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'model':'jev-1.14.0','answers':{},'usage':{'input_tokens':1,'output_tokens':0}}).encode()
        def fake(req, timeout):
            sent.append(req)
            return Reply()
        with patch.object(client.opener, 'open', side_effect=fake):
            client.ask({'model':'jev-1.14.0','state':'photo','questions':{'target':{'type':'box','instructions':'red rectangle'}},'assets':{'photo':{}}})
        self.assertEqual(dict((k.lower(),v) for k,v in sent[0].header_items())['typesafe-danger-zone-images'], 'true')
        self.assertNotIn(b'test-secret', sent[0].data)

    def test_api_error_not_false_and_no_retry(self):
        client = JevClient('test-secret')
        with patch.object(client.opener, 'open', side_effect=HTTPError('url',401,'secret-body',{},None)) as call:
            with self.assertRaisesRegex(JevError, 'HTTP 401') as err:
                client.ask(claim_request('evidence', 'claim'))
            self.assertNotIn('secret-body', str(err.exception))
            self.assertEqual(call.call_count, 1)

    def test_box_requires_presence_and_valid_coordinates(self):
        r={'answers':{'present':{'type':'noul','noul':0.1},'target':{'type':'box','box':{'left':0.2,'right':0.6,'top':0.2,'bottom':0.6}}}}
        self.assertIsNone(visible_box(r))
        r['answers']['present']['noul']=0.99
        self.assertEqual(visible_box(r)['left'],0.2)
        r['answers']['target']['box']['right']=0.1
        with self.assertRaises(JevError): visible_box(r)
