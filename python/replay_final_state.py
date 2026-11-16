"""Reconstruct final official bank state from an actual completed tool trajectory."""
import os
os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True'
import argparse,hashlib,json,socket
from pathlib import Path
socket.create_connection=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Network forbidden in state reconstruction'))
socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Network forbidden in state reconstruction'))
from tau2.domains.banking_knowledge.environment import get_environment,get_tasks
from tau2.data_model.simulation import Results
from tau2.runner.build import _derive_read_log_allowlist

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 files=list(a.root.glob('episodes/*/result.json'))
 if len(files)!=1:raise SystemExit('Exactly one completed official result required')
 source=files[0];sim=Results.model_validate(json.loads(source.read_text())).simulations[0]
 task=next(t for t in get_tasks() if t.id==sim.task_id)
 env=get_environment(retrieval_variant='bm25',task=task,read_log_allowlist=_derive_read_log_allowlist(task));initial=task.initial_state
 env.set_state(initialization_data=initial.initialization_data if initial else None,initialization_actions=initial.initialization_actions if initial else None,message_history=sim.messages,strict=True)
 result={'source_result_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'task_id':task.id,'strict_reconstruction':True,'model_calls':0,'final_agent_db_hash':env.get_db_hash(),'final_user_db_hash':env.get_user_db_hash(),'official_reward_unchanged':sim.reward_info.reward,'scope':'Reconstructed official business state; not Core checkpoint state or full model-response replay'}
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
