"""Independent structured extraction followed by deterministic recommendation checks."""
from runtime_guards import compare_candidates


NUMBER = {'type': ['number', 'string']}
COMPARISON = {'type': 'object', 'properties': {
    'candidates': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'id': {'type': 'string'}, 'values': {'type': 'object', 'additionalProperties': NUMBER},
        'units': {'type': 'object', 'additionalProperties': {'type': 'string'}}},
        'required': ['id', 'values', 'units'], 'additionalProperties': False}},
    'requirements': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'field': {'type': 'string'}, 'op': {'enum': ['ge', 'gt', 'le', 'lt', 'eq']},
        'value': NUMBER, 'unit': {'type': 'string'}}, 'required': ['field', 'op', 'value', 'unit'], 'additionalProperties': False}},
    'preferences': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'field': {'type': 'string'}, 'direction': {'enum': ['min', 'max']}}, 'required': ['field', 'direction'], 'additionalProperties': False}},
    'selected_id': {'type': ['string', 'null']}},
    'required': ['candidates', 'requirements', 'preferences', 'selected_id'], 'additionalProperties': False}
SCHEMA = {'type': 'object', 'properties': {'completed_goal_ids': {'type': 'array', 'uniqueItems': True, 'items': {'type': 'string'}},
                                         'comparison': {'anyOf': [COMPARISON, {'type': 'null'}]}},
          'required': ['completed_goal_ids', 'comparison'], 'additionalProperties': False}
SCHEMA['properties']['claims'] = {'type': 'array', 'maxItems': 64, 'items': {
    'type': 'object', 'properties': {'quote': {'type': 'string', 'minLength': 1},
        'kind': {'enum': ['policy', 'capability', 'operation', 'customer', 'progress']},
        'evidence_refs': {'type': 'array', 'items': {'type': 'string'}}},
    'required': ['quote', 'kind', 'evidence_refs'], 'additionalProperties': False}}
SCHEMA['required'].append('claims')


class ResponseReview:
    def __init__(self, planner, judgments, workflow=None):
        self.planner, self.judgments, self.workflow = planner, judgments, workflow

    def extract(self, content, state):
        return self.planner.complete('response-review', {'candidate_response': content, 'visible_state': state}, SCHEMA)

    def check(self, content, state, *, now, proposal=None):
        if proposal is None: proposal = self.extract(content, state)
        goals = {g['goal_id']: g for g in state['task']['goals']}
        established = set(state.get('established_goal_ids', []))
        if any(goal not in goals or (goals[goal]['outcome'] != 'success' and goal not in established) for goal in proposal['completed_goal_ids']):
            return {'status': 'deny', 'reason': 'unfinished-goal-declared-complete', 'proposal': proposal}
        questions = {
            'comparison_needed': {'type': 'noul', 'instructions': 'In candidate_response itself, is a product recommended or selected on the basis of numeric costs, limits, requirements or preferences? A request for identity details, even two or more details, is not a product recommendation. Goal descriptions are context, not the outward answer.'},
            'completion_declarations_complete': {'type': 'noul', 'instructions':
                'Does completed_goal_ids account for every business goal that candidate_response claims is complete? A question or explicit unfinished status claims no goal completion.'}}
        # Classify the outward text, not policy documents or S2's suggested answer.
        # Evidence is introduced only when a concrete comparison needs validation.
        surface = {'candidate_response': content, 'goal_index': [
            {'goal_id': goal['goal_id'], 'description': goal.get('description', '')} for goal in goals.values()],
            'completed_goal_ids': proposal['completed_goal_ids']}
        values, ref = self.judgments.ask(surface, questions, now=now)
        policy = self.judgments.policy
        if values['completion_declarations_complete'] <= policy.high:
            return {'status': 'unknown', 'reason': 'unverified-extraction', 'observation_ref': ref, 'proposal': proposal}
        comparison = proposal['comparison']
        if comparison is None:
            status = 'allow' if values['comparison_needed'] < policy.low else 'unknown'
            return {'status': status, 'reason': 'no-verified-numeric-comparison', 'proposal': proposal, 'observation_ref': ref}
        extraction, extraction_ref = self.judgments.ask({'candidate_response': content,
            'visible_state': state, 'proposal': proposal}, {'extraction_faithful': {'type': 'noul', 'instructions':
                'Is the structured comparison a faithful extraction of the customer requirements, visible evidence and actual response, including candidate values, units, boundaries and preference order?'}}, now=now)
        if extraction['extraction_faithful'] <= policy.high:
            return {'status': 'unknown', 'reason': 'unverified-extraction', 'observation_ref': ref, 'proposal': proposal}
        ref = extraction_ref
        compute = lambda: self._compare(comparison, proposal, ref)
        if self.workflow is not None:
            return self.workflow(comparison, {'status': 'allow', 'model': policy.expected_model,
                'observation_ref': ref}, compute, now=now)
        return compute()

    def _compare(self, comparison, proposal, ref):
        try:
            for rule in comparison['requirements']:
                for candidate in comparison['candidates']:
                    if candidate['units'].get(rule['field']) != rule['unit']: raise ValueError('Unit mismatch')
            for preference in comparison['preferences']:
                units = {candidate['units'].get(preference['field']) for candidate in comparison['candidates']}
                if None in units or len(units) != 1: raise ValueError('Preference units inconsistent')
            ranked = compare_candidates(comparison['candidates'], comparison['requirements'], comparison['preferences'])
        except (KeyError, ValueError):
            return {'status': 'unknown', 'reason': 'numeric-data-incomplete-or-incomparable', 'proposal': proposal}
        selected = comparison['selected_id']
        correct = (not ranked and selected is None) or (ranked and selected == ranked[0])
        return {'status': 'allow' if correct else 'deny', 'reason': 'numeric-preference-check',
                'ranked_candidates': ranked, 'proposal': proposal, 'observation_ref': ref}
