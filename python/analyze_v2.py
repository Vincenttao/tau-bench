"""Post-run analysis only; no evaluator/runner edits. Explicit denominators and roles."""
import sys,json,collections,statistics,itertools,math,re,csv
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'manifest.json').read_text());normal={'user_stop','agent_stop'}
def canonical(v):
 if isinstance(v,dict):
  out={}
  for k,x in sorted(v.items()):
   if k=='arguments' and isinstance(x,str):
    try:
     parsed=json.loads(x)
     if isinstance(parsed,(dict,list)):x=parsed
    except (ValueError,TypeError):pass
   out[k]=canonical(x)
  return out
 if isinstance(v,list):return [canonical(x) for x in v]
 if isinstance(v,float) and v.is_integer():return int(v)
 return v
def action(call,role):
 name=call['name'];args=canonical(call.get('arguments',{}))
 for wrapper,key in [('call_discoverable_agent_tool','agent_tool_name'),('call_discoverable_user_tool','user_tool_name')]:
  if name==wrapper:
   name=args.get(key,name);args=args.get('arguments',{})
 return {'actor':role,'name':name,'arguments':args}
def sig(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def similarity(a,b):
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  curr=[i]
  for j,y in enumerate(b,1):curr.append(min(curr[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
  prev=curr
 return 1-prev[-1]/max(len(a),len(b),1)
def sequence_metrics(rs,field):
 nonempty=[r[field] for r in rs if r.get(field)];empty=sum(not r.get(field) for r in rs)
 pairs=list(itertools.combinations(nonempty,2))
 return {'eligible_runs':len(rs),'nonempty_runs':len(nonempty),'empty_or_unavailable_runs':empty,'comparable_pairs':len(pairs),'exact_all_equal':len({tuple(p) for p in nonempty})==1 if len(nonempty)>=2 and empty==0 else None,'pairwise_exact_rate':sum(a==b for a,b in pairs)/len(pairs) if pairs else None,'pairwise_edit_similarity':statistics.mean(similarity(a,b) for a,b in pairs) if pairs else None,'distinct_nonempty_sequences':len({tuple(p) for p in nonempty})}
rows=[]
for e in manifest['episodes']:
 out=root/'episodes'/e['key'];sp=out/'status.json'
 if not sp.exists():continue
 r={**e,**json.loads(sp.read_text())};result=out/'result.json';unscored=out/'trajectory-unscored.json';trace=None;task=None
 if result.exists():
  d=json.loads(result.read_text());trace=d['simulations'][0];task=d['tasks'][0]
 elif unscored.exists():trace=json.loads(unscored.read_text())
 elif (out/'official-trajectory.jsonl').exists():trace={'messages':[json.loads(l) for l in (out/'official-trajectory.jsonl').read_text().splitlines()]}
 if trace:
  reason=trace.get('termination_reason',r.get('termination_reason'));r['termination_reason']=reason;r['complete_normal']=reason in normal
  msgs=trace.get('messages',[]);actions=[];selected=[];r['agent_tool_calls']=0;r['user_tool_calls']=0
  for msg in msgs:
   role=msg.get('role')
   if role not in ['assistant','user']:continue
   for c in msg.get('tool_calls')or[]:
    ac=action(c,'agent' if role=='assistant' else 'user');actions.append(ac);r['agent_tool_calls' if role=='assistant' else 'user_tool_calls']+=1
    if role=='user' or c['name'] in ['call_discoverable_agent_tool','change_user_email','log_verification','give_discoverable_user_tool','transfer_to_human_agents']:selected.append(ac)
  r['system_action_sequence']=[sig(x) for x in actions];r['system_tool_name_sequence']=[x['actor']+':'+x['name'] for x in actions]
  r['selected_operation_sequence']=[sig(x) for x in selected];r['selected_operation_names']=[x['actor']+':'+x['name'] for x in selected]
  r['messages']=len(msgs);r['tool_errors']=sum(bool(msg.get('error')) for msg in msgs if msg.get('role')=='tool');r['reward_breakdown']=(trace.get('reward_info')or{}).get('reward_breakdown')
  if r.get('reward')==0:
   breakdown=r.get('reward_breakdown')or{}
   if reason in normal:r['failure_class']='official_state_mismatch' if breakdown.get('DB')==0 else ('official_action_mismatch' if breakdown.get('ACTION')==0 else ('official_nl_assertion_failure' if breakdown.get('NL_ASSERTION')==0 else 'official_reward_failure'))
   else:r['failure_class']='execution_limit' if reason in ['max_steps','too_many_errors','timeout'] else 'runtime_or_model_failure'
 if (out/'exception.txt').exists():
  error=(out/'exception.txt').read_text();r['failure_class']='judge_or_evaluator' if r['status']=='evaluation_error' else ('model_gateway' if any(s in error for s in ['RateLimit','APIConnection','Timeout','OpenAIException']) else 'adapter_or_framework')
 logs='\n'.join(p.read_text(errors='replace') for p in (out/'java').glob('*.stderr.log')) if (out/'java').exists() else ''
 r['rail_rejections']=logs.count('action=reject');r['java_tokens']=sum(map(int,re.findall(r'event=react_model_call_completed[^\n]*total_tokens=(\d+)',logs)))
 r['gateway_user_judge_tokens']=sum(json.loads(l).get('total_tokens',0) for p in out.glob('user-usage.jsonl') for l in p.read_text().splitlines())
 rows.append(r)
tasks=[]
for tid in sorted({e['task_id'] for e in manifest['episodes']}):
 rs=sorted([r for r in rows if r['task_id']==tid],key=lambda r:r['trial']);sc=[r for r in rs if r['status']=='scored'];n=len(sc);wins=sum(r.get('reward')==1 for r in sc)
 successful=[r for r in sc if r.get('reward')==1 and r.get('complete_normal')];failed=[r for r in sc if r.get('reward')!=1 and r.get('complete_normal')];complete_scored=successful+failed
 t={'task_id':tid,'planned':manifest['trials'],'finished':len(rs),'not_finished':manifest['trials']-len(rs),'scored':n,'unscored_finished':len(rs)-n,'wins':wins,'observed_success_rate_scored':wins/n if n else None,'all_planned_trials_scored':n==manifest['trials'],'observed_pass_hat_k_scored_subset':{str(k):math.comb(wins,k)/math.comb(n,k) for k in range(1,n+1)},'outcomes':[{'trial':r['trial'],'status':r['status'],'reward':r.get('reward'),'termination':r.get('termination_reason')} for r in rs],'successful_complete_runs':len(successful),'failed_complete_runs':len(failed),'error_or_truncated_or_unscored_runs':len(rs)-len(complete_scored),'trajectory':{}}
 for label,subset in [('successful_only',successful),('failed_complete_only',failed),('all_scored_complete',complete_scored)]:
  t['trajectory'][label]={field:sequence_metrics(subset,field) for field in ['selected_operation_sequence','selected_operation_names','system_tool_name_sequence','system_action_sequence']}
 tasks.append(t)
scored=sum(r['status']=='scored' for r in rows);wins=sum(r.get('reward')==1 for r in rows);complete_tasks=[t for t in tasks if t['all_planned_trials_scored']]
summary={'planned':len(manifest['episodes']),'finished':len(rows),'not_finished':len(manifest['episodes'])-len(rows),'scored':scored,'unscored_finished':len(rows)-scored,'wins':wins,'success_rate_scored_subset':wins/scored if scored else None,'full_scored_tasks':len(complete_tasks),'total_tasks':len(tasks),'macro_pass_hat_k_complete_tasks_only':{str(k):statistics.mean(t['observed_pass_hat_k_scored_subset'][str(k)] for t in complete_tasks) for k in range(1,manifest['trials']+1)} if complete_tasks else {},'status_counts':dict(collections.Counter(r['status'] for r in rows)),'failure_counts':dict(collections.Counter(r['failure_class'] for r in rows if r.get('failure_class'))),'java_tokens_completed_episodes':sum(r['java_tokens'] for r in rows),'gateway_user_judge_tokens_completed_episodes':sum(r['gateway_user_judge_tokens'] for r in rows),'notes':['No pending or unscored episode is converted to an official score. Subset success/pass^k denominators are explicit; full-suite macro metrics need all 97 tasks fully scored, otherwise only complete-task subset is reported.','pass^k means all k draws succeed, not at least one succeeds. Five trials have limited precision.','Successful-only, failed-complete and all-scored-complete paths are separated. Errors/truncations/unscored trajectories do not enter these similarity estimates. Empty selected sequences are not 100% agreement.','Selected operations include all user tools and agent discovery invocations/verification/grants/changes/transfer, and may include reads. This is not exclusively write operations. Full system tool/action sequences are also reported.','Role, business IDs, argument content and operation order are retained. Only generated tool call IDs/timestamps/prose are omitted. Nested arguments JSON is parsed recursively only when it is object/list; integral numbers normalized. No arbitrary numeric strings/IDs are converted.','Failure labels identify the official grading layer, not proven root cause; offline replay is needed to distinguish business defects from bookkeeping differences.','Edit similarity is descriptive and not an official benchmark score; consistent failure is not reliability. No seed guarantees identical server model backend.'],'tasks':tasks,'runs':rows}
(root/'analysis-v2.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
fields=['task_id','planned','finished','not_finished','scored','unscored_finished','wins','observed_success_rate_scored','all_planned_trials_scored','successful_complete_runs','failed_complete_runs','error_or_truncated_or_unscored_runs']
with (root/'task-summary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:t[k] for k in fields} for t in tasks)
print(json.dumps({k:v for k,v in summary.items() if k not in ['tasks','runs','notes']},indent=2,ensure_ascii=False))
