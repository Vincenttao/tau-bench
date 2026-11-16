import ast,os,signal,subprocess,json
from pathlib import Path
module=ast.parse(Path('python/full_run.py').read_text())
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='terminate')
namespace={'os':os,'signal':signal,'subprocess':subprocess}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-terminate','exec'),namespace)
results=[]
for resistant in (False,True):
 script='import time,signal;'+('signal.signal(signal.SIGTERM,signal.SIG_IGN);' if resistant else '')+'print("ready",flush=True);time.sleep(60)'
 p=subprocess.Popen(['python','-c',script],start_new_session=True,stdout=subprocess.PIPE,text=True)
 assert p.stdout.readline().strip()=='ready'
 namespace['terminate'](p)
 assert p.poll() is not None
 results.append({'ignores_sigterm':resistant,'returncode':p.returncode,'passed':True})
Path('runs/enterprise-v02-20261114/P02-process-termination.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
