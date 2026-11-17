"""One short authorized model request after a transport failure; separate evidence."""
import argparse,getpass,json,time,urllib.error,urllib.request
from pathlib import Path
from eval_config import GATEWAY,MODEL
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Use a new preflight evidence file')
key=getpass.getpass('API key (not saved): ')
if not key:raise SystemExit('Missing key')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':'Reply only OK.'}],'temperature':0,'max_tokens':32}).encode()
record={'kind':'network_recovery_preflight','benchmark_episode':False,'model_requested':MODEL,'recorded_at':time.time(),'usage':None}
started=time.monotonic()
try:
 request=urllib.request.Request(GATEWAY+'/chat/completions',data=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.build_opener(NoRedirect).open(request,timeout=120) as response:
  result=json.load(response);record.update(status='transport_ready',http_status=response.status,returned_model=result.get('model'),usage=result.get('usage'),finish_reasons=[x.get('finish_reason') for x in result.get('choices',[])],request_id=response.headers.get('x-request-id'),nonempty_assistant_message=any((x.get('message') or {}).get('content') or (x.get('message') or {}).get('tool_calls') for x in result.get('choices',[])))
except Exception as error:
 record.update(status='failed',error_type=type(error).__name__,http_status=error.code if isinstance(error,urllib.error.HTTPError) else None)
record['elapsed_seconds']=time.monotonic()-started
a.output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record,ensure_ascii=False));raise SystemExit(0 if record['status']=='transport_ready' else 1)
