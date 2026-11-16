import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from collect_metrics_v02 import collect

class EnterpriseMetricsTest(unittest.TestCase):
 def test_real_task_namespace_and_missing_usage(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);folder=root/'episodes/case';java=folder/'java';java.mkdir(parents=True)
   (root/'manifest.json').write_text(json.dumps({'implementation':'runtime-moa-main-local-skill','model':'fixture','token_limit':None,'episodes':[{'key':'case','task_id':'task_001','trial':0,'seed':300,'domain':'banking_knowledge'}]}))
   with self.assertRaises(ValueError):collect(root)
   empty=collect(root,implementation='runtime-moa-main-local-skill')
   self.assertIsNone(empty['facts']['observed_runtime_task_count'])
   events=[{'event':'a2a_response','body':{'result':{'task':{'id':'actual-task','contextId':'actual-context','status':{'state':state}}}}} for state in ['TASK_STATE_INPUT_REQUIRED','TASK_STATE_COMPLETED']]
   events += [{'event':'official_tool_request','boot_id':'boot-one','call_id':'call-one','core_session_id':'core-session-one','operation':'read','event_sequence':3,'monotonic_nanos':30},
              {'event':'official_tool_result','boot_id':'boot-one','call_id':'call-one','core_session_id':'core-session-one','operation':'read','event_sequence':4,'monotonic_nanos':40,'success':False}]
   (java/'runtime-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
   (folder/'user-usage.jsonl').write_text(json.dumps({'total_tokens':None,'prompt_tokens':None,'completion_tokens':None})+'\n')
   result=collect(root,implementation='runtime-moa-main-local-skill')
   self.assertEqual(result['facts']['observed_runtime_task_count'],1)
   self.assertEqual(result['facts']['observed_core_tool_call_count'],1)
   self.assertFalse(result['episodes'][0]['core_tool_call_observations'][0]['success'])
   self.assertEqual(result['episodes'][0]['core_tool_call_observations'][0]['core_session_id'],'core-session-one')
   self.assertIsNone(result['facts']['runtime_task_count'])
   self.assertIsNone(result['facts']['observed_token_sum'])
   self.assertEqual(result['episodes'][0]['runtime_task_id'],'actual-task')
   self.assertEqual(result['episodes'][0]['runtime_task_snapshots'][0]['last_observed_state'],'TASK_STATE_COMPLETED')
   self.assertIsNone(result['episodes'][0]['parent_task_id'])
   self.assertTrue(all(m['value'] is None for m in result['metrics']))
   self.assertEqual(next(m for m in result['metrics'] if m['id']=='E06')['evaluation_result'],'不适用')
   self.assertNotIn('未接 Runtime',next(m for m in result['metrics'] if m['id']=='R01')['reason'])
   with (folder/'user-usage.jsonl').open('a') as f:f.write(json.dumps({'total_tokens':17,'prompt_tokens':12,'completion_tokens':5})+'\n')
   partial=collect(root,implementation='runtime-moa-main-local-skill')
   self.assertEqual(partial['facts']['observed_token_sum'],17)
   self.assertIsNone(partial['episodes'][0]['python_usage']['total_tokens'])
   self.assertEqual(partial['episodes'][0]['python_usage_records_missing_total'],1)

if __name__=='__main__':unittest.main()
