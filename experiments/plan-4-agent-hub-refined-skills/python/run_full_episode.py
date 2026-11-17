"""Development episode using the pinned official simulator and unchanged evaluator."""
import argparse,json,os,traceback,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--index',type=int,default=0);a=p.parse_args()
m=json.loads(Path(a.manifest).read_text());limits=m['limits'];e=m['episodes'][a.index];out=Path(m['output'])/'episodes'/e['key'];out.mkdir(parents=True,exist_ok=True)
os.environ['JAVA_LOG_DIR']=str(out/'java')
os.environ['OPENAI_MODEL']=m['model']
os.environ['OPENAI_API_BASE']=m['api_base']
os.environ['OPENAI_BASE_URL']=m['api_base']
os.environ['JAVA_AGENT_EVENT_TIMEOUT']=str(limits['bridge_call_timeout_seconds'])
os.environ['JAVA_AGENT_COMPLETION_TIMEOUT']=str(limits['core_call_timeout_seconds'])
os.environ['MODEL_REQUEST_TIMEOUT_SECONDS']=str(limits['model_request_timeout_seconds'])
if m['driver'] in ('deepagent', 'moa-pilot', 'hub-read-pilot', 'hub-evidence-control'):
 from skill_assets import pin_manifest_skill
 pin_manifest_skill(m)
from loguru import logger
logger.remove()
secret=os.getenv('OPENAI_API_KEY','')
def redact_log(message):
 with (out/'runner.log').open('a') as stream:
  stream.write(str(message).replace(secret,'[REDACTED]') if secret else str(message))
logger.add(redact_log,level='WARNING')
from tau2.utils import llm_utils
ACTIVE_AGENT=None
user_model_pin=None
original_completion=llm_utils.completion
usage_file=out/'user-usage.jsonl'
def metered_completion(*args,**kwargs):
 global user_model_pin
 if ACTIVE_AGENT is not None:ACTIVE_AGENT.task.call('charge',now=int(time.time()),kind='user')
 model=kwargs.get('model','')
 if model not in ['openai/'+m['model'],m['model'],'gpt-4.1-2025-04-14']:raise ValueError('Unapproved model route '+model)
 # Route even the official judge only to the user's specified gateway, never api.openai.com.
 kwargs['api_base']=os.environ['OPENAI_API_BASE']
 kwargs['model']='openai/'+m['model']
 kwargs['num_retries']=0
 kwargs['timeout']=limits['model_request_timeout_seconds']
 result=original_completion(*args,**kwargs)
 actual_model=result.get('model')
 if not actual_model:raise ValueError('User model identity missing')
 if user_model_pin is not None and actual_model!=user_model_pin:raise ValueError('User model version drift')
 if user_model_pin is None:
  user_model_pin=actual_model
  (out/'user-model-pin.json').write_text(json.dumps({'actual_model':actual_model}))
 u=result.get('usage') or {}
 event={'time':time.time(),'requested_model':model,'model':result.get('model'),'prompt_tokens':u.get('prompt_tokens',0),'completion_tokens':u.get('completion_tokens',0),'total_tokens':u.get('total_tokens',0)}
 with usage_file.open('a') as f:f.write(json.dumps(event)+'\n')
 return result
llm_utils.completion=metered_completion
from tau2.registry import registry
from tau2.runner import get_tasks,run_single_task,get_info
from tau2.data_model.simulation import Results,TextRunConfig
from tau2.evaluator.evaluator import EvaluationType
from tau2.runner import simulation as simulation_module
from tau2.runner import batch as batch_module
from java_agent import JavaMoaAgent,cleanup
if m['driver'] == 'hub-evidence-control':
 from full_hub_agent import FullHubAgent
 JavaMoaAgent = FullHubAgent
elif m["driver"] == "deepagent":
 from deepagent_java_agent import DeepAgentJavaAgent
 JavaMoaAgent = DeepAgentJavaAgent
