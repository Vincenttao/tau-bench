"""Hub-adopted internal workflow and wait nodes; no banking tool capability.

Only the trusted coordinator calls this module after independent judgment. Node
payloads are immutable. Unknown dispatch outcomes are not automatically retried.
"""
import json
from pathlib import Path

from controlled_effects import digest
from task_session import durable_json


class ControlledNodes:
    VERSION = 'banking-evidence-control'
    REGISTERED = {'candidate-comparison', 'dependent-goals', 'receipt-reconciliation', 'await-user'}

    def __init__(self, task, hub, directory):
        self.task, self.hub, self.directory = task, hub, Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def start(self, kind, goal, arguments, proof, *, now):
        state = self.task.call('status', now=now)
        if (kind not in self.REGISTERED or not state['can_dispatch']
                or not any(g['goal_id'] == goal and g['state'] == 'active' for g in state['goals'])
                or proof.get('status') != 'allow' or not proof.get('observation_ref') or not proof.get('model')):
            raise PermissionError('Node lacks a registered route, active goal or verified judgment')
        payload = {'episode': self.task.episode, 'operation': 'internal-node',
                   'arguments': {'kind': kind, 'version': self.VERSION, 'value': arguments}}
        identity = digest([self.task.episode, goal, kind, state['revision'], payload])
        path = self.directory/(identity+'.json')
        if path.exists(): raise PermissionError('Node already started or outcome unknown; no retry')
        grants = [{'kind': 'tool', 'selector': 'internal-node://'+kind+'@'+self.VERSION,
                   'actions': ['execute'], 'effect': 'none'}]
        record = {'id': identity, 'goal': goal, 'kind': kind, 'version': self.VERSION,
                  'payload': payload, 'proof': proof, 'status': 'adoption_attempt'}
        durable_json(path, record)
        decision = {'adoption_version': '0.1.0', 'identity': {
            'business_request_id': self.task.episode, 'operation_id': identity,
            'evaluation_revision': str(state['revision'])}, 'versions': {
                'evidence': digest(proof), 'rule': self.VERSION, 'model': proof['model'],
                'readout': 'internal-node-controller', 'policy': digest(sorted(self.REGISTERED))},
                'grants_at_decision': grants}
        if not self.hub.call('decide', decision=decision, payload=payload)['ok']:
            raise PermissionError('Hub refused node adoption')
        current = self.task.call('status', now=now)
        if current['revision'] != state['revision'] or not current['can_dispatch']:
            raise PermissionError('Task changed before internal node dispatch')
        self.task.call('start_node', node_id=identity, goal=goal, revision=state['revision'],
                       kind=kind, version=self.VERSION, decision_ref=identity, now=now)
        record['status'] = 'dispatch_attempt'; durable_json(path, record)
        if not self.hub.call('dispatch', operation=identity, payload=payload, grants=grants)['ok']:
            raise PermissionError('Hub refused node dispatch')
        record['status'] = 'running'; durable_json(path, record)
        return identity

    def _record(self, identity):
        if not isinstance(identity, str) or len(identity) != 64 or any(c not in '0123456789abcdef' for c in identity):
            raise PermissionError('Invalid node identity')
        return json.loads((self.directory/(identity+'.json')).read_text())

    def finish(self, identity, *, success=True):
        record = self._record(identity)
        final = 'completed' if success else 'failed'
        if record['status'] == final: return
        if record['status'] not in ('running', 'waiting'):
            raise PermissionError('Node result is conflicting or unresolved')
        if not self.hub.call('complete', operation=identity, success=success)['ok']:
            raise RuntimeError('Hub refused node terminal observation')
        self.task.call('observe_node', node_id=identity, status=final)
        record['status'] = final; durable_json(self.directory/(identity+'.json'), record)

    def wait(self, identity):
        record = self._record(identity)
        if record['kind'] != 'await-user' or record['status'] != 'running':
            raise PermissionError('Only a running await-user node can wait')
        self.task.call('observe_node', node_id=identity, status='waiting')
        record['status'] = 'waiting'; durable_json(self.directory/(identity+'.json'), record)

    def resume_waits(self, *, now):
        state = self.task.call('status', now=now)
        goals = {goal['goal_id']: goal for goal in state['goals']}
        for path in self.directory.glob('*.json'):
            record = json.loads(path.read_text())
            if record['kind'] != 'await-user' or record['status'] != 'waiting': continue
            goal = goals.get(record['goal'])
            if goal is None: raise PermissionError('Wait goal missing from authoritative task')
            if goal['state'] == 'active' and not goal['waiting_for'] and state['can_dispatch']:
                self.finish(record['id'])
            elif goal['state'] == 'closed': self.finish(record['id'], success=False)
