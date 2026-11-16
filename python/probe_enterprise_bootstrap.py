"""Actual Runtime/MOA boot check. Model route is deliberately local and unavailable."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--trace-source',type=Path,required=True);a=p.parse_args()
with a.trace_source.open() as source:row=json.loads(source.readline())
init=row['data']
if row['direction']!='to_java' or init['type']!='session_init':raise ValueError('Expected recorded official session initialization only')
a.output.mkdir(parents=True,exist_ok=False)
env={**os.environ,'OPENAI_API_KEY':'zero-model-startup-probe','OPENAI_BASE_URL':'http://127.0.0.1:9/v1','JAVA_LOG_DIR':str(a.output.resolve()),'JAVA_AGENT_COMPLETION_TIMEOUT':'1200','JAVA_AGENT_MAIN_COMPLETION_TIMEOUT':'1500'}
files=[*sorted((ROOT/'enterprise-java/src').rglob('*.java')),*sorted((ROOT/'enterprise-java/target/classes').rglob('*.class')),*sorted((ROOT/'java/target/classes').rglob('*.class')),ROOT/'python/probe_enterprise_bootstrap.py',ROOT/'java/classpath.txt']
files += [Path(name) for name in (ROOT/'java/classpath.txt').read_text().strip().split(os.pathsep)]
def fingerprints():return {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
before=fingerprints()
(a.output/'evidence-manifest.json').write_text(json.dumps({'sha256_before_boot':before,'actual_model_route':'http://127.0.0.1:9/v1','scope':'Compiled artifact/source fingerprint; startup/protocol only'},ensure_ascii=False,indent=2)+'\n')
with (a.output/'process.log').open('w') as log,(a.output/'protocol.stdout.log').open('w') as protocol:
 result=subprocess.run(['bash',str(ROOT/'enterprise-java/run.sh'),'--startup-probe'],input=json.dumps(init)+'\n',text=True,stdout=protocol,stderr=log,env=env,timeout=90,cwd=ROOT)
log=(a.output/'process.log').read_text(errors='replace')
protocol=(a.output/'protocol.stdout.log').read_text()
frames=[json.loads(line.removeprefix('TAU2_JSON:')) for line in protocol.splitlines() if line.startswith('TAU2_JSON:')]
calls=log.count('event=react_model_call_started')
events=[json.loads(line) for line in (a.output/'runtime-events.jsonl').read_text().splitlines()] if (a.output/'runtime-events.jsonl').exists() else []
unchanged=before==fingerprints()
event_metadata=bool(events) and len({e.get('boot_id') for e in events})==1 and all(e.get('boot_id') and isinstance(e.get('recorded_at_epoch_millis'),int) and isinstance(e.get('monotonic_nanos'),int) for e in events) and [e.get('event_sequence') for e in events]==list(range(1,len(events)+1))
passed=result.returncode==0 and calls==0 and unchanged and event_metadata and any(x['type']=='probe_pass' for x in frames) and any(x['event']=='runtime_main_customized' for x in events) and any(x['event']=='runtime_ready' for x in events)
status={'status':'passed' if passed else 'failed','exit_code':result.returncode,'startup_only':True,'protocol_stdout_verified':bool(frames),'artifacts_unchanged_during_probe':unchanged,'event_identity_and_time_fields_verified':event_metadata,'runtime_model_call_events':calls,'model_route':'http://127.0.0.1:9/v1 deliberately unavailable','official_reward':None,'scope':'Real Runtime/MOA MAIN/local-delegate assembly, local HTTP Agent Card and framed stdout only; no bank business execution or recovery proof'}
(a.output/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(status,ensure_ascii=False));raise SystemExit(0 if passed else 1)
