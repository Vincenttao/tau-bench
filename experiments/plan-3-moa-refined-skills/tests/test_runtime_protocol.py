from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from runtime_protocol import customer_reply


class RuntimeProtocolTest(unittest.TestCase):
    def test_only_actual_customer_output_is_returned(self):
        pending = {'id': 'task-a', 'status': {'state': 'TASK_STATE_INPUT_REQUIRED',
                   'message': {'parts': [{'text': 'Which account?'}]}}}
        self.assertEqual(customer_reply(pending)['content'], 'Which account?')
        self.assertTrue(customer_reply(pending)['waiting'])
        complete = {'id': 'task-a', 'status': {'state': 'TASK_STATE_COMPLETED'},
                    'artifacts': [{'parts': [{'text': 'Application submitted.'}]}]}
        self.assertFalse(customer_reply(complete)['waiting'])

    def test_failed_and_empty_completed_are_not_successful_answers(self):
        for state in ('TASK_STATE_FAILED', 'TASK_STATE_COMPLETED', 'TASK_STATE_WORKING'):
            with self.subTest(state=state), self.assertRaises(ValueError):
                customer_reply({'id': 'task-a', 'status': {'state': state}})
