"""Offline action-check diagnostic; exports field names and counts, not customer data."""
import collections,json,sys
from pathlib import Path
root=Path(sys.argv[1])
for path in root.glob('episodes/*/result.json'):
 sim=json.loads(path.read_text())['simulations'][0];reward=sim.get('reward_info') or {}
 if reward.get('reward')!=0:continue
 calls=collections.defaultdict(list)
 for msg in sim['messages']:
  for c in msg.get('tool_calls') or []:
   args=c['arguments'];calls[c['name']].append(json.loads(args) if isinstance(args,str) else args)
 unmatched=[]
 for check in reward.get('action_checks') or []:
  if check['action_match']:continue
  action=check['action'];matches=calls[action['name']]
  item={'action_id':action['action_id'],'name':action['name'],'requestor':action['requestor'],'compare_args':action.get('compare_args'),'observed_same_name_calls':len(matches)}
  if len(matches)==1:
   expected=action['arguments'];actual=matches[0];keys=action.get('compare_args')
   if keys is None:keys=list(actual)
   item['missing_compared_fields']=[k for k in keys if k not in actual]
   item['different_compared_fields']=[k for k in keys if actual.get(k)!=expected.get(k)]
   item['actual_compared_fields_absent_from_expected']=[k for k in keys if k in actual and k not in expected]
  unmatched.append(item)
 doc={'task_id':sim['task_id'],'official_reward':reward['reward'],'reward_basis':reward.get('reward_basis'),'reward_breakdown':reward.get('reward_breakdown'),'db_match':(reward.get('db_check') or {}).get('db_match'),'duration':sim['duration'],'termination_reason':sim['termination_reason'],'unmatched_actions':unmatched,'tool_counts':{k:len(v) for k,v in calls.items()},'note':'Offline diagnostic, no original score changes. Multiple same-name calls are not automatically paired. No model/framework root cause inferred.'}
 doc.update(schema='action-diagnostic-v2',comparison_rule='Official Action.compare_with_tool_call: compare_args None uses actual submitted keys; empty list compares no fields. Field diagnostics only; official scores unchanged.')
 (root/'action-diagnostic-v2.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2));print(json.dumps(doc,ensure_ascii=False,indent=2))
