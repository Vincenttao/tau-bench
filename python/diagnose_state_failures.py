"""One-pass offline strict DB replay; preserves benchmark files and scores. No model calls."""
import os
os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True'
import argparse,json,hashlib
from pathlib import Path
from deepdiff import DeepDiff
from tau2.domains.banking_knowledge.environment import get_environment,get_tasks
from tau2.data_model.simulation import Results
from tau2.runner.build import _derive_read_log_allowlist
# Fail closed if accidental model/network access is introduced into replay dependencies.
import socket
socket.create_connection=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Network forbidden in offline diagnostic'))
socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Network forbidden in offline diagnostic'))
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--task-id');a=p.parse_args()
D=a.root/'diagnostics';D.mkdir(exist_ok=True);tasks={t.id:t for t in get_tasks()}
for status in sorted((a.root/'episodes').glob('*/status.json')):
 st=json.loads(status.read_text());tid=st.get('task_id');trial=st.get('trial')
 if st.get('status')!='scored' or (a.task_id and tid!=a.task_id):continue
 out=D/f'{tid.replace("task_","task")}-trial{trial}-db-diff.json'
 if out.exists():continue
 src=status.parent/'result.json'
 if not src.exists():continue
 s=Results.model_validate(json.loads(src.read_text())).simulations[0]
 if not s.reward_info or not s.reward_info.db_check or s.reward_info.db_check.db_match is not False:continue
 t=tasks[tid];kw={'retrieval_variant':'bm25','task':t,'read_log_allowlist':_derive_read_log_allowlist(t)}
 doc={'task_id':tid,'trial':trial,'official_reward_unchanged':s.reward_info.reward,'source_result_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'replay':{'strict':True,'retrieval_variant':'bm25','model_calls':0,'read_log_allowlist':sorted(kw['read_log_allowlist'])},'source_locations':['src/tau2/evaluator/evaluator_env.py:85-131','src/tau2/environment/toolkit.py:242-244'],'note':'Diagnostic only; no original result, task, evaluator or reward modification.'}
 try:
  actual=get_environment(**kw);gold=get_environment(**kw);init=t.initial_state
  initargs={'initialization_data':init.initialization_data if init else None,'initialization_actions':init.initialization_actions if init else None}
  actual.set_state(**initargs,message_history=s.messages,strict=True)
  gold.set_state(**initargs,message_history=init.message_history if init and init.message_history else [],strict=True)
  for x in t.evaluation_criteria.actions:gold.make_tool_call(tool_name=x.name,requestor=x.requestor,**x.arguments)
  ag=actual.tools.db.model_dump();gg=gold.tools.db.model_dump()
  doc.update(hashes={'gold_agent':gold.get_db_hash(),'actual_agent':actual.get_db_hash(),'gold_user':gold.get_user_db_hash(),'actual_user':actual.get_user_db_hash()},deepdiff_gold_to_actual=json.loads(DeepDiff(gg,ag,verbose_level=2).to_json()),user_deepdiff_gold_to_actual=json.loads(DeepDiff(gold.user_tools.db.model_dump(),actual.user_tools.db.model_dump(),verbose_level=2).to_json()))
  doc['replay_completed']=True
 except Exception as ex:doc.update(replay_completed=False,error_type=type(ex).__name__,error=str(ex))
 out.write_text(json.dumps(doc,indent=2,ensure_ascii=False));print(out)
