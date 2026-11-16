"""Real enterprise ready handshake and JVM identity; no user/business input."""
import argparse,json,os,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
os.environ.update(OPENAI_API_KEY='local-identity-probe-only',OPENAI_BASE_URL='http://127.0.0.1:9/v1',OPENAI_MODEL='deepseek-v4-flash',JAVA_LOG_DIR=str(a.output/'java'),JAVA_AGENT_COMMAND='bash '+str(ROOT/'enterprise-java/run.sh'),LITELLM_LOCAL_MODEL_COST_MAP='True')
os.environ.pop('JAVA_EVAL_OTEL_ENDPOINT',None)
from enterprise_java_agent import EnterpriseJavaAgent
from process_tree import identity
from enterprise_run import drain_registered_jvm
agent=EnterpriseJavaAgent(tools=[],domain_policy='Initialization-only identity probe. No bank operation is requested.',llm='openai/deepseek-v4-flash',llm_args={})
passed=False;report={}
try:
 agent._start(SimpleNamespace(system_messages=[],messages=[]))
 info=json.loads((a.output/'java/java-process.json').read_text());current=identity(agent.proc.pid)
 passed=info['pid']==agent.proc.pid and current is not None and info['start_ticks']==current[0] and bool(info['boot_id'])
 agent._send({'type':'close'});agent.proc.wait(timeout=20)
 drain=drain_registered_jvm(a.output)
 report={'status':'passed' if passed and drain['state']=='terminal' else 'failed','actual_jvm_identity_registered':passed,'shutdown':drain,'gateway_model_calls':0,'scope':'Actual Runtime readiness/PID/boot identity and normal shutdown only; no bank Task or user/model input'}
finally:
 if agent.proc is not None and agent.proc.poll() is None:agent.proc.terminate();agent.proc.wait(timeout=15)
 time.sleep(.05)
 for name in ['trace','log']:
  stream=getattr(agent,name,None)
  if stream:stream.close()
 if agent.proc is not None:
  agent.proc.stdin.close();agent.proc.stdout.close()
if sum(log.read_text(errors='replace').count('event=react_model_call_started') for log in (a.output/'java').glob('*.stderr.log')):report['status']='failed'
(a.output/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report.get('status')=='passed' else 1)
