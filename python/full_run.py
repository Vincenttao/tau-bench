"""Resumable full-suite supervisor. Defaults to planning only, never spends tokens implicitly."""
import argparse,json,os,random,time,hashlib,re,signal,subprocess,sys
from pathlib import Path
from eval_config import configure
model, api_base = configure()
p=argparse.ArgumentParser()
p.add_argument('--output',required=True);p.add_argument('--trials',type=int,default=5);p.add_argument('--concurrency',type=int,default=3);p.add_argument('--max-steps',type=int,default=200);p.add_argument('--max-errors',type=int,default=10);p.add_argument('--seed',type=int,default=300);p.add_argument('--token-limit',type=int);p.add_argument('--reserve-per-active',type=int,default=250000);p.add_argument('--episode-timeout',type=int,default=3600);p.add_argument('--max-hours',type=float,default=72);p.add_argument('--execute',action='store_true');p.add_argument('--domains',nargs='+',default=['banking_knowledge']);p.add_argument('--task-ids',nargs='*');p.add_argument('--trial-seed-mode',choices=['fixed','varied'],default='fixed');p.add_argument('--implementation',choices=['native-skill-stdio','deepagent-todo-skill-mcp'],default='native-skill-stdio');a=p.parse_args()
if a.trials<1 or a.concurrency<1:raise ValueError('trials/concurrency must be positive')
root=Path(a.output).resolve();root.mkdir(parents=True,exist_ok=True)
repo=Path(os.environ['TAU2_REPO']).resolve()
rng=random.Random(a.seed);seeds=[a.seed if a.trial_seed_mode=='fixed' else rng.randint(0,1000000) for _ in range(a.trials)]
episodes=[]
for domain in a.domains:
 if domain not in ['banking_knowledge']:raise ValueError('Only standard official domains supported; expansion must be explicit separate implementation')
 tasks=[json.loads(f.read_text()) for f in sorted((repo/'data/tau2/domains'/domain/'tasks').glob('task_*.json'))]
 if a.task_ids:
  missing=set(a.task_ids)-{t['id'] for t in tasks}
  if missing:raise ValueError('Unknown task IDs: '+str(sorted(missing)))
  tasks=[t for t in tasks if t['id'] in a.task_ids]
 if not tasks:raise ValueError('No official tasks found; check TAU2_REPO')
 for trial in range(a.trials):
  for task in tasks:
   key=f'{domain}-t{trial}-'+hashlib.sha256(task['id'].encode()).hexdigest()[:16]
   episodes.append(dict(domain=domain,task_id=task['id'],trial=trial,seed=seeds[trial],key=key))
dataset_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((repo/'data/tau2/domains/banking_knowledge/tasks').glob('task_*.json'))}
adapter_hashes={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['episode.py','java_agent.py','full_run.py','analyze_v2.py','eval_config.py','deepagent_java_agent.py','benchmark_mcp.py','skill_assets.py']}
bridge_hash=hashlib.sha256((Path(__file__).resolve().parents[1]/'java/src/main/java/eval/Tau2Bridge.java').read_bytes()).hexdigest()
source_root=Path(__file__).resolve().parents[1]
if a.implementation == 'deepagent-todo-skill-mcp':
 os.environ['JAVA_AGENT_COMMAND']='bash '+str(source_root/'java/run-deepagent.sh')
def repo_evidence(path):
 try:
  commit=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
  dirty=bool(subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True))
  return {'commit':commit,'dirty':dirty}
 except subprocess.CalledProcessError:return {'commit':None,'dirty':None}
