"""Sequential independent episodes with append-only plan ledger; no token budget."""
import argparse,getpass,json,os,subprocess,sys,time
from pathlib import Path
from eval_config import configure
from study_contract import compare
from retry_resolution import approved_retry,resolved_terminal,failure_kind
from reviewed_timeout import retained_timeout
from reviewed_core_error import retained_core_error
ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'runs/enterprise-v02-20261114'

def event(row):
    row['recorded_at']=time.time()
    with (SUITE/'execution-ledger.jsonl').open('a') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['P05','P06','P07','P08'],required=True)
    parser.add_argument('--suite',type=Path,default=SUITE)
    parser.add_argument('--prerequisite-suite',type=Path,help='P06 may reference an earlier P05; recorded separately from current scores')
    parser.add_argument('--resume',action='store_true',help='Skip verified terminal attempts only; never rerun failed or incomplete attempts')
    parser.add_argument('--continue-reviewed-timeouts',action='store_true',help='P07 only: retain reviewed timeouts and continue unstarted cases; no P08 gate resolution')
    parser.add_argument('--continue-reviewed-core-errors',action='store_true',help='P07 only: retain reviewed Core lookup errors; no retry or P08 release')
    args=parser.parse_args();SUITE=args.suite.resolve()
    if (args.continue_reviewed_timeouts or args.continue_reviewed_core_errors) and (args.stage!='P07' or not args.resume):raise SystemExit('Failure retention requires P07 --resume')
    if not SUITE.is_dir():raise SystemExit('Prepare frozen suite directory first')
    scope_file=SUITE/'single-round-scope.json'
    if scope_file.exists():
        scope=json.loads(scope_file.read_text())
        if scope.get('mode')!='single_round' or scope.get('rounds_per_case')!=1 or args.stage!='P07':
            raise SystemExit('Current user scope allows P07 single round only; repeated stages disabled')
    prerequisite_suite=(args.prerequisite_suite or SUITE).resolve()
    if args.prerequisite_suite and args.stage!='P06':raise SystemExit('External prerequisites supported for P06 only')
    configure()
    os.environ.setdefault('TAU2_REPO',str(ROOT/'.deps/tau2-bench'))
    os.environ.setdefault('TAU2_DATA_DIR',str(Path(os.environ['TAU2_REPO'])/'data'))
    os.environ.setdefault('JAVA_AGENT_COMMAND','bash '+str(ROOT/'java/run.sh'))
    os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP','True')
    if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
    if args.stage=='P08':
        review=SUITE/'P07-stage-review.json'
        if not review.exists() or json.loads(review.read_text()).get('status')!='COMPLETED':
            raise SystemExit('P07 complete evidence review required before P08')
        plan=json.loads((SUITE/'P08-schedule.json').read_text())
        schedule=[(e['case_id'],e['repetition_index']) for e in plan['episodes']]
        if len(schedule)!=485 or len(set(schedule))!=485:raise SystemExit('Invalid P08 schedule')
        for case,index in schedule:
            if index!=0:continue
            if resolved_terminal(SUITE/f'P07-{case}-r00-a00',case,json.loads((SUITE/'P07-execution-anchor.json').read_text())) is None:raise SystemExit('P07 unresolved infrastructure result: '+case)
    elif args.stage=='P07':
        for case in ['task_001','task_041']:
            for index in range(3):
                statuses=list((SUITE/f'P06-{case}-r{index:02d}-a00').glob('episodes/*/status.json'))
                if len(statuses)!=1 or json.loads(statuses[0].read_text())['status']!='scored':
                    raise SystemExit('P06 prerequisite not scored: '+case+str(index))
        plan=json.loads((SUITE/'P07-schedule.json').read_text())
        schedule=[(e['case_id'],0) for e in plan['episodes']]
        if len(schedule)!=97 or len(set(schedule))!=97:raise SystemExit('Invalid P07 schedule')
    elif args.stage=='P06':
        for prerequisite in ['task_002','task_041','task_080']:
            statuses=list((prerequisite_suite/('P05-'+prerequisite+'-r00-a00')).glob('episodes/*/status.json'))
            if len(statuses)!=1 or json.loads(statuses[0].read_text())['status']!='scored':
                raise SystemExit('P05 prerequisite not scored: '+prerequisite)
        rules=json.loads((ROOT/'config/repetition-study-v1.json').read_text())['P06']
        schedule=[(case,index) for case in rules['cases'] for index in range(rules['independent_runs_per_case'])]
    else:schedule=[(case,0) for case in ['task_002','task_041','task_080']]
    for case,repetition in schedule:
        out=SUITE/(args.stage+'-'+case+f'-r{repetition:02d}-a00')
        primary=out;attempt_index=0
        if out.exists():
            if not args.resume:raise SystemExit('Existing attempt: inspect ledger and evidence before continuing '+str(out))
            anchor=SUITE/(args.stage+'-execution-anchor.json')
            if not anchor.exists():raise SystemExit('Missing execution anchor')
            resolved=resolved_terminal(primary,case,json.loads(anchor.read_text()))
            if resolved is not None:
                print('Verified terminal resolution; skipping',resolved,'primary retained:',primary,flush=True);continue
            if args.continue_reviewed_timeouts and retained_timeout(primary):
                event({'suite_id':SUITE.name,'plan_item':args.stage,'case_id':case,'repetition_index':repetition,'attempt_index':0,'output_dir':str(primary),'status':'REVIEWED_TIMEOUT_RETAINED','technical_gate_resolved':False})
                print('Retaining reviewed timeout; next unstarted case only:',primary,flush=True);continue
            if args.continue_reviewed_core_errors and retained_core_error(primary):
                event({'suite_id':SUITE.name,'plan_item':args.stage,'case_id':case,'repetition_index':repetition,'attempt_index':0,'output_dir':str(primary),'status':'REVIEWED_CORE_ERROR_RETAINED','technical_gate_resolved':False})
                print('Retaining reviewed Core error; next unstarted case only:',primary,flush=True);continue
            retry=approved_retry(primary)
            if retry is None:raise SystemExit('Cannot resume unresolved attempt: '+str(primary))
            if retry.exists():raise SystemExit('Reviewed retry already exists but is unresolved; no further automatic retry: '+str(retry))
            out=retry;attempt_index=1
        row={'suite_id':SUITE.name,'plan_item':args.stage,'case_id':case,'repetition_index':repetition,'attempt_index':attempt_index,'seed':300,'output_dir':str(out),'executor':'Codex','reviewer':None,'prerequisite_suite':str(prerequisite_suite),'parent_attempt':str(primary) if attempt_index else None,'retry_reason':failure_kind(primary) if attempt_index else None}
        event({**row,'status':'RUNNING'})
        command=[sys.executable,str(ROOT/'python/full_run.py'),'--output',str(out),'--task-ids',case,'--trials','1','--concurrency','1','--seed','300','--episode-timeout','1800','--max-hours','1','--execute']
        if args.stage in ['P06','P07','P08']:
            subprocess.run(command[:-1],check=True,cwd=ROOT)
            proposed=json.loads((out/'manifest.json').read_text())
            anchor=SUITE/(args.stage+'-execution-anchor.json')
            if anchor.exists():
                verdict=compare([json.loads(anchor.read_text()),proposed])
                if not verdict['comparable']:
                    event({**row,'status':'BLOCKED','contract_mismatch':verdict})
                    raise SystemExit('Execution configuration drift; new experiment required')
            else:anchor.write_text(json.dumps(proposed,indent=2))
        code=subprocess.call(command,cwd=ROOT)
        for script in ['analyze_v2.py','collect_metrics_v02.py']:
            subprocess.run([sys.executable,str(ROOT/'python'/script),str(out)],check=True,cwd=ROOT)
        statuses=[json.loads(p.read_text()) for p in out.glob('episodes/*/status.json')]
        healthy=len(statuses)==1 and statuses[0]['status']=='scored'
        if not healthy and args.stage in ['P07','P08'] and case=='task_102' and len(statuses)==1 and statuses[0]['status']=='evaluation_error':
            exceptions=list(out.glob('episodes/*/exception.txt'))
            healthy=bool(exceptions) and all('404' in p.read_text() and 'NotFoundError' in p.read_text() for p in exceptions)
        event({**row,'status':('UNSCORED' if statuses and statuses[0]['status']=='evaluation_error' else 'COMPLETED') if healthy else 'FAILED','process_exit':code,'episode_statuses':statuses})
        if not healthy:raise SystemExit('Infrastructure error: stage stopped, inspect evidence')
