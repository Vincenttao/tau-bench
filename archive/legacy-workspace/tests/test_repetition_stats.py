import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from repetition_stats import describe
class RepetitionTest(unittest.TestCase):
 def test_missing_not_removed_from_planned_denominator(self):
  result=describe([{'official_reward':1,'duration':2},{'official_reward':None,'duration':None}],3)
  self.assertEqual(result['missing_score'],2)
  self.assertIsNone(result['official_pass_fraction_planned'])
  self.assertAlmostEqual(result['confirmed_success_fraction_lower_bound'],1/3)
  self.assertEqual(result['possible_success_fraction_upper_bound'],1)
  self.assertIsNone(result['quality_stdev_scored_subset'])
  self.assertIsNone(result['enterprise_K05'])
 def test_sample_stdev(self):
  result=describe([{'official_reward':1,'duration':2},{'official_reward':0,'duration':4}],2)
  self.assertEqual(result['official_pass_fraction_planned'],0.5)
  self.assertAlmostEqual(result['quality_stdev_scored_subset'],2**-.5)
  self.assertAlmostEqual(result['duration_stdev_observed_subset'],2**.5)
if __name__=='__main__':unittest.main()
