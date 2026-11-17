"""Evidence, typed observations, numeric invariants and the final text boundary."""
import copy
from decimal import Decimal, InvalidOperation
import json
import re
from pathlib import Path
import time
import uuid

from controlled_effects import digest
from jev_provider import JevError, probability
from task_session import durable_json


class EvidenceStore:
    SOURCES = {'official-policy', 'official-tool', 'official-user', 'published-skill', 'controller'}

    def __init__(self, directory, episode):
        self.directory, self.episode = Path(directory), episode
        self.directory.mkdir(parents=True, exist_ok=True)

    def add(self, source, content, *, customer=None):
        if source not in self.SOURCES or not isinstance(content, str) or not content:
            raise ValueError('Trusted evidence source and content required')
        record = {'episode_id': self.episode, 'source': source, 'content': content, 'customer': customer}
        ref = digest(record)
        path = self.directory/(ref+'.json')
        if not path.exists(): durable_json(path, record)
        return ref

    def get(self, ref, *, customer=None):
        if not isinstance(ref, str) or len(ref) != 64 or any(c not in '0123456789abcdef' for c in ref):
            raise PermissionError('Unknown evidence reference')
        path = self.directory/(ref+'.json')
        if not path.exists(): raise PermissionError('Unknown evidence reference')
        record = json.loads(path.read_text())
        if digest(record) != ref or record['episode_id'] != self.episode:
            raise PermissionError('Evidence changed or belongs to another episode')
        if record['customer'] is not None and record['customer'] != customer:
            raise PermissionError('Evidence customer scope mismatch')
        return record

    def visible(self):
        # Runtime has access only to this episode's Agent-visible facts.
        return {p.stem: self.get(p.stem, customer=json.loads(p.read_text())['customer'])
                for p in sorted(self.directory.glob('*.json'))}

    def resolve_refs(self, references):
        """Expand exact, observed KB document aliases to immutable evidence records.

        User text and model proposals cannot register aliases. Include every observed
        record for an alias, so a model cannot silently select an inconsistent excerpt.
        """
        known = self.visible()
        aliases = {}
        for ref, record in known.items():
            if record['source'] != 'official-policy': continue
            for alias in re.findall(r'^\s*ID:\s+(\S+)\s*$', record['content'], re.MULTILINE):
                aliases.setdefault(alias, set()).add(ref)
        resolved = set()
        for ref in references:
            if ref in known: resolved.add(ref)
            elif ref in aliases: resolved.update(aliases[ref])
            else: raise PermissionError('Unobserved evidence reference')
        return sorted(resolved)


class JudgmentService:
    def __init__(self, client, task, directory, policy):
        self.client, self.task, self.policy = client, task, policy
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)

    def ask(self, state, questions, *, now=None):
        self.task.call('charge', now=int(time.time()) if now is None else now, kind='judgment')
        request = {'model': self.policy.request_model, 'state': copy.deepcopy(state),
                   'questions': copy.deepcopy(questions)}
        path = self.directory/uuid.uuid4().hex
        durable_json(path.with_suffix('.request.json'), request)
        response = self.client.ask(request)
        durable_json(path.with_suffix('.response.json'), response)
        if (response.get('model') != self.policy.expected_model or not isinstance(response.get('answers'), dict)
                or set(response['answers']) != set(questions)
                or any(not isinstance(v, dict) for v in response['answers'].values())):
            raise JevError('Judgment identity or typed answer mismatch')
        usage = response.get('usage', {})
        if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise JevError('Judgment usage missing')
        observations = {key: probability(response, key) for key in questions}
        return observations, str(path.with_suffix('.response.json'))

    def requirements(self, state, questions, *, now=None):
        values, ref = self.ask(state, questions, now=now)
        conditions = {key: ('satisfied' if value > self.policy.high else
                            'violated' if value < self.policy.low else 'unknown') for key, value in values.items()}
        status = 'allow' if all(v == 'satisfied' for v in conditions.values()) else (
            'deny' if any(v == 'violated' for v in conditions.values()) else 'unknown')
        return {'status': status, 'conditions': conditions, 'observation_ref': ref,
                'model': self.policy.expected_model, 'values': values}


class OutputGate:
    def __init__(self, judgments): self.judgments = judgments

    def check(self, content, visible_state, *, now=None):
        if not isinstance(content, str) or not content.strip():
            raise ValueError('Empty external response')
        questions = {
            'factual_support': {'type': 'noul', 'instructions':
                'Are all factual business claims in candidate_response supported by the visible evidence? Pure questions and explicit uncertainty do not assert facts.'},
            'requirements_respected': {'type': 'noul', 'instructions':
                'Does candidate_response respect the customer hard requirements and stated preference order? A request for genuinely missing information respects them.'},
            'completion_consistent': {'type': 'noul', 'instructions':
                'Are claims about completed, approved, pending or remaining work consistent with authoritative tool receipts and goal states, or explicitly supplied audited proposed_acceptance_proofs? An unverified proposal is not such a proof. Asking for information does not claim completion.'},
        }
        return self.judgments.requirements({'candidate_response': content, 'visible_state': copy.deepcopy(visible_state)}, questions, now=now)


def numeric(value):
    if type(value) not in (int, float, str): raise ValueError('Invalid numeric value')
    try: result = Decimal(str(value))
    except InvalidOperation as error: raise ValueError('Invalid numeric value') from error
    if not result.is_finite(): raise ValueError('Nonfinite value')
    return result


def compare_candidates(candidates, requirements, preferences):
    rows = []
    ids = set()
    for item in candidates:
        if item['id'] in ids: raise ValueError('Duplicate candidate')
        ids.add(item['id'])
        values = {key: numeric(value) for key, value in item['values'].items()}
        valid = True
        for rule in requirements:
            if rule['field'] not in values: raise ValueError('Missing candidate value')
            lhs, rhs = values[rule['field']], numeric(rule['value'])
            comparisons = {'ge': lhs >= rhs, 'gt': lhs > rhs, 'le': lhs <= rhs, 'lt': lhs < rhs, 'eq': lhs == rhs}
            if rule['op'] not in comparisons: raise ValueError('Unknown numeric comparison')
            valid &= comparisons[rule['op']]
        if valid:
            ranking = []
            for pref in preferences:
                if pref['direction'] not in ('min', 'max'): raise ValueError('Unknown preference direction')
                ranking.append(values[pref['field']] * (-1 if pref['direction'] == 'max' else 1))
            rows.append((tuple(ranking), item['id']))
    return [row[1] for row in sorted(rows)]


def resolve_operation(name, arguments, catalog):
    effective, parameters = name, arguments
    if name == 'call_discoverable_agent_tool':
        if not isinstance(arguments, dict) or set(arguments) - {'agent_tool_name', 'arguments'}:
            raise PermissionError('Invalid discoverable wrapper')
        effective = arguments.get('agent_tool_name')
        try: parameters = json.loads(arguments.get('arguments', '{}'))
        except (ValueError, TypeError) as error: raise PermissionError('Invalid inner arguments') from error
        if not isinstance(parameters, dict): raise PermissionError('Inner arguments must be an object')
    if effective not in catalog or catalog[effective].get('principal') == 'official-user-simulator':
        raise PermissionError('Unknown operation or wrong actor')
    return {'name': effective, 'arguments': parameters, **catalog[effective]}
