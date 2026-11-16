import json,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from reviewed_timeout import create_review,retained_timeout
from retry_resolution import resolved_terminal

class ReviewedTimeoutTest(unittest.TestCase):
 def prepare(self,root):
  p=Path(root)/'P07-task_fixture-r00-a00';ep=p/'episodes/fixture';ep.mkdir(parents=True)
  (p/'manifest.json').write_text(json.dumps({'model':'fixture','episodes':[{'task_id':'task_fixture'}]}))
  (p/'progress.json').write_text(json.dumps({'observed_tokens':123}))
  (ep/'status.json').write_text(json.dumps({'status':'timeout','task_id':'task_fixture'}))
  (ep/'official-trajectory.jsonl').write_text('{}\n')
  proof=Path(root)/'process.json';proof.write_text(json.dumps({'original_attempt':str(p.resolve()),'controller_terminal_exit':1,'remaining_matching_processes':[],'recorded_at':time.time()+1}))
  return p,proof
 def test_retention_never_resolves_gate_or_retries(self):
  with tempfile.TemporaryDirectory() as root:
   p,proof=self.prepare(root);before=(p/'episodes/fixture/status.json').read_bytes();create_review(p,proof)
   self.assertTrue(retained_timeout(p));self.assertIsNone(resolved_terminal(p,'task_fixture'))
   self.assertEqual(before,(p/'episodes/fixture/status.json').read_bytes())
   self.assertFalse(p.with_name(p.name[:-3]+'a01').exists())
   with self.assertRaises(ValueError):create_review(p,proof)
 def test_rejects_active_process_and_non_timeout(self):
  for variant in ['live','scored']:
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as root:
    p,proof=self.prepare(root)
    if variant=='live':
     d=json.loads(proof.read_text());d['remaining_matching_processes']=[123];proof.write_text(json.dumps(d))
    else:(p/'episodes/fixture/status.json').write_text(json.dumps({'status':'scored','task_id':'task_fixture','reward':0}))
    with self.assertRaises(ValueError):create_review(p,proof)
 def test_rejects_changed_trajectory_and_forged_release(self):
  for variant in ['trajectory','release']:
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as root:
    p,proof=self.prepare(root);create_review(p,proof)
    if variant=='trajectory':(p/'episodes/fixture/official-trajectory.jsonl').write_text('changed')
    else:
     f=p/'retain-timeout-review.json';d=json.loads(f.read_text());d['technical_gate_resolved']=True;f.write_text(json.dumps(d))
    with self.assertRaises(ValueError):retained_timeout(p)
