import json,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from retry_resolution import create_review,approved_retry,resolved_terminal,retry_path,create_resume_review,user_interrupted,create_mid_episode_review

class RetryResolutionTest(unittest.TestCase):
 def prepare_mid(self,root):
  primary,preflight,manifest=self.prepare_empty(root);folder=primary/'episodes/case'
  (folder/'status.json').write_text(json.dumps({'status':'execution_error','error_type':'ValueError','task_id':'task_fixture'}))
  with (folder/'official-trajectory.jsonl').open('a') as f:f.write(json.dumps({'role':'user','content':'Transfer money'})+'\n')
  with (folder/'user-usage.jsonl').open('a') as f:f.write(json.dumps({'requested_model':'openai/deepseek-v4-flash','total_tokens':123})+'\n')
  (folder/'java').mkdir();(folder/'java/trace.jsonl').write_text('{}\n')
  isolation=Path(root)/'isolation.json';isolation.write_text(json.dumps({'original_attempt':str(primary.resolve()),'controller_terminal_exit':1,'remaining_matching_processes':[],'independent_environment_verified':True,'external_business_endpoints':False,'recorded_at':time.time()+1}))
  return primary,preflight,manifest,isolation
 def test_mid_episode_recovery_is_separate_and_accepts_reward_zero(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest,isolation=self.prepare_mid(tmp);original=(primary/'episodes/case/status.json').read_bytes()
   with self.assertRaises(ValueError):create_review(primary,preflight)
   create_mid_episode_review(primary,preflight,isolation);self.assertEqual(approved_retry(primary),retry_path(primary))
   retry=self.complete(primary,manifest,reward=0);self.assertEqual(resolved_terminal(primary,'task_fixture',manifest),retry)
   self.assertEqual(original,(primary/'episodes/case/status.json').read_bytes())
   with self.assertRaises(ValueError):create_mid_episode_review(primary,preflight,isolation)
 def test_mid_episode_recovery_requires_isolated_state_and_stopped_processes(self):
  for key,value in [('remaining_matching_processes',[123]),('independent_environment_verified',False),('external_business_endpoints',True)]:
   with self.subTest(key=key),tempfile.TemporaryDirectory() as tmp:
    primary,preflight,_,isolation=self.prepare_mid(tmp);data=json.loads(isolation.read_text());data[key]=value;isolation.write_text(json.dumps(data))
    with self.assertRaises(ValueError):create_mid_episode_review(primary,preflight,isolation)
 def test_mid_episode_recovery_rejects_changed_evidence_and_second_error(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest,isolation=self.prepare_mid(tmp);create_mid_episode_review(primary,preflight,isolation)
   retry=self.complete(primary,manifest);(retry/'episodes/case/status.json').write_text(json.dumps({'status':'execution_error','task_id':'task_fixture'}))
   self.assertIsNone(resolved_terminal(primary,'task_fixture',manifest))
   with self.assertRaises(ValueError):create_mid_episode_review(retry,preflight,isolation)
   with (primary/'episodes/case/java/trace.jsonl').open('a') as f:f.write('{}\n')
   with self.assertRaises(ValueError):approved_retry(primary)
 def prepare_pause(self,root):
  primary,_,manifest=self.prepare(root)
  (primary/'episodes/case/status.json').unlink()
  (primary/'episodes/case/exception.txt').unlink()
  (primary/'progress.json').write_text(json.dumps({'observed_tokens':123,'active':1}))
  (primary.parent/'user-pause.json').write_text(json.dumps({'status':'PAUSED_BY_USER','interrupted_attempt':primary.name,'remaining_live_pids':[],'captured_pids':[123]}))
  return primary,manifest
 def test_user_resume_retains_interruption_and_accepts_scored_failure(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,manifest=self.prepare_pause(tmp);create_resume_review(primary)
   self.assertTrue(user_interrupted(primary));self.assertEqual(approved_retry(primary),retry_path(primary))
   retry=self.complete(primary,manifest,reward=0)
   self.assertEqual(resolved_terminal(primary,'task_fixture',manifest),retry)
   self.assertFalse((primary/'episodes/case/status.json').exists())
   with self.assertRaises(ValueError):create_resume_review(primary)
 def test_user_resume_rejects_terminal_score_and_live_process(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,_=self.prepare_pause(tmp);p=primary.parent/'user-pause.json';data=json.loads(p.read_text());data['remaining_live_pids']=[123];p.write_text(json.dumps(data))
   with self.assertRaises(ValueError):create_resume_review(primary)
   data['remaining_live_pids']=[];p.write_text(json.dumps(data));(primary/'episodes/case/status.json').write_text(json.dumps({'status':'scored','reward':0}))
   with self.assertRaises(ValueError):create_resume_review(primary)
 def test_user_resume_freezes_original_trajectory(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,_=self.prepare_pause(tmp);create_resume_review(primary)
   with (primary/'episodes/case/official-trajectory.jsonl').open('a') as f:f.write('{}\n')
   with self.assertRaises(ValueError):approved_retry(primary)
 def test_analysis_stop_resumes_once_without_changing_primary(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,manifest=self.prepare_pause(tmp)
   pause=primary.parent/'user-pause.json';data=json.loads(pause.read_text());pause.unlink()
   data['status']='STOPPED_BY_USER_FOR_ANALYSIS'
   stop=primary.parent/'user-stop-for-analysis.json';stop.write_text(json.dumps(data))
   before=stop.read_bytes();review=create_resume_review(primary)
   self.assertEqual(review['pause_record'],str(stop.resolve()))
   self.assertEqual(approved_retry(primary),retry_path(primary))
   retry=self.complete(primary,manifest,reward=0)
   self.assertEqual(resolved_terminal(primary,'task_fixture',manifest),retry)
   self.assertEqual(stop.read_bytes(),before)
   self.assertFalse((primary/'episodes/case/status.json').exists())
 def test_analysis_stop_live_process_or_changed_evidence_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,_=self.prepare_pause(tmp);pause=primary.parent/'user-pause.json';data=json.loads(pause.read_text());pause.unlink()
   data.update(status='STOPPED_BY_USER_FOR_ANALYSIS',remaining_live_pids=[123])
   stop=primary.parent/'user-stop-for-analysis.json';stop.write_text(json.dumps(data))
   with self.assertRaises(ValueError):create_resume_review(primary)
   data['remaining_live_pids']=[];stop.write_text(json.dumps(data));create_resume_review(primary)
   data['recorded_at']=1;stop.write_text(json.dumps(data))
   with self.assertRaises(ValueError):approved_retry(primary)
 def prepare(self,root):
  primary=Path(root)/'P07-task_fixture-r00-a00';folder=primary/'episodes/case';folder.mkdir(parents=True)
  manifest={'model':'deepseek-v4-flash','episodes':[{'task_id':'task_fixture','seed':300}]}
  (primary/'manifest.json').write_text(json.dumps(manifest))
  (folder/'status.json').write_text(json.dumps({'status':'execution_error','task_id':'task_fixture'}))
  (folder/'exception.txt').write_text('[Errno -3] Temporary failure in name resolution\nself.user.generate_next_message')
  (folder/'official-trajectory.jsonl').write_text(json.dumps({'role':'assistant','content':'Hi! How can I help you today?','tool_calls':None,'raw_data':None})+'\n')
  preflight=Path(root)/'preflight.json';preflight.write_text(json.dumps({'status':'transport_ready','http_status':200,'model_requested':'deepseek-v4-flash','benchmark_episode':False,'recorded_at':time.time()+1}))
  return primary,preflight,manifest
 def complete(self,primary,manifest,reward=0):
  retry=retry_path(primary);folder=retry/'episodes/case';folder.mkdir(parents=True)
  (retry/'manifest.json').write_text(json.dumps(manifest))
  (folder/'status.json').write_text(json.dumps({'status':'scored','task_id':'task_fixture','reward':reward}))
  (folder/'result.json').write_text(json.dumps({'simulations':[{'task_id':'task_fixture','reward_info':{'reward':reward}}]}))
  for name in ['metrics-v02.json','analysis-v2.json']:(retry/name).write_text('{}')
  return retry
 def test_one_reviewed_retry_does_not_require_business_pass(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare(tmp);before=(primary/'episodes/case/status.json').read_bytes();create_review(primary,preflight)
   self.assertEqual(approved_retry(primary),retry_path(primary));self.assertIsNone(resolved_terminal(primary,'task_fixture',manifest))
   retry=self.complete(primary,manifest,reward=0)
   self.assertEqual(resolved_terminal(primary,'task_fixture',manifest),retry)
   self.assertEqual((primary/'episodes/case/status.json').read_bytes(),before)
   with self.assertRaises(ValueError):retry_path(retry)
 def test_changed_evidence_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare(tmp);create_review(primary,preflight)
   (primary/'episodes/case/exception.txt').write_text('different error')
   with self.assertRaises(ValueError):approved_retry(primary)
 def test_business_activity_prevents_automatic_retry(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare(tmp)
   with (primary/'episodes/case/official-trajectory.jsonl').open('a') as f:f.write(json.dumps({'role':'user','tool_calls':[{'name':'write'}]})+'\n')
   with self.assertRaises(ValueError):create_review(primary,preflight)
 def test_retry_configuration_drift_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare(tmp);create_review(primary,preflight);self.complete(primary,{**manifest,'model':'different'})
   with self.assertRaises(ValueError):resolved_terminal(primary,'task_fixture',manifest)
 def test_no_loop_of_additional_retries(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare(tmp);review=create_review(primary,preflight);review['max_additional_attempts']=2
   (primary/'dns-retry-review.json').write_text(json.dumps(review))
   with self.assertRaises(ValueError):approved_retry(primary)
 def prepare_empty(self,root):
  primary,preflight,manifest=self.prepare(root);folder=primary/'episodes/case'
  (folder/'exception.txt').write_text('user_msg.validate()\nValueError: UserMessage must have either content or tool_calls.')
  (folder/'user-usage.jsonl').write_text(json.dumps({'requested_model':'openai/deepseek-v4-flash','total_tokens':777})+'\n')
  data=json.loads(preflight.read_text());data['nonempty_assistant_message']=True;preflight.write_text(json.dumps(data))
  return primary,preflight,manifest
 def test_empty_first_user_message_has_separate_bounded_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare_empty(tmp);review=create_review(primary,preflight)
   self.assertEqual(review['classification'],'user_simulator_empty_initial_message')
   self.assertTrue((primary/'pre-agent-retry-review.json').exists())
   retry=self.complete(primary,manifest,reward=0)
   self.assertEqual(resolved_terminal(primary,'task_fixture',manifest),retry)
 def test_empty_response_requires_nonempty_recovery_check(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare_empty(tmp);data=json.loads(preflight.read_text());data['nonempty_assistant_message']=False;preflight.write_text(json.dumps(data))
   with self.assertRaises(ValueError):create_review(primary,preflight)
 def test_empty_response_retry_rejects_prior_java_activity(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare_empty(tmp);folder=primary/'episodes/case/java';folder.mkdir();(folder/'trace.jsonl').write_text('{}')
   with self.assertRaises(ValueError):create_review(primary,preflight)
 def test_empty_response_usage_evidence_is_immutable(self):
  with tempfile.TemporaryDirectory() as tmp:
   primary,preflight,manifest=self.prepare_empty(tmp);create_review(primary,preflight)
   (primary/'episodes/case/user-usage.jsonl').write_text(json.dumps({'requested_model':'openai/deepseek-v4-flash','total_tokens':778})+'\n')
   with self.assertRaises(ValueError):approved_retry(primary)
