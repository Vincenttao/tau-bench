"""Actual native Runtime OTLP export probe; no bank model invocation."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from local_otlp_process import LocalOTLPProcess,ROOT
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--trace-source',type=Path,required=True);a=p.parse_args()
a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
with LocalOTLPProcess(a.output/'receiver','zero-model-startup-probe') as receiver:
 env={**os.environ,'JAVA_EVAL_OTEL_ENDPOINT':receiver.endpoint}
 result=subprocess.run([sys.executable,str(ROOT/'python/probe_enterprise_bootstrap.py'),'--output',str(a.output/'bootstrap'),'--trace-source',str(a.trace_source.resolve())],env=env,cwd=ROOT)
capture=a.output/'receiver/capture';file=capture/'spans.jsonl';spans=[json.loads(x) for x in file.read_text().splitlines()] if file.exists() else []
events=[json.loads(x) for x in (a.output/'bootstrap/runtime-events.jsonl').read_text().splitlines()] if (a.output/'bootstrap/runtime-events.jsonl').exists() else []
status=json.loads((capture/'status.json').read_text()) if (capture/'status.json').exists() else {}
observed=any(s['name']=='tau3.bootstrap_probe' for s in spans);enabled=any(e.get('event')=='otel_bootstrap_probe' and e.get('skill_observation_enabled') is True for e in events)
passed=result.returncode==0 and observed and enabled and status.get('secret_payloads_rejected')==0
report={'status':'passed' if passed else 'failed','native_runtime_otel_enabled':enabled,'actual_otlp_probe_span_received':observed,'received_span_records':len(spans),'gateway_model_calls':0,'secret_payloads_rejected':status.get('secret_payloads_rejected'),'scope':'Actual Runtime standard OTel provider/exporter and local protobuf receiver. The manual bootstrap span is not bank business coverage or P11 completion.'}
(a.output/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if passed else 1)
