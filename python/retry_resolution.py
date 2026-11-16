"""One reviewed additional attempt; original errors and user interruptions retained."""
import hashlib,json,time
from pathlib import Path
from study_contract import compare

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def one(folder,name):
 files=list(Path(folder).glob('episodes/*/'+name))
 if len(files)!=1:raise ValueError('Exactly one '+name+' required: '+str(folder))
 return files[0]
def status(folder):
 files=list(Path(folder).glob('episodes/*/status.json'))
 return json.loads(files[0].read_text()) if len(files)==1 else None
def healthy(folder,case):
 folder=Path(folder);state=status(folder)
 if not state or state.get('task_id')!=case:return False
 if not all((folder/name).exists() for name in ['manifest.json','analysis-v2.json','metrics-v02.json']):return False
 if state['status']=='scored':
  results=list(folder.glob('episodes/*/result.json'))
  if len(results)!=1:return False
  simulations=json.loads(results[0].read_text()).get('simulations',[])
  return len(simulations)==1 and simulations[0].get('task_id')==case and simulations[0].get('reward_info',{}).get('reward') is not None and simulations[0]['reward_info']['reward']==state.get('reward')
 if case=='task_102' and state['status']=='evaluation_error':
  errors=list(folder.glob('episodes/*/exception.txt'))
  return bool(errors) and all('404' in path.read_text() and 'NotFoundError' in path.read_text() for path in errors) and bool(list(folder.glob('episodes/*/trajectory-unscored.json')))
 return False

def initial_only_before_agent(folder):
 folder=Path(folder);state=status(folder)
 if not state or state.get('status')!='execution_error':return False
 manifest=json.loads((folder/'manifest.json').read_text())
 if len(manifest.get('episodes',[]))!=1 or manifest['episodes'][0]['task_id']!=state.get('task_id'):return False
 exceptions=list(folder.glob('episodes/*/exception.txt'))
 journals=list(folder.glob('episodes/*/official-trajectory.jsonl'))
 if len(exceptions)!=1 or len(journals)!=1 or list(folder.glob('episodes/*/java/*')):return False
 rows=[json.loads(line) for line in journals[0].read_text().splitlines()]
 return len(rows)==1 and rows[0].get('role')=='assistant' and rows[0].get('content')=='Hi! How can I help you today?' and not rows[0].get('tool_calls') and rows[0].get('raw_data') is None

def failure_kind(folder):
 folder=Path(folder)
 if user_interrupted(folder):return 'user_requested_pause_restart'
 if mid_episode_empty_user(folder):return 'user_simulator_empty_mid_episode_message'
 if not initial_only_before_agent(folder):return None
 detail=one(folder,'exception.txt').read_text()
 if all(marker in detail for marker in ['[Errno -3]','Temporary failure in name resolution','self.user.generate_next_message']):return 'user_simulator_dns_before_agent'
 if all(marker in detail for marker in ['user_msg.validate()','ValueError: UserMessage must have either content or tool_calls.']):
  usage=list(folder.glob('episodes/*/user-usage.jsonl'))
  if len(usage)!=1:return None
  records=[json.loads(line) for line in usage[0].read_text().splitlines()]
  manifest=json.loads((folder/'manifest.json').read_text())
  if len(records)==1 and records[0].get('requested_model')=='openai/'+manifest['model'] and records[0].get('total_tokens',0)>0:return 'user_simulator_empty_initial_message'
 return None

def review_file(primary):
 paths=[Path(primary)/name for name in ['dns-retry-review.json','pre-agent-retry-review.json','user-resume-review.json','mid-episode-retry-review.json']]
 existing=[path for path in paths if path.exists()]
 if len(existing)>1:raise ValueError('Multiple retry reviews are not allowed')
 return existing[0] if existing else None

def mid_episode_empty_user(primary):
 primary=Path(primary);state=status(primary)
 if not state or state.get('status')!='execution_error' or state.get('error_type')!='ValueError':return False
 if list(primary.glob('episodes/*/result.json')) or list(primary.glob('episodes/*/trajectory-unscored.json')):return False
 try:
  manifest=json.loads((primary/'manifest.json').read_text())
  if len(manifest.get('episodes',[]))!=1 or manifest['episodes'][0]['task_id']!=state.get('task_id'):return False
  detail=one(primary,'exception.txt').read_text()
  if not all(x in detail for x in ['user_msg.validate()','ValueError: UserMessage must have either content or tool_calls.']):return False
  rows=[json.loads(x) for x in one(primary,'official-trajectory.jsonl').read_text().splitlines()]
  usage=[json.loads(x) for x in one(primary,'user-usage.jsonl').read_text().splitlines()]
  return (len(rows)>1 and any(x.get('role')=='user' for x in rows)
          and bool(list(primary.glob('episodes/*/java/*.jsonl'))) and len(usage)>1
          and all(x.get('requested_model')=='openai/'+manifest['model'] and x.get('total_tokens',0)>0 for x in usage))
 except (ValueError,KeyError,FileNotFoundError):return False

