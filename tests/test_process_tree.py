import json,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from process_tree import identity,terminate_tree
class ProcessTreeTest(unittest.TestCase):
 def test_detached_resistant_child_is_stopped(self):
  with tempfile.TemporaryDirectory() as tmp:
   child=Path(tmp)/'child.py';child.write_text('import signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\nprint("ready",flush=True)\ntime.sleep(60)\n')
   script='import subprocess,sys,time\np=subprocess.Popen([sys.executable,sys.argv[1]],start_new_session=True,stdout=subprocess.PIPE,text=True)\np.stdout.readline()\nprint(p.pid,flush=True)\ntime.sleep(60)\n'
   proc=subprocess.Popen([sys.executable,'-c',script,str(child)],start_new_session=True,stdout=subprocess.PIPE,text=True)
   child_pid=int(proc.stdout.readline());before=identity(child_pid)
   try:
    terminate_tree(proc,grace_seconds=.15)
    self.assertIsNotNone(proc.poll())
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
     current=identity(child_pid)
     if current is None or current[1]=='Z':break
     time.sleep(.05)
    after=identity(child_pid);self.assertTrue(after is None or after[1]=='Z' or after[0]!=before[0])
   finally:
    if proc.poll() is None:terminate_tree(proc,grace_seconds=.1)
    proc.stdout.close()
if __name__=='__main__':unittest.main()
