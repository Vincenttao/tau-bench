"""Actual Go-gated read-only integration pilot; full bank-write judgment is pending."""
import atexit
import hashlib
import json
import os
from pathlib import Path

from deepagent_java_agent import DeepAgentJavaAgent
from hub_gate import HubGate
from hub_boundary import GatedEventQueue

ROOT = Path(__file__).resolve().parents[3]
ARM = Path(__file__).resolve().parents[1]
GATES = []


@atexit.register
def close_gates():
    for gate in GATES:
        gate.close()
    GATES.clear()


class HubPilotAgent(DeepAgentJavaAgent):
    def _start(self, state):
        directory = Path(os.environ['JAVA_LOG_DIR']).parent / 'hub'
        directory.mkdir(parents=True, exist_ok=False)
        ownership = json.loads((ROOT / 'studies/banking-architecture-comparison/contracts/business-ownership.json').read_text())
        reads = {entry['operation'] for entry in ownership['operations'] if entry['access'] == 'read'
                 and entry['principal'] != 'official-user-simulator'}
        policy = directory / 'read-policy.json'
        policy.write_text(json.dumps({'allowed_read_operations': sorted(reads),
                                     'scope': 'read-only integration pilot; bank writes refused'}))
        self.hub = HubGate(ARM / 'go/target/banking-gate', directory / 'ledger.jsonl',
                           ROOT.parent / 'agent-hub-alpha/agent-festival/schema', read_policy=policy)
        GATES.append(self.hub)
        super()._start(state)

        def decision(call):
            if call['name'] not in reads:
                raise PermissionError('Full write judgment is not implemented; read-only pilot refused operation')
            return {'adoption_version': '0.1.0', 'identity': {
                        'business_request_id': self.session_id, 'operation_id': call['id']},
                    'versions': {'evidence': hashlib.sha256(self.domain_policy.encode()).hexdigest(),
                                 'rule': 'official-read-access', 'model': os.environ['OPENAI_MODEL'],
                                 'readout': 'public-operation-access', 'policy': 'read-only-pilot'},
                    'grants_at_decision': [{'kind': 'data', 'selector': 'bank://' + call['name'],
                                           'actions': ['read'], 'effect': 'reversible'}]}
        self.facade.events = GatedEventQueue(self.events, self.hub, self.session_id, decision,
                                             lambda call: decision(call)['grants_at_decision'])

    def _send(self, value):
        if value.get('type') == 'tool_result':
            result = self.hub.call('complete', operation=value['tool_call_id'], success=not value['error'])
            if not result['ok']:
                raise RuntimeError('Go receipt ledger refused completion')
        super()._send(value)

    def generate_next_message(self, message, state):
        result, state = super().generate_next_message(message, state)
        result.raw_data['bridge'] = 'deepagent-actual-go-read-pilot-write-judgment-pending'
        return result, state
