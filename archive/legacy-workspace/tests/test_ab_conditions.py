import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from run_ab_stage import pair_check,prerequisite,SHARED

class ABConditionsTest(unittest.TestCase):
 def fixtures(self):
  a={key:1 for key in SHARED};a.update(implementation='native-skill-stdio',episodes=[{'task_id':'task_002','seed':300}])
  b=copy.deepcopy(a);b.update(implementation='runtime-moa-main-local-skill',main_core_completion_timeout=1500,enterprise_differences={'prompts':'MAIN plus Skill'})
  return a,b
 def test_declared_main_and_prompt_differences_remain_explicit(self):
  a,b=self.fixtures();result=pair_check(a,b)
  self.assertEqual(result['differences'],b['enterprise_differences'])
  self.assertIn('Not isolated Runtime',result['attribution'])
 def test_old_timeout_or_wrong_seed_cannot_be_comparable(self):
  for mutation in ['core_completion_timeout','seed']:
   a,b=self.fixtures()
   if mutation=='seed':b['episodes'][0]['seed']=301
   else:b[mutation]=600
   with self.assertRaises(ValueError):pair_check(a,b)
 def test_review_label_without_actual_business_evidence_is_insufficient(self):
  with tempfile.TemporaryDirectory() as directory:
   suite=Path(directory);output=suite/'nonexistent-business-output'
   (suite/'P11-stage-review.json').write_text(json.dumps({'status':'COMPLETED','output_dir':str(output)}))
   with self.assertRaises(ValueError):prerequisite(suite)

if __name__=='__main__':unittest.main()
