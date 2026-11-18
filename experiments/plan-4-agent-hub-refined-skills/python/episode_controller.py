"""Complete episode control surface; official scheduling remains outside this module."""
import copy
import json
from pathlib import Path
import time
import threading
import uuid
from dataclasses import asdict
from control_recording import recorded, logical_task, CallTape, AuditPlanner, AuditJev, AuditHub, ControlJournal

from business_judgment import BusinessJudge, parse_credit_dispute_receipt
from controlled_effects import ControlledEffects, digest
from input_router import InputRouter
from dispatch_policy import (CLAUSE_SCHEMA, SCOPE_VERSION, POLICY, partition_fragments, split_later_clauses, review_scope_exclusions, check_bindings,
                             policy_fragments, numbered_documents, resolve_numbers, material_plan, review_contract)
from planner_client import ProposalFormatError, GOAL_SCHEMA, STEP_SCHEMA, TOOL_STEP_SCHEMA
from runtime_guards import EvidenceStore, JudgmentService, OutputGate, resolve_operation
from task_session import TaskSession, durable_json
from response_review import ResponseReview, QUESTION_REVISION
from receipt_registry import ReceiptInterpreter
from completion_policy import permits_completion
from controlled_nodes import ControlledNodes
from output_claims import ClaimGate
from quote_binding import bind_proposal
from input_proposals import normalize_context_routes


class StepPlanRefused(PermissionError):
    """The proposal failed validation before adoption or dispatch."""


