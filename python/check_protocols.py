"""P01/P03 protocol checks; no banking effects, credentials only in memory."""
import getpass,json,os,time
from pathlib import Path
from openai import OpenAI, APIStatusError
from eval_config import configure
model,base=configure()
key=os.getenv('OPENAI_API_KEY') or getpass.getpass('API key (not saved): ')
client=OpenAI(api_key=key,base_url=base,timeout=60,max_retries=0)
rows=[]
for name in ['tool_call','stream','official_judge']:
 row={'check':name,'started_at':time.time(),'requested_model':model if name!='official_judge' else 'gpt-4.1-2025-04-14'}
 try:
  if name=='tool_call':
   r=client.chat.completions.create(model=model,messages=[{'role':'user','content':'Call echo with text OK.'}],tools=[{'type':'function','function':{'name':'echo','parameters':{'type':'object','properties':{'text':{'type':'string'}},'required':['text'],'additionalProperties':False}}}],tool_choice={'type':'function','function':{'name':'echo'}},temperature=0)
   calls=r.choices[0].message.tool_calls or []
   row.update(passed=bool(calls) and calls[0].function.name=='echo' and json.loads(calls[0].function.arguments).get('text')=='OK',returned_model=r.model,usage=r.usage.model_dump() if r.usage else None)
  elif name=='stream':
   content='';usage=None;returned=None
   for chunk in client.chat.completions.create(model=model,messages=[{'role':'user','content':'Reply OK only.'}],temperature=0,stream=True,stream_options={'include_usage':True}):
    returned=chunk.model
    if chunk.usage:usage=chunk.usage.model_dump()
    if chunk.choices:content+=chunk.choices[0].delta.content or ''
   row.update(passed=bool(content.strip()),returned_model=returned,usage=usage)
  else:
   r=client.chat.completions.create(model='gpt-4.1-2025-04-14',messages=[{'role':'user','content':'Reply OK only.'}],max_tokens=16)
   row.update(passed=bool(r.choices[0].message.content),returned_model=r.model,usage=r.usage.model_dump() if r.usage else None)
 except APIStatusError as e:row.update(passed=False,http_status=e.status_code,error_type=type(e).__name__)
 except Exception as e:row.update(passed=False,error_type=type(e).__name__)
 row['finished_at']=time.time();rows.append(row)
 Path('runs/enterprise-v02-20261114/P01-P03-protocols.json').write_text(json.dumps(rows,indent=2))
 print(json.dumps(row),flush=True)