def create_mid_episode_review(primary,preflight,isolation):
 """Explicit review for one fresh isolated episode, never resume business writes."""
 primary=Path(primary).resolve();preflight=Path(preflight).resolve();isolation=Path(isolation).resolve()
 if not mid_episode_empty_user(primary):raise ValueError('Verified mid-episode empty simulator message required')
 if review_file(primary) or retry_path(primary).exists():raise ValueError('Additional attempt already reviewed or exists')
 check=json.loads(preflight.read_text());proof=json.loads(isolation.read_text());manifest=json.loads((primary/'manifest.json').read_text())
 after=one(primary,'status.json').stat().st_mtime
 if (check.get('status')!='transport_ready' or check.get('http_status')!=200 or check.get('model_requested')!=manifest['model']
     or check.get('benchmark_episode') is not False or check.get('nonempty_assistant_message') is not True or check.get('recorded_at',0)<after):raise ValueError('Fresh nonempty recovery preflight required')
 if (proof.get('original_attempt')!=str(primary) or proof.get('controller_terminal_exit')!=1
     or proof.get('remaining_matching_processes')!=[] or proof.get('independent_environment_verified') is not True
     or proof.get('external_business_endpoints') is not False or proof.get('recorded_at',0)<after):raise ValueError('Fresh process and isolated bank environment evidence required')
 review={'classification':'user_simulator_empty_mid_episode_message','max_additional_attempts':1,
         'original_attempt':str(primary),'retry_attempt':str(retry_path(primary)),
         'original_evidence':interruption_evidence(primary),'recovery_preflight':str(preflight),
         'recovery_preflight_sha256':sha(preflight),'isolation_evidence':str(isolation),'isolation_evidence_sha256':sha(isolation),
         'recorded_at':time.time(),'reviewer':'Codex explicit technical recovery review',
         'primary_score_policy':'Original execution error and partial business trajectory retained. Secondary fresh environment only; no checkpoint recovery, no replacement or selection for reward1.'}
 (primary/'mid-episode-retry-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');return review

def interruption_record(primary):
 primary=Path(primary).resolve()
 if status(primary) is not None or list(primary.glob('episodes/*/result.json')):return None
 matches=[]
 for name,expected in [('user-pause.json','PAUSED_BY_USER'),('user-stop-for-analysis.json','STOPPED_BY_USER_FOR_ANALYSIS')]:
  pause=primary.parent/name
  if not pause.exists():continue
  data=json.loads(pause.read_text())
  if (data.get('status')==expected and data.get('interrupted_attempt')==primary.name
      and data.get('remaining_live_pids')==[] and bool(data.get('captured_pids'))):matches.append(pause)
 if len(matches)>1:raise ValueError('Ambiguous user interruption evidence')
 return matches[0] if matches else None

def user_interrupted(primary):
 return interruption_record(primary) is not None

def interruption_evidence(primary):
 primary=Path(primary)
 files=[primary/'manifest.json',primary/'progress.json',*sorted((primary/'episodes').rglob('*'))]
 return {str(p.relative_to(primary)):sha(p) for p in files if p.is_file()}

