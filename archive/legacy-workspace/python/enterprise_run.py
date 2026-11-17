"""Isolated single-episode B-path supervisor; default is plan only."""
import argparse,getpass,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
from eval_config import configure
from local_otlp_process import LocalOTLPProcess
from process_tree import identity

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def terminate(proc):
 try:os.killpg(proc.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:proc.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try:os.killpg(proc.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  proc.wait(timeout=5)

def drain_registered_jvm(folder):
 path=folder/'java/java-process.json'
 if not path.exists():return {'state':'unknown_no_registered_jvm'}
 info=json.loads(path.read_text());pid=info['pid'];start=info.get('start_ticks')
 if start is None:return {'state':'unknown_missing_start_identity'}
 def alive():
  current=identity(pid);return current is not None and current[0]==start and current[1]!='Z'
 deadline=time.monotonic()+15
 while alive() and time.monotonic()<deadline:time.sleep(.1)
 forced=alive()
 if forced:
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  deadline=time.monotonic()+5
  while alive() and time.monotonic()<deadline:time.sleep(.1)
  if alive():
   try:os.kill(pid,signal.SIGKILL)
   except ProcessLookupError:pass
 return {'state':'terminal' if not alive() else 'termination_not_yet_observed','forced':forced,'boot_id':info.get('boot_id')}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--task-id',default='task_001');p.add_argument('--gate-suite',type=Path,default=ROOT/'runs/enterprise-v02-timeout1200-20261114');p.add_argument('--execute',action='store_true');a=p.parse_args()
 configure();os.environ.setdefault('TAU2_REPO',str(ROOT/'.deps/tau2-bench'));os.environ.setdefault('TAU2_DATA_DIR',str(Path(os.environ['TAU2_REPO'])/'data'))
 os.environ['JAVA_AGENT_COMPLETION_TIMEOUT']='1200';os.environ['JAVA_AGENT_MAIN_COMPLETION_TIMEOUT']='1500';os.environ['JAVA_AGENT_COMMAND']='bash '+str(ROOT/'enterprise-java/run.sh');os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP','True')
 if a.execute:
  gate=a.gate_suite/'P10-stage-review.json'
  if not gate.exists() or json.loads(gate.read_text()).get('status')!='COMPLETED':raise SystemExit('P10 fixed-response replay evidence review required before P11 business execution')
 if a.output.exists():raise SystemExit('Existing evidence directory; choose a new attempt')
 classes=list((ROOT/'enterprise-java/target/classes').rglob('*.class'))
 if not classes:raise SystemExit('Build enterprise-java first')
 a.output=a.output.resolve()
 # Reuse official dataset/version discovery, without executing the A-path adapter.
 subprocess.run([sys.executable,str(ROOT/'python/full_run.py'),'--output',str(a.output/'planning-source'),'--task-ids',a.task_id,'--trials','1','--concurrency','1','--seed','300','--episode-timeout','1800','--max-hours','1'],check=True,cwd=ROOT)
 m=json.loads((a.output/'planning-source/manifest.json').read_text())
 m.update(implementation='runtime-moa-main-local-skill',output=str(a.output),execution_entrypoint='python/enterprise_episode.py',transport_adapter='python/enterprise_java_agent.py',planning_source_manifest='planning-source/manifest.json')
 m['main_core_completion_timeout']=1500
 for f in sorted((ROOT/'enterprise-java/src').rglob('*.java')):m['java_source_sha256'][str(f.relative_to(ROOT))]=digest(f)
 for f in classes:m['artifact_sha256'][str(f.relative_to(ROOT))]=digest(f)
 for name in ['enterprise_episode.py','enterprise_java_agent.py','enterprise_run.py','process_tree.py','local_otlp_process.py','otlp_capture.py']:
  m['adapter_sha256'][name]=digest(ROOT/'python'/name)
 m['java_bridge_sha256']=digest(ROOT/'enterprise-java/src/eval/EnterpriseBankingBridge.java')
 m['enterprise_differences']={'entrypoint':'actual Runtime A2A SendMessage HTTP','main':'MOA auto-configured MAIN with planning/routing rails','delegation':'local bank-skill through LocalSkillDelegate','prompts':'default MOA MAIN prompt plus official bank policy; separate bank Skill prompt','sampling':{'temperature':0,'top_p':1},'routing_analysis_timeout_seconds':30,'runtime_task_acceptance':'not automatically equivalent to benchmark episode or safety-complete acceptance'}
 m['enterprise_differences'].update(observed_tool_data_scope='Core Skill session state; A-path cache is episode scoped',timeouts={'skill_core_seconds':1200,'main_core_seconds':1500,'episode_seconds':1800,'bridge_inactivity_seconds':m['event_timeout']},extra_observation='native OTel export plus boot/session/call event metadata; measure overhead separately')
 m['otel']={'enabled_on_execute':True,'exporter':'native Runtime OTLP HTTP/protobuf','destination':'local ephemeral loopback receiver','prompt_completion_redaction':True,'receiver_environment':os.getenv('TAU3_OTEL_PYTHON','/tmp/tau3-otel-collector-venv/bin/python'),'coverage':'must be measured; exporter enabled is not complete trace coverage'}
 m['otel']['receiver_requirements_sha256']=digest(ROOT/'config/otel-collector-requirements.txt')
 mp=a.output/'manifest.json';mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'implementation':m['implementation'],'episodes':len(m['episodes']),'execute':a.execute,'token_limit':None,'output':str(a.output)},ensure_ascii=False),flush=True)
 if not a.execute:raise SystemExit(0)
 if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
 if not os.environ['OPENAI_API_KEY']:raise SystemExit('Missing key')
 repo=Path(os.environ['TAU2_REPO']);commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
 if commit!=m['benchmark_commit']:raise SystemExit('Official benchmark commit mismatch')
 subprocess.run(['git','-C',str(repo),'diff','--quiet','HEAD','--','src','data'],check=True)
 episode=m['episodes'][0];folder=a.output/'episodes'/episode['key'];folder.mkdir(parents=True)
 with LocalOTLPProcess(folder/'java/otel',os.environ['OPENAI_API_KEY']) as receiver:
  with (folder/'process.log').open('w') as log:
   env={**os.environ,'JAVA_EVAL_OTEL_ENDPOINT':receiver.endpoint}
   proc=subprocess.Popen([sys.executable,str(ROOT/'python/enterprise_episode.py'),'--manifest',str(mp),'--index','0'],stdout=log,stderr=log,cwd=ROOT,start_new_session=True,env=env)
   (a.output/'process.json').write_text(json.dumps({'pid':proc.pid,'started_at':time.time(),'token_limit':None,'otel_endpoint':receiver.endpoint},indent=2))
   timed_out=False
   try:proc.wait(timeout=m['episode_timeout'])
   except subprocess.TimeoutExpired:timed_out=True;terminate(proc)
   finally:
    if proc.poll() is None:terminate(proc)
  (a.output/'jvm-drain.json').write_text(json.dumps(drain_registered_jvm(folder),indent=2)+'\n')
 status=folder/'status.json'
 if not status.exists():status.write_text(json.dumps({'status':'timeout' if timed_out else 'process_error','task_id':episode['task_id'],'domain':episode['domain'],'trial':0,'returncode':proc.returncode},indent=2))
 for script in ['analyze_v2.py','collect_enterprise_metrics.py']:subprocess.run([sys.executable,str(ROOT/'python'/script),str(a.output)],check=True,cwd=ROOT)
 print(status.read_text(),flush=True)
 otel_status=folder/'java/otel/capture/status.json'
 rejected=json.loads(otel_status.read_text()).get('secret_payloads_rejected',0) if otel_status.exists() else None
 if rejected:
  (a.output/'security-incident.json').write_text(json.dumps({'kind':'model_credential_detected_in_OTLP','payload_storage':'rejected','count':rejected,'action':'stop further B cases pending review; original official score retained'},indent=2)+'\n')
 raise SystemExit(0 if json.loads(status.read_text())['status']=='scored' and rejected==0 else 1)
