"""Bind a proposed dispatch to observed arguments and an independently extracted policy inventory."""
import json
import re

from controlled_effects import digest


def object_schema(fields):
    return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}


TEXT = {'type': 'string', 'minLength': 1}
SOURCE = object_schema({'ref': TEXT, 'quote': TEXT})
SCOPE_VERSION = 'operation-obligations-by-stage'
LATER_CLAUSES = {'type': 'array', 'maxItems': 40, 'items': object_schema({
    'clause_id': TEXT, 'stage': {'enum': ['receipt', 'goal_completion']}})}
SCOPE_EXCLUSIONS = {'type': 'array', 'maxItems': 40, 'items': object_schema({
    'clause_id': TEXT, 'scope_quote': TEXT})}
CLAUSE_SCHEMA = object_schema({'fragment_numbers': {'type': 'array', 'uniqueItems': True,
                                                    'maxItems': 40, 'items': {'type': 'integer', 'minimum': 1}}})
BINDINGS = {'type': 'array', 'maxItems': 100, 'items': object_schema({
    'parameter': TEXT, 'mode': {'enum': ['literal', 'derived']},
    'sources': {'type': 'array', 'minItems': 1, 'items': SOURCE}})}
POLICY = {'official-policy', 'published-skill'}
FACTS = {'official-user', 'official-tool'}


def cited_text(item, records, sources, label):
    record = records.get(item['ref'])
    if not record or record['source'] not in sources or not item['quote'].strip() or item['quote'] not in record['content']:
        raise PermissionError(f'{label}: missing exact quote from an allowed source')
    return item['quote']


def policy_fragments(records):
    """Addresses refer to exact text within a single immutable episode evidence record."""
    fragments = {}
    for ref, record in sorted(records.items()):
        if record['source'] not in POLICY:
            continue
        for line_no, line in enumerate(record['content'].splitlines()):
            for part, text in enumerate(re.split(r'(?<=[.!?。！？])\s+(?=[A-Z])', line.strip())):
                if not text:
                    continue
                key = 'F'+digest([ref, line_no, part])[:16]
                if key in fragments:
                    raise ValueError('Policy fragment identity collision')
                fragments[key] = {'ref': ref, 'line': line_no+1, 'quote': text}
    return fragments


def numbered_documents(fragments, records):
    documents, addresses = {}, []
    for key, fragment in fragments.items():
        ref = fragment['ref']
        document = documents.setdefault(ref, {'source': records[ref]['source'], 'fragments': []})
        addresses.append(key)
        document['fragments'].append({'number': len(addresses), 'text': fragment['quote']})
    return documents, addresses


def resolve_numbers(numbers, addresses, fragments):
    if any(type(n) is not int or not 1 <= n <= len(addresses) for n in numbers):
        raise PermissionError('Selected fragment number is outside this policy snapshot')
    return select_fragments([addresses[n-1] for n in numbers], fragments)


def select_fragments(ids, fragments):
    if not ids or set(ids) - fragments.keys():
        raise PermissionError('No usable selection of visible policy fragment IDs')
    return {key: fragments[key] for key in sorted(set(ids))}


def partition_fragments(candidates, values, low, high):
    if set(values) != set(candidates):
        raise PermissionError('Incomplete fragment applicability judgment')
    required, unresolved = {}, {}
    for key, fragment in candidates.items():
        if values[key] > high:
            required[key] = fragment
        elif not values[key] < low:
            unresolved[key] = fragment
    if not required and not unresolved:
        raise PermissionError('No applicable prerequisite established for this operation')
    return required, unresolved


def split_later_clauses(clauses, proposed):
    current = dict(clauses)
    later, checks = {}, {}
    for row in proposed:
        key, stage = row['clause_id'], row['stage']
        if key not in current or stage not in ('receipt', 'goal_completion'):
            raise PermissionError('Invalid or duplicate later clause: '+key)
        later[key] = {**current.pop(key), 'stage': stage}
        checks['later_'+key] = {'type': 'noul', 'instructions': {
            'clause': later[key], 'question': 'Does this whole clause govern only the named later stage '
            'of this operation or its goal? receipt means checking or recording the actual returned result; '
            'goal_completion means reporting or reconciling the goal at close. A condition, approval, '
            'prohibition or action basis needed at dispatch, even within a mixed clause, rules out deferral.'}}
    return current, later, checks


