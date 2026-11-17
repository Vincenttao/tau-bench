"""Task-aware adoption and final dispatch, with durable intent and receipt records.

The trusted caller supplies a business judgment and a frozen operation catalog.
This component does not manufacture evidence or enable the official runner.
"""
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import json
from pathlib import Path

from task_session import durable_json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()


class ControlledEffects:
    def __init__(self, task, hub, directory, catalog, live_permission=None):
        self.task, self.hub = task, hub
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.catalog = copy.deepcopy(catalog)
        self.live_permission = live_permission or (lambda operation: operation in self.catalog)

    @contextmanager
    def locked(self):
        with (self.directory/'writer.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def _path(self, operation):
        if not isinstance(operation, str) or len(operation) != 64 or any(c not in '0123456789abcdef' for c in operation):
            raise PermissionError('Invalid internal operation identity')
        return self.directory/(operation+'.json')

    def status(self, operation):
        return json.loads(self._path(operation).read_text())

    def _task(self, goal, now):
        state = self.task.call('status', now=now)
        if not state['can_dispatch'] or not any(g['goal_id'] == goal and g['state'] == 'active' for g in state['goals']):
            raise PermissionError('Task does not allow this goal to dispatch')
        return state

    def adopt(self, goal, step, tool, arguments, judgment, *, now):
        with self.locked():
            state = self._task(goal, now)
            # Import locally to avoid a cycle: runtime_guards also uses the canonical digest.
            from runtime_guards import resolve_operation
            resolved = resolve_operation(tool, arguments, self.catalog)
            effective = resolved['name']
            if not isinstance(step, str) or not step.strip() or not self.live_permission(effective):
                raise PermissionError('Unregistered step/tool or permission unavailable')
            if resolved.get('access') not in ('read', 'write', 'control'):
                raise PermissionError('Unsupported operation role')
            payload = {'episode': self.task.episode, 'operation': tool, 'arguments': copy.deepcopy(arguments)}
            payload_hash = digest(payload)
            if (judgment.get('episode_id') != self.task.episode or judgment.get('goal_id') != goal
                    or judgment.get('status') != 'allow' or judgment.get('payload_hash') != payload_hash
                    or not judgment.get('evidence_refs') or not judgment.get('rule_version') or not judgment.get('model')
                    or not isinstance(judgment.get('conditions'), dict) or not judgment['conditions']
                    or any(v != 'satisfied' for v in judgment['conditions'].values())):
                raise PermissionError('Business judgment missing, unknown, or not bound to final action')
            operation = digest([self.task.episode, goal, step])
            path = self._path(operation)
            if path.exists():
                prior = self.status(operation)
                if prior['payload_hash'] != payload_hash:
                    raise PermissionError('Stable business step cannot change payload')
                if prior['phase'] != 'adopted' or prior['task_revision'] != state['revision']:
                    raise PermissionError('Existing step already dispatched, unknown, or stale')
                return operation
            access = 'write' if resolved['access'] == 'control' else resolved['access']
            grants = [{'kind': 'data', 'selector': 'bank://'+effective, 'actions': [access],
                       'effect': 'irreversible' if access == 'write' else 'reversible'}]
            record = {'operation_id': operation, 'episode_id': self.task.episode, 'goal_id': goal,
                      'step': step, 'task_revision': state['revision'], 'tool': tool, 'effective_tool': effective, 'payload': payload,
                      'payload_hash': payload_hash, 'judgment': copy.deepcopy(judgment), 'grants': grants,
                      'phase': 'adoption_attempt', 'business_status': 'unknown', 'goal_outcome': 'undetermined',
                      'observations': []}
            durable_json(path, record)
            decision = {'adoption_version': '0.1.0', 'identity': {
                'business_request_id': self.task.episode, 'operation_id': operation,
                'evaluation_revision': str(state['revision'])},
                'versions': {'evidence': digest(judgment['evidence_refs']), 'rule': judgment['rule_version'],
                             'model': judgment['model'], 'readout': 'business-judgment-adapter',
                             'policy': digest(self.catalog)}, 'grants_at_decision': grants}
            response = self.hub.call('decide', decision=decision, payload=payload)
            if not response['ok']:
                raise PermissionError('Go adoption refused')
            record['phase'] = 'adopted'; durable_json(path, record)
            return operation

    def dispatch(self, operation, call_id, official_queue, *, now):
        with self.locked():
            record = self.status(operation)
            state = self._task(record['goal_id'], now)
            if (record['phase'] != 'adopted' or state['revision'] != record['task_revision']
                    or not isinstance(call_id, str) or not call_id or not self.live_permission(record.get('effective_tool', record['tool']))):
                raise PermissionError('Duplicate, stale or unauthorized dispatch')
            # Persist before remote request. Failure at any subsequent point is unknown, not retryable.
            record['phase'] = 'dispatch_attempt'; record['call_id'] = call_id
            durable_json(self._path(operation), record)
            response = self.hub.call('dispatch', operation=operation, payload=record['payload'], grants=record['grants'])
            if not response['ok']:
                raise PermissionError('Go final dispatch refused')
            record['phase'] = 'dispatched'; durable_json(self._path(operation), record)
            official_queue.put({'type': 'tool_calls', 'tool_calls': [{
                'id': call_id, 'name': record['tool'], 'arguments': copy.deepcopy(record['payload']['arguments'])}]})

    def receipt(self, operation, call_id, receipt, *, error):
        """Receipt must already be normalized by a trusted per-tool contract parser."""
        with self.locked():
            record = self.status(operation)
            if call_id != record.get('call_id') or record['phase'] not in ('dispatched', 'completed', 'failed'):
                raise PermissionError('Receipt not bound to dispatched operation')
            if not isinstance(receipt, dict) or type(error) is not bool:
                raise PermissionError('Invalid receipt contract')
            observation = digest({'receipt': receipt, 'error': error})
            if observation in record['observations']:
                return
            if record['phase'] in ('completed', 'failed'):
                raise PermissionError('Conflicting terminal receipt')
            status = receipt.get('status', 'unknown')
            if status not in ('accepted', 'pending', 'succeeded', 'rejected', 'unknown'):
                raise PermissionError('Unsupported business status')
            # A transport error does not prove business rejection.
            if error: status = 'unknown'
            record['business_status'] = status
            record['last_receipt'] = copy.deepcopy(receipt)
            # Nonterminal observations can be deduplicated immediately. For a terminal
            # receipt, do not mark it consumed until Go has durably accepted it.
            if status not in ('succeeded', 'rejected'):
                record['observations'].append(observation)
            durable_json(self._path(operation), record)
            if status in ('succeeded', 'rejected'):
                response = self.hub.call('complete', operation=operation, success=status == 'succeeded')
                if not response['ok']: raise RuntimeError('Go terminal receipt refused; reconciliation required')
                record['phase'] = 'completed' if status == 'succeeded' else 'failed'
                record['observations'].append(observation)
                durable_json(self._path(operation), record)
            # Goal acceptance is a separate obligation; operation success never closes the goal here.
