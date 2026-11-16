"""Single banking episode, interactive secret input, isolated output directory."""
import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from eval_config import configure
configure()
parser=argparse.ArgumentParser()
parser.add_argument('--task-id',default='task_001')
parser.add_argument('--output',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
os.environ.setdefault('TAU2_REPO',str(root/'.deps/tau2-bench'))
os.environ.setdefault('TAU2_DATA_DIR',str(Path(os.environ['TAU2_REPO'])/'data'))
os.environ.setdefault('JAVA_AGENT_COMMAND','bash '+str(root/'java/run.sh'))
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP','True')
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
if not os.environ['OPENAI_API_KEY']:sys.exit('Missing key')
output=args.output or root/'runs'/('smoke-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
if output.exists():sys.exit('Existing evidence directory; use a new attempt: '+str(output))
code=subprocess.call([sys.executable,str(root/'python/full_run.py'),'--output',str(output),'--task-ids',args.task_id,'--trials','1','--concurrency','1','--max-hours','1','--episode-timeout','1800','--execute'])
if (output/'manifest.json').exists():
    subprocess.run([sys.executable,str(root/'python/analyze_v2.py'),str(output)],check=False)
if (output/'manifest.json').exists():
    subprocess.run([sys.executable,str(root/'python/collect_metrics_v02.py'),str(output)],check=True)
print('Evidence directory:',output)
sys.exit(code)