def review_scope_exclusions(clauses, scope, exclusions, records):
    """An exclusion remains provisional until all returned S1 checks pass."""
    remaining = dict(clauses)
    checks = {}
    for row in exclusions:
        key = row['clause_id']
        if key not in scope.get('unresolved', []) or key not in remaining:
            raise PermissionError(f'{key}: invalid or duplicate scope exclusion')
        fragment = remaining.pop(key)
        quote = cited_text({'ref': fragment['ref'], 'quote': row['scope_quote']}, records, POLICY, key)
        checks['scope_'+key] = {'type': 'noul', 'instructions': {
            'candidate': fragment, 'scope_quote': quote,
            'question': 'Does the cited original document explicitly restrict this entire candidate to a '
                        'different operation? A later duty for this same operation or goal must remain tracked and cannot be excluded. '
                        'A heading for a different rule, silence, a conflicting rule or missing customer '
                        'evidence cannot establish that exclusion.'}}
    if not remaining:
        raise PermissionError('No applicable prerequisite established for this operation')
    return remaining, checks


def check_bindings(bindings, arguments, records):
    names = [binding['parameter'] for binding in bindings]
    if sorted(names) != sorted(arguments):
        raise PermissionError('Expected exactly one binding for each final argument: '+', '.join(sorted(arguments)))
    for binding in bindings:
        name = binding['parameter']
        quotes = [cited_text(src, records, FACTS | POLICY, name) for src in binding['sources']]
        identifier = name == 'id' or name.endswith('_id')
        if identifier and (binding['mode'] != 'literal' or not any(
                records[src['ref']]['source'] in FACTS for src in binding['sources'])):
            raise PermissionError(name+': object identity requires an observed literal')
        if binding['mode'] == 'literal':
            value = arguments[name]
            token = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            pattern = r'(?<![\w-])'+re.escape(token)+r'(?![\w-])'
            if not any(re.search(pattern, quote) for src, quote in zip(binding['sources'], quotes)
                       if not identifier or records[src['ref']]['source'] in FACTS):
                raise PermissionError(name+': final value differs from cited observation')


def review_contract(plan, clauses, records):
    covered = set(plan.get('goal_basis_clause_ids', []))
    if covered - clauses.keys():
        raise PermissionError('Action basis references an unknown or excluded policy clause')
    for condition in plan['conditions']:
        linked = condition.get('clause_ids', [])
        if not linked or set(linked) - clauses.keys():
            raise PermissionError(condition['id']+': applicable policy clause not bound')
        if not any(records.get(ref, {}).get('source') in FACTS for ref in condition['evidence_refs']):
            raise PermissionError(condition['id']+': missing observed factual evidence for '+', '.join(linked))
        covered.update(linked)
    missing = [f"{key}: {clauses[key]['quote']}" for key in sorted(clauses.keys() - covered)]
    if missing:
        raise PermissionError("Unmapped policy clauses: " + " | ".join(missing))


def material_plan(plan):
    mappings = sorted(digest([sorted(c.get('clause_ids', [])), sorted(c.get('evidence_refs', [])),
                              c.get('prior_receipt_call_id')]) for c in plan.get('conditions', []))
    bindings = sorted(digest([b['parameter'], b['mode'], sorted(digest(s) for s in b['sources'])])
                      for b in plan.get('argument_bindings', []))
    return digest([plan.get('status'), plan.get('goal_id'), plan.get('goal_relation'), mappings, bindings,
                   sorted(digest(row) for row in plan.get('later_clauses', [])),
                   sorted(digest(row) for row in plan.get('scope_exclusions', [])), sorted(plan.get('goal_basis_clause_ids', [])), sorted(plan.get('policy_refs', [])), sorted(plan.get('dependencies', []))])