def create_resume_review(primary):
 primary=Path(primary).resolve()
 if not user_interrupted(primary):raise ValueError('Verified user interruption with no terminal score required')
 if review_file(primary) or retry_path(primary).exists():raise ValueError('Additional attempt already reviewed or exists')
 manifest=json.loads((primary/'manifest.json').read_text())
 if len(manifest.get('episodes',[]))!=1:raise ValueError('Single isolated episode required')
 review={'classification':'user_requested_pause_restart','max_additional_attempts':1,
         'original_attempt':str(primary),'retry_attempt':str(retry_path(primary)),
         'pause_record':str(interruption_record(primary)),'pause_record_sha256':sha(interruption_record(primary)),
         'original_evidence':interruption_evidence(primary),'recorded_at':time.time(),
         'reviewer':'Codex technical evidence review after explicit user continue instruction',
         'primary_score_policy':'Original user interruption retained, not a failure or score; fresh isolated episode, no checkpoint claim or success selection'}
 (primary/'user-resume-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
 return review

def retry_path(primary):
 primary=Path(primary)
 if not primary.name.endswith('-a00'):raise ValueError('Only first attempt may receive one reviewed additional attempt')
 return primary.with_name(primary.name[:-3]+'a01')

def create_review(primary,preflight):
 primary=Path(primary).resolve();preflight=Path(preflight).resolve()
 kind=failure_kind(primary)
 if kind not in ['user_simulator_dns_before_agent','user_simulator_empty_initial_message']:raise ValueError('Not a classified pre-agent simulator failure; no automatic business retry')
 check=json.loads(preflight.read_text());manifest=json.loads((primary/'manifest.json').read_text())
 if check.get('status')!='transport_ready' or check.get('http_status')!=200 or check.get('model_requested')!=manifest['model'] or check.get('benchmark_episode') is not False:raise ValueError('Successful independent recovery preflight required')
 if check.get('recorded_at',0)<one(primary,'status.json').stat().st_mtime:raise ValueError('Recovery preflight predates failure')
 if kind=='user_simulator_empty_initial_message' and check.get('nonempty_assistant_message') is not True:raise ValueError('Nonempty independent model reply required after empty initial message')
 review={'classification':kind,'max_additional_attempts':1,'original_attempt':str(primary),'retry_attempt':str(retry_path(primary)),
         'exception_sha256':sha(one(primary,'exception.txt')),'journal_sha256':sha(one(primary,'official-trajectory.jsonl')),'status_sha256':sha(one(primary,'status.json')),'manifest_sha256':sha(primary/'manifest.json'),
         'recovery_preflight':str(preflight),'recovery_preflight_sha256':sha(preflight),'recorded_at':time.time(),'reviewer':'Codex technical evidence review','primary_score_policy':'Original unscored/error retained; retry official score reported separately; never select for reward1'}
 if kind=='user_simulator_empty_initial_message':review['user_usage_sha256']=sha(one(primary,'user-usage.jsonl'))
 target=primary/('dns-retry-review.json' if kind=='user_simulator_dns_before_agent' else 'pre-agent-retry-review.json')
 if review_file(primary) is not None:raise ValueError('Review already exists; inspect it rather than overwrite')
 target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');return review

def approved_retry(primary):
 primary=Path(primary).resolve();file=review_file(primary)
 if file is None:return None
 review=json.loads(file.read_text());expected=retry_path(primary)
 if review.get('classification')=='user_simulator_empty_mid_episode_message':
  if (review.get('max_additional_attempts')!=1 or review.get('original_attempt')!=str(primary)
      or review.get('retry_attempt')!=str(expected) or not mid_episode_empty_user(primary)
      or review.get('original_evidence')!=interruption_evidence(primary)
      or review.get('recovery_preflight_sha256')!=sha(Path(review['recovery_preflight']))
      or review.get('isolation_evidence_sha256')!=sha(Path(review['isolation_evidence']))):raise ValueError('Mid-episode recovery evidence changed or invalid review')
  return expected
 if review.get('classification')=='user_requested_pause_restart':
  if (review.get('max_additional_attempts')!=1 or review.get('original_attempt')!=str(primary)
      or review.get('retry_attempt')!=str(expected) or not user_interrupted(primary)
      or review.get('pause_record')!=str(interruption_record(primary))
      or review.get('pause_record_sha256')!=sha(interruption_record(primary))
      or review.get('original_evidence')!=interruption_evidence(primary)):
   raise ValueError('User interruption evidence changed or invalid continuation review')
  return expected
 if review.get('classification') not in ['user_simulator_dns_before_agent','user_simulator_empty_initial_message'] or review.get('max_additional_attempts')!=1 or review.get('original_attempt')!=str(primary) or review.get('retry_attempt')!=str(expected):raise ValueError('Invalid bounded retry review')
 if failure_kind(primary)!=review['classification']:raise ValueError('Original failure no longer matches review')
 if review['classification']=='user_simulator_empty_initial_message' and review.get('user_usage_sha256')!=sha(one(primary,'user-usage.jsonl')):raise ValueError('Reviewed user usage changed')
 for key,path in [('exception_sha256',one(primary,'exception.txt')),('journal_sha256',one(primary,'official-trajectory.jsonl')),('status_sha256',one(primary,'status.json')),('manifest_sha256',primary/'manifest.json'),('recovery_preflight_sha256',Path(review['recovery_preflight']))]:
  if review.get(key)!=sha(path):raise ValueError('Reviewed evidence changed: '+key)
 return expected

def resolved_terminal(primary,case,anchor=None):
 primary=Path(primary);candidate=primary if healthy(primary,case) else approved_retry(primary)
 if candidate is None or not healthy(candidate,case):return None
 manifest=json.loads((candidate/'manifest.json').read_text())
 if len(manifest.get('episodes',[]))!=1 or manifest['episodes'][0]['task_id']!=case:raise ValueError('Resolved case identity mismatch')
 sources=[json.loads((primary/'manifest.json').read_text()),manifest]
 if anchor is not None:sources.insert(0,anchor)
 if not compare(sources)['comparable']:raise ValueError('Retry execution contract changed')
 return candidate
