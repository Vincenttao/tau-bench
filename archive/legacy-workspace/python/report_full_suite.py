"""P07 full planned denominator report, including unstarted and unknown episodes."""
import argparse,collections,json
from datetime import datetime,timezone
from pathlib import Path
from retry_resolution import approved_retry,resolved_terminal,sha,review_file,user_interrupted
ROOT=Path(__file__).resolve().parents[1];SUITE=ROOT/'runs/enterprise-v02-20261114'

def report(suite=SUITE):
 global SUITE
 SUITE=Path(suite).resolve()
 plan=json.loads((SUITE/'P07-schedule.json').read_text());rows=[];retry_rows=[]
 anchor_file=SUITE/'P07-execution-anchor.json';anchor=json.loads(anchor_file.read_text()) if anchor_file.exists() else None
 for entry in plan['episodes']:
  folder=ROOT/entry['output_dir'];status_files=list(folder.glob('episodes/*/status.json'))
  if len(status_files)>1:raise ValueError('Multiple statuses for single planned attempt')
  status=json.loads(status_files[0].read_text()) if status_files else None
  progress=json.loads((folder/'progress.json').read_text()) if (folder/'progress.json').exists() else None
  metrics=json.loads((folder/'metrics-v02.json').read_text()) if (folder/'metrics-v02.json').exists() else None
  state=status['status'] if status else 'RUNNING_OR_UNKNOWN' if (folder/'manifest.json').exists() else 'NOT_STARTED'
  if user_interrupted(folder):state='USER_INTERRUPTED'
  stop_file=SUITE/'user-stop-for-analysis.json'
  if stop_file.exists() and status is None:
   stop=json.loads(stop_file.read_text())
   if (stop.get('status')=='STOPPED_BY_USER_FOR_ANALYSIS' and stop.get('interrupted_attempt')==folder.name
       and stop.get('remaining_live_pids')==[] and stop.get('captured_pids')):state='USER_INTERRUPTED'
  resolution=resolved_terminal(folder,entry['case_id'],anchor) if anchor else None
  retry=approved_retry(folder)
  if retry is not None and retry.exists():
   retry_statuses=list(retry.glob('episodes/*/status.json'));rs=json.loads(retry_statuses[0].read_text()) if len(retry_statuses)==1 else None
   rm=json.loads((retry/'metrics-v02.json').read_text()) if (retry/'metrics-v02.json').exists() else None
   rp=json.loads((retry/'progress.json').read_text()) if (retry/'progress.json').exists() else None
   retry_rows.append({'case_id':entry['case_id'],'output_dir':str(retry),'primary_attempt':str(folder),'status':rs['status'] if rs else 'RUNNING_OR_UNKNOWN','official_reward':rs.get('reward') if rs else None,'observed_tokens':rm['facts']['observed_token_sum'] if rm else rp.get('observed_tokens') if rp else None,'score_use':'secondary only; does not replace primary'})
  rows.append({**entry,'status':state,'official_reward':status.get('reward') if status else None,
               'duration':status.get('duration') if status else None,
               'observed_tokens':metrics['facts']['observed_token_sum'] if metrics else progress.get('observed_tokens') if progress else None,
               'enterprise_acceptance':None,'technical_gate_resolved':resolution is not None,'resolved_attempt':str(resolution) if resolution else None,'retry_review_sha256':sha(review_file(folder)) if review_file(folder) else None})
 counts=collections.Counter(x['status'] for x in rows)
 result={'stage':'P07','generated_at_utc':datetime.now(timezone.utc).isoformat(),'planned':len(rows),'status_counts':dict(counts),'scored':sum(x['status']=='scored' for x in rows),
         'official_reward_one_count':sum(x['status']=='scored' and x['official_reward']==1 for x in rows),
         'observed_tokens_available_sum':sum(x['observed_tokens'] for x in rows if x['observed_tokens'] is not None),
         'observed_tokens_all_attempts_available_sum':sum(x['observed_tokens'] for x in rows+retry_rows if x['observed_tokens'] is not None),
         'token_observation_missing_count':sum(x['observed_tokens'] is None for x in rows),
         'technical_gate_resolved_case_count':sum(x['technical_gate_resolved'] for x in rows),'reviewed_retry_attempt_count':len(retry_rows),'retry_rows':retry_rows,
         'enterprise_Q08':None,'rows':rows,
         'note':'All97 primary attempts retained, including user interruptions; reviewed additional attempts are secondary and never substitute primary scores. Token fields distinguish primary/all-attempt available sums; missing usage remains unknown. No interim score extrapolation or enterprise acceptance.'}
 (SUITE/'P07-full-suite-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--suite',type=Path,default=SUITE);args=parser.parse_args()
 r=report(args.suite);print(json.dumps({k:v for k,v in r.items() if k not in ['rows']},ensure_ascii=False))
