from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from receipt_registry import ReceiptInterpreter


class ReceiptTests(unittest.TestCase):
    def test_known_control_receipts_do_not_imply_customer_business_completion(self):
        parser = ReceiptInterpreter(None)
        self.assertEqual(parser.parse('unlock_discoverable_agent_tool', {'agent_tool_name': 'tool'}, 'Tool unlocked: tool\nDescription: example', False, now=900)['status'], 'succeeded')
        self.assertEqual(parser.parse('give_discoverable_user_tool', {'discoverable_tool_name': 'apply'}, 'Tool given to user: apply\nDescription: apply', False, now=900)['status'], 'succeeded')
        self.assertEqual(parser.parse('transfer_to_human_agents', {}, 'Transfer successful (reason: other). A human agent will assist you shortly.', False, now=900)['status'], 'accepted')

    def test_semantic_conflict_and_provider_failure_remain_unknown(self):
        class Service:
            class Policy: low=.3; high=.7
            policy=Policy()
            def ask(self, state, questions, now=None): return {q:.99 for q in questions}, 'fixture'
        parser = ReceiptInterpreter(Service())
        self.assertEqual(parser.parse('write', {}, 'some receipt', False, now=900)['status'], 'unknown')
        self.assertEqual(parser.parse('write', {}, 'timeout', True, now=900)['status'], 'unknown')
