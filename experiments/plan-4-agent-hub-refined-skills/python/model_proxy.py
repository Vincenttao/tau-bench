"""Private loopback model transport: freeze actual response identity before delivery.

The native executor receives only an episode-local token. Real upstream credentials
stay in this Python process. No retry, arbitrary forwarding or silent model drift.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import threading
import urllib.request
from urllib.error import HTTPError
import uuid

from jev_provider import NoRedirect
from task_session import durable_json


def inspect_response(body, content_type):
    if content_type.startswith('text/event-stream'):
        packets = [json.loads(line[5:].strip()) for line in body.decode().splitlines()
                   if line.startswith('data:') and line[5:].strip() not in ('', '[DONE]')]
    else: packets = [json.loads(body)]
    models = {packet['model'] for packet in packets if isinstance(packet.get('model'), str) and packet['model']}
    if len(models) != 1: raise ValueError('Missing or inconsistent actual model identity')
    usage = next((packet['usage'] for packet in reversed(packets) if packet.get('usage')), {})
    return {'actual_model': next(iter(models)), 'usage': usage}


class ModelProxy:
    def __init__(self, directory, base, key, model):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.pin_path=self.directory/'actual-model.json'
        self.actual_model=json.loads(self.pin_path.read_text())['actual_model'] if self.pin_path.exists() else None
        self.token=secrets.token_urlsafe(32)
        self.lock=threading.Lock()
        proxy=self
        opener=urllib.request.build_opener(NoRedirect())

        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def reply(self,status,body,kind='application/json'):
                self.send_response(status);self.send_header('Content-Type',kind)
                self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def do_POST(self):
                if self.path!='/v1/chat/completions' or self.headers.get('Authorization')!='Bearer '+proxy.token:
                    self.reply(403,b'{"error":"private model route"}');return
                identity=proxy.directory/uuid.uuid4().hex
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<size<=4_000_000:raise ValueError('Invalid native request length')
                    data=self.rfile.read(size);request=json.loads(data)
                    if request.get('model')!=model:raise ValueError('Unapproved native model route')
                    durable_json(identity.with_suffix('.request.json'),request)
                    upstream=urllib.request.Request(base.rstrip('/')+'/chat/completions',data,
                        {'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                    with opener.open(upstream,timeout=120) as response:
                        content_type=response.headers.get('Content-Type','application/json')
                        body=response.read(16_000_001)
                    if len(body)>16_000_000:raise ValueError('Native response exceeds diagnostic bound')
                    metadata=inspect_response(body,content_type)
                    with proxy.lock:
                        if proxy.actual_model is not None and proxy.actual_model!=metadata['actual_model']:
                            raise ValueError('Actual native model version drift')
                        if proxy.actual_model is None:
                            proxy.actual_model=metadata['actual_model'];durable_json(proxy.pin_path,metadata)
                    durable_json(identity.with_suffix('.metadata.json'),metadata)
                    path=identity.with_suffix('.response.txt')
                    with path.open('wb') as stream:
                        import os
                        os.chmod(path,0o600);stream.write(body)
                    self.reply(200,body,content_type)
                except HTTPError as error:
                    durable_json(identity.with_suffix('.error.json'),{'error':'upstream-http','status':error.code})
                    self.reply(502,b'{"error":"upstream model refused; no retry"}')
                except Exception as error:
                    # Only our fixed validation messages may enter evidence; never echo an upstream body.
                    reason = str(error) if isinstance(error, ValueError) else 'transport-failure'
                    durable_json(identity.with_suffix('.error.json'),{'error_type':type(error).__name__, 'reason':reason})
                    self.reply(502,b'{"error":"model transport or identity verification failed; no retry"}')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:%d/v1'%self.server.server_port

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)
