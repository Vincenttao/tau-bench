"""Explicit single-group DeepAgent runner; immutable evidence, no token budget."""
import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys
from skill_assets import project_root
sys.path.insert(0, str(project_root() / 'python'))
from eval_config import configure

p=argparse.ArgumentParser()
p.add_argument('--output', required=True)
p.add_argument('--task-ids', nargs='+', default=['task_001'])
p.add_argument('--execute', action='store_true')
a=p.parse_args()
root=project_root()
output=Path(a.output).resolve()
if output.exists(): raise SystemExit('Use a new output directory; existing evidence is immutable')
configure()
os.environ.update(TAU2_REPO=str(root/'.deps/tau2-bench'), TAU2_DATA_DIR=str(root/'.deps/tau2-bench/data'),
                  JAVA_AGENT_COMMAND='bash '+str(root/'java/run-deepagent.sh'),
                  LITELLM_LOCAL_MODEL_COST_MAP='True', JAVA_AGENT_EVENT_TIMEOUT='1500', JAVA_AGENT_COMPLETION_TIMEOUT='1200')
os.environ['PYTHONPATH']=os.pathsep.join([str(root/'.deps/tau2-bench/src'),str(root/'python'),os.getenv('PYTHONPATH','')])
if a.execute and not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
if a.execute and not os.getenv('OPENAI_API_KEY'): raise SystemExit('Missing API key')
command=[sys.executable,str(root/'python/full_run.py'),'--implementation','deepagent-todo-skill-mcp',
         '--output',str(output),'--task-ids',*a.task_ids,'--trials','1','--concurrency','1',
         '--episode-timeout','2400','--max-hours','72']
if a.execute: command.append('--execute')
raise SystemExit(subprocess.call(command))
