"""Offline evidence review; fresh strict replay, no model calls or score changes."""
import os
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
import argparse, copy, hashlib, json, socket
from datetime import datetime, timezone
from pathlib import Path

def forbidden(*args, **kwargs):
    raise RuntimeError('Network forbidden during paused review')
socket.create_connection = forbidden
socket.socket.connect = forbidden

from deepdiff import DeepDiff
from tau2.data_model.simulation import Results
from tau2.domains.banking_knowledge.environment import get_environment, get_tasks
from tau2.runner.build import _derive_read_log_allowlist

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def review(suite):
    tasks = {t.id: t for t in get_tasks()}
    folders = [*sorted(suite.glob('P06-task_041-r*-a00')),
               *[suite / f'P07-task_{n}-r00-a00' for n in ['041', '023', '053']]]
    output = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'model_calls': 0, 'network_blocked': True, 'execution_remains_paused': True,
              'scope': 'Fresh strict offline reconstruction; state projections are diagnostic, not official rescoring.',
              'cases': []}
    for folder in folders:
        src = next(folder.glob('episodes/*/result.json'))
        before = digest(src)
        sim = Results.model_validate_json(src.read_text()).simulations[0]
        task = tasks[sim.task_id]
        kwargs = dict(retrieval_variant='bm25', task=task,
                      read_log_allowlist=_derive_read_log_allowlist(task))
        actual, gold = get_environment(**kwargs), get_environment(**kwargs)
        initial = task.initial_state
        init = dict(initialization_data=initial.initialization_data if initial else None,
                    initialization_actions=initial.initialization_actions if initial else None)
        actual.set_state(**init, message_history=sim.messages, strict=True)
        gold.set_state(**init, message_history=initial.message_history if initial and initial.message_history else [], strict=True)
        for action in task.evaluation_criteria.actions:
            gold.make_tool_call(tool_name=action.name, requestor=action.requestor, **action.arguments)
        ad, gd = actual.tools.db.model_dump(), gold.tools.db.model_dump()
        diff = json.loads(DeepDiff(gd, ad, verbose_level=2).to_json())
        previous = json.loads(next((folder / 'diagnostics').glob('*-db-diff.json')).read_text())
        hashes = dict(gold_agent=gold.get_db_hash(), actual_agent=actual.get_db_hash(),
                      gold_user=gold.get_user_db_hash(), actual_user=actual.get_user_db_hash())
        assert hashes == previous['hashes'], folder
        assert diff == previous['deepdiff_gold_to_actual'], folder
        calls = [(i, c) for i, msg in enumerate(sim.messages) for c in (getattr(msg, 'tool_calls', None) or [])]
        row = dict(attempt=folder.name, source_result=str(src), source_result_sha256=before,
                   official_reward=sim.reward_info.reward, fresh_hashes=hashes,
                   existing_diagnostic_reproduced=True, difference=diff,
                   action_checks_all_match=all(c.action_match for c in sim.reward_info.action_checks))
        if sim.task_id == 'task_041':
            def inner(args):
                return json.loads(args['arguments']) if isinstance(args['arguments'], str) else args['arguments']
            expected = {inner(a.arguments)['transaction_id']: inner(a.arguments)
                        for a in task.evaluation_criteria.actions
                        if a.name == 'call_discoverable_agent_tool' and a.arguments.get('agent_tool_name') == 'file_credit_card_transaction_dispute_4829'}
            filed = [(i, inner(c.arguments)) for i, c in calls if c.name == 'call_discoverable_agent_tool'
                     and c.arguments.get('agent_tool_name') == 'file_credit_card_transaction_dispute_4829']
            mismatches = []
            for i, args in filed:
                target = expected[args['transaction_id']]
                fields = {k: {'gold': target.get(k), 'actual': args.get(k)} for k in set(target) | set(args)
                          if target.get(k) != args.get(k)}
                if fields:
                    mismatches.append(dict(message_index=i, transaction_id=args['transaction_id'], fields=fields))
            row.update(filed_count=len(filed), gold_eligible_count=sum(a['eligible_for_provisional_credit'] for a in expected.values()),
                       actual_eligible_count=sum(a['eligible_for_provisional_credit'] for _, a in filed),
                       argument_mismatches=mismatches,
                       history_call_indices=[i for i,c in calls if c.name == 'call_discoverable_agent_tool' and c.arguments.get('agent_tool_name') == 'get_user_dispute_history_7291'])
        if sim.task_id == 'task_023':
            row['application_calls'] = [dict(message_index=i, requestor=str(c.requestor), arguments=c.arguments)
                                        for i,c in calls if c.name == 'apply_for_credit_card']
            row['assistant_rebate_statements'] = [dict(message_index=i, content=m.content) for i,m in enumerate(sim.messages)
                         if m.role == 'assistant' and m.content and ('did earn the $150' in m.content or 'you did not qualify' in m.content)]
        # Remove only extra records in a copy, never change the replayed DB or reward.
        projected = copy.deepcopy(ad)
        removed = []
        for table in ad:
            if not isinstance(ad[table], dict) or not isinstance(ad[table].get('data'), dict):
                continue
            for key in set(ad[table]['data']) - set(gd[table]['data']):
                removed.append(dict(table=table, key=key, value=projected[table]['data'].pop(key)))
        row['extra_record_projection'] = dict(removed=removed, full_agent_db_equals_gold_after_removal=projected == gd,
                                               interpretation='In-memory projection only, not an alternate benchmark score.')
        assert digest(src) == before
        row['source_result_unchanged'] = True
        output['cases'].append(row)
    target = suite / 'paused-case-review-evidence.json'
    output['review_script_sha256'] = digest(Path(__file__))
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps({'evidence': str(target), 'fresh_strict_replays': len(folders), 'model_calls': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', type=Path, required=True)
    review(parser.parse_args().suite.resolve())
