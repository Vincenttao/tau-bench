"""Small Chat Completions connectivity check; never prints credentials or raw errors."""
import getpass
import json
import os
import sys
import urllib.request
import urllib.error
from eval_config import configure
model, base = configure()
key = os.getenv('OPENAI_API_KEY') or getpass.getpass('API key (not saved): ')
if not key:
    sys.exit('Missing API key')
body = {'model': model, 'messages': [{'role':'user','content':'Reply with OK only.'}], 'temperature':0, 'max_tokens':64}
request = urllib.request.Request(base+'/chat/completions', data=json.dumps(body).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        data=json.load(response)
    choices=data.get('choices') or []
    if not choices or not isinstance(choices[0].get('message'),dict):
        sys.exit('Invalid Chat Completions response: missing message')
    print(json.dumps({'status':'connected','requested_model':model,'returned_model':data.get('model'),'has_content':bool(choices[0]['message'].get('content')),'finish_reason':choices[0].get('finish_reason'),'usage':data.get('usage')},ensure_ascii=False))
except urllib.error.HTTPError as exc:
    sys.exit('Gateway HTTP error: '+str(exc.code))
except (urllib.error.URLError, TimeoutError):
    sys.exit('Gateway unreachable: check DNS, network and proxy')