class EpisodeController:
    PUBLIC_READS = {'KB_search', 'get_current_time', 'list_discoverable_agent_tools'}
    NODE_VERSION = 'banking-evidence-control'
    NODES = {'evidence-investigation': 'agent_loop', 'candidate-comparison': 'workflow',
             'guarded-operation': 'tool', 'dependent-goals': 'workflow',
             'receipt-reconciliation': 'workflow', 'await-user': 'wait'}

    def __init__(self, task, hub, planner, jev, policy, directory, catalog, domain_policy, receipt_contracts=None, *, capture_replay=False):
        self.task, self.hub, self.planner, self.jev, self.policy = task, hub, planner, jev, policy
        self._operation_lock = threading.RLock()
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.journal = None
        if capture_replay:
            if receipt_contracts: raise ValueError('Replay requires published receipt contracts, not injected callbacks')
            tape = CallTape(self.directory/'replay'/'providers')
            # Journal creates its root separately, after all initial state is ready.
            self.planner = planner = AuditPlanner(planner, task, tape)
            self.jev = jev = AuditJev(jev, tape)
            self.hub = hub = AuditHub(hub, tape)
        self.catalog = copy.deepcopy(catalog)
        self.receipt_contracts = receipt_contracts or {}
        self.evidence = EvidenceStore(self.directory/'evidence', task.episode)
        self.policy_ref = self.evidence.add('official-policy', domain_policy)
        self.judgments = JudgmentService(jev, task, self.directory/'judgments', policy)
        self.output = OutputGate(self.judgments)
        self.claims = ClaimGate(self.judgments, self.evidence.resolve_refs)
        self.nodes = ControlledNodes(task, hub, self.directory/'internal-nodes')
        self.review = ResponseReview(planner, self.judgments, self._comparison_workflow)
        self.receipts = ReceiptInterpreter(self.judgments)
        self.inputs = TaskSession(task, InputRouter(jev, policy), self.directory/'inputs')
        unlocked_path = self.directory/'unlocked-tools.json'
        self.unlocked = set(json.loads(unlocked_path.read_text())) if unlocked_path.exists() else set()
        self.effects = ControlledEffects(task, hub, self.directory/'effects', catalog,
            live_permission=lambda name: name in self.catalog and (
                not self.catalog[name].get('discoverable', False) or name in self.unlocked))
        question_path = self.directory/'last-question.json'
        self.last_question = json.loads(question_path.read_text())['question'] if question_path.exists() else ''
        message_path = self.directory/'last-assistant-message.json'
        self.last_assistant_message = json.loads(message_path.read_text())['content'] if message_path.exists() else ''
        self.bindings_path = self.directory/'call-bindings.json'
        self.bindings = json.loads(self.bindings_path.read_text()) if self.bindings_path.exists() else {}
        if capture_replay:
            self.journal = ControlJournal(self, self.directory/'control-replay',
                {'episode': task.episode, 'catalog': catalog, 'domain_policy': domain_policy,
                 'policy': asdict(policy), 'call_limit': task.call_limit})
            # Provider trace belongs to the same sealed artifact.
            tape.directory = self.journal.directory/'providers'; tape.directory.mkdir()

    def state(self, now):
        return logical_task(self.task.call('status', now=now))

    def rebind_controls(self, task, hub):
        if task.episode != self.task.episode: raise PermissionError('Control restart cannot change episode identity')
        for owner in (self, self.inputs, self.judgments, self.effects, self.nodes, self.planner):
            owner.task = task
        if isinstance(self.hub, AuditHub):
            self.hub.delegate = hub
            hub = self.hub
        self.hub = hub
        self.effects.hub = hub
        self.nodes.hub = hub

    def visible(self, now):
        state = {'task': self.state(now), 'evidence': self.evidence.visible(), 'last_question': self.last_question,
                 'last_assistant_message': self.last_assistant_message}
        duties = self._goal_obligations()
        if duties:
            state['operation_obligations'] = duties
        return state

    def pending_user_questions(self, *, now):
        return list(dict.fromkeys(goal['waiting_for'] for goal in self.state(now)['goals']
            if goal['state'] == 'waiting' and goal.get('waiting_kind') == 'user' and goal['waiting_for']))

    def clarification_prompt(self, *, now):
        questions = self.pending_user_questions(now=now)
        if questions:
            return 'Please clarify your answer to the outstanding question: '+'\n'.join(questions)
        return ('I have kept the details you supplied. Please clarify whether you want to continue '
                'the existing requests, change one of them, or start a new request.')

    @recorded
    def reserve_model(self, kind, *, now):
        self.task.call('charge', now=now, kind=kind)

    @recorded
    def add_published_evidence(self, source, content):
        if source not in ('published-skill', 'published-tool-contract'):
            raise ValueError('Only validated published assets may enter this boundary')
        return self.evidence.add(source, content)

    @recorded
    def stop(self, reason):
        self.task.call('stop', reason=reason)

    def seal_replay(self):
        if self.journal is not None: self.journal.seal()

    @recorded
    def remember_assistant(self, content, *, kind='accepted_assistant_message'):
        if kind not in ('accepted_assistant_message', 'controller_clarification') or not isinstance(content, str) or not content:
            raise ValueError('Trusted outward conversation event required')
        self.last_assistant_message = content
        durable_json(self.directory/'last-assistant-message.json', {'content': content})
        self.evidence.add('controller', json.dumps({'type': kind, 'content': content}, ensure_ascii=False))

    def _input_proposal(self, message, content, now):
        path = self.directory/('goals-'+digest(message)+'.json')
        if path.exists():
            return json.loads(path.read_text())
        attempt = path.with_suffix('.attempt.json')
        if attempt.exists():
            record = json.loads(attempt.read_text())
            if record.get('status') == 'repair_started':
                # A lost response to a tool-free formatting call cannot authorize a route.
                # Preserve its spent reservation and hand the original message to durable clarification.
                durable_json(path, None)
                return None
            if record.get('status') != 'repairable':
                raise RuntimeError('Previous S2 proposal outcome unknown; no replay')
            if self.state(now)['revision'] != record['repair_revision']:
                raise PermissionError('Input revision changed before format repair')
            state = record['state']
        else:
            state = {'content': content, 'task': self.state(now), 'last_question': self.last_question,
                     'last_assistant_message': self.last_assistant_message}
            durable_json(attempt, {'status': 'started'})
            try:
                proposal = self.planner.complete('new-goals', state, GOAL_SCHEMA)
            except ProposalFormatError as error:
                state = {**state, 'format_feedback': str(error)}
                durable_json(attempt, {'status': 'repairable', 'state': state,
                                       'repair_revision': self.state(now)['revision']})
            else:
                durable_json(path, proposal)
                return proposal

        # The retry uses the original planning snapshot. Its separate budget charge
        # advances the Java revision; input commit still checks the current revision.
        durable_json(attempt, {'status': 'repair_started'})
        try:
            proposal = self.planner.complete('new-goals', state, GOAL_SCHEMA)
        except ProposalFormatError:
            proposal = None
        except Exception:
            durable_json(attempt, {'status': 'repair_failed'})
            raise
        durable_json(path, proposal)
        return proposal

    @recorded
    def user(self, message, content, *, now):
        self.task.call('receive', episode=self.task.episode, message=message, content=content)
        self.evidence.add('official-user', content)
        proposal = self._input_proposal(message, content, now)
        if proposal is None:
            result = self.inputs.handle(message, content, [], now=now, last_question=self.last_question,
                                        format_failure=True)
            durable_json(self.directory/'latest-input.json', result)
            return result
        original = proposal
        proposal = normalize_context_routes(content, bind_proposal(content, proposal))
        if proposal != original:
            normalization = self.directory/('goals-'+digest(message)+'.input-normalization.json')
            durable_json(normalization, {'original': original, 'bound': proposal,
                'rules': ['unique-exact-visible-text; paired-markdown-emphasis-only',
                          'coalesce-compatible-context-spans-only; preserve-conflicting-actions']})
        result = self.inputs.handle(message, content, proposal['goals'], now=now, last_question=self.last_question,
                                    route_proposals=proposal.get('existing_routes'), last_assistant_message=self.last_assistant_message,
                                    context_quote=proposal.get('context_quote'))
        if result['status'] == 'ready':
            self.nodes.resume_waits(now=now)
            if self.last_question and not self.pending_user_questions(now=now):
                # Dialogue history remains immutable. This retires only the
                # live pointer; it never verifies identity or grants an effect.
                self.last_question = ''
                durable_json(self.directory/'last-question.json', {'question': ''})
        durable_json(self.directory/'latest-input.json', result)
        return result

    def _comparison_workflow(self, arguments, proof, compute, *, now):
        goals = [goal for goal in self.state(now)['goals'] if goal['state'] == 'active']
        if not goals: return compute()  # Historical status answer; no new task effects.
        node = self.nodes.start('candidate-comparison', goals[0]['goal_id'], arguments, proof, now=now)
        try: result = compute()
        except Exception:
            self.nodes.finish(node, success=False)
            raise
        self.nodes.finish(node)
        return result

    def _policy_inventory(self, state, now):
        records = state['evidence']
        fragments = policy_fragments(records)
        operation = state['effective_operation']
        documents, addresses = numbered_documents(fragments, records)
        scope = {'operation': operation, 'stage': 'before_dispatch', 'documents': documents}
        path = self.directory/('policy-inventory-'+digest([SCOPE_VERSION, scope, asdict(self.policy)])+'.json')
        if path.exists():
            cached = json.loads(path.read_text())
        else:
            selection = self.planner.complete('dispatch-policy', scope, CLAUSE_SCHEMA)
            candidates = resolve_numbers(selection['fragment_numbers'], addresses, fragments)
            # S2 can nominate references; the fixed S1 question determines scope.
            source_refs = sorted({row['ref'] for row in candidates.values()})
            evidence = {'operation': operation, 'stage': 'before_dispatch', 'candidates': candidates,
                        'source_documents': {ref: {'source': records[ref]['source'], 'text': records[ref]['content']}
                                             for ref in source_refs}}
            questions = {key: {'type': 'noul', 'instructions':
                f'Does candidate {key}, read in its original context, govern the proposed operation at the '
                'pre-dispatch stage or prescribe handling its receipt or closing its selected goal? A rule solely '
                'for another business operation does not. '
                'A conditional prerequisite of this operation remains relevant even if its factual trigger '
                'has yet to be checked. Judge applicability, not whether the customer meets the requirement. '
                'A Skill cannot override official policy.'} for key in candidates}
            values, observation = self.judgments.ask(evidence, questions, now=now)
            cached = {'spec': SCOPE_VERSION, 'candidates': candidates, 'values': values, 'observation': observation}
            durable_json(path, cached)
        required, unresolved = partition_fragments(cached['candidates'], cached['values'], self.policy.low, self.policy.high)
        display = {f'P{i}': {**fragment, 'fragment_id': key}
                   for i, (key, fragment) in enumerate({**required, **unresolved}.items(), start=1)}
        return display, {'spec': SCOPE_VERSION, 'observation': cached['observation'], 'scope_digest': digest(scope),
                         'unresolved': [alias for alias, row in display.items() if row['fragment_id'] in unresolved],
                         'residual_fragment_count': len(fragments) - len(display)}

    def _plan(self, purpose, state, *, now):
        if purpose != 'tool-step':
            proposal = self.planner.complete(purpose, state, STEP_SCHEMA)
            return self._validate_plan(purpose, state, proposal, now=now)

        operation = state.get('effective_operation', {})
        feedback_path = self.directory/('step-refusal-'+digest(operation)+'.json')
        state = {**state, 'prior_receipts': self._prior_receipts()}
        visible_refs = sorted(ref for ref, record in state.get('evidence', {}).items()
                              if record['source'] in POLICY | {'official-user', 'official-tool', 'published-tool-contract'})
        context = digest([visible_refs, state.get('task', {}).get('goals', []),
                          state['prior_receipts'], state['dispatch_clauses']])
        prior = json.loads(feedback_path.read_text()) if feedback_path.exists() else None
        scope_revision = bool(state.get('policy_scope', {}).get('unresolved'))
        if scope_revision:
            # Reserve the single revision before calling S2, including across restarts or new tool-call IDs.
            attempt = self.directory/('scope-revision-'+digest([operation, context, state['policy_scope']])+'.json')
            if attempt.exists():
                reason = prior['reason'] if prior and prior['context'] == context else 'revision already attempted'
                raise PermissionError('Same scope and evidence: '+reason)
            durable_json(attempt, {'policy_scope': state['policy_scope'], 'clauses': state['dispatch_clauses']})
        planner_state = {**state, 'previous_refusal': prior} if prior else state
        proposal = self.planner.complete(purpose, planner_state, TOOL_STEP_SCHEMA)
        if prior and material_plan(prior['proposal']) == material_plan(proposal) and prior['context'] == context:
            raise PermissionError('Rejected proposal unchanged with the same evidence: '+prior['reason'])
        try:
            return self._validate_plan(purpose, state, proposal, now=now)
        except PermissionError as error:
            durable_json(feedback_path, {'proposal': proposal, 'reason': str(error), 'context': context})
            if proposal['status'] == 'proposed' and not scope_revision:
                raise StepPlanRefused(str(error)) from error
            raise

    def _prior_receipts(self):
        receipts = {}
        for call_id, binding in self.bindings.items():
            if binding['effective']['access'] == 'read':
                continue
            path = self.directory/('receipt-'+digest(call_id)+'.json')
            if path.exists():
                record = json.loads(path.read_text())
                receipts[call_id] = {'operation': binding['effective'], 'receipt': record['receipt'],
                                      'evidence_ref': record['evidence_ref']}
        return receipts

    def _goal_obligations(self, goal_id=None):
        duties = []
        for call_id, binding in self.bindings.items():
            if not binding.get('later_obligations') or goal_id and binding['goal'] != goal_id:
                continue
            path = self.directory/('receipt-'+digest(call_id)+'.json')
            receipt = json.loads(path.read_text()) if path.exists() else None
            for key, clause in binding['later_obligations'].items():
                duties.append({'goal_id': binding['goal'], 'operation': binding['effective'],
                               'call_id': call_id, 'clause_id': key, 'clause': clause, 'receipt': receipt})
        return duties

    def _validate_plan(self, purpose, state, original, *, now):
        plan = copy.deepcopy(original)
        if plan['status'] != 'proposed' or not plan['conditions']:
            raise PermissionError('S2 has not established a bounded plan')
        if purpose == 'tool-step' and 'policy_refs' not in plan:
            linked = set(plan.get('goal_basis_clause_ids', []))
            for condition in plan['conditions']:
                linked.update(condition.get('clause_ids', []))
            clauses = state['dispatch_clauses']
            if linked - clauses.keys():
                raise PermissionError('Unobserved policy clause in step')
            plan['policy_refs'] = sorted({clauses[key]['ref'] for key in linked})
        plan['policy_refs'] = self.evidence.resolve_refs(plan['policy_refs'])
        for condition in plan['conditions']:
            if not condition['evidence_refs']:
                raise PermissionError(f"Condition {condition['id']}: empty evidence references")
            try:
                condition['evidence_refs'] = self.evidence.resolve_refs(condition['evidence_refs'])
            except PermissionError as error:
                if str(error) != 'Unobserved evidence reference':
                    raise
                raise PermissionError(f"Condition {condition['id']}: unobserved evidence reference") from error
            if purpose == 'tool-step' and 'prior_receipt_call_id' in condition:
                prior = state['prior_receipts'].get(condition.pop('prior_receipt_call_id'))
                if (prior is None or prior['evidence_ref'] not in condition['evidence_refs']
                        or prior['receipt']['status'] not in ('succeeded', 'accepted')):
                    raise PermissionError(f"Condition {condition['id']}: correlated prior receipt missing or unresolved")
                previous_args = prior['operation']['arguments']
                current_args = state['effective_operation']['arguments']
                if any(previous_args[k] != current_args[k] for k in previous_args.keys() & current_args.keys()
                       if k.endswith('_id')):
                    raise PermissionError(f"Condition {condition['id']}: prior receipt subject mismatch")
        known = self.evidence.visible()
        if not plan['policy_refs'] or any(ref not in known or known[ref]['source'] not in
                                         ('official-policy', 'published-skill') for ref in plan['policy_refs']):
            raise PermissionError('Plan has missing or fabricated policy references')
        snapshot = {'proposal': plan, **state}
        questions = {
            'goal_link': {'type': 'noul', 'instructions': 'Does the proposal concern the stated customer goal and the actual proposed action or completion result?'},
            'conditions_grounded': {'type': 'noul', 'instructions': 'Are the proposed conditions grounded in the original customer requirements and applicable visible policy, without inventing or weakening requirements?'},
            'conditions_complete': {'type': 'noul', 'instructions': 'Do the proposed conditions cover all applicable requirements for this proposed action or goal completion, including prerequisites, ordering and confirmation where required by visible policy?'}}
        if purpose == 'tool-step':
            stage_current, later, stage_checks = split_later_clauses(state['dispatch_clauses'], plan.get('later_clauses', []))
            clauses, scope_checks = review_scope_exclusions(stage_current, state.get('policy_scope', {}),
                                                          plan.get('scope_exclusions', []), known)
            questions.update(scope_checks)
            questions.update(stage_checks)
            if later:
                plan['later_obligations'] = later
            check_bindings(plan.get('argument_bindings', []), state['effective_operation'].get('arguments', {}), known)
            review_contract(plan, clauses, known)
            plan['dispatch_clauses'] = clauses
            if 'policy_scope' in state:
                plan['policy_scope'] = state['policy_scope']
            for key, clause in clauses.items():
                mapped = [c for c in plan['conditions'] if key in c['clause_ids']]
                if key in plan.get('goal_basis_clause_ids', []):
                    questions['basis_'+key] = {'type': 'noul', 'instructions': {
                        'clause': clause['quote'], 'question': 'Does this clause in its source context prescribe '
                        'or permit performing this specific effective_operation for the selected goal and object?'}}
                    questions['clause_'+key] = {'type': 'noul', 'instructions': {
                        'clause': clause['quote'], 'mapped_conditions': mapped,
                        'question': 'Are all prerequisites or restrictions in this clause covered by the mapped '
                        'conditions and proven by their cited facts for this object? If it solely directs the '
                        'current action, there are no prior facts to prove for this clause. Any unmet trigger, '
                        'missing prior approval, exception or prohibition fails this check.'}}
                    continue
                questions['clause_'+key] = {'type': 'noul', 'instructions': {
                    'clause': clause['quote'], 'mapped_conditions': [
                        {'statement': c['statement'], 'fact_refs': c['evidence_refs']} for c in mapped],
                    'question': 'For this subject and final operation, do these conditions faithfully implement '
                                'the applicable clause AND do their cited observations establish the required '
                                'facts before dispatch, including every applicable qualification, exception or '
                                'conflicting constraint? A policy quote alone cannot prove consent or an outcome.'}}
            for index, binding in enumerate(plan['argument_bindings']):
                name = binding['parameter']
                questions[f'arg_{index}'] = {'type': 'noul', 'instructions': {
                    'parameter': name, 'final_value': state['effective_operation']['arguments'][name],
                    'sources': binding['sources'], 'question': 'Do these quoted sources in their original records '
                    'support this exact final value for the correct subject, intended action and field, '
                    'including any necessary derivation? A different customer or unrelated occurrence is insufficient.'}}
            questions['goal_link']['instructions'] = (
                'Does the selected active goal authorize the proposed action directly or require this step '
                'under cited policy for this same customer and object? A shared prerequisite can advance a '
                'single selected goal without completing it. Check the proposed goal_basis independently.')
            for condition in plan['conditions']:
                questions['pre_'+condition['id']] = {'type': 'noul', 'instructions': {
                    'condition': condition['statement'],
                    'question': 'Is this a genuine pre-dispatch requirement for this precise action under the cited policy? '
                                'Reject a restatement of the proposed effect as already accomplished. If this requires a prior '
                                'operation outcome, check the original condition cites a correlated receipt in prior_receipts '
                                'for the correct subject and required status. Accepted alone cannot prove a final effect.'}}
            # Include competing policy and observed facts for coverage and subject checks;
            # keep dialogue internals, drafts and rejection history outside the S1 snapshot.
            snapshot = {'proposal': plan, 'proposed_conditions': original['conditions'],
                        'effective_operation': state['effective_operation'], 'stage': 'before_dispatch',
                        'active_goals': [{k: goal.get(k) for k in ('goal_id', 'description', 'dependencies')}
                                         for goal in state.get('task', {}).get('goals', [])
                                         if goal.get('state') == 'active'],
                        'prior_receipts': state.get('prior_receipts', {}),
                        'dispatch_clauses': clauses, 'evidence': {
                            ref: record for ref, record in known.items()
                            if record['source'] in POLICY | {'official-user', 'official-tool', 'published-tool-contract'}}}
            questions['conditions_grounded']['instructions'] = (
                'Is every listed condition an applicable prerequisite for this exact effective_operation '
                'with its final arguments under the visible policy and customer instructions? '
                'A future receipt or a requirement only for a later action is not a prerequisite.')
            questions['conditions_complete']['instructions'] = (
                'Independently check ALL visible policy and Skill records, including those the proposal did not cite. '
                'Do the clauses retained for pre-dispatch cover every pre-dispatch prerequisite for this operation? '
                'The proposal separately tracks later_obligations; an obligation entirely due after dispatch is not missing. '
                'Parameter provenance is checked separately. An applicable uncited restriction means coverage fails.')
            # Only the omission-of-source-text check is decidable by set membership.
            # Every clause still needs its full semantic and evidence review above.
            # Tracked later clauses have their own mandatory stage checks and remain bound
            # through acceptance. Only excluded or unexamined text needs an omission scan.
            if not scope_checks and state.get('policy_scope', {}).get('residual_fragment_count') == 0:
                del questions['conditions_complete']
            else:
                questions['later_coverage'] = {'type': 'noul', 'instructions': 'Do the tracked later_obligations '
                    'cover the specific receipt or closing duties imposed by the visible source documents on this '
                    'operation or its goal? If there are none, an empty list is complete. Duties solely for other '
                    'operations or goals are outside this check.'}
        if purpose == 'goal-completion':
            duties = self._goal_obligations(plan['goal_id'])
            if duties:
                snapshot['operation_obligations'] = duties
                for index, duty in enumerate(duties):
                    if not duty['receipt']:
                        raise PermissionError('Missing correlated receipt for later policy obligation')
                    receipt_record = duty['receipt']
                    if duty['clause']['stage'] == 'receipt':
                        observed = receipt_record.get('receipt_obligations', {}).get('conditions', {})
                        if observed.get(duty['clause_id']) != 'satisfied':
                            fresh = {ref for ref, record in known.items() if record['source'] == 'official-tool'}
                            if not fresh.difference(receipt_record.get('official_facts_at_receipt', fresh)):
                                raise PermissionError('Outstanding receipt obligation lacks a new official observation')
                    questions[f'obligation_{index}'] = {'type': 'noul', 'instructions': {
                        'obligation': duty, 'question': 'Does the evidence establish this duty for the bound operation '
                        'and customer at goal close? Check its correlated receipt and any required readback. '
                        'The proposed response may fulfill a reporting duty, but cannot prove a bank effect.'}}
            questions['completion_boundary_grounded'] = {'type': 'noul', 'instructions':
                'Does completion_boundary faithfully describe the original customer goal? submission means the customer requested filing or submitting a request, not receiving approval or the eventual effect. information means providing requested information; final_effect requires the actual bank outcome.'}
        if plan.get('dependencies'):
            questions['dependencies_grounded'] = {'type': 'noul', 'instructions':
                'Does every proposed dependency represent a whole customer goal that must finish before this action under visible policy or explicit user instructions? Priority alone does not create a dependency; do not defer a service until unrelated eventual bank processing is finished.'}
        check = self.judgments.requirements(snapshot, questions, now=now)
        if purpose == 'tool-step' and state.get('policy_scope', {}).get('unresolved'):
            plan['scope_review'] = {'observation': check['observation_ref'],
                                    'candidates': {key: state['dispatch_clauses'][key]
                                                   for key in state['policy_scope']['unresolved']}}
        durable_json(self.directory/('plan-'+uuid.uuid4().hex+'.json'), {'original_proposal': original, 'proposal': plan, 'validation': check})
        if check['status'] != 'allow':
            failed = ', '.join(f'{name}={value}' for name, value in check['conditions'].items()
                               if value != 'satisfied')
            details = []
            if purpose == 'tool-step':
                for key, value in check['conditions'].items():
                    if value == 'satisfied':
                        continue
                    if key.startswith('clause_'):
                        details.append(state['dispatch_clauses'][key[7:]]['quote'])
                    elif key.startswith('scope_'):
                        details.append(state['dispatch_clauses'][key[6:]]['quote'])
                    elif key.startswith('arg_'):
                        details.append('argument '+plan['argument_bindings'][int(key[4:])]['parameter'])
            raise PermissionError(f'Plan evidence/coverage not established ({failed})' +
                                  ('; '+ ' | '.join(details) if details else ''))
        if plan.get('dependencies'):
            current = self.state(now)
            goals = {goal['goal_id']: goal for goal in current['goals']}
            if plan['goal_id'] not in goals or plan['goal_id'] in plan['dependencies'] or any(parent not in goals for parent in plan['dependencies']):
                raise PermissionError('Dependency references are invalid')
            dependencies = sorted(set(goals[plan['goal_id']]['dependencies']) | set(plan['dependencies']))
            self.task.call('configure_goal', goal=plan['goal_id'], revision=current['revision'],
                requirements=[condition['id'] for condition in plan['conditions']],
                source_ref=digest(plan['policy_refs']), dependencies=dependencies)
        return plan

    def _judge(self, plan, payload, *, now):
        records = self.evidence.visible()
        selected = set(plan['policy_refs']) | {ref for c in plan['conditions'] for ref in c['evidence_refs']}
        for binding in plan.get('argument_bindings', []):
            selected.update(src['ref'] for src in binding['sources'])
        selected.update(row['ref'] for row in plan.get('dispatch_clauses', {}).values())
        selected.update(row['ref'] for row in plan.get('scope_review', {}).get('candidates', {}).values())
        evidence = [{'ref': ref, 'episode_id': self.task.episode, 'goal_id': plan['goal_id'],
                     'source': records[ref]['source'], 'content': records[ref]['content']} for ref in sorted(selected)]
        self.task.call('charge', now=now, kind='judgment')
        business_conditions = [{k: c[k] for k in ('id', 'statement', 'evidence_refs')} for c in plan['conditions']]
        result = BusinessJudge(self.jev, self.policy).judge(self.task.episode, plan['goal_id'], payload,
                    digest(plan), business_conditions, evidence)
        durable_json(self.directory/('business-'+uuid.uuid4().hex+'.json'), result)
        return result

    @recorded
    def tool(self, call, official_queue, *, now, request_deadline=None):
        with self._operation_lock:
            return self._tool(call, official_queue, now=now, request_deadline=request_deadline)

    def _tool(self, call, official_queue, *, now, request_deadline=None):
        if request_deadline is not None and time.monotonic() >= request_deadline:
            raise PermissionError('Request deadline passed before planning')
        operation = resolve_operation(call['name'], call['arguments'], self.catalog)
        state = self.visible(now)
        if not state['task']['can_dispatch']: raise PermissionError('Input or task blocks dispatch')
        active = [g for g in state['task']['goals'] if g['state'] == 'active']
        if not active: raise PermissionError('No active goal')
        if operation['access'] == 'write' and operation['name'] != 'unlock_discoverable_agent_tool':
            self.effects.check_business_ready(active[0]['goal_id'], now)
        payload = {'episode': self.task.episode, 'operation': call['name'], 'arguments': copy.deepcopy(call['arguments'])}
        # Reads supply episode evidence, often shared by several goals. Attribution
        # is bookkeeping; customer scope is the independent authorization check.
        if operation['name'] == 'unlock_discoverable_agent_tool':
            target = operation['target_operation']
            disclosed = [ref for ref, record in state['evidence'].items()
                         if record['source'] in ('official-policy', 'published-skill') and target in record['content']]
            if not disclosed: raise PermissionError('Capability was not disclosed by visible published policy or Skill')
            plan = {'goal_id': active[0]['goal_id']}
            judgment = {'episode_id': self.task.episode, 'goal_id': plan['goal_id'], 'status': 'allow',
                'payload_hash': digest(payload), 'rule_version': 'observed-agent-capability-metadata',
                'evidence_refs': sorted(disclosed), 'model': 'deterministic-capability-boundary',
                'conditions': {'registered_agent_capability_disclosed': 'satisfied'}}
        elif operation['access'] == 'read':
            goal = active[0]
            if operation['name'] not in self.PUBLIC_READS:
                scope = self.judgments.requirements({'call': operation,
                    'customer_messages_and_observed_facts': {ref: value for ref, value in state['evidence'].items()
                        if value['source'] in ('official-user', 'official-tool')}, 'goal': goal}, {
                    'customer_scope': {'type': 'noul', 'instructions':
                        'Is the requested read about the customer or business objects identified in the visible conversation and official facts, rather than an unrelated person? Lookup of the customer by their supplied name is in scope.'}}, now=now)
                if scope['status'] != 'allow': raise PermissionError('Read customer scope unresolved')
            plan = {'goal_id': goal['goal_id']}
            judgment = {'episode_id': self.task.episode, 'goal_id': goal['goal_id'], 'status': 'allow',
                'payload_hash': digest(payload), 'rule_version': 'published-read-catalog',
                'evidence_refs': [self.policy_ref], 'model': 'deterministic-read-boundary',
                'conditions': {'registered_read_and_subject_scope': 'satisfied'}}
        else:
            planning_state = {**state, 'actual_call': call, 'effective_operation': operation}
            planning_state['dispatch_clauses'], planning_state['policy_scope'] = self._policy_inventory(planning_state, now)
            try:
                plan = self._plan('tool-step', planning_state, now=now)
            except StepPlanRefused:
                # A revision uses the existing model budget and can never resend a dispatched operation.
                if request_deadline is not None and time.monotonic() >= request_deadline:
                    raise
                plan = self._plan('tool-step', planning_state, now=now)
            if any(binding['effective'] == operation and
                   'required_prerequisite' in (binding.get('goal_relation'), plan.get('goal_relation'))
                   for binding in self.bindings.values()):
                raise PermissionError('Shared prerequisite already adopted; consult its bound receipt before proceeding')
            judgment = self._judge(plan, payload, now=now)
        if plan['goal_id'] not in {g['goal_id'] for g in active}: raise PermissionError('Wrong or inactive goal')
        if judgment['status'] != 'allow':
            missing = [condition['id']+' ('+', '.join(condition.get('clause_ids', []))+')'
                       for condition in plan['conditions']
                       if judgment['conditions'].get(condition['id']) != 'satisfied']
            raise PermissionError('Business evidence unresolved or denied: '+', '.join(missing))
        identifiers = {k: v for k, v in operation['arguments'].items()
                       if k.endswith('_id') or 'last_4' in k or k in ('agent_tool_name', 'discoverable_tool_name')}
        step = (operation['name']+':'+digest(identifiers)) if operation['access'] != 'read' else ('read:'+call['id'])
        if request_deadline is not None and time.monotonic() >= request_deadline:
            raise PermissionError('Request expired during planning; no operation adopted')
        final_now = int(time.time()) if request_deadline is not None else now
        adopted = self.effects.adopt(plan['goal_id'], step, call['name'], call['arguments'], judgment, now=final_now)
        self.bindings[call['id']] = {'operation': adopted, 'effective': operation, 'goal': plan['goal_id']}
        if plan.get('later_obligations'):
            self.bindings[call['id']]['later_obligations'] = plan['later_obligations']
        if plan.get('goal_relation'):
            self.bindings[call['id']]['goal_relation'] = plan['goal_relation']
        durable_json(self.bindings_path, self.bindings)
        node = 'evidence-investigation' if operation['access'] == 'read' else 'guarded-operation'
        self.task.call('start_node', node_id=adopted, goal=plan['goal_id'], revision=self.state(now)['revision'],
                       kind=node, version=self.NODE_VERSION, decision_ref=adopted, now=now)
        durable_json(self.directory/('node-'+adopted+'.json'), {'node': node, 'version': self.NODE_VERSION,
            'kind': self.NODES[node], 'decision_ref': adopted, 'goal': plan['goal_id'], 'status': 'running'})
        self.effects.dispatch(adopted, call['id'], official_queue, now=final_now, deadline=request_deadline)

    @recorded
    def receipt(self, call_id, content, error, *, now):
        with self._operation_lock:
            return self._receipt(call_id, content, error, now=now)

    def _receipt(self, call_id, content, error, *, now):
        if call_id not in self.bindings: raise PermissionError('Uncorrelated tool result')
        binding = self.bindings[call_id]
        source = 'official-policy' if binding['effective']['name'] == 'KB_search' else 'official-tool'
        ref = self.evidence.add(source, content)
        receipt_path = self.directory/('receipt-'+digest(call_id)+'.json')
        if receipt_path.exists():
            prior = json.loads(receipt_path.read_text())
            if prior['evidence_ref'] == ref and prior.get('raw_error') == error:
                return prior['receipt']
        reconciliation = None
        if binding['effective']['access'] != 'read':
            state = self.state(now)
            if state['can_dispatch'] and any(g['goal_id'] == binding['goal'] and g['state'] == 'active' for g in state['goals']):
                reconciliation = self.nodes.start('receipt-reconciliation', binding['goal'],
                    {'call_id': call_id, 'operation': binding['operation'], 'evidence_ref': ref, 'error': error},
                    {'status': 'allow', 'model': 'official-correlated-receipt-contract', 'observation_ref': ref}, now=now)
        if error: receipt = {'status': 'unknown'}
        elif content.startswith('Error:'): receipt = {'status': 'rejected'}
        elif binding['effective']['access'] == 'read': receipt = {'status': 'succeeded'}
        elif binding['effective']['name'] in self.receipt_contracts:
            receipt = self.receipt_contracts[binding['effective']['name']](content, binding['effective']['arguments'])
        else: receipt = self.receipts.parse(binding['effective']['name'], binding['effective']['arguments'], content, error, now=now)
        self.effects.receipt(binding['operation'], call_id, receipt, error=error)
        if reconciliation is not None: self.nodes.finish(reconciliation)
        if binding['effective']['name'] == 'unlock_discoverable_agent_tool' and receipt['status'] == 'succeeded':
            self.unlocked.add(binding['effective']['arguments']['agent_tool_name'])
            durable_json(self.directory/'unlocked-tools.json', sorted(self.unlocked))
        node_status = {'succeeded': 'completed', 'rejected': 'failed', 'accepted': 'waiting',
                       'pending': 'waiting', 'unknown': 'unknown'}[receipt['status']]
        self.task.call('observe_node', node_id=binding['operation'], status=node_status)
        record = {'call_id': call_id, 'receipt': receipt, 'evidence_ref': ref, 'raw_error': error}
        duties = {key: row for key, row in binding.get('later_obligations', {}).items() if row['stage'] == 'receipt'}
        if duties:
            record['official_facts_at_receipt'] = sorted(k for k, v in self.evidence.visible().items()
                                                        if v['source'] == 'official-tool')
        durable_json(receipt_path, record)
        if duties:
            check = self.judgments.requirements({'operation': binding['effective'],
                'persisted_operation_binding': {'call_id': call_id, 'operation_id': binding['operation'],
                                                'effective_operation': binding['effective']},
                'persisted_receipt_record': record, 'official_result': content}, {
                key: {'type': 'noul', 'instructions': {'clause': row['quote'],
                      'question': 'Do the durable host records and the returned official result establish this clause for this operation? '
                                  'A separate required readback still outstanding is not satisfied.'}}
                for key, row in duties.items()}, now=now)
            durable_json(receipt_path, {**record, 'receipt_obligations': check})
        return receipt

    def _wait_for_question(self, goal_id, question, proof, *, now):
        node = self.nodes.start('await-user', goal_id, {'question': question}, proof, now=now)
        self.task.call('wait_goal', goal=goal_id, revision=self.state(now)['revision'], question=question)
        self.nodes.wait(node)

    @recorded
    def repair_question(self, draft, *, now):
        state = self.visible(now)
        active = {g['goal_id']: g for g in state['task']['goals'] if g['state'] == 'active'}
        if not active:
            return None
        proposal = self.planner.complete('question-revision', {'draft': draft,
            'active_goals': {key: g['description'] for key, g in active.items()},
            'customer_messages': [r['content'] for r in state['evidence'].values() if r['source'] == 'official-user']},
            QUESTION_REVISION)
        candidate = proposal['clarification']
        if candidate is None:
            return None
        question = candidate['question'].strip()
        goal = active.get(candidate['goal_id'])
        if (not goal or not candidate['source_quote'].strip() or candidate['source_quote'] not in draft
                or not question or len(question) > 300):
            return None
        proof = self.judgments.requirements({'draft_request': candidate['source_quote'], 'question': question,
            'goal': goal['description'], 'evidence': state['evidence']}, {
            'needed_fact': {'type': 'noul', 'instructions': 'Does this question request one specific fact or choice '
                'still needed from this customer for the selected goal under the visible rules, and raised in draft_request? '
                'A fact established in the available evidence or available only from bank records does not qualify.'},
            'neutral_question': {'type': 'noul', 'instructions': 'Is the text solely a neutral request for that '
                'information without asserting verification, completion, terms, prices or a preferred answer?'}}, now=now)
        if proof['status'] != 'allow':
            return None
        proposal = self.review.extract(question, state)
        if proposal['completed_goal_ids'] or 'claims' not in proposal:
            return None
        review = self.review.check(question, state, proposal=proposal, now=now)
        if review['status'] != 'allow' or self.claims.check(question, proposal['claims'], state, now=now)['status'] != 'allow':
            return None
        self._wait_for_question(goal['goal_id'], question, proof, now=now)
        self.last_question = question
        durable_json(self.directory/'last-question.json', {'question': question})
        self.evidence.add('controller', json.dumps({'type': 'assistant_question', 'content': question}, ensure_ascii=False))
        self.remember_assistant(question)
        return question

    @recorded
    def response(self, content, *, waiting, now):
        established = []
        proof_failures = []
        extraction = self.review.extract(content, self.visible(now))
        claimed = set(extraction['completed_goal_ids'])
        if not waiting:
            for goal in self.state(now)['goals']:
                if goal['state'] != 'active' or goal['goal_id'] not in claimed: continue
                statuses = [self.effects.status(binding['operation'])['business_status']
                            for binding in self.bindings.values() if binding['goal'] == goal['goal_id']]
                if 'unknown' in statuses:
                    continue
                try:
                    plan = self._plan('goal-completion', {'goal': goal, 'candidate_response': content, **self.visible(now)}, now=now)
                    if plan['goal_id'] != goal['goal_id']: raise PermissionError('Wrong goal completion proposal')
                    if not permits_completion(statuses, plan.get('completion_boundary', 'final_effect')):
                        raise PermissionError('Receipt has not reached the requested completion boundary')
                    current_goals = {item['goal_id']: item for item in self.state(now)['goals']}
                    if any(current_goals[parent]['outcome'] != 'success' for parent in current_goals[goal['goal_id']]['dependencies']):
                        raise PermissionError('Goal dependencies have not completed')
                    judgment = self._judge(plan, {'episode': self.task.episode, 'operation': 'goal_completion', 'arguments': {'goal': goal['goal_id']}}, now=now)
                    if judgment['status'] != 'allow': continue
                    established.append((goal, plan, judgment))
                except PermissionError as error:
                    proof_failures.append({'goal_id': goal['goal_id'], 'reason': str(error)})
        context = {**self.visible(now), 'established_goal_ids': [goal['goal_id'] for goal, _, _ in established],
                   'proposed_acceptance_proofs': [{'goal_id': goal['goal_id'], 'proof': judgment} for goal, _, judgment in established]}
        review = self.review.check(content, context, now=now, proposal=extraction)
        if review['status'] != 'allow': result = dict(review)
        elif 'claims' in extraction: result = self.claims.check(content, extraction['claims'], context, now=now)
        else: result = self.output.check(content, context, now=now)  # Component fixtures using the older extraction shape.
        if result['status'] == 'allow':
            for goal, plan, judgment in established:
                self.task.call('configure_goal', goal=goal['goal_id'], revision=self.state(now)['revision'],
                    requirements=[c['id'] for c in plan['conditions']], source_ref=digest(plan['policy_refs']),
                    dependencies=next(item['dependencies'] for item in self.state(now)['goals'] if item['goal_id'] == goal['goal_id']))
                for condition in plan['conditions']:
                    self.task.call('record_condition', goal=goal['goal_id'], revision=self.state(now)['revision'],
                        condition=condition['id'], value=judgment['conditions'][condition['id']], evidence_ref=digest(judgment))
                self.task.call('accept_goal', goal=goal['goal_id'], revision=self.state(now)['revision'])
        result['structured_review'] = review
        result['proof_failures'] = proof_failures
        durable_json(self.directory/('output-'+uuid.uuid4().hex+'.json'), {'content': content, 'waiting': waiting, 'validation': result})
        if result['status'] == 'allow':
            self.remember_assistant(content)
        if result['status'] == 'allow' and waiting:
            self.last_question = content
            durable_json(self.directory/'last-question.json', {'question': content})
            self.evidence.add('controller', json.dumps({'type': 'assistant_question', 'content': content}, ensure_ascii=False))
            goals = [g for g in self.state(now)['goals'] if g['state'] == 'active']
            if goals:
                questions = {f'goal{i}_wait': {'type': 'noul', 'instructions': {
                    'question': 'Does this question request information needed for this goal?', 'goal': goal['description']}}
                    for i, goal in enumerate(goals)}
                values, ref = self.judgments.ask({'question': content}, questions, now=now)
                for i, goal in enumerate(goals):
                    if values[f'goal{i}_wait'] > self.policy.high:
                        self._wait_for_question(goal['goal_id'], content,
                            {'status': 'allow', 'model': self.policy.expected_model, 'observation_ref': ref}, now=now)
        return result
