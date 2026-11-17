"""P10: capture both preselected P06 cases, then replay each exactly twice."""
import argparse,getpass,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from eval_config import configure,MODEL,GATEWAY
from fixed_response_gateway import Transcript,LocalGateway
from process_tree import terminate_tree
from study_contract import compare

ROOT=Path(__file__).resolve().parents[1]
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def phase(root,gateway,store,key,task_id,suite):
 root.mkdir()
 mode='P10_CAPTURE' if store.mode=='capture' else 'P10_REPLAY'
 row={'suite_id':suite.name,'plan_item':mode,'case_id':task_id,'repetition_index':0 if store.mode=='capture' else int(root.name.removeprefix('replay-')),'attempt_index':0,'seed':300,'output_dir':str(root),'token_accounting':'actual_observed' if store.mode=='capture' else 'historical_response_usage_only'}
 ledger=suite/('execution-ledger.jsonl' if store.mode=='capture' else 'fixed-response-replay-ledger.jsonl')
 def event(status,**extra):
  with ledger.open('a') as stream:stream.write(json.dumps({**row,'status':status,'recorded_at':time.time(),**extra},ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
 write(root/'phase-context.json',row);event('RUNNING')
 env={**os.environ,'OPENAI_API_KEY':key,'OPENAI_API_BASE':gateway.base_url,'OPENAI_BASE_URL':gateway.base_url,'OPENAI_MODEL':MODEL,
      'JAVA_AGENT_COMPLETION_TIMEOUT':'1200','JAVA_AGENT_COMMAND':'bash '+str(ROOT/'java/run.sh'),'TAU2_REPO':str(ROOT/'.deps/tau2-bench'),
      'TAU2_DATA_DIR':str(ROOT/'.deps/tau2-bench/data'),'LITELLM_LOCAL_MODEL_COST_MAP':'True'}
 command=[sys.executable,str(ROOT/'python/full_run.py'),'--output',str(root),'--task-ids',task_id,'--trials','1','--concurrency','1','--seed','300','--episode-timeout','1800','--max-hours','1','--execute']
 aborted=None
 with (root/'controller.log').open('w') as log:
  proc=subprocess.Popen(command,stdout=log,stderr=log,env=env,cwd=ROOT,start_new_session=True)
  write(root/'controller-process.json',{'pid':proc.pid,'started_at':time.time(),'mode':store.mode,'model_base':gateway.base_url})
  deadline=time.monotonic()+1840
  try:
   while proc.poll() is None:
    if store.failed:aborted='strict_transcript_failure';terminate_tree(proc);break
    if time.monotonic()>deadline:aborted='supervisor_timeout';terminate_tree(proc);break
    time.sleep(.2)
  finally:
   if proc.poll() is None:terminate_tree(proc)
 manifests=root/'manifest.json';statuses=list(root.glob('episodes/*/status.json'))
 status=json.loads(statuses[0].read_text()) if len(statuses)==1 else None
 write(root/'transport-verdict.json',{**store.verdict(),'process_exit':proc.returncode,'aborted':aborted,'official_status':status})
 if status is None and manifests.exists():
  m=json.loads(manifests.read_text());folder=root/'episodes'/m['episodes'][0]['key'];folder.mkdir(parents=True,exist_ok=True)
  status={'status':'aborted_'+aborted if aborted else 'process_error','task_id':task_id,'domain':'banking_knowledge','trial':0,'reward':None}
  write(folder/'status.json',status)
 state=None;sequence=None
 if status and status['status']=='scored':
  with (root/'state-replay.log').open('w') as log:
   subprocess.run([sys.executable,str(ROOT/'python/replay_final_state.py'),str(root),'--output',str(root/'state-hashes.json')],stdout=log,stderr=log,check=True,env=env,cwd=ROOT)
  state=json.loads((root/'state-hashes.json').read_text())
  simulation=json.loads(next(root.glob('episodes/*/result.json')).read_text())['simulations'][0]
  sequence=[{'actor':message['role'],'name':call['name'],'arguments':call['arguments']} for message in simulation['messages'] for call in message.get('tool_calls') or []]
  write(root/'official-tool-sequence.json',sequence)
 historical=json.loads((root/'progress.json').read_text()).get('observed_tokens') if (root/'progress.json').exists() else None
 event('COMPLETED' if status and status['status']=='scored' and not store.failed else 'FAILED',official_status=status,actual_model_token_consumption=0 if store.mode=='replay' else None,historical_replayed_usage_tokens=historical if store.mode=='replay' else None)
 return {'status':status,'state':state,'sequence':sequence,'manifest':json.loads(manifests.read_text()) if manifests.exists() else None,'transport':store.verdict()}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suite',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 suite=a.suite.resolve();output=a.output.resolve()
 if a.execute:
  review=suite/'P09-stage-review.json'
  if not review.exists() or json.loads(review.read_text()).get('status')!='COMPLETED':raise SystemExit('P09 complete review required before P10')
 if output.exists():raise SystemExit('Use a fresh P10 evidence directory')
 output.mkdir(parents=True)
 cases=json.loads((ROOT/'config/repetition-study-v1.json').read_text())['P06']['cases']
 plan={'stage':'P10','task_ids':cases,'capture_episodes':len(cases),'independent_replays_per_case':2,'seed':300,'token_limit':None,
       'model':MODEL,'capture_upstream':GATEWAY,'replay_upstream':None,'matching':'exact JSON values; object key order ignored, array order and all message/tool arguments retained',
       'normalization':'Only generated official tool call IDs excluded from final official-tool sequence comparison; full model HTTP request bodies have no ignored fields',
       'usage':'Capture usage is actual observed model usage; replay usage is historical and not new Token consumption',
       'core_checkpoint_state_equality':None,'collection_gap':'Core internal checkpoint snapshots are not exposed by the frozen A bridge; cannot collect full internal-state equality',
       'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__),ROOT/'python/fixed_response_gateway.py',ROOT/'python/process_tree.py',ROOT/'python/replay_final_state.py',ROOT/'config/repetition-study-v1.json']}}
 write(output/'plan.json',plan)
 if not a.execute:print(json.dumps({'execute':False,'output':str(output),'capture_episodes':len(cases),'replays':len(cases)*2},ensure_ascii=False));raise SystemExit(0)
 configure()
 if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
 key=os.environ['OPENAI_API_KEY']
 if not key:raise SystemExit('Missing API key')
 replays=[]
 for task_id in cases:
  case_root=output/task_id;case_root.mkdir();transcript=case_root/'transcript';store=Transcript(transcript,'capture',key)
  with LocalGateway(store) as gateway:captured=phase(case_root/'capture',gateway,store,key,task_id,suite)
  if not captured['status'] or captured['status']['status']!='scored' or store.failed:
   write(output/'stage-status.json',{'status':'CAPTURE_FAILED','case_id':task_id,'transport':store.verdict(),'official_status':captured['status']});raise SystemExit('P10 capture incomplete; raw evidence retained')
  store.seal()
  subprocess.run([sys.executable,str(ROOT/'python/collect_metrics_v02.py'),str(case_root/'capture')],check=True,cwd=ROOT)
  for index in range(2):
   local_key='local-replay-only';replay=Transcript(transcript,'replay',local_key)
   with LocalGateway(replay) as gateway:result=phase(case_root/f'replay-{index:02d}',gateway,replay,local_key,task_id,suite)
   comparison=compare([captured['manifest'],result['manifest']]) if result['manifest'] else {'changed_fields':['manifest_missing']}
   same_contract=not(set(comparison['changed_fields'])-{'api_base'})
   same_state=bool(result['state']) and bool(captured['state']) and all(result['state'][k]==captured['state'][k] for k in ['final_agent_db_hash','final_user_db_hash'])
   same_sequence=result['sequence'] is not None and result['sequence']==captured['sequence']
   passed=bool(result['status']) and result['status']['status']=='scored' and replay.verdict()['strict_match_complete'] and same_contract and same_state and same_sequence and result['status']['reward']==captured['status']['reward']
   replays.append({'case_id':task_id,'capture_official_status':captured['status'],'repetition_index':index,'passed':passed,'transport':replay.verdict(),'execution_contract_comparable_except_local_port':same_contract,'final_official_state_hashes_equal':same_state,'official_tool_sequence_equal':same_sequence,'official_status':result['status'],'new_model_token_consumption':0})
   write(output/'replay-analysis.json',{'capture_observed_tokens_files':[str((output/c/'capture/metrics-v02.json').relative_to(output)) for c in cases],'replays':replays,'core_checkpoint_state_equality':None,'collection_gap':plan['collection_gap'],'scope':'Fixed-response external behavior and reconstructed official business state; not production determinism or enterprise acceptance'})
 passed=len(replays)==len(cases)*2 and all(r['passed'] for r in replays)
 review={'stage':'P10','status':'COMPLETED' if passed else 'FAILED','recorded_at':time.time(),'replays':replays,'evidence_directory':str(output),'reviewer':'Codex technical evidence review','core_checkpoint_state_equality':None,'collection_gap':plan['collection_gap'],'enterprise_acceptance':None}
 write(output/'stage-status.json',review)
 if passed:write(suite/'P10-stage-review.json',review)
 raise SystemExit(0 if passed else 1)
