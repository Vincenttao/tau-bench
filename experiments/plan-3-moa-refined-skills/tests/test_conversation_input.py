import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from conversation_input import task_input


class ConversationInputTest(unittest.TestCase):
    def test_retry_preserves_visible_answers_without_hidden_policy(self):
        messages = [SimpleNamespace(role='system', content='hidden expected answer'),
                    SimpleNamespace(role='user', content='Personal card, low annual fee'),
                    SimpleNamespace(role='assistant', content='Which subscription?'),
                    SimpleNamespace(role='tool', content='internal result')]
        result = task_input('Try again', messages, False)
        self.assertIn('Personal card, low annual fee', result)
        self.assertNotIn('hidden expected answer', result)
        self.assertNotIn('internal result', result)
        self.assertEqual(json.loads(result.split('\n', 1)[1])['current_request'], 'Try again')

    def test_pending_answer_is_not_wrapped(self):
        self.assertEqual(task_input('Yes', [SimpleNamespace(role='user', content='old')], True), 'Yes')

    def test_first_request_unchanged(self):
        self.assertEqual(task_input('Compare cards', [], False), 'Compare cards')
        self.assertEqual(task_input('Compare cards', [SimpleNamespace(
            role='assistant', content='How can I help?')], False), 'Compare cards')
