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

p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--skill-version',default='banking-evidence-guides');p.add_argument('--language',choices=['en','zh'],default='en');p.add_argument('--prompt-version',choices=['baseline-v1','evidence-todo-v1'],default='evidence-todo-v1');p.add_argument('--restart-executor',action='store_true');p.add_argument('--read-before-wait',action='store_true');p.add_argument('--restart-controls',action='store_true')
p.add_argument('--reject-first-question', action='store_true');args=p.parse_args()
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
if args.reject_first_question:
 index=next(i for i,item in enumerate(script) if item[0]=='ask_user')
 revised=json.loads(json.dumps(script[index][1]))
 revised['questions'][0]['question']='Please confirm the synthetic value 8 before proceeding?'
 script.insert(index+1,('ask_user',revised))
if args.read_before_wait:
 script.insert(0,('invoke_skill',{'skill_id':'banking-mcp','operation':'read_fixture','arguments':{}}))
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

server=ThreadingHTTPServer(('127.0.0.1',0),ModelHandler)
threading.Thread(target=server.serve_forever,daemon=True).start()
from unittest.mock import patch
from tau2.environment.tool import Tool
from tau2.data_model.message import UserMessage, ToolMessage
from full_hub_agent import FullHubAgent
from controlled_effects import digest

class FakePlanner:
 def __init__(self,task,*args):self.task=task
 def complete(self,purpose,state,schema):
  import time
  self.task.call('charge',now=int(time.time()),kind='execution')
  if purpose=='response-review':return {'completed_goal_ids':([g['goal_id'] for g in state['visible_state']['task']['goals']] if 'completed' in state['candidate_response'] else []),'comparison':None,
    'claims':[{'quote':state['candidate_response'],'kind':'operation','evidence_refs':[ref for ref, record in state['visible_state']['evidence'].items() if record['source']=='official-tool']}] if 'completed' in state['candidate_response'] else []}
  if purpose=='new-goals':
   return {'goals':[] if state['task']['goals'] else [{'description':'write synthetic value 8 after confirmation','quote':state['content']}],
     'existing_routes':[{'goal_id':goal['goal_id'],'action':'respond' if goal['waiting_for'] else 'context','quote':state['content']} for goal in state['task']['goals']]}
  goal=state.get('goal') or next(g for g in state['task']['goals'] if g['state']=='active')
  return {'goal_id':goal['goal_id'],'status':'proposed','policy_refs':[ref for ref, record in state['evidence'].items() if record['source'] in ('official-policy','published-skill')],
          'conditions':[{'id':'fixture_result' if purpose=='goal-completion' else 'fixture_consent',
           'statement':'Synthetic value 8 was written.' if purpose=='goal-completion' else 'Customer confirmed synthetic value 8.',
           'evidence_refs':list(state['evidence'])}]}

class FakeJev:
 def __init__(self,*args,**kwargs):pass
 def ask(self,request):
  answers={}
  for name in request['questions']:
   yes=True
   if name in ['ambiguous','no_business','comparison_needed'] or name.endswith('_violated'):yes=False
   if 'has_new' in request['questions']:
    yes=name in ['covered'] or (name=='has_new' and bool(request['state']['new_goal_proposals'])) or name.startswith(('new','route'))
    if name.endswith('_respond'):yes=bool(request['state']['last_question'])
   answers[name]=({'type':'choice','choice':'pause','probabilities':{'cancel':.005,'pause':.99,'resume':.005}} if request['questions'][name]['type']=='choice' else {'type':'noul','noul':.99 if yes else .01})
  return {'model':'jev-1.14.0','answers':answers,'usage':{'input_tokens':1,'output_tokens':1}}

def write_fixture(amount:float)->str:
 """Write a synthetic value after customer confirmation.

 Args:
     amount: Synthetic value.
 """
 return json.dumps({'written':amount})

def read_fixture()->str:
 """Read a synthetic marker."""
 return '{"read":true}'

os.environ.update(OPENAI_API_KEY='synthetic-only',TYPESAFE_API_KEY='synthetic-only',OPENAI_MODEL='fixture',
 OPENAI_BASE_URL='http://127.0.0.1:%d/v1'%server.server_port,JAVA_LOG_DIR=str(out/'java'))
