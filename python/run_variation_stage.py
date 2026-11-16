"""P09: frozen cases/seeds, separate from fixed-condition repetitions."""
import argparse,getpass,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from eval_config import configure
from study_contract import compare
from retry_resolution import resolved_terminal

ROOT=Path(__file__).resolve().parents[1]
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def prerequisite(suite):
 plan=json.loads((suite/'P08-schedule.json').read_text())
 if len(plan['episodes'])!=485 or len({(e['case_id'],e['repetition_index']) for e in plan['episodes']})!=485:raise ValueError('Invalid P08 denominator')
 anchor=json.loads((suite/'P08-execution-anchor.json').read_text())
 for entry in plan['episodes']:
  folder=ROOT/entry['output_dir'];files=list(folder.glob('episodes/*/status.json'))
  if len(files)!=1:raise ValueError('P08 not terminal: '+entry['output_dir'])
  resolved=resolved_terminal(folder,entry['case_id'],anchor)
  if resolved is None:raise ValueError('P08 unresolved execution error: '+entry['output_dir'])
  m=json.loads((resolved/'manifest.json').read_text())
  if m['episodes'][0]['task_id']!=entry['case_id'] or not compare([anchor,m])['comparable']:raise ValueError('P08 evidence identity/contract mismatch')
 return {'planned':485,'terminal':485,'review':'Codex technical evidence review; no enterprise acceptance inference'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suite',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();suite=a.suite.resolve()
 if not suite.is_dir():raise SystemExit('Prepare frozen suite first')
 if a.execute:
  try:review=prerequisite(suite)
  except (ValueError,FileNotFoundError) as error:raise SystemExit('P08 complete review required before P09: '+str(error))
  write(suite/'P08-stage-review.json',{'stage':'P08','status':'COMPLETED','recorded_at':time.time(),**review})
 rules=json.loads((ROOT/'config/repetition-study-v1.json').read_text())['P09']
 entries=[{'case_id':case,'seed':seed,'repetition_index':index,'directory':str(suite/f'P09-{case}-seed{seed}-a00')} for case in rules['cases'] for index,seed in enumerate(rules['seeds'])]
 plan={'stage':'P09','episodes':entries,'token_limit':None,'concurrency':1,'scope':'Varied simulation seeds, separate from fixed-seed repeatability; record actual user input hashes; no exclusive causality claim for seed changes'}
 target=suite/'P09-schedule.json'
 if target.exists() and json.loads(target.read_text())!=plan:raise SystemExit('P09 schedule drift')
 write(target,plan)
 if not a.execute:print(json.dumps({'planned':len(entries),'execute':False},ensure_ascii=False));raise SystemExit(0)
 configure();os.environ.setdefault('TAU2_REPO',str(ROOT/'.deps/tau2-bench'));os.environ.setdefault('TAU2_DATA_DIR',str(Path(os.environ['TAU2_REPO'])/'data'))
 os.environ.setdefault('JAVA_AGENT_COMMAND','bash '+str(ROOT/'java/run.sh'));os.environ['JAVA_AGENT_COMPLETION_TIMEOUT']='1200';os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP','True')
 if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
 results=[];anchor=None
 for entry in entries:
  out=Path(entry['directory'])
  if out.exists():raise SystemExit('Existing attempt requires evidence review: '+str(out))
  row={'suite_id':suite.name,'plan_item':'P09','case_id':entry['case_id'],'seed':entry['seed'],'repetition_index':entry['repetition_index'],'attempt_index':0,'output_dir':str(out)}
  def event(status):
   with (suite/'execution-ledger.jsonl').open('a') as f:f.write(json.dumps({**row,'status':status,'recorded_at':time.time()},ensure_ascii=False)+'\n')
  event('RUNNING')
  command=[sys.executable,str(ROOT/'python/full_run.py'),'--output',str(out),'--task-ids',entry['case_id'],'--trials','1','--concurrency','1','--seed',str(entry['seed']),'--episode-timeout','1800','--max-hours','1']
  subprocess.run(command,check=True,cwd=ROOT);m=json.loads((out/'manifest.json').read_text())
  if anchor is None:anchor=m;write(suite/'P09-execution-anchor.json',m)
  if set(compare([anchor,m])['changed_fields'])-{'episode_seeds'}:raise SystemExit('Unexpected P09 execution drift')
  subprocess.run(command+['--execute'],check=True,cwd=ROOT)
  for script in ['analyze_v2.py','collect_metrics_v02.py']:subprocess.run([sys.executable,str(ROOT/'python'/script),str(out)],check=True,cwd=ROOT)
  status=json.loads(next(out.glob('episodes/*/status.json')).read_text())
  if status['status']!='scored':event('FAILED');raise SystemExit('P09 infrastructure error; original attempt retained')
  simulation=json.loads(next(out.glob('episodes/*/result.json')).read_text())['simulations'][0]
  user=[x.get('content') for x in simulation['messages'] if x.get('role')=='user']
  facts=json.loads((out/'metrics-v02.json').read_text())['facts']
  results.append({**entry,'official_reward':status['reward'],'duration':status['duration'],'observed_tokens':facts['observed_token_sum'],'user_inputs_sha256':hashlib.sha256(json.dumps(user,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
  event('COMPLETED');write(suite/'P09-analysis.json',{'scope':plan['scope'],'planned':len(entries),'results':results,'enterprise_acceptance':None})
 write(suite/'P09-stage-review.json',{'stage':'P09','status':'COMPLETED','recorded_at':time.time(),'scored':len(results),'planned':len(entries),'reviewer':'Codex technical evidence review','enterprise_acceptance':None})
