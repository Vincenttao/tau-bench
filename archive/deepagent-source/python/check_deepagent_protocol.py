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
from skill_assets import project_root, skill_init_payload, skill_documents

p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--skill-version',default='3.0.0');p.add_argument('--language',choices=['en','zh'],default='en');p.add_argument('--prompt-version',choices=['baseline-v1','evidence-todo-v1'],default='evidence-todo-v1');args=p.parse_args()
os.environ['TAU3_SKILL_VERSION']=args.skill_version
documents=skill_documents()
dispute_guide=next((name for name in documents if name != 'SKILL.md' and ('# Card dispute handling' in documents[name] or '# 卡片交易争议处理' in documents[name])),None)
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
if dispute_guide:
 script.insert(2,('skill_tool',{'skill_name':'banking-mcp','relative_path':dispute_guide}))
if args.language == 'zh':
 for name, value in script:
  if name == 'ask_user':value['questions'][0]['question']='请确认是否写入模拟数值 8？'
 script[-1]=(None,'模拟操作已完成。')
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
 send({'type':'session_init','session_id':'protocol-fixture','language':args.language,'system_prompt_version':args.prompt_version,'domain_policy':'Synthetic test only. Confirm before writing.','tools':schema,'messages':[],'model':'fixture','workspace':str(workspace),**skill_init_payload(),'mcp_url':facade.url,'mcp_token':facade.token})
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
 assert any(x['event']=='tool_end' and x['data']['name']=='todo_modify' and ('Successfully updated' in str(x['data']['result']) or '成功' in str(x['data']['result'])) for x in records)
 assert any(x['event']=='language' and x['data']=={'benchmark_language':args.language,'core_language':'cn' if args.language=='zh' else 'en'} for x in records)
 assert any(x['event']=='system_prompt' and x['data']['version']==args.prompt_version and len(x['data']['sha256'])==64 for x in records)
 first_context=json.dumps(requests[0]['messages'])
 assert ('Business requirements and evidence-backed Todo:' in first_context)==(args.prompt_version=='evidence-todo-v1')
 if args.language=='zh':
  assert '模拟操作已完成' in final['content']
  assert '请确认' in question['content']
  assert 'Keep customer responses concise and in English' not in json.dumps(requests)
 assert any(x['event']=='tool_end' and x['data']['name']=='invoke_skill' and 'Invalid operation arguments' in str(x['data']['result']) for x in records)
 for name, content in skill_documents().items():
  assert (workspace/'skills/banking-mcp'/name).read_text()==content, name
 if dispute_guide:
  assert not any(('## Provisional credit' in json.dumps(r['messages']) or '## 临时贷记' in json.dumps(r['messages'],ensure_ascii=False)) for r in requests[:3])
  assert any(('## Provisional credit' in json.dumps(r['messages']) or '## 临时贷记' in json.dumps(r['messages'],ensure_ascii=False)) for r in requests[3:])
 assert any(x['event']=='tool_end' and x['data']['name']=='skill_tool' and ('## Provisional credit' in str(x['data']['result']) or '## 临时贷记' in str(x['data']['result'])) for x in records)
 (out/'model-requests.json').write_text(json.dumps(requests,indent=2))
 (out/'result.json').write_text(json.dumps({'status':'passed','skill_version':args.skill_version,'language':args.language,'system_prompt_version':args.prompt_version,'guide_loading':'on-demand' if dispute_guide else 'legacy-bundled','external_model_calls':0,'fixture_model_calls':len(requests),'question':question,'final':final,'checks':['native Todo visible','Skill-only boundary','MCP initialize','MCP tools/call','official queue roundtrip','ask_user interrupt/resume','Todo completion','same conversation','Skill assets deployed byte-for-byte; dispute content observed in model context','benchmark language mapped to Core language','selected system prompt reaches model']},indent=2))
 print('PASS deterministic DeepAgent + Todo + Skill + real MCP + interrupt/resume:',out)
finally:
 if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 facade.close();server.shutdown();server.server_close();log.close()
