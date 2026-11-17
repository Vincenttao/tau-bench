"""Jev observations -> auditable input proposal. Never dispatches or mutates tasks.

Only trusted official-visible snapshots are accepted. Thresholds must be explicitly
supplied by the caller; test policies are not a frozen banking policy.
"""
from dataclasses import dataclass, asdict
import copy
import hashlib
import json
import math

from jev_provider import JevError, probability


@dataclass(frozen=True)
class RoutingPolicy:
    policy_id: str
    low: float
    high: float
    request_model: str
    expected_model: str

    def __post_init__(self):
        if (any(type(v) not in (float, int) or not math.isfinite(v) for v in (self.low, self.high))
                or not 0 <= self.low < self.high <= 1
                or any(not isinstance(v, str) or not v.strip()
                       for v in (self.policy_id, self.request_model, self.expected_model))):
            raise ValueError('Explicit versioned routing policy required')


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Nonempty text required')


def validate_snapshot(snapshot):
    fields = {'episode_id', 'message_id', 'based_on_revision', 'source', 'kind', 'content',
              'last_question', 'context_complete', 'goals', 'new_goal_proposals'}
    if not isinstance(snapshot, dict) or set(snapshot) - {'unresolved_inputs'} != fields:
        raise ValueError('Invalid input snapshot fields; evaluator-only data is prohibited')
    for key in ('episode_id', 'message_id', 'content'):
        _text(snapshot[key])
    if (snapshot['source'] != 'official-user' or snapshot['kind'] != 'free_text'
            or type(snapshot['based_on_revision']) is not int or snapshot['based_on_revision'] < 0
            or type(snapshot['context_complete']) is not bool
            or not isinstance(snapshot['last_question'], str)):
        raise ValueError('Invalid trusted envelope or revision')
    goals, proposals = snapshot['goals'], snapshot['new_goal_proposals']
    if (not isinstance(goals, list) or not isinstance(proposals, list)
            or len(goals) > 32 or len(proposals) > 32):
        raise ValueError('Candidate bound exceeded or invalid list')
    ids = set()
    for goal in goals:
        if not isinstance(goal, dict) or set(goal) != {'goal_id', 'episode_id', 'description', 'state', 'waiting_for'}:
            raise ValueError('Invalid goal fields')
        for key in ('goal_id', 'description'):
            _text(goal[key])
        if (goal['goal_id'] in ids or goal['episode_id'] != snapshot['episode_id']
                or goal['state'] not in ('active', 'waiting', 'closed')
                or not isinstance(goal['waiting_for'], str)):
            raise ValueError('Invalid candidate scope or state')
        ids.add(goal['goal_id'])
    seen = set()
    unresolved = snapshot.get('unresolved_inputs', [])
    if not isinstance(unresolved, list):
        raise ValueError('Invalid clarification context')
    unresolved_ids = set()
    for item in unresolved:
        if not isinstance(item, dict) or set(item) != {'message_id', 'content'}:
            raise ValueError('Invalid unresolved input')
        _text(item['message_id']); _text(item['content'])
        if item['message_id'] in unresolved_ids:
            raise ValueError('Duplicate clarification identity')
        unresolved_ids.add(item['message_id'])
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {'description', 'quote'}:
            raise ValueError('Invalid new goal proposal; model IDs are prohibited')
        for key in ('description', 'quote'):
            _text(proposal[key])
        pair = (proposal['description'], proposal['quote'])
        if proposal['quote'] not in snapshot['content'] or pair in seen:
            raise ValueError('Fabricated or duplicate proposal evidence')
        seen.add(pair)


