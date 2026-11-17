import copy
from pathlib import Path
import queue
import sys
import tempfile
import unittest

ARM = Path(__file__).resolve().parents[1]
ROOT = ARM.parents[1]
sys.path[:0] = [str(ARM / 'python'), str(ROOT / 'shared/python')]
from hub_gate import HubGate, HubUnavailable
from hub_boundary import GatedEventQueue


class EffectBoundaryTest(unittest.TestCase):
    def test_go_must_authorize_exact_payload_before_official_queue(self):
        with tempfile.TemporaryDirectory() as temp:
            hub = HubGate(ARM / 'go/target/banking-gate', Path(temp) / 'ledger.jsonl',
                          ROOT.parent / 'agent-hub-alpha/agent-festival/schema')
            self.addCleanup(hub.close)
            official = queue.Queue()
            event = {'type': 'tool_calls', 'tool_calls': [{'id': 'call-one', 'name': 'write', 'arguments': {'amount': 5}}]}
            def decision_provider(call):
                return {'adoption_version': '0.1.0',
                    'identity': {'business_request_id': 'episode', 'operation_id': call['id']},
                    'versions': {k: k+'-fixture' for k in ('evidence', 'rule', 'model', 'readout', 'policy')},
                    'grants_at_decision': [{'kind': 'data', 'selector': 'bank://account',
                                          'actions': ['write'], 'effect': 'irreversible'}]}
            boundary = GatedEventQueue(official, hub, 'episode', decision_provider,
                                      lambda call: decision_provider(call)['grants_at_decision'])
            boundary.put(event)
            self.assertEqual(official.get_nowait(), event)
            changed = copy.deepcopy(event)
            changed['tool_calls'][0]['arguments']['amount'] = 6
            with self.assertRaises(PermissionError):
                boundary.put(changed)
            self.assertTrue(official.empty())
            revoked = copy.deepcopy(event)
            revoked['tool_calls'][0]['id'] = 'revoked'
            boundary.live_grants = lambda call: []
            with self.assertRaises(PermissionError):
                boundary.put(revoked)
            self.assertTrue(official.empty())
            hub.close()
            event['tool_calls'][0]['id'] = 'call-two'
            with self.assertRaises(HubUnavailable):
                boundary.put(event)
            self.assertTrue(official.empty())
