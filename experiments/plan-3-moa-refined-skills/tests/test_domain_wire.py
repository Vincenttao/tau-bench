"""Exercise the real MCP response after a policy refusal on the official queue boundary."""
import json
from pathlib import Path
import queue
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from urllib.request import Request, urlopen

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM / 'python'), str(ARM.parents[1] / 'shared/python')]
from benchmark_mcp import BenchmarkMcpFacade
from domain_boundary import DomainBoundary


class DomainWireTest(unittest.TestCase):
    def test_refusal_and_next_call_share_one_session(self):
        wrapper = 'call_discoverable_agent_tool'
        schema = {'type': 'object', 'properties': {'agent_tool_name': {'type': 'string'}}}
        tools = [{'function': {'name': wrapper, 'parameters': schema}}]
        rules = {wrapper: {'allowed_requesters': ['cards', 'payments']},
                 'pay': {'allowed_requesters': ['payments']},
                 'read': {'allowed_requesters': ['cards', 'payments']}}
        events, receipts = queue.Queue(), {}
        with tempfile.TemporaryDirectory() as directory:
            facade = BenchmarkMcpFacade(tools, 'session-cards', events, directory, timeout=3)
            try:
                facade.events = DomainBoundary('cards', rules, events, receipts, facade.deliver)

                def call(target, invocation):
                    args = {'skill_id': 'banking-mcp', 'session_id': 'session-cards',
                            'invocation_id': invocation, 'arguments': {'agent_tool_name': target}}
                    body = {'jsonrpc': '2.0', 'id': invocation, 'method': 'tools/call',
                            'params': {'name': wrapper, 'arguments': args}}
                    headers = {'Authorization': 'Bearer ' + facade.token,
                               'Mcp-Session-Id': facade.protocol_session}
                    with urlopen(Request(facade.url, json.dumps(body).encode(), headers), timeout=4) as resp:
                        return json.load(resp)['result']

                refused = call('pay', 'r1')
                self.assertTrue(refused['isError'])
                details = json.loads(refused['content'][0]['text'])
                self.assertEqual(details['error'], 'DOMAIN_NOT_AUTHORIZED')
                self.assertFalse(details['submitted'])
                self.assertTrue(events.empty())
                self.assertFalse(receipts)
                self.assertFalse(facade.pending)
                self.assertTrue(call('pay', 'r1')['isError'])
                self.assertTrue(events.empty())
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(call, 'read', 'r2')
                    event = events.get(timeout=2)
                    deliver, local_id = receipts.pop(event['tool_calls'][0]['id'])
                    deliver(local_id, 'Synthetic result', False)
                    self.assertFalse(future.result()['isError'])
            finally:
                facade.close()
