"""Local exact-JSON capture/replay transport. Replay never has an upstream route."""
import contextlib,hashlib,json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from eval_config import GATEWAY,MODEL

def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(body):return json.dumps(json.loads(body),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

@contextlib.contextmanager
def live_forward(body,key):
    import httpx
    with httpx.Client(trust_env=False,timeout=httpx.Timeout(300,connect=30)) as client:
        with client.stream('POST',GATEWAY+'/chat/completions',content=body,
                           headers={'Content-Type':'application/json','Authorization':'Bearer '+key,'Accept-Encoding':'identity'}) as response:
            headers={k:v for k,v in response.headers.items() if k.lower() in {'content-type','content-encoding'}}
            yield response.status_code,headers,response.iter_raw()

class Transcript:
    def __init__(self,directory,mode,secret):
        if mode not in {'capture','replay'}:raise ValueError('Unknown transcript mode')
        if not secret:raise ValueError('Local client authentication required')
        self.root=Path(directory);self.mode=mode;self.secret=secret;self.lock=threading.Lock()
        self.position=0;self.failed=False;self.failure=None;self.gateway_calls=0
        if mode=='capture':
            self.root.mkdir(parents=True,exist_ok=False)
            self.metadata={'schema':1,'mode':'capture','state':'OPEN','model':MODEL,'upstream':GATEWAY,'request_match':'exact JSON values and order of arrays; JSON object key order ignored; no ignored fields','entries':[]}
            self.write_manifest()
        else:
            self.metadata=json.loads((self.root/'transcript.json').read_text())
            if self.metadata.get('state')!='SEALED':raise ValueError('Only a complete sealed transcript may be replayed')
            if not self.metadata.get('entries'):raise ValueError('Empty transcript cannot prove replay')
            for entry in self.metadata['entries']:
                for field in ['request','response']:
                    data=(self.root/entry[field]['file']).read_bytes()
                    if digest(data)!=entry[field]['sha256']:raise ValueError('Transcript integrity failure: '+field)

    def write_manifest(self):
        tmp=self.root/'transcript.tmp';tmp.write_text(json.dumps(self.metadata,ensure_ascii=False,indent=2)+'\n');tmp.replace(self.root/'transcript.json')

    def fail(self,reason):
        with self.lock:
            self.failed=True;self.failure=self.failure or reason.replace(self.secret,'[REDACTED]')
            if self.mode=='capture':
                self.metadata['state']='FAILED';self.metadata['failure']=self.failure;self.write_manifest()

    def begin(self,body):
        clean=canonical(body)
        if self.secret.encode() in clean:raise ValueError('Credential found in request body; refusing transcript storage')
        if json.loads(body).get('model')!=MODEL:raise ValueError('Unapproved model in capture/replay request')
        with self.lock:
            if self.failed:raise ValueError('Replay/capture has already failed')
            index=self.position
            if self.mode=='replay':
                entries=self.metadata['entries']
                if index>=len(entries) or digest(clean)!=entries[index]['request']['sha256']:
                    self.failed=True
                    self.failure='strict_request_mismatch_at_index_'+str(index)
                    raise ValueError(self.failure)
            else:
                name=f'{index:06d}.request.json';(self.root/name).write_bytes(clean)
                self.metadata['entries'].append({'index':index,'request':{'file':name,'sha256':digest(clean)},'response':None})
                self.gateway_calls+=1;self.write_manifest()
            self.position+=1
            return index

    def complete(self,index,status,headers,payload):
        if self.secret.encode() in payload:raise ValueError('Credential found in upstream body; refusing transcript storage')
        with self.lock:
            name=f'{index:06d}.response.bin';(self.root/name).write_bytes(payload)
            self.metadata['entries'][index]['response']={'file':name,'sha256':digest(payload),'status':status,'headers':headers,'bytes':len(payload)}
            if status!=200:self.failed=True;self.failure='upstream_http_'+str(status)
            self.write_manifest()

    def seal(self):
        with self.lock:
            entries=self.metadata['entries']
            if self.mode!='capture' or self.failed or not entries or any(e['response'] is None for e in entries):raise ValueError('Cannot seal incomplete or failed capture')
            self.metadata['state']='SEALED';self.metadata['upstream_request_attempt_count']=self.gateway_calls;self.write_manifest()

    def replay_response(self,index):
        if self.mode!='replay':raise ValueError('Not a replay store')
        entry=self.metadata['entries'][index]['response']
        return entry['status'],entry['headers'],(self.root/entry['file']).read_bytes()

    def verdict(self):
        return {'mode':self.mode,'requests_consumed':self.position,'expected_requests':len(self.metadata['entries']),
                'strict_match_complete':self.mode=='replay' and not self.failed and self.position==len(self.metadata['entries']),
                'failed':self.failed,'failure':self.failure,'real_gateway_call_count':None if self.mode=='capture' else 0,'upstream_request_attempt_count':self.gateway_calls,
                'usage_note':'Replay response usage is historical; it is not new model Token consumption.'}

class LocalGateway:
    def __init__(self,transcript,forwarder=live_forward):
        self.transcript=transcript
        # The replay branch does not receive or invoke an upstream client.
        self.forwarder=forwarder if transcript.mode=='capture' else None
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                if self.path!='/v1/chat/completions':self.send_error(404);return
                if self.headers.get('Authorization')!='Bearer '+owner.transcript.secret:self.send_error(403);return
                headers_sent=False
                try:
                    length=int(self.headers.get('Content-Length','0'))
                    if length<=0:raise ValueError('Empty request')
                    body=self.rfile.read(length);index=owner.transcript.begin(body)
                    if owner.transcript.mode=='replay':
                        status,headers,payload=owner.transcript.replay_response(index)
                        self.send_response(status)
                        for k,v in headers.items():self.send_header(k,v)
                        self.send_header('Content-Length',str(len(payload)));self.end_headers();headers_sent=True;self.wfile.write(payload);self.wfile.flush()
                    else:
                        with owner.forwarder(body,owner.transcript.secret) as (status,headers,chunks):
                            self.send_response(status)
                            for k,v in headers.items():self.send_header(k,v)
                            self.send_header('Connection','close');self.end_headers();headers_sent=True;parts=[]
                            for chunk in chunks:
                                parts.append(chunk);self.wfile.write(chunk);self.wfile.flush()
                            owner.transcript.complete(index,status,headers,b''.join(parts))
                except Exception as error:
                    owner.transcript.fail(str(error))
                    if headers_sent:self.close_connection=True;return
                    try:
                        self.send_response(409);self.send_header('Content-Type','application/json');self.end_headers()
                        self.wfile.write(json.dumps({'error':{'message':'Strict transcript failure; inspect local verdict','type':'replay_failure'}}).encode())
                    except (BrokenPipeError,ConnectionResetError):pass
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.base_url='http://127.0.0.1:'+str(self.server.server_address[1])+'/v1'
    def __enter__(self):self.thread.start();return self
    def __exit__(self,*args):self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)