agent=None
try:
 with patch('full_hub_agent.PlannerClient',FakePlanner),patch('full_hub_agent.JevClient',FakeJev):
  # This fixture injects operation/receipt contracts after assembly. It validates
  # native wiring, while test_control_replay uses a frozen catalog end to end.
  agent=FullHubAgent(tools=[Tool(write_fixture),Tool(read_fixture)],domain_policy='Synthetic test only. Confirm before writing.',llm='fixture',capture_replay=False)
 agent.controller.catalog={'write_fixture':{'access':'write','principal':'fixture-agent'},'read_fixture':{'access':'read','principal':'shared-read'}}
 agent.controller.effects.catalog=agent.controller.catalog
 agent.controller.receipt_contracts={'write_fixture':lambda content,args:{'status':'succeeded'} if json.loads(content)=={'written':args['amount']} else {'status':'unknown'}}
 if args.reject_first_question:
  original_response=agent.controller.response;rejected=[False]
  def reject_unpublished_once(content,*,waiting,now):
   if waiting and not rejected[0]:
    rejected[0]=True
    return {'status':'deny','reason':'synthetic-unpublished-question'}
   return original_response(content,waiting=waiting,now=now)
  agent.controller.response=reject_unpublished_once
 state=agent.get_init_state()
 question,state=agent.generate_next_message(UserMessage(role='user',content='Please write synthetic value 8 after confirmation.'),state)
 first_call_id=None
 if args.read_before_wait:
  assert question.tool_calls and question.tool_calls[0].name=='read_fixture',question
  first_call_id=question.tool_calls[0].id
  question,state=agent.generate_next_message(ToolMessage(role='tool',id=first_call_id,name='read_fixture',content=read_fixture(),error=False),state)
 assert question.content and not question.tool_calls,question
 if args.reject_first_question:
  assert 'Please confirm the synthetic value 8 before proceeding?' in question.content,question
 if args.restart_controls:
  before=agent.task.call('status',now=int(__import__('time').time()))
  agent.restart_controls()
  after=agent.task.call('status',now=int(__import__('time').time()))
  assert all(before[key]==after[key] for key in ('episode_id','revision','calls','deadline','resumes','goals','nodes')),'Control restart lost state or reset budget'
 if args.restart_executor:agent.restart_executor(state)
 call,state=agent.generate_next_message(UserMessage(role='user',content='Yes, confirmed.'),state)
 assert call.tool_calls and call.tool_calls[0].arguments=={'amount':8},call
 if first_call_id:assert call.tool_calls[0].id!=first_call_id,'Restart reused a previous invocation ID'
 receipt=write_fixture(**call.tool_calls[0].arguments)
 final,state=agent.generate_next_message(ToolMessage(role='tool',id=call.tool_calls[0].id,name='write_fixture',content=receipt,error=False),state)
 assert final.content=='Synthetic operation completed.',final
 assert str(out) not in json.dumps(requests), 'Local episode path leaked into native model messages'
 if args.reject_first_question:
  rejection_messages=[m for req in requests for m in req.get('messages',[]) if 'QUESTION_NOT_PUBLISHED' in str(m.get('content',''))]
  assert rejection_messages,'Controller rejection did not reach the executor'
  assert all(m['role']=='tool' and 'User has answered your questions:' not in str(m.get('content','')) for m in rejection_messages),'Controller review became a customer answer'
 final_task=agent.task.call('status',now=int(__import__('time').time()))
 assert final_task['outcome']=='success',final_task
 assert len(final_task['nodes'])==(4 if args.read_before_wait else 3) and all(n['status']=='completed' for n in final_task['nodes']),final_task
 ledger=[json.loads(line) for line in (agent.control_root/'ledger.jsonl').read_text().splitlines()]
 assert sum(row['outcome']['status']=='dispatched' for row in ledger)==(4 if args.read_before_wait else 3)
 assert list((agent.workspace/'checkpoints').parent.glob('checkpoints*'))
 result={'status':'passed','scope':'real native Java DeepAgent + persistent task + real MCP + real Go; scripted S2 proposals/Jev + synthetic effect',
  'external_model_calls':0,'native_fixture_calls':len(requests),'official_business_score':None,
  'task':final_task,'checks':['per-turn input interpretation','native model budget callback','ask_user waiting/resume','Go dispatch','receipt correlation','goal acceptance','persistent framework checkpoint']}
 if args.reject_first_question:result['checks'].append('controller rejection remains tool error; real user reply alone resumes as answer')
 (out/'result.json').write_text(json.dumps(result,indent=2))
 print('PASS complete controlled native fixture:',out)
finally:
 if agent:agent.close()
 from java_agent import cleanup
 cleanup()
 from deepagent_java_agent import close_facades
 close_facades()
 server.shutdown();server.server_close()
