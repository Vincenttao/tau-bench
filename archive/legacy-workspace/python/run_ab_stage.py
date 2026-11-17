"""P12 fresh A/B pairs; default plans only, real execution requires verified P11."""
import argparse,getpass,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from retry_resolution import healthy
from study_contract import compare

ROOT=Path(__file__).resolve().parents[1]
CASES=['task_002','task_041','task_080']
SHARED=['model','api_base','api_protocol','retrieval_config','benchmark_commit','dataset_sha256','max_steps','max_errors','episode_timeout','event_timeout','core_completion_timeout','concurrency','trial_seed_mode']
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def pair_check(a,b):
 changed=[key for key in SHARED if a.get(key)!=b.get(key)]
 if [(e['task_id'],e['seed']) for e in a['episodes']]!=[(e['task_id'],e['seed']) for e in b['episodes']]:changed.append('episode_case_and_seed')
 if a.get('implementation')!='native-skill-stdio' or b.get('implementation')!='runtime-moa-main-local-skill':changed.append('implementation_identity')
 if changed:raise ValueError('A/B shared conditions differ: '+','.join(changed))
 return {'matched_shared_fields':SHARED+['episode_case_and_seed'],'differences':b['enterprise_differences'],'attribution':'Combined assembly comparison; prompts, rails, routing, context ownership and observation overhead differ. Not isolated Runtime causal effect.'}

def prerequisite(suite):
 review=json.loads((suite/'P11-stage-review.json').read_text())
 if review.get('status')!='COMPLETED':raise ValueError('P11 review not completed')
 output=Path(review['output_dir'])
 if not output.is_absolute():output=ROOT/output
 if not healthy(output,'task_001'):raise ValueError('P11 task_001 lacks healthy scored business evidence')
 manifest=json.loads((output/'manifest.json').read_text())
 metrics=json.loads((output/'metrics-v02.json').read_text())
 if manifest['implementation']!='runtime-moa-main-local-skill' or not any(e.get('runtime_task_ids') for e in metrics['episodes']):raise ValueError('P11 actual Runtime Task evidence required')
 if (output/'security-incident.json').exists():raise ValueError('P11 security incident requires review; no automatic P12 release')
 return {'review':str(suite/'P11-stage-review.json'),'output_dir':str(output),'review_sha256':hashlib.sha256((suite/'P11-stage-review.json').read_bytes()).hexdigest()}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--suite',type=Path,required=True);parser.add_argument('--execute',action='store_true');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
 suite=args.suite.resolve()
 if not suite.is_dir():raise SystemExit('Prepare suite first')
 plan={'stage':'P12','cases':CASES,'seed':300,'token_limit':None,'order':'A then B for each case, serial; order effect not excluded','A':'Fresh1200-second NativeSkillAgent attempts; never substitute historical600-second P05','B':'Fresh Runtime/MOA MAIN/local Skill attempts, Skill1200/Main1500 seconds','shared':'same official task, independent official initial state, model, gateway, seed, step/error limits and1800-second episode deadline','scope':'Three controlled assembly pairs; no full97-case B quality or stability claim','episodes':[{'case_id':case,'variant':variant,'output_dir':str(suite/f'P12-{variant}-{case}-r00-a00')} for case in CASES for variant in ['A','B']]}
 target=suite/'P12-schedule.json'
 if target.exists() and json.loads(target.read_text())!=plan:raise SystemExit('P12 schedule drift')
 if not target.exists():write(target,plan)
 if not args.execute:print(json.dumps({'planned':6,'execute':False,'token_limit':None}));raise SystemExit(0)
 try:gate=prerequisite(suite)
 except (ValueError,KeyError,FileNotFoundError) as error:raise SystemExit('P11 business review required: '+str(error))
 os.environ['JAVA_AGENT_COMPLETION_TIMEOUT']='1200';os.environ['JAVA_AGENT_EVENT_TIMEOUT']='300'
 if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
 if not os.environ['OPENAI_API_KEY']:raise SystemExit('Missing key')
 anchors={};results=[]
 for entry in plan['episodes']:
  folder=Path(entry['output_dir']);case=entry['case_id'];variant=entry['variant']
  def event(state):
   with (suite/'execution-ledger.jsonl').open('a') as stream:stream.write(json.dumps({**entry,'plan_item':'P12','attempt_index':0,'status':state,'recorded_at':time.time()})+'\n');stream.flush();os.fsync(stream.fileno())
  if folder.exists():
   if not args.resume or not healthy(folder,case):raise SystemExit('Existing incomplete/unreviewed attempt; no automatic retry: '+str(folder))
  else:
   event('RUNNING')
   if variant=='A':
    command=[sys.executable,str(ROOT/'python/full_run.py'),'--output',str(folder),'--task-ids',case,'--trials','1','--concurrency','1','--seed','300','--episode-timeout','1800','--max-hours','1','--execute']
    env={**os.environ,'JAVA_AGENT_COMMAND':'bash '+str(ROOT/'java/run.sh')}
   else:
    command=[sys.executable,str(ROOT/'python/enterprise_run.py'),'--output',str(folder),'--task-id',case,'--gate-suite',str(suite),'--execute'];env=os.environ.copy()
   code=subprocess.call(command,cwd=ROOT,env=env)
   if variant=='A':
    for script in ['analyze_v2.py','collect_metrics_v02.py']:subprocess.run([sys.executable,str(ROOT/'python'/script),str(folder)],check=True,cwd=ROOT)
   if code!=0 or not healthy(folder,case) or (folder/'security-incident.json').exists():event('FAILED');raise SystemExit('P12 execution failed; preserve original evidence and inspect')
   event('COMPLETED')
  manifest=json.loads((folder/'manifest.json').read_text())
  if variant in anchors and not compare([anchors[variant],manifest])['comparable']:raise SystemExit('Within-variant execution contract drift')
  anchors.setdefault(variant,manifest)
  metrics=json.loads((folder/'metrics-v02.json').read_text());status=json.loads(next(folder.glob('episodes/*/status.json')).read_text())
  item={**entry,'official_reward':status['reward'],'duration':status['duration'],'observed_facts':metrics['facts'],'enterprise_acceptance':None}
  if variant=='B':item['pair_conditions']=pair_check(json.loads((Path(plan['episodes'][len(results)-1]['output_dir'])/'manifest.json').read_text()),manifest)
  results.append(item);write(suite/'P12-analysis.json',{'scope':plan['scope'],'planned':6,'results':results,'prerequisite':gate,'enterprise_acceptance':None})
 write(suite/'P12-stage-review.json',{'stage':'P12','status':'COMPLETED','recorded_at':time.time(),'scored':6,'reviewer':'Codex technical evidence review','independent_enterprise_acceptance':None})
