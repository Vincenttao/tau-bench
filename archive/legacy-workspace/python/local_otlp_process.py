"""Run the OTLP parser in its own environment; baseline dependencies stay frozen."""
import json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LocalOTLPProcess:
 def __init__(self,directory,model_secret=''):
  self.root=Path(directory);self.secret=model_secret;self.proc=None
 def __enter__(self):
  self.root.mkdir(parents=True,exist_ok=False);self.ready=self.root/'ready.json';self.log=(self.root/'collector.log').open('w')
  interpreter=os.getenv('TAU3_OTEL_PYTHON','/tmp/tau3-otel-collector-venv/bin/python')
  env={**os.environ,'OPENAI_API_KEY':self.secret}
  self.proc=subprocess.Popen([interpreter,str(ROOT/'python/otlp_capture.py'),'--output',str(self.root/'capture'),'--ready-file',str(self.ready)],stdout=self.log,stderr=self.log,env=env,cwd=ROOT)
  deadline=time.monotonic()+10
  while time.monotonic()<deadline and self.proc.poll() is None and not self.ready.exists():time.sleep(.05)
  if not self.ready.exists():self.close();raise RuntimeError('Local OTLP receiver did not start; inspect '+str(self.root/'collector.log'))
  self.endpoint=json.loads(self.ready.read_text())['endpoint'];return self
 def close(self):
  if self.proc is not None and self.proc.poll() is None:
   self.proc.terminate()
   try:self.proc.wait(timeout=10)
   except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=5)
  self.log.close()
 def __exit__(self,*args):self.close()
