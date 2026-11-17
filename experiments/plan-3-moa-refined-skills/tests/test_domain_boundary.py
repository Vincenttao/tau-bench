import copy
from pathlib import Path
import queue
import sys
import unittest

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM / 'python'))
from domain_boundary import DomainBoundary, moa_ownership_rules


class DomainBoundaryTest(unittest.TestCase):
    def test_shared_identity_logging_is_allowed_without_mutating_other_rules(self):
        entries = [{'operation': 'log_verification', 'access': 'write', 'discoverable': False,
                    'allowed_requesters': ['account-opening-agent']},
                   {'operation': 'other_write', 'allowed_requesters': ['cards']}]
        rules = moa_ownership_rules(entries, ['cards', 'payments'])
        self.assertEqual(entries[0]['allowed_requesters'], ['account-opening-agent'])
        self.assertEqual(rules['other_write']['allowed_requesters'], ['cards'])
        for actor in ('cards', 'payments'):
            events, receipts = queue.Queue(), {}
            boundary = DomainBoundary(actor, rules, events, receipts, lambda *args: None)
            boundary.put({'type': 'tool_calls', 'tool_calls': [
                {'id': 'v', 'name': 'log_verification', 'arguments': {}}]})
            self.assertEqual(events.get_nowait()['tool_calls'][0]['name'], 'log_verification')
        with self.assertRaises(PermissionError):
            DomainBoundary('payments', rules, queue.Queue(), {}, lambda *args: None).put(
                {'type': 'tool_calls', 'tool_calls': [{'id': 'w', 'name': 'other_write', 'arguments': {}}]})

    def test_wrapper_cannot_bypass_business_owner(self):
        rules = {'wrapper': {'allowed_requesters': ['cards', 'payments']},
                 'pay': {'allowed_requesters': ['payments']}, 'read': {'allowed_requesters': ['cards', 'payments']}}
        events = queue.Queue()
        receipts = {}
        boundary = DomainBoundary('cards', rules, events, receipts, lambda *args: None, wrapper='wrapper')
        blocked = {'type': 'tool_calls', 'tool_calls': [{'id': 'one', 'name': 'wrapper',
                    'arguments': {'agent_tool_name': 'pay', 'arguments': '{}'}}]}
        with self.assertRaises(PermissionError):
            boundary.put(blocked)
        self.assertTrue(events.empty())
        event = copy.deepcopy(blocked)
        event['tool_calls'][0]['name'] = 'read'
        event['tool_calls'][0]['arguments'] = {}
        boundary.put(event)
        self.assertEqual(events.get_nowait()['tool_calls'][0]['id'], 'cards-one')
        self.assertIn('cards-one', receipts)

    def test_distinct_domain_local_call_ids_cannot_collide(self):
        events, receipts = queue.Queue(), {}
        rules = {'read': {'allowed_requesters': ['cards', 'payments']}}
        event = {'type': 'tool_calls', 'tool_calls': [{'id': 'one', 'name': 'read', 'arguments': {}}]}
        for name in ('cards', 'payments'):
            DomainBoundary(name, rules, events, receipts, lambda *args: None).put(event)
        self.assertEqual(set(receipts), {'cards-one', 'payments-one'})
        self.assertEqual(events.qsize(), 2)
