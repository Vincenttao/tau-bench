"""Deterministic real-Java / real-MCP fixture; synthetic model and business data only."""
import argparse
import json
import os
import queue
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from benchmark_mcp import BenchmarkMcpFacade
from skill_assets import project_root, bundled_skill_document

p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
root=project_root();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
events=queue.Queue();requests=[]
schema=[{'function':{'name':'write_fixture','description':'Write a synthetic value after customer confirmation.','parameters':{'type':'object','properties':{'amount':{'type':'number'}},'required':['amount']}}}]
script=[
 ('skill_tool',{'skill_name':'banking-mcp'}),
 ('skill_tool',{'skill_name':'banking-mcp','relative_path':'operations.json'}),
 ('todo_create',{'tasks':[{'id':'fixture','content':'Confirm customer input and execute fixture','activeForm':'Executing fixture','description':'Synthetic integration check'}]}),
 ('ask_user',{'questions':[{'header':'Confirm','question':'Confirm the synthetic value 8?','options':[{'label':'Yes','description':'Proceed'},{'label':'No','description':'Stop'}]}]}),
 ('invoke_skill',{'skill_id':'banking-mcp','operation':'write_fixture','arguments':{'amount':'invalid'}}),
 ('invoke_skill',{'skill_id':'banking-mcp','operation':'write_fixture','arguments':{'amount':8}}),
 ('todo_modify',{'action':'update','todos':[{'id':'fixture','status':'completed'}]}),
 (None,'Synthetic operation completed.')]
class ModelHandler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  request=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append(request)
  i=len(requests)-1
  if i>=len(script):
   name,arguments=None,'Synthetic operation completed.'
  else:name,arguments=script[i]
  available={t['function']['name'] for t in request.get('tools',[])}
  assert available <= {'skill_tool','list_skill','invoke_skill','ask_user','todo_create','todo_modify','todo_get','todo_list'}, available
  assert {'todo_create','todo_modify','invoke_skill'} <= available, available
  msg={'role':'assistant','content':arguments if name is None else ''}
  if name:msg['tool_calls']=[{'id':'model-'+str(i),'type':'function','function':{'name':name,'arguments':json.dumps(arguments)}}]
  if name: msg['tool_calls'][0]['index']=0
  chunk={'id':'fixture-'+str(i),'object':'chat.completion.chunk','created':1,'model':'fixture','choices':[{'index':0,'delta':msg,'finish_reason':'tool_calls' if name else 'stop'}],'usage':{'prompt_tokens':10,'completion_tokens':3,'total_tokens':13}}
  body=('data: '+json.dumps(chunk)+'\n\ndata: [DONE]\n\n').encode()
  self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
server=ThreadingHTTPServer(('127.0.0.1',0),ModelHandler);threading.Thread(target=server.serve_forever,daemon=True).start()
facade=BenchmarkMcpFacade(schema,'protocol-fixture',events,out/'mcp')
log=(out/'java.stderr.log').open('w')
env={**os.environ,'OPENAI_API_KEY':'synthetic-local-key','OPENAI_BASE_URL':'http://127.0.0.1:%d/v1'%server.server_port}
proc=subprocess.Popen(['bash',str(root/'java/run-deepagent.sh')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,env=env)
def reader():
 for line in proc.stdout:
  if line.startswith('TAU2_JSON:'):events.put(json.loads(line[len('TAU2_JSON:'):]))
 events.put({'type':'error','error':'Java stdout closed'})
threading.Thread(target=reader,daemon=True).start()
def send(value):proc.stdin.write(json.dumps(value)+'\n');proc.stdin.flush()
try:
 workspace=out/'workspace';workspace.mkdir()
 send({'type':'session_init','session_id':'protocol-fixture','domain_policy':'Synthetic test only. Confirm before writing.','tools':schema,'messages':[],'model':'fixture','workspace':str(workspace),'skill_document':bundled_skill_document(),'mcp_url':facade.url,'mcp_token':facade.token})
 ready=events.get(timeout=60);assert ready['type']=='ready',ready
 send({'type':'user','content':'Please write synthetic value 8 after confirmation.'})
 question=events.get(timeout=60);assert question['type']=='content' and question['waiting'],question
 send({'type':'user','content':'Yes, confirmed.'})
 call=events.get(timeout=60);assert call['type']=='tool_calls',call
 assert call['tool_calls'][0]['arguments']=={'amount':8},call
 facade.deliver(call['tool_calls'][0]['id'],'{"written":8}',False)
 final=events.get(timeout=60);assert final['type']=='content' and not final['waiting'],final
 send({'type':'close'});proc.wait(timeout=15);assert proc.returncode==0
 records=[json.loads(s) for s in (workspace/'deepagent-events.jsonl').read_text().splitlines()]
 assert any(x['event']=='tool_end' and x['data']['name']=='todo_modify' and 'Successfully updated' in str(x['data']['result']) for x in records)
 assert any(x['event']=='tool_end' and x['data']['name']=='invoke_skill' and 'Invalid operation arguments' in str(x['data']['result']) for x in records)
 assert any('Bundled business guide: dispute-processing' in json.dumps(r['messages']) for r in requests)
 (out/'model-requests.json').write_text(json.dumps(requests,indent=2))
 (out/'result.json').write_text(json.dumps({'status':'passed','external_model_calls':0,'fixture_model_calls':len(requests),'question':question,'final':final,'checks':['native Todo visible','Skill-only boundary','MCP initialize','MCP tools/call','official queue roundtrip','ask_user interrupt/resume','Todo completion','same conversation','bundled dispute guide in actual model request']},indent=2))
 print('PASS deterministic DeepAgent + Todo + Skill + real MCP + interrupt/resume:',out)
finally:
 if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 facade.close();server.shutdown();server.server_close();log.close()
