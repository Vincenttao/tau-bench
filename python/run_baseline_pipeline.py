"""P06 -> reviewed P07 -> reviewed P08. Secret stays in process memory."""
import argparse,getpass,json,os,subprocess,sys,time
from pathlib import Path
from study_contract import compare
from report_repetitions import report as repetition_report
from report_full_suite import report as full_report

ROOT=Path(__file__).resolve().parents[1]
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suite',type=Path,required=True);p.add_argument('--prerequisite-suite',type=Path,required=True);a=p.parse_args()
 suite=a.suite.resolve();prior=a.prerequisite_suite.resolve()
 if (suite/'single-round-scope.json').exists():raise SystemExit('Single-round scope active: use P07 controller; historical P06/P08 pipeline disabled')
 freeze=json.loads((suite/'freeze.json').read_text())
 if freeze['core_completion_timeout_seconds']!=1200 or freeze['token_limit'] is not None:raise SystemExit('Unexpected frozen experiment conditions')
 os.environ['JAVA_AGENT_COMPLETION_TIMEOUT']='1200'
 if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
 if not os.environ['OPENAI_API_KEY']:raise SystemExit('Missing API key')
 for stage in ['P06','P07','P08']:
  command=[sys.executable,str(ROOT/'python/run_plan_stage.py'),'--stage',stage,'--suite',str(suite),'--resume']
  if stage=='P06':command+=['--prerequisite-suite',str(prior)]
  subprocess.run(command,check=True,cwd=ROOT)
  if stage=='P06':
   analysis=repetition_report(suite)
   manifests=[json.loads(p.read_text()) for p in sorted(suite.glob('P06-*/manifest.json'))]
   frozen=json.loads((suite/'freeze-plan/manifest.json').read_text())
   contract=compare([frozen,*manifests])
   if len(manifests)!=6 or not contract['comparable'] or any(x['scored']!=3 for x in analysis['cases']):raise SystemExit('P06 technical gate failed')
   write(suite/'P06-stage-review.json',{'stage':'P06','status':'COMPLETED','recorded_at':time.time(),'cases':analysis['cases'],'execution_contracts':contract,'P07_release':'six scored attempts and frozen contract verified; official failures retained','reviewer':'Codex technical evidence review','independent_human_enterprise_acceptance':None})
  elif stage=='P07':
   report=full_report(suite)
   allowed=all(x['technical_gate_resolved'] for x in report['rows'])
   if report['planned']!=97 or not allowed:raise SystemExit('P07 evidence review incomplete')
   write(suite/'P07-stage-review.json',{'stage':'P07','status':'COMPLETED','recorded_at':time.time(),'planned':97,'primary_status_counts':report['status_counts'],'reviewed_retry_attempts':report['reviewed_retry_attempt_count'],'P08_release':'all97 planned cases technically resolved; original errors/user interruptions retained; reviewed additional attempts separate; unavailable judge unscored; no primary score substitution','reviewer':'Codex technical evidence review','independent_human_enterprise_acceptance':None})
  write(suite/'pipeline-progress.json',{'last_completed_stage':stage,'recorded_at':time.time(),'goal_complete':False,'remaining':'P09–P16 and analysis; P08 also remains until its terminal record'})
