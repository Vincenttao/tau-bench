import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from study_contract import compare
class ContractTest(unittest.TestCase):
 def test_output_directory_not_execution_condition(self):
  a={'model':'same','output':'one','episodes':[{'seed':300}]};b={**a,'output':'two'}
  self.assertTrue(compare([a,b])['comparable'])
 def test_seed_or_model_change_detected(self):
  a={'model':'same','episodes':[{'seed':300}]}
  self.assertIn('episode_seeds',compare([a,{**a,'episodes':[{'seed':301}]}])['changed_fields'])
  self.assertIn('model',compare([a,{**a,'model':'other'}])['changed_fields'])
  self.assertIn('main_core_completion_timeout',compare([{**a,'main_core_completion_timeout':1500},{**a,'main_core_completion_timeout':1600}])['changed_fields'])
if __name__=='__main__':unittest.main()
