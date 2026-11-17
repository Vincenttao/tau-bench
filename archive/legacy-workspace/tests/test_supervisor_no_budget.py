"""Exercise real supervision across two local episodes, with no gateway calls."""
import json,os,runpy,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class SupervisorNoBudgetTest(unittest.TestCase):
 def test_unbounded_usage_and_next_episode(self):
  with tempfile.TemporaryDirectory(prefix='supervisor-test-') as temporary:
   base=Path(temporary);output=base/'evidence';stub=base/'local_episode.py'
   stub.write_text('''import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--manifest');p.add_argument('--index',type=int);a=p.parse_args()
m=json.loads(Path(a.manifest).read_text());e=m['episodes'][a.index]
out=Path(m['output'])/'episodes'/e['key'];out.mkdir(parents=True,exist_ok=True)
(out/'user-usage.jsonl').write_text(json.dumps({'total_tokens':2000000000000000})+'\\n')
(out/'status.json').write_text(json.dumps({'status':'scored','reward':1,'task_id':e['task_id'],'trial':e['trial']}))
''')
   original_popen=subprocess.Popen;started=[]
   def local_popen(command,*args,**kwargs):
    if isinstance(command,list) and len(command)>1 and Path(command[1]).name=='episode.py':
     command=[command[0],str(stub),*command[2:]];started.append(command)
    return original_popen(command,*args,**kwargs)
   env={'TAU2_REPO':str(ROOT/'.deps/tau2-bench'),'OPENAI_API_KEY':'local-fixture-no-network','JAVA_AGENT_COMMAND':'unused-local-fixture'}
   argv=['full_run.py','--output',str(output),'--trials','2','--concurrency','1','--task-ids','task_001','--episode-timeout','15','--max-hours','0.02','--execute']
   with patch.dict(os.environ,env),patch.object(sys,'argv',argv),patch.object(subprocess,'Popen',local_popen):
    runpy.run_path(str(ROOT/'python/full_run.py'),run_name='__main__')
   self.assertEqual(len(started),2)
   self.assertEqual(len(list(output.glob('episodes/*/status.json'))),2)
   progress=json.loads((output/'progress.json').read_text())
   self.assertIsNone(progress['token_limit'])
   self.assertGreater(progress['observed_tokens'],10**15)
   self.assertEqual(progress['scored'],2)

if __name__=='__main__':unittest.main()
