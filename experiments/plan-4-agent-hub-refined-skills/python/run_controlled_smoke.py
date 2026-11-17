"""Java -> Jev -> Go -> official tool implementation, synthetic DB only.

This is a component-chain diagnostic, NOT an official simulator episode or score.
No hidden task data or reference action is loaded. --execute enables live Jev.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import time

from business_judgment import BusinessJudge, parse_credit_dispute_receipt
from controlled_effects import ControlledEffects
from input_router import InputRouter, RoutingPolicy
from jev_provider import JevClient
from hub_gate import HubGate
from task_session import JavaTask, TaskSession, durable_json, ARM, ROOT


class MeteredClient:
    def __init__(self, client, directory):
        self.client, self.directory, self.calls = client, directory, 0
        self.input_tokens = self.output_tokens = 0

    def ask(self, request):
        if self.calls >= 24: raise RuntimeError('Diagnostic request bound reached')
        self.calls += 1
        prefix = self.directory/('judgment-%02d' % self.calls)
        durable_json(prefix.with_suffix('.request.json'), request)
        durable_json(prefix.with_suffix('.attempt.json'), {'attempted': True, 'automatic_retry': False})
        response = self.client.ask(request)
        durable_json(prefix.with_suffix('.response.json'), response)
        self.input_tokens += response['usage']['input_tokens']; self.output_tokens += response['usage']['output_tokens']
        return response


def run(output, scenario='multi-intent'):
    from tau2.domains.banking_knowledge.data_model import TransactionalDB
    from tau2.domains.banking_knowledge.tools import KnowledgeTools
    # These are artificial identities and a fresh empty official DB object.
    tool = 'file_credit_card_transaction_dispute_4829'
    arguments = {'transaction_id': 'synthetic-tx', 'card_action': 'keep_active', 'card_last_4_digits': '1234',
                 'full_name': 'Synthetic Customer', 'user_id': 'synthetic-user', 'phone': '+10000000000',
                 'email': 'synthetic@example.invalid', 'address': 'Synthetic Test Address', 'contacted_merchant': True,
                 'purchase_date': '11/01/2026', 'issue_noticed_date': '11/02/2026', 'dispute_reason': 'duplicate_charge',
                 'resolution_requested': 'full_refund', 'eligible_for_provisional_credit': False}
    policy = RoutingPolicy('synthetic-smoke-thresholds-not-formal-bank-policy', .3, .7, 'jev-latest', 'jev-1.14.0')
    client = MeteredClient(JevClient(os.environ['TYPESAFE_API_KEY'], timeout=120), output)
    observations = []
    hub = None
    summary = {'scope': 'real Java/Jev/Go plus official tool implementation and synthetic DB',
               'scenario': scenario,
               'official_simulator_episodes': 0, 'official_reward': None, 'full_design_acceptance': 'not-evaluated',
               'observations': observations}
    try:
        with JavaTask(output/'task', 'synthetic-episode', int(time.time())+600, 64) as task:
            session = TaskSession(task, InputRouter(client, policy), output/'routes')
            turns = [
                ('m1', 'Please submit a credit card dispute for a duplicate charge.',
                 [{'description': 'submit a credit card dispute for duplicate charge', 'quote': 'submit a credit card dispute for a duplicate charge'}], 'new'),
                ('m2', 'Pause the credit card dispute for now. Also check my account balance.',
                 [{'description': 'check account balance', 'quote': 'check my account balance'}], 'pause-and-new'),
                ('m3', 'Please resume the credit card dispute.', [], 'resume'),
                ('m4', 'Cancel the account balance check.', [], 'cancel-second'),
                ('m5', 'What is the status of my credit card dispute?', [], 'query-first'),
            ]
            if scenario == 'submission-only':
                turns = turns[:1]
            for message, text, proposals, expected in turns:
                result = session.handle(message, text, proposals, now=int(time.time()))
                state = task.call('status', now=int(time.time()))
                passed = result['status'] == 'ready'
                if expected == 'new': passed &= len(state['goals']) == 1
                if expected == 'pause-and-new': passed &= len(state['goals']) == 2 and state['goals'][0]['state'] == 'waiting'
                if expected == 'resume': passed &= state['goals'][0]['state'] == 'active'
                if expected == 'cancel-second': passed &= state['goals'][1]['state'] == 'closed'
                if expected == 'query-first': passed &= result['targets'] == [{'goal_id': state['goals'][0]['goal_id'], 'action': 'query'}]
                observations.append({'message': message, 'expected': expected, 'proposal_status': result['status'], 'passed': bool(passed), 'reason': result['reason']})
                if not passed: raise RuntimeError('Input semantic diagnostic did not meet expected route; retained without tuning')
            goal = task.call('status', now=int(time.time()))['goals'][0]['goal_id']
            payload = {'episode': task.episode, 'operation': tool, 'arguments': arguments}
            evidence = [{'ref': 'synthetic-user-record', 'episode_id': task.episode, 'goal_id': goal,
                         'content': 'This is an explicitly synthetic fixture. The test customer requests submission of a duplicate-charge dispute. The proposed fields describe that synthetic customer and transaction. This is not a claim about production banking eligibility.'}]
            conditions = [{'id': 'synthetic_request', 'statement': 'The synthetic test customer requests submission of this duplicate-charge dispute.',
                           'evidence_refs': ['synthetic-user-record']}]
            judgment = BusinessJudge(client, policy).judge(task.episode, goal, payload, 'synthetic-tool-contract-only', conditions, evidence)
            durable_json(output/'business-judgment.json', judgment)
            if judgment['status'] != 'allow': raise RuntimeError('Synthetic business observation not resolved')
            hub = HubGate(ARM/'go/target/banking-gate', output/'ledger.jsonl', ROOT.parent/'agent-hub-alpha/agent-festival/schema')
            effects = ControlledEffects(task, hub, output/'effects', {tool: {'access': 'write'}})
            operation = effects.adopt(goal, 'submit-dispute', tool, arguments, judgment, now=int(time.time()))
            official_queue = queue.Queue()
            effects.dispatch(operation, 'synthetic-call-one', official_queue, now=int(time.time()))
            queued = official_queue.get_nowait()['tool_calls'][0]
            database = TransactionalDB(); toolkit = KnowledgeTools(database)
            # Tool-level contract test uses the public unlock/call API; it is not an agent discovery test.
            toolkit.unlock_discoverable_agent_tool(tool)
            raw = toolkit.call_discoverable_agent_tool(queued['name'], json.dumps(queued['arguments']))
            receipt = parse_credit_dispute_receipt(raw)
            durable_json(output/'official-tool-receipt.json', {'raw': raw, 'parsed': receipt})
            effects.receipt(operation, queued['id'], receipt, error=False)
            duplicate_refused = False
            try: effects.dispatch(operation, 'synthetic-call-two', official_queue, now=int(time.time()))
            except PermissionError: duplicate_refused = True
            write_count = len(database.transaction_disputes.data)
            observations.append({'check': 'official-tool-submission', 'passed': write_count == 1 and receipt['status'] == 'accepted',
                                 'write_count': write_count, 'business_status': receipt['status'], 'approved': False})
            observations.append({'check': 'different-call-id-duplicate', 'passed': duplicate_refused and official_queue.empty()})
            # Missing evidence must not adopt or execute a second write.
            missing = dict(judgment, evidence_refs=[], status='unknown')
            refused = False
            try: effects.adopt(goal, 'missing-evidence', tool, arguments, missing, now=int(time.time()))
            except PermissionError: refused = True
            observations.append({'check': 'missing-evidence-zero-extra-writes', 'passed': refused and len(database.transaction_disputes.data) == 1})
            summary['status'] = 'component-chain-passed' if all(x['passed'] for x in observations) else 'component-chain-failed'
    except Exception as error:
        summary.update(status='component-chain-failed', error_type=type(error).__name__, error=str(error))
    finally:
        if hub: hub.close()
        summary['usage'] = {'requests': client.calls, 'input_tokens': client.input_tokens, 'output_tokens': client.output_tokens}
        durable_json(output/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--scenario', choices=['multi-intent', 'submission-only'], default='multi-intent')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    durable_json(args.output/'manifest.json', {
        'purpose': 'component-diagnostic-not-official-episode', 'scenario': args.scenario,
        'request_limit': 24, 'automatic_retry': False,
        'source_hashes': {str(p.relative_to(ROOT)): __import__('hashlib').sha256(p.read_bytes()).hexdigest()
                          for p in [*ARM.joinpath('python').glob('*.py'),
                                    *ARM.joinpath('java/src/main/java').rglob('*.java'),
                                    ARM/'go/target/banking-gate']}})
    if not args.execute:
        durable_json(args.output/'preparation.json', {'execution_started': False, 'scope': 'component-chain-not-formal-benchmark'})
        return
    result = run(args.output, args.scenario)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['status'] == 'component-chain-passed' else 1)


if __name__ == '__main__': main()
