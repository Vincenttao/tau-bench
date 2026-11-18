import json
from pathlib import Path
import queue
import sys
import tempfile
import unittest
from types import SimpleNamespace

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM / 'python'), str(ARM.parents[1] / 'shared/python')]
from benchmark_mcp import BenchmarkMcpFacade
from domain_boundary import DomainBoundary
from moa_pilot_agent import MoaPilotAgent
from receipt_context import ReceiptContext


class LateReceiptTest(unittest.TestCase):
    def test_late_duplicate_unknown_closed_and_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            owners = {}
            for episode in ('episode-a', 'episode-b'):
                root = Path(directory) / episode
                root.mkdir()
                events = queue.Queue()
                context = ReceiptContext(root)
                facade = BenchmarkMcpFacade([{'function': {'name': 'write',
                    'parameters': {'type': 'object'}}}], episode, events, root, timeout=.01)
                self.addCleanup(facade.close)
                seen = []
                owner = SimpleNamespace(receipt_context=context, receipts={}, completed_calls=set(),
                                        _record=lambda *args, seen=seen: seen.append(args))
                facade.events = DomainBoundary('domain', {'write': {'allowed_requesters': ['domain'],
                    'access': 'write'}}, events, owner.receipts, facade.deliver_if_waiting, context=context)
                args = {'skill_id': 'banking-mcp', 'session_id': episode, 'invocation_id': 'one', 'arguments': {}}
                self.assertFalse(facade.invoke('write', args)['success'])  # real waiter expired
                self.assertEqual(events.qsize(), 1)
                self.assertEqual(json.loads(context.path.read_text())['domain-one']['state'], 'no official reply yet')
                owners[episode] = owner, facade, events, seen
            def send(owner, call, content):
                MoaPilotAgent._send(owner, {'type': 'tool_result', 'tool_call_id': call,
                                            'content': content, 'error': False})
            for episode, (owner, facade, events, seen) in owners.items():
                if episode == 'episode-b':
                    self.assertNotIn('receipt-a', owner.receipt_context.path.read_text())
                    facade.closed = True
                send(owner, 'other', 'unrelated')
                send(owner, 'domain-one', 'receipt-' + episode[-1])
                send(owner, 'domain-one', 'duplicate body')
                result = json.loads(owner.receipt_context.path.read_text())
                self.assertEqual(result['domain-one']['reply'], 'receipt-' + episode[-1])
                self.assertEqual([e for e, _ in seen], ['unmatched_official_reply',
                                                        'official_receipt', 'duplicate_official_reply'])
                self.assertEqual(events.qsize(), 1)