class InputRouter:
    def __init__(self, client, policy):
        if not isinstance(policy, RoutingPolicy):
            raise ValueError('RoutingPolicy required')
        self.client, self.policy = client, policy

    def request(self, snapshot):
        validate_snapshot(snapshot)
        questions = {
            'ambiguous': {'type': 'noul', 'instructions':
                'Does the current user message leave unresolved which existing goal or requested change it refers to?'},
            'has_new': {'type': 'noul', 'instructions':
                'Does the current user message request a business service not yet represented in the existing task index `goals`? '
                '`new_goal_proposals` are uncommitted suggestions, not existing tasks.',
                'criteria': {'true': 'The user requests a service absent from existing goals; when goals is empty, any requested business service is new to the index.',
                             'false': 'The message only answers, changes, pauses, resumes, cancels or queries an existing goal, or requests no business service.'}},
            'no_business': {'type': 'noul', 'instructions':
                'Is the current user message only social conversation with no business request, change, answer, or progress question?'},
            'covered': {'type': 'noul', 'instructions':
                'Can every business request in the current message be associated with a listed existing goal or a proposed new goal?',
                'criteria': {'true': 'Every request has a corresponding existing goal or new proposal. Changes to, pausing, resuming, cancelling, and asking about an existing goal count as references to that goal; the requested changes need not already appear in its old description.',
                             'false': 'At least one requested business service has no corresponding existing goal or new proposal.'}}
        }
        verbs = {
            'respond': 'supply the specific missing information requested in its waiting_for field',
            'modify': 'correct or replace a previously stated specific requirement, rather than provide the first answer to a request for missing requirements',
            'query': 'ask about its progress or known outcome',
        }
        for i, goal in enumerate(snapshot['goals']):
            if goal['state'] == 'active' and not goal['waiting_for']:
                questions[f'g{i}_reaffirm'] = {'type': 'noul', 'instructions': {
                    'question': 'Does the current message restate or reaffirm this already active business request without changing its requirements? This supplies no new consent or confirmation.',
                    'goal': goal}}
            for action, verb in verbs.items():
                if action == 'respond' and not goal['waiting_for']:
                    continue  # No pending slot is a known protocol fact, not a model judgment.
                questions[f'g{i}_{action}'] = {'type': 'noul', 'instructions': {
                    'question': f'Does the current message {verb} for this goal?',
                    'goal': goal}}
            questions[f'g{i}_lifecycle_requested'] = {'type': 'noul', 'instructions': {
                'question': 'Does the CURRENT user message explicitly request cancelling, temporarily pausing, or resuming execution of this goal?',
                'goal': goal['description']}, 'criteria': {
                    'true': 'The user explicitly asks to stop, defer or resume this service.',
                    'false': 'The user provides requested information, states product requirements, asks about progress, or makes no execution-lifecycle request. An existing waiting state is not a new pause request.'}}
            questions[f'g{i}_lifecycle_action'] = {'type': 'choice', 'instructions': {
                'question': 'Which execution-lifecycle change does the CURRENT message request for this goal?',
                'goal': goal['description']}, 'criteria': {
                    'cancel': 'Permanently stop this requested service.',
                    'pause': 'Defer the service while retaining it for later continuation.',
                    'resume': 'Continue a previously paused service.'}}
        for i, proposal in enumerate(snapshot['new_goal_proposals']):
            questions[f'new{i}_supported'] = {'type': 'noul', 'instructions': {
                'question': 'Does the quoted user text explicitly request this proposed new service?',
                'proposal': proposal}}
        for i, item in enumerate(snapshot.get('unresolved_inputs', [])):
            questions[f'clarify{i}_resolved'] = {'type': 'noul', 'instructions': {
                'question': 'Does the complete current message resolve the ambiguity in this earlier user message?',
                'earlier_message': item}}
        return {'model': self.policy.request_model, 'state': copy.deepcopy(snapshot), 'questions': questions}

    def interpret(self, snapshot):
        request = self.request(snapshot)
        # Copy once: caller mutation cannot change the stored input/interpretation.
        snapshot = request['state']
        result = {'schema_version': 1, 'episode_id': snapshot['episode_id'],
                  'message_id': snapshot['message_id'], 'based_on_revision': snapshot['based_on_revision'],
                  'status': 'clarify', 'reason': 'context_incomplete', 'targets': [], 'new_goal_proposals': [],
                  'policy_id': self.policy.policy_id, 'policy': asdict(self.policy),
                  'input_snapshot': copy.deepcopy(snapshot), 'request': copy.deepcopy(request),
                  'input_hash': hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                  'evidence_refs': [{'message_id': snapshot['message_id'], 'quote': snapshot['content']}],
                  'raw_response': None}
        result['resolved_messages'] = []
        if not snapshot['context_complete']:
            return result
        response = self.client.ask(copy.deepcopy(request))
        if not isinstance(response, dict) or response.get('model') != self.policy.expected_model:
            raise JevError('Input routing provider model drift; progression refused')
        if not isinstance(response.get('answers'), dict) or set(response['answers']) != set(request['questions']):
            raise JevError('Input routing question/answer mismatch')
        usage = response.get('usage')
        if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
                                            for k in ('input_tokens', 'output_tokens')):
            raise JevError('Input routing usage missing or invalid')
        result['raw_response'] = copy.deepcopy(response)
        if any(not isinstance(answer, dict) for answer in response['answers'].values()):
            raise JevError('Malformed input routing typed answer')
        values = {name: probability(response, name) for name, question in request['questions'].items() if question['type'] == 'noul'}
        choices = {}
        for name, question in request['questions'].items():
            if question['type'] != 'choice': continue
            answer = response['answers'][name]
            distribution = answer.get('probabilities')
            if (answer.get('type') != 'choice' or answer.get('choice') not in question['criteria']
                    or not isinstance(distribution, dict) or set(distribution) != set(question['criteria'])
                    or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in distribution.values())
                    or abs(sum(distribution.values())-1) > .01):
                raise JevError('Malformed lifecycle Choice answer')
            choices[name] = answer
        # Boundaries belong to the unresolved band; never round into permission.
        if any(self.policy.low <= value <= self.policy.high for value in values.values()):
            result['reason'] = 'uncertain_observation'; return result
        yes = {name for name, value in values.items() if value > self.policy.high}
        if 'ambiguous' in yes:
            result['reason'] = 'ambiguous_target'; return result
        if 'covered' not in yes:
            result['reason'] = 'uncovered_requirements'; return result
        unresolved = snapshot.get('unresolved_inputs', [])
        if any(f'clarify{i}_resolved' not in yes for i in range(len(unresolved))):
            result['reason'] = 'prior_clarification_unresolved'; return result
        result['resolved_messages'] = [item['message_id'] for item in unresolved]
        targets = []
        for i, goal in enumerate(snapshot['goals']):
            actions = [action for action in ('respond', 'modify', 'query') if f'g{i}_{action}' in yes]
            if f'g{i}_reaffirm' in yes and not actions:
                actions = ['respond']
            if f'g{i}_lifecycle_requested' in yes:
                answer = choices[f'g{i}_lifecycle_action']
                if answer['probabilities'][answer['choice']] <= self.policy.high:
                    result['reason'] = 'uncertain_lifecycle_choice'; return result
                actions.append(answer['choice'])
            if set(actions) == {'respond', 'modify'}:
                actions = ['modify']  # Preserve the revision; old confirmation/requirements must be invalidated.
            if len(actions) > 1 or (actions and goal['state'] == 'closed' and actions != ['query']):
                result['reason'] = 'conflicting_or_closed_goal'; return result
            if actions:
                targets.append({'goal_id': goal['goal_id'], 'action': actions[0]})
        proposals = [copy.deepcopy(p) for i, p in enumerate(snapshot['new_goal_proposals']) if f'new{i}_supported' in yes]
        if ('has_new' in yes) != bool(proposals):
            result['reason'] = 'new_goal_coverage_mismatch'; return result
        if 'no_business' in yes:
            if targets or proposals or 'has_new' in yes:
                result['reason'] = 'conflicting_social_classification'; return result
            result.update(status='no_business_action', reason='social_only'); return result
        if not targets and not proposals:
            result['reason'] = 'no_reliable_route'; return result
        result.update(status='ready', reason='observations_resolved', targets=targets, new_goal_proposals=proposals)
        return result
