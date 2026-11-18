"""MOA-only ownership enforcement before the common official execution queue."""
import copy
import re

from benchmark_mcp import OperationNotAuthorized


def moa_ownership_rules(entries, domain_ids):
    """Grant shared identity logging to MOA domains without changing the frozen study contract."""
    rules = {entry['operation']: copy.deepcopy(entry) for entry in entries}
    verification = rules['log_verification']
    if verification['access'] != 'write' or verification['discoverable']:
        raise ValueError('Unexpected identity verification tool contract')
    verification['allowed_requesters'] = list(domain_ids)
    return rules


def candidate_description(actor, summary, rules):
    """Publish business capabilities, leaving tool discovery to the official KB."""
    writes = sorted(re.sub(r'_\d{4}$', '', op).replace('_', ' ')
                    for op, rule in rules.items()
                    if rule['access'] == 'write' and rule['principal'] == actor
                    and actor in rule['allowed_requesters'])
    return summary + ('. Assigned writes: ' + ', '.join(writes) if writes else '')


class DomainBoundary:
    def __init__(self, actor, rules, events, receipts, deliver, wrapper='call_discoverable_agent_tool',
                 context=None):
        self.actor, self.rules, self.events = actor, rules, events
        self.context = context
        self.receipts, self.deliver, self.wrapper = receipts, deliver, wrapper

    def put(self, event):
        snapshot = copy.deepcopy(event)
        if snapshot.get('type') != 'tool_calls' or len(snapshot.get('tool_calls', [])) != 1:
            raise ValueError('Expected one official bank call')
        call = snapshot['tool_calls'][0]
        operations = [call['name']]
        if call['name'] in (self.wrapper, 'unlock_discoverable_agent_tool'):
            operations.append(call['arguments'].get('agent_tool_name'))
        for operation in operations:
            if self.actor not in self.rules.get(operation, {}).get('allowed_requesters', []):
                owners = self.rules.get(operation, {}).get('allowed_requesters', [])
                if self.context is not None:
                    self.context.refused(self.actor + '-' + call['id'], self.actor, operation, owners)
                raise OperationNotAuthorized(owners)
        local_id = call['id']
        call['id'] = self.actor + '-' + local_id
        if call['id'] in self.receipts:
            raise ValueError('Duplicate official call identity')
        actual = operations[-1]
        if (self.context is not None and call['name'] != 'unlock_discoverable_agent_tool'
                and self.rules[actual]['access'] in ('write', 'control')):
            self.context.start(call['id'], self.actor, actual)
        deliver = self.deliver_history if call['name'] == 'list_discoverable_agent_tools' else self.deliver
        self.receipts[call['id']] = (deliver, local_id)
        self.events.put(snapshot)

    def deliver_history(self, local_id, content, error):
        """Only project names actually returned by the official history operation."""
        if not error and content.startswith('Your called agent tools:'):
            names = re.findall(r'^   tool_name: ([a-zA-Z0-9_]+)$', content, re.MULTILINE)
            allowed = [name for name in names
                       if self.actor in self.rules.get(name, {}).get('allowed_requesters', [])]
            content = ('Previously called tools available to this domain: ' + ', '.join(allowed)
                       if allowed else 'No authorized tool names found in the returned history.')
        self.deliver(local_id, content, error)
