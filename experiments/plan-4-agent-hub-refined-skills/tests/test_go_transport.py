"""Requires the real Go host; no fixed-allow substitute."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM / 'python'))
from hub_gate import HubGate, HubUnavailable


class ActualGoTransportTest(unittest.TestCase):
    def test_ledger_path_is_absolute_before_changing_working_directory(self):
        with patch('hub_gate.subprocess.Popen') as process, patch('hub_gate.threading.Thread'):
            HubGate('relative/gate', 'relative/ledger.jsonl', '/tmp')
            command = process.call_args.args[0]
            self.assertTrue(Path(command[0]).is_absolute())
            self.assertTrue(Path(command[1]).is_absolute())

    def test_control_process_does_not_inherit_model_credentials(self):
        import os
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-openai', 'TYPESAFE_API_KEY': 'synthetic-jev'}, clear=True):
            with patch('hub_gate.subprocess.Popen') as process, patch('hub_gate.threading.Thread'):
                HubGate('/synthetic/gate', '/synthetic/ledger', '/tmp')
                env = process.call_args.kwargs['env']
                self.assertNotIn('OPENAI_API_KEY', env)
                self.assertNotIn('TYPESAFE_API_KEY', env)

    def test_go_enforces_read_pilot_policy_independently_of_python(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = Path(temp) / 'policy.json'
            policy.write_text(json.dumps({'allowed_read_operations': ['KB_search']}))
            gate = HubGate(ARM / 'go/target/banking-gate', Path(temp) / 'ledger.jsonl',
                           ARM.parents[1].parent / 'agent-hub-alpha/agent-festival/schema', read_policy=policy)
            self.addCleanup(gate.close)
            response = gate.call('dispatch', operation='untrusted', payload={'operation': 'transfer_money'}, grants=[])
            self.assertFalse(response['ok'])
            self.assertIn('read-only', response['error'])

    def test_actual_go_binding_and_process_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            gate = HubGate(ARM / 'go/target/banking-gate', Path(temp) / 'ledger.jsonl',
                           ARM.parents[1].parent / 'agent-hub-alpha/agent-festival/schema')
            self.addCleanup(gate.close)
            decision = {'adoption_version': '0.1.0',
                'identity': {'business_request_id': 'episode', 'operation_id': 'operation'},
                'versions': {k: k+'-one' for k in ('evidence', 'rule', 'model', 'readout', 'policy')},
                'grants_at_decision': [{'kind': 'data', 'selector': 'bank://account',
                                         'actions': ['write'], 'effect': 'irreversible'}]}
            self.assertTrue(gate.call('decide', decision=decision, payload={'amount': 5})['ok'])
            self.assertFalse(gate.call('dispatch', operation='operation', payload={'amount': 6},
                                      grants=decision['grants_at_decision'])['ok'])
            self.assertTrue(gate.call('dispatch', operation='operation', payload={'amount': 5},
                                     grants=decision['grants_at_decision'])['ok'])
            gate.close()
            with self.assertRaises(HubUnavailable):
                gate.call('dispatch', operation='operation', payload={'amount': 5}, grants=[])
            events = [json.loads(line) for line in (Path(temp) / 'ledger.jsonl').read_text().splitlines()]
            self.assertEqual(sum(e['outcome']['status'] == 'dispatched' for e in events), 1)
