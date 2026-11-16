"""Wait for this exact controller, then collect and diagnose without any model calls."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.deps/tau2-bench').exists())
sys.path.insert(0,str(ROOT/'python'))
from process_tree import identity

p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
run=a.run.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
controller=json.loads((run/'controller.json').read_text());pid=controller['pid'];expected=controller['process_identity']
if expected is None:raise SystemExit('No controller process identity')
while True:
    current=identity(pid)
    if current is None or current[0]!=expected[0] or current[1]=='Z':break
    time.sleep(5)
state=json.loads((run/'progress.json').read_text())
if state['state'] not in ('completed','stopped'):raise SystemExit('Controller disappeared without terminal status; manual audit required')
env={**os.environ,'PYTHONPATH':os.pathsep.join([str(ROOT/'python'),str(ROOT/'.deps/tau2-bench/src')]),
     'TAU2_DATA_DIR':str(ROOT/'.deps/tau2-bench/data'),'LITELLM_LOCAL_MODEL_COST_MAP':'True'}
commands=[
 [sys.executable,str(ROOT/'python/collect_deepagent.py'),str(run)],
 [sys.executable,str(ROOT/'python/analyze_v2.py'),str(run)],
 [sys.executable,str(ROOT/'python/diagnose_state_failures.py'),str(run)],
 [sys.executable,str(Path(__file__).with_name('report_round.py')),str(run),'--output',str(out)]]
try:
    with (out/'postprocess.log').open('a') as log:
        for command in commands:
            subprocess.run(command,env=env,cwd=ROOT,stdout=log,stderr=log,check=True)
    (out/'postprocess-status.json').write_text(json.dumps({'status':'completed','controller_state':state['state'],'finished_at':time.time(),'model_calls':0},indent=2)+'\n')
    print('Post-run collection and strict diagnostics completed:',out,flush=True)
except Exception as error:
    (out/'postprocess-status.json').write_text(json.dumps({'status':'failed','error_type':type(error).__name__,'message':str(error),'model_calls':0},indent=2)+'\n')
    raise
