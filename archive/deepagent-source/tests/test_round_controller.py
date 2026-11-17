"""Deterministic controller tests with synthetic subprocesses; no model or bank calls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'python'))
import run_round as module

STUB='''import argparse,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--manifest');p.add_argument('--index',type=int);a=p.parse_args()
m=json.loads(Path(a.manifest).read_text());e=m['episodes'][a.index];root=Path(m['output']);folder=root/'episodes'/e['key']
with (root/'launches.jsonl').open('a') as f:f.write(json.dumps(e['task_id'])+'\\n')
if m.get('sleep'):time.sleep(m['sleep'])
s='execution_error' if e['task_id']==m.get('fail') else 'scored'
if s=='execution_error':(folder/'exception.txt').write_text('Connection refused during model transport')
(folder/'status.json').write_text(json.dumps({'status':s,'task_id':e['task_id'],'trial':0,**({'reward':0 if a.index%2 else 1} if s=='scored' else {})}))
'''

class RoundControllerTest(unittest.TestCase):
    def setup_round(self, root, count=22, **extra):
        script=root/'fixture.py';script.write_text(STUB)
        episodes=[{'task_id':f'fixture_{n:03}','key':f'key-{n}','order':n+1,'wave':1 if n<11 else 2,'domain':'synthetic'} for n in range(count)]
        manifest={'output':str(root),'episodes':episodes,**extra}
        module.write(root/'manifest.json',manifest)
        plan={'conditions':{'batch_wall_time_seconds':20,'episode_timeout_seconds':5}}
        return script,manifest,plan
    def run_fixture(self, root, script, manifest, plan):
        return module.run_round(root,plan,manifest,check=lambda _:None,episode_script=script,poll_seconds=.01)
    def test_22_in_exact_order_business_zero_continues_and_resume_never_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);script,m,p=self.setup_round(root)
            result=self.run_fixture(root,script,m,p)
            self.assertEqual(result['state'],'completed');self.assertEqual(result['scored'],22)
            self.assertEqual(result['successful'],11)
            launches=[json.loads(x) for x in (root/'launches.jsonl').read_text().splitlines()]
            self.assertEqual(launches,[x['task_id'] for x in m['episodes']])
            self.run_fixture(root,script,m,p)
            self.assertEqual(len((root/'launches.jsonl').read_text().splitlines()),22)
    def test_systemic_fault_stops_and_review_resumes_only_unstarted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);script,m,p=self.setup_round(root,count=3,fail='fixture_001')
            result=self.run_fixture(root,script,m,p)
            self.assertEqual(result['stop_reason'],'gateway_transport')
            self.assertEqual(len((root/'launches.jsonl').read_text().splitlines()),2)
            self.run_fixture(root,script,m,p)
            self.assertEqual(len((root/'launches.jsonl').read_text().splitlines()),2)
            (root/'reviews').mkdir()
            module.write(root/'reviews/fixture_001.json',{'decision':'continue_unstarted_only','status_sha256':module.sha(root/'episodes/key-1/status.json'),'reason':'Synthetic audit fixture only'})
            result=self.run_fixture(root,script,m,p)
            self.assertEqual(result['state'],'completed')
            self.assertEqual(len((root/'launches.jsonl').read_text().splitlines()),3)
    def test_hard_batch_deadline_kills_inflight_and_leaves_pending(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);script,m,p=self.setup_round(root,count=3,sleep=5)
            p['conditions']['batch_wall_time_seconds']=.2
            result=self.run_fixture(root,script,m,p)
            self.assertEqual(result['stop_reason'],'batch_wall_time')
            self.assertEqual(result['finished'],1);self.assertEqual(result['pending'],2)
            self.assertEqual(json.loads((root/'episodes/key-0/status.json').read_text())['status'],'aborted_batch_wall_time')
    def test_elapsed_deadline_survives_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);script,m,p=self.setup_round(root,count=3)
            module.write(root/'runtime.json',{'started_at':0,'wall_time_limit':20})
            result=self.run_fixture(root,script,m,p)
            self.assertEqual(result['stop_reason'],'batch_wall_time')
            self.assertFalse((root/'launches.jsonl').exists())
    def test_frozen_change_fails_before_next_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'input';path.write_text('original')
            module.write(root/'freeze.json',{'files':{str(path):module.sha(path)}})
            path.write_text('changed')
            with self.assertRaisesRegex(RuntimeError,'Frozen input changed'):module.verify_frozen(root)

if __name__=='__main__':unittest.main()
