import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EnterpriseRunGateTest(unittest.TestCase):
 def test_no_business_process_before_replay_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'must-not-start'
   result=subprocess.run([sys.executable,str(ROOT/'python/enterprise_run.py'),'--execute','--output',str(output),'--gate-suite',tmp],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15,cwd=ROOT)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('P10 fixed-response replay evidence review required',result.stderr)
   self.assertFalse(output.exists())
 def test_no_variation_runs_before_full_repetition_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   result=subprocess.run([sys.executable,str(ROOT/'python/run_variation_stage.py'),'--execute','--suite',tmp],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15,cwd=ROOT)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('P08 complete review required before P09',result.stderr)
   self.assertFalse((Path(tmp)/'P09-schedule.json').exists())
 def test_no_capture_before_variation_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'must-not-capture'
   result=subprocess.run([sys.executable,str(ROOT/'python/run_fixed_response_stage.py'),'--execute','--suite',tmp,'--output',str(output)],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15,cwd=ROOT)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('P09 complete review required before P10',result.stderr)
   self.assertFalse(output.exists())
 def test_replay_plan_retains_both_preselected_cases(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'plan-only'
   result=subprocess.run([sys.executable,str(ROOT/'python/run_fixed_response_stage.py'),'--suite',tmp,'--output',str(output)],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15,cwd=ROOT)
   self.assertEqual(result.returncode,0,result.stderr)
   plan=json.loads((output/'plan.json').read_text());cases=json.loads((ROOT/'config/repetition-study-v1.json').read_text())['P06']['cases']
   self.assertEqual(plan['task_ids'],cases)
   self.assertEqual(plan['capture_episodes'],len(cases))
   self.assertEqual(plan['independent_replays_per_case'],2)
   self.assertFalse((output/cases[0]).exists())
if __name__=='__main__':unittest.main()