java_hashes={str(f.relative_to(source_root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((source_root/'java/src').rglob('*.java'))}
artifacts={}
cp=source_root/'java/classpath.txt'
if cp.exists():
 for name in cp.read_text().strip().split(os.pathsep):
  f=Path(name)
  if f.is_file():artifacts[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
for f in sorted((source_root/'java/target/classes').rglob('*.class')):
 artifacts[str(f.relative_to(source_root))]=hashlib.sha256(f.read_bytes()).hexdigest()
manifest=dict(core_completion_timeout=float(os.getenv('JAVA_AGENT_COMPLETION_TIMEOUT','600')),schema_version=2,skill_asset_sha256={str(f.relative_to(source_root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((source_root/'experiments/deepagent-todo-skill-mcp/skills').rglob('*')) if f.is_file()},implementation=a.implementation,api_base=api_base,api_protocol='chat_completions',trial_seed_mode=a.trial_seed_mode,java_source_sha256=java_hashes,artifact_sha256=artifacts,source_repositories={n:repo_evidence(source_root.parent/n) for n in ['agent-core-java','agent-runtime-java','agent-solution']},episode_timeout=a.episode_timeout,event_timeout=float(os.environ['JAVA_AGENT_EVENT_TIMEOUT']),concurrency=a.concurrency,max_hours=a.max_hours,token_limit=a.token_limit,reserve_per_active=a.reserve_per_active,adapter_sha256=adapter_hashes,java_bridge_sha256=bridge_hash,retrieval_config='bm25',judge='gpt-4.1-2025-04-14 via authorized gateway only',dataset_sha256=dataset_sha256,benchmark_commit='fc0055dc4e0a316c3f83133267fbd6faaa770992',model=model,trials=a.trials,seed=a.seed,max_steps=a.max_steps,max_errors=a.max_errors,output=str(root),episodes=episodes)
mp=root/'manifest.json'
if mp.exists():
 if json.loads(mp.read_text())!=manifest:raise ValueError('Existing manifest differs; use new output directory')
else:mp.write_text(json.dumps(manifest,indent=2))
print(json.dumps({'episodes':len(episodes),'unique_tasks':len(episodes)//a.trials,'expected_tokens_at_previous_mean':round(len(episodes)*1050476),'serial_hours_at_previous_mean':round(len(episodes)*368.690442717/3600,2),'parallel_ideal_hours':round(len(episodes)*368.690442717/3600/a.concurrency,2),'execute':a.execute}),flush=True)
if not a.execute:sys.exit(0)
# Omitted --token-limit disables the token guard; usage remains observable.
for var in ['OPENAI_API_KEY','OPENAI_API_BASE','OPENAI_BASE_URL','JAVA_AGENT_COMMAND']:
 if not os.getenv(var):raise ValueError('Missing '+var)
if subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()!=manifest['benchmark_commit']:raise ValueError('Wrong benchmark commit')
subprocess.run(['git','-C',str(repo),'diff','--quiet','HEAD','--','src','data'],check=True)
if not artifacts:raise ValueError('Build Java bridge and classpath.txt before executing')
ledger=root/'supervisor.jsonl'
def event(data):
 with ledger.open('a') as f:f.write(json.dumps(dict(time=time.time(),**data))+'\n')
def status_path(e):return root/'episodes'/e['key']/'status.json'
def used_tokens():
 total=0
 for f in root.glob('episodes/*/user-usage.jsonl'):
  for line in f.read_text().splitlines():
   try:total+=json.loads(line).get('total_tokens',0)
   except json.JSONDecodeError:pass
 for f in root.glob('episodes/*/java/*.stderr.log'):
  total+=sum(int(v) for v in re.findall(r'event=react_model_call_completed[^\n]*total_tokens=(\d+)',f.read_text(errors='replace')))
 return total
# Preserve interrupted attempts instead of silently rerunning and replacing their evidence.
for e in episodes:
 out=root/'episodes'/e['key']
 if (out/'process.log').exists() and not status_path(e).exists():
  status_path(e).write_text(json.dumps({'status':'interrupted_previous_run','task_id':e['task_id'],'domain':e['domain'],'trial':e['trial']}))
def terminate(proc):
 try:os.killpg(proc.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:proc.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try:os.killpg(proc.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  proc.wait(timeout=5)
pending=[e for e in episodes if not status_path(e).exists()];active={};start=time.monotonic();stopped=False
try:
 while pending or active:
  consumed=used_tokens()
  quota_errors=[]
  for ef in root.glob('episodes/*/exception.txt'):
   error=ef.read_text(errors='replace').lower()
   if any(marker in error for marker in ['insufficient_quota','quota_exceeded','insufficient credits','credit balance is too low','account balance is insufficient','余额不足','额度不足']):quota_errors.append(str(ef))
  if quota_errors:
   event({'event':'quota_stop','evidence':quota_errors,'observed_tokens':consumed});stopped=True
   for proc,(e,t,log) in list(active.items()):
    if proc.poll() is None:terminate(proc)
    if not status_path(e).exists():status_path(e).write_text(json.dumps({'status':'aborted_quota','task_id':e['task_id'],'domain':e['domain'],'trial':e['trial']}))
   (root/'quota-stop.json').write_text(json.dumps({'reason':'API quota/credit exhaustion detected; stopped for user to replace API key','evidence':quota_errors,'observed_tokens':consumed},indent=2))
   break
  recent=sorted(root.glob('episodes/*/status.json'),key=lambda f:f.stat().st_mtime)[-6:]
  systemic_pause=len(recent)==6 and all(json.loads(f.read_text()).get('status') in ['execution_error','process_error','timeout'] for f in recent)
  if systemic_pause and not active:
   event({'event':'systemic_execution_error_pause','observed_tokens':consumed});stopped=True;break
  token_stop=a.token_limit is not None and consumed>=a.token_limit
  wall_time_stop=time.monotonic()-start>a.max_hours*3600
  if token_stop or wall_time_stop:
   reason='token_limit' if token_stop else 'supervisor_wall_time'
   event({'event':reason+'_stop','observed_tokens':consumed});stopped=True
   for proc,(e,t,log) in list(active.items()):
    terminate(proc);status_path(e).write_text(json.dumps({'status':'aborted_'+reason,'task_id':e['task_id'],'domain':e['domain'],'trial':e['trial']}));log.close()
   break
  while pending and not systemic_pause and len(active)<a.concurrency and (a.token_limit is None or consumed+(len(active)+1)*a.reserve_per_active<=a.token_limit):
   e=pending.pop(0);out=root/'episodes'/e['key'];out.mkdir(parents=True,exist_ok=True);log=(out/'process.log').open('a')
   proc=subprocess.Popen([sys.executable,str(Path(__file__).with_name('episode.py')),'--manifest',str(mp),'--index',str(episodes.index(e))],stdout=log,stderr=log,start_new_session=True)
   active[proc]=(e,time.monotonic(),log);event({'event':'start','key':e['key']})
  for proc,(e,t,log) in list(active.items()):
   timed_out=time.monotonic()-t>a.episode_timeout
   if proc.poll() is not None or timed_out:
    if timed_out:terminate(proc)
    if not status_path(e).exists():status_path(e).write_text(json.dumps({'status':'timeout' if timed_out else 'process_error','task_id':e['task_id'],'domain':e['domain'],'trial':e['trial'],'returncode':proc.poll()}))
    log.close();active.pop(proc);event({'event':'finish','key':e['key'],'status':json.loads(status_path(e).read_text())})
  statuses=[json.loads(f.read_text()) for f in root.glob('episodes/*/status.json')]
  progress={'planned':len(episodes),'finished':len(statuses),'scored':sum(s['status']=='scored' for s in statuses),'successful':sum(s.get('reward')==1 for s in statuses),'infrastructure_failures':sum(s['status']!='scored' for s in statuses),'active':len(active),'pending':len(pending),'observed_tokens':consumed,'token_limit':a.token_limit,'systemic_error_pause':systemic_pause,'note':'Observed usage only; token guard disabled when token_limit is null. Supervisor and episode timeouts are separate limits.'}
  tmp=root/'progress.tmp';tmp.write_text(json.dumps(progress,indent=2));tmp.replace(root/'progress.json')
  if pending and not active and a.token_limit is not None and consumed+a.reserve_per_active>a.token_limit:
   event({'event':'reserve_limit_stop','observed_tokens':consumed});stopped=True;break
  if pending or active:time.sleep(2)
finally:
 for proc,(e,t,log) in active.items():
  if proc.poll() is None:terminate(proc)
  log.close()
print(json.dumps({'finished':not stopped,'observed_tokens':used_tokens()}),flush=True)