elif m['driver'] == 'moa-pilot':
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments/plan-3-moa-refined-skills/python'))
 from moa_pilot_agent import MoaPilotAgent
 JavaMoaAgent = MoaPilotAgent
elif m['driver'] == 'hub-read-pilot':
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments/plan-4-agent-hub-refined-skills/python'))
 from hub_pilot_agent import HubPilotAgent
 JavaMoaAgent = HubPilotAgent
else:
 raise ValueError('Unsupported diagnostic driver')
# Factory never forwards the task/answer/evaluation criteria to the Java agent.
def factory(*,tools,domain_policy,llm,llm_args,**ignored):
 global ACTIVE_AGENT
 ACTIVE_AGENT=JavaMoaAgent(tools=tools,domain_policy=domain_policy,llm=llm,llm_args=llm_args,
                     benchmark_language=m['language'],system_prompt_version=m['system_prompt_version'])
 return ACTIVE_AGENT
registry.register_agent_factory(factory,'openjiuwen_java_moa')
args={'temperature':0.0,'api_base':os.environ['OPENAI_API_BASE'],'timeout':120,'num_retries':0}
config=TextRunConfig(domain=e['domain'],agent='openjiuwen_java_moa',user='user_simulator',llm_agent='openai/'+m['model'],llm_args_agent={'temperature':0.0},llm_user='openai/'+m['model'],llm_args_user=args,max_steps=limits['max_steps'],max_errors=limits['max_errors'],retrieval_config='bm25',num_trials=1,seed=e['seed'])
task=get_tasks(e['domain'],task_ids=[e['task_id']])[0]
original_evaluate=simulation_module.evaluate_simulation
captured=[]
def observed_evaluate(*args,**kwargs):
 sim=kwargs['simulation'];sim.trial=e['trial'];captured.append(sim)
 (out/'trajectory-unscored.json').write_text(sim.model_dump_json(indent=2))
 return original_evaluate(*args,**kwargs)
simulation_module.evaluate_simulation=observed_evaluate
# Observation-only step journal: preserve official user-side tools even if a later model call fails.
original_build=batch_module.build_orchestrator
orchestrators=[]
def observed_build(*args,**kwargs):
 orch=original_build(*args,**kwargs);orchestrators.append(orch);original_step=orch.step;written=[0]
 def observed_step(*a,**kw):
  try:return original_step(*a,**kw)
  finally:
   trajectory=getattr(orch,'trajectory',[])
   with (out/'official-trajectory.jsonl').open('a') as f:
    for msg in trajectory[written[0]:]:f.write(msg.model_dump_json()+'\n')
   written[0]=len(trajectory)
 orch.step=observed_step
 return orch
batch_module.build_orchestrator=observed_build
try:
 sim=run_single_task(config,task,evaluation_type=EvaluationType.ALL,seed=e['seed'],save_dir=out,verbose_logs=True);sim.trial=e['trial']
 result=Results(info=get_info(config),tasks=[task],simulations=[sim]);tmp=out/'result.tmp';result.save(tmp);tmp.replace(out/'result.json')
 status={'status':'scored','domain':e['domain'],'task_id':e['task_id'],'trial':e['trial'],'reward':sim.reward_info.reward,'termination_reason':sim.termination_reason,'duration':sim.duration}
except Exception as ex:
 secret=os.getenv('OPENAI_API_KEY','');detail=traceback.format_exc();detail=detail.replace(secret,'[REDACTED]') if secret else detail
 (out/'exception.txt').write_text(detail)
 status={'status':'evaluation_error' if captured else 'execution_error','domain':e['domain'],'task_id':e['task_id'],'trial':e['trial'],'error_type':type(ex).__name__,'trajectory_preserved':bool(captured)}
finally:
 if ACTIVE_AGENT is not None:ACTIVE_AGENT.close()
 cleanup()
(out/'status.json').write_text(json.dumps(status,indent=2))
