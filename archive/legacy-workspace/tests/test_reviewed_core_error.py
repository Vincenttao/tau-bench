import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import test_reviewed_timeout as timeout_fixture
from reviewed_core_error import create_review,retained_core_error
from retry_resolution import resolved_terminal

class ReviewedCoreErrorTest(unittest.TestCase):
 def prepare(self,root):
  p,proof=timeout_fixture.ReviewedTimeoutTest().prepare(root);ep=p/'episodes/fixture'
  (ep/'status.json').write_text(json.dumps({'status':'execution_error','error_type':'RuntimeError','task_id':'task_fixture'}))
  (ep/'exception.txt').write_text('Core execution error: Ability not found in resource_mgr: unlock_discoverable_agent_tool')
  (ep/'java').mkdir();(ep/'java/log.stderr.log').write_text('[LLM]   tool_call: unlock_discoverable_agent_tool\ntool_name=unlock_discoverable_agent_tool outcome=not_found')
  return p,proof
 def test_retained_core_error_does_not_resolve_gate(self):
  with tempfile.TemporaryDirectory() as root:
   p,proof=self.prepare(root);create_review(p,proof);self.assertTrue(retained_core_error(p))
   self.assertIsNone(resolved_terminal(p,'task_fixture'))
   self.assertFalse(p.with_name(p.name[:-3]+'a01').exists())
   with self.assertRaises(ValueError):create_review(p,proof)
 def test_rejects_unrelated_error_and_missing_direct_call_evidence(self):
  for variant in ['exception','log']:
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as root:
    p,proof=self.prepare(root)
    f=p/('episodes/fixture/exception.txt' if variant=='exception' else 'episodes/fixture/java/log.stderr.log');f.write_text('different')
    with self.assertRaises(ValueError):create_review(p,proof)
 def test_rejects_live_process_and_mutated_evidence(self):
  with tempfile.TemporaryDirectory() as root:
   p,proof=self.prepare(root);d=json.loads(proof.read_text());d['remaining_matching_processes']=[123];proof.write_text(json.dumps(d))
   with self.assertRaises(ValueError):create_review(p,proof)
   d['remaining_matching_processes']=[];proof.write_text(json.dumps(d));create_review(p,proof)
   (p/'episodes/fixture/java/log.stderr.log').write_text('changed')
   with self.assertRaises(ValueError):retained_core_error(p)
