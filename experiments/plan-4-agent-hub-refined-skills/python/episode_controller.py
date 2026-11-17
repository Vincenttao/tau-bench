"""Complete episode control surface; official scheduling remains outside this module."""
import copy
import json
from pathlib import Path
import time
import uuid

from business_judgment import BusinessJudge, parse_credit_dispute_receipt
from controlled_effects import ControlledEffects, digest
from input_router import InputRouter
from planner_client import GOAL_SCHEMA, STEP_SCHEMA
from runtime_guards import EvidenceStore, JudgmentService, OutputGate, resolve_operation
from task_session import TaskSession, durable_json
from response_review import ResponseReview
from receipt_registry import ReceiptInterpreter
from completion_policy import permits_completion
from controlled_nodes import ControlledNodes


class EpisodeController:
    NODE_VERSION = 'banking-evidence-control'
    NODES = {'evidence-investigation': 'agent_loop', 'candidate-comparison': 'workflow',
             'guarded-operation': 'tool', 'dependent-goals': 'workflow',
             'receipt-reconciliation': 'workflow', 'await-user': 'wait'}

    def __init__(self, task, hub, planner, jev, policy, directory, catalog, domain_policy, receipt_contracts=None):
        self.task, self.hub, self.planner, self.jev, self.policy = task, hub, planner, jev, policy
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.catalog = copy.deepcopy(catalog)
        self.receipt_contracts = receipt_contracts or {}
        self.evidence = EvidenceStore(self.directory/'evidence', task.episode)
        self.policy_ref = self.evidence.add('official-policy', domain_policy)
        self.judgments = JudgmentService(jev, task, self.directory/'judgments', policy)
        self.output = OutputGate(self.judgments)
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
        self.bindings_path = self.directory/'call-bindings.json'
        self.bindings = json.loads(self.bindings_path.read_text()) if self.bindings_path.exists() else {}

    def state(self, now):
        return self.task.call('status', now=now)

    def visible(self, now):
        return {'task': self.state(now), 'evidence': self.evidence.visible(), 'last_question': self.last_question}

    def user(self, message, content, *, now):
        # Receive before even tool-free S2 planning: new input blocks old dispatch immediately.
        self.task.call('receive', episode=self.task.episode, message=message, content=content)
        self.evidence.add('official-user', content)
        plan_path = self.directory/('goals-'+digest(message)+'.json')
        if plan_path.exists(): proposal = json.loads(plan_path.read_text())
        else:
            attempt = plan_path.with_suffix('.attempt.json')
            if attempt.exists(): raise RuntimeError('Previous S2 proposal outcome unknown; no replay')
            durable_json(attempt, {'attempted': True})
            proposal = self.planner.complete('new-goals', {'content': content,
                'task': self.state(now), 'last_question': self.last_question}, GOAL_SCHEMA)
            durable_json(plan_path, proposal)
        result = self.inputs.handle(message, content, proposal['goals'], now=now, last_question=self.last_question)
        if result['status'] == 'ready': self.nodes.resume_waits(now=now)
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

    def _plan(self, purpose, state, *, now):
        plan = self.planner.complete(purpose, state, STEP_SCHEMA)
        original = copy.deepcopy(plan)
        if plan['status'] != 'proposed' or not plan['conditions']:
            raise PermissionError('S2 has not established a bounded plan')
        plan['policy_refs'] = self.evidence.resolve_refs(plan['policy_refs'])
        for condition in plan['conditions']:
            condition['evidence_refs'] = self.evidence.resolve_refs(condition['evidence_refs'])
        known = self.evidence.visible()
        if not plan['policy_refs'] or any(ref not in known or known[ref]['source'] not in
                                         ('official-policy', 'published-skill') for ref in plan['policy_refs']):
            raise PermissionError('Plan has missing or fabricated policy references')
        for condition in plan['conditions']:
            if not condition['evidence_refs'] or any(ref not in known for ref in condition['evidence_refs']):
                raise PermissionError('Condition evidence is missing or fabricated')
        snapshot = {'proposal': plan, **state}
        questions = {
            'goal_link': {'type': 'noul', 'instructions': 'Does the proposal concern the stated customer goal and the actual proposed action or completion result?'},
            'conditions_grounded': {'type': 'noul', 'instructions': 'Are the proposed conditions grounded in the original customer requirements and applicable visible policy, without inventing or weakening requirements?'},
            'conditions_complete': {'type': 'noul', 'instructions': 'Do the proposed conditions cover all applicable requirements for this proposed action or goal completion, including prerequisites, ordering and confirmation where required by visible policy?'}}
        if purpose == 'goal-completion':
            questions['completion_boundary_grounded'] = {'type': 'noul', 'instructions':
                'Does completion_boundary faithfully describe the original customer goal? submission means the customer requested filing or submitting a request, not receiving approval or the eventual effect. information means providing requested information; final_effect requires the actual bank outcome.'}
        if plan.get('dependencies'):
            questions['dependencies_grounded'] = {'type': 'noul', 'instructions':
                'Does every proposed dependency represent a whole customer goal that must finish before this action under visible policy or explicit user instructions? Priority alone does not create a dependency; do not defer a service until unrelated eventual bank processing is finished.'}
        check = self.judgments.requirements(snapshot, questions, now=now)
        durable_json(self.directory/('plan-'+uuid.uuid4().hex+'.json'), {'original_proposal': original, 'proposal': plan, 'validation': check})
        if check['status'] != 'allow': raise PermissionError('Plan evidence/coverage not established')
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
        evidence = [{'ref': ref, 'episode_id': self.task.episode, 'goal_id': plan['goal_id'],
                     'source': records[ref]['source'], 'content': records[ref]['content']} for ref in selected]
        self.task.call('charge', now=now, kind='judgment')
        result = BusinessJudge(self.jev, self.policy).judge(self.task.episode, plan['goal_id'], payload,
                    digest({'policy_refs': plan['policy_refs'], 'conditions': plan['conditions']}), plan['conditions'], evidence)
        durable_json(self.directory/('business-'+uuid.uuid4().hex+'.json'), result)
        return result

    def tool(self, call, official_queue, *, now):
        operation = resolve_operation(call['name'], call['arguments'], self.catalog)
        state = self.visible(now)
        if not state['task']['can_dispatch']: raise PermissionError('Input or task blocks dispatch')
        active = [g for g in state['task']['goals'] if g['state'] == 'active']
        if not active: raise PermissionError('No active goal')
        payload = {'episode': self.task.episode, 'operation': call['name'], 'arguments': copy.deepcopy(call['arguments'])}
        # Reads supply episode evidence, often shared by several goals. Attribution
        # is bookkeeping; customer scope is the independent authorization check.
        if operation['access'] == 'read':
            goal = active[0]
            if operation['name'] not in ('KB_search', 'get_current_time'):
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
            plan = self._plan('tool-step', {**state, 'actual_call': call, 'effective_operation': operation}, now=now)
            judgment = self._judge(plan, payload, now=now)
        if plan['goal_id'] not in {g['goal_id'] for g in active}: raise PermissionError('Wrong or inactive goal')
        if judgment['status'] != 'allow': raise PermissionError('Business conditions are unresolved or denied')
        identifiers = {k: v for k, v in operation['arguments'].items()
                       if k.endswith('_id') or 'last_4' in k or k in ('agent_tool_name', 'discoverable_tool_name')}
        step = (operation['name']+':'+digest(identifiers)) if operation['access'] != 'read' else ('read:'+call['id'])
        adopted = self.effects.adopt(plan['goal_id'], step, call['name'], call['arguments'], judgment, now=now)
        self.bindings[call['id']] = {'operation': adopted, 'effective': operation, 'goal': plan['goal_id']}
        durable_json(self.bindings_path, self.bindings)
        node = 'evidence-investigation' if operation['access'] == 'read' else 'guarded-operation'
        self.task.call('start_node', node_id=adopted, goal=plan['goal_id'], revision=self.state(now)['revision'],
                       kind=node, version=self.NODE_VERSION, decision_ref=adopted, now=now)
        durable_json(self.directory/('node-'+adopted+'.json'), {'node': node, 'version': self.NODE_VERSION,
            'kind': self.NODES[node], 'decision_ref': adopted, 'goal': plan['goal_id'], 'status': 'running'})
        self.effects.dispatch(adopted, call['id'], official_queue, now=now)

    def receipt(self, call_id, content, error, *, now):
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
        durable_json(receipt_path, {'call_id': call_id, 'receipt': receipt, 'evidence_ref': ref, 'raw_error': error})
        return receipt

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
        result = self.output.check(content, context, now=now) if review['status'] == 'allow' else dict(review)
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
                        node = self.nodes.start('await-user', goal['goal_id'], {'question': content},
                            {'status': 'allow', 'model': self.policy.expected_model, 'observation_ref': ref}, now=now)
                        self.task.call('wait_goal', goal=goal['goal_id'], revision=self.state(now)['revision'], question=content)
                        self.nodes.wait(node)
        return result
