import json
import queue
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from benchmark_mcp import BenchmarkMcpFacade, KnowledgeProjection

SCHEMA = [{'function': {'name': 'write_fixture', 'description': 'Synthetic write', 'parameters': {'type': 'object', 'properties': {'amount': {'type': 'number'}}, 'required': ['amount'], 'additionalProperties': False}}}]

class FacadeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.events = queue.Queue()
        self.facade = BenchmarkMcpFacade(SCHEMA, 'episode-a', self.events, self.temp.name, timeout=.1)
    def tearDown(self):
        self.facade.close()
        self.temp.cleanup()
    def args(self, **changes):
        return dict(session_id='episode-a', skill_id='banking-mcp', invocation_id='call-1', arguments={'amount': 8}, **changes)
    def test_scheduler_roundtrip_error_and_duplicate(self):
        result = []
        thread = threading.Thread(target=lambda: result.append(self.facade.invoke('write_fixture', self.args())))
        thread.start()
        event = self.events.get(timeout=1)
        self.assertEqual(event['tool_calls'][0]['name'], 'write_fixture')
        with self.assertRaises(ValueError): self.facade.deliver('wrong-id', 'bad', False)
        self.facade.deliver('call-1', 'official business denial', True)
        thread.join(1)
        self.assertFalse(thread.is_alive())
        self.assertFalse(result[0]['success'])
        self.assertEqual(result[0]['content'], 'official business denial')
        self.assertEqual(self.facade.invoke('write_fixture', self.args())['error'], 'DUPLICATE_INVOCATION_NOT_REEXECUTED')
        self.assertTrue(self.events.empty())
    def test_boundary_and_schema(self):
        for key, value in [('session_id','another'), ('skill_id','forged'), ('operation','hidden_write'), ('arguments',{'bad':1})]:
            args = self.args(); args[key] = value
            with self.assertRaises(Exception): self.facade.invoke('write_fixture', args)
        self.assertTrue(self.events.empty())
    def test_timeout_no_second_write(self):
        self.assertFalse(self.facade.invoke('write_fixture', self.args())['success'])
        self.assertEqual(self.events.qsize(), 1)
        self.facade.invoke('write_fixture', self.args())
        self.assertEqual(self.events.qsize(), 1)
        with self.assertRaises(ValueError): self.facade.deliver('call-1', 'late', False)
    def test_http_handshake_and_auth(self):
        def request(headers):
            req = urllib.request.Request(self.facade.url, json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26'}}).encode(), headers)
            return urllib.request.urlopen(req, timeout=2)
        with self.assertRaises(Exception): request({})
        with request({'Authorization':'Bearer '+self.facade.token}) as result:
            self.assertEqual(result.headers['Mcp-Session-Id'], self.facade.protocol_session)
            self.assertEqual(json.load(result)['result']['protocolVersion'], '2025-03-26')
    def test_wire_catalog_and_named_call(self):
        def rpc(method, params=None, request_id=1):
            headers={'Authorization':'Bearer '+self.facade.token, 'Mcp-Session-Id':self.facade.protocol_session, 'Content-Type':'application/json'}
            body=json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':params or {}}).encode()
            with urllib.request.urlopen(urllib.request.Request(self.facade.url,body,headers),timeout=2) as response:
                return json.load(response)
        tools=rpc('tools/list')['result']['tools']
        self.assertEqual([t['name'] for t in tools],['write_fixture'])
        self.assertEqual(tools[0]['inputSchema']['properties']['arguments'],SCHEMA[0]['function']['parameters'])
        self.assertIn('error',rpc('tools/call',{'name':'skill_execute','arguments':self.args()}))
        self.assertTrue(self.events.empty())
        received=[]
        thread=threading.Thread(target=lambda:received.append(rpc('tools/call',{'name':'write_fixture','arguments':self.args()},2)))
        thread.start()
        event=self.events.get(timeout=1)
        self.assertEqual(event['tool_calls'][0]['name'],'write_fixture')
        self.facade.deliver('call-1','synthetic success',False)
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(json.loads(received[0]['result']['content'][0]['text'])['success'])

    def test_projection_versions_and_dynamic_data(self):
        p = KnowledgeProjection()
        text = '1. Policy\n   ID: P1\n   Score: 1.0000\n   Content: exact policy\n\n\n[Timing: retrieval=1ms]'
        first, metrics = p.project('KB_search', text, 0)
        self.assertIn('exact policy', first)
        second, metrics = p.project('KB_search', text, 0)
        self.assertNotIn('exact policy', second)
        self.assertEqual(metrics['repeated_documents'], 1)
        self.assertIn('exact policy', next(iter(p.docs.values())))
        changed, metrics = p.project('KB_search', text.replace('exact policy','changed policy'), 0)
        self.assertIn('changed policy', changed)
        self.assertEqual(len(p.docs), 2)
        self.assertEqual(p.project('write_fixture', text, 0)[0], text)
        self.assertEqual(p.project('KB_search', 'unknown formatter', 0)[0], 'unknown formatter')
        for _ in range(4): p.project('KB_search', text, 0)
        self.assertEqual(len(p.warned), 1)

if __name__ == '__main__': unittest.main()
