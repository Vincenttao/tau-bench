"""MOA-only ownership enforcement before the common official execution queue."""
import copy


class DomainBoundary:
    def __init__(self, actor, rules, events, receipts, deliver, wrapper='call_discoverable_agent_tool'):
        self.actor, self.rules, self.events = actor, rules, events
        self.receipts, self.deliver, self.wrapper = receipts, deliver, wrapper

    def put(self, event):
        snapshot = copy.deepcopy(event)
        if snapshot.get('type') != 'tool_calls' or len(snapshot.get('tool_calls', [])) != 1:
            raise ValueError('Expected one official bank call')
        call = snapshot['tool_calls'][0]
        operations = [call['name']]
        if call['name'] == self.wrapper:
            operations.append(call['arguments'].get('agent_tool_name'))
        for operation in operations:
            if self.actor not in self.rules.get(operation, {}).get('allowed_requesters', []):
                raise PermissionError('Operation is outside this business Agent scope')
        local_id = call['id']
        call['id'] = self.actor + '-' + local_id
        if call['id'] in self.receipts:
            raise ValueError('Duplicate official call identity')
        self.receipts[call['id']] = (self.deliver, local_id)
        self.events.put(snapshot)
