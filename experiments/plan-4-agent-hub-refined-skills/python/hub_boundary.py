"""Arm-4-only final effect queue. Requires a trusted decision provider.

The full banking evidence/judgment provider is not implemented yet. Tests use
explicit synthetic decisions; this class alone does not enable the live arm.
"""
import copy


class GatedEventQueue:
    def __init__(self, official_queue, hub, episode_id, decision_provider, live_grants):
        self.official_queue = official_queue
        self.hub = hub
        self.episode_id = episode_id
        self.decision_provider = decision_provider
        self.live_grants = live_grants

    def put(self, event):
        # Snapshot before authorization, so callers cannot mutate a queued payload.
        snapshot = copy.deepcopy(event)
        if snapshot.get('type') != 'tool_calls' or len(snapshot.get('tool_calls', [])) != 1:
            raise ValueError('Expected one bank operation at the final effect boundary')
        call = snapshot['tool_calls'][0]
        decision = self.decision_provider(copy.deepcopy(call))
        identity = decision.get('identity', {})
        if identity.get('business_request_id') != self.episode_id or not identity.get('operation_id'):
            raise PermissionError('Decision is not bound to this episode and operation')
        payload = {'episode': self.episode_id, 'operation': call['name'], 'arguments': call['arguments']}
        adopted = self.hub.call('decide', decision=decision, payload=payload)
        if not adopted['ok']:
            raise PermissionError('Hub adoption refused')
        dispatched = self.hub.call('dispatch', operation=identity['operation_id'], payload=payload,
                                   grants=self.live_grants(copy.deepcopy(call)))
        if not dispatched['ok']:
            raise PermissionError('Hub final dispatch refused')
        self.official_queue.put(snapshot)
