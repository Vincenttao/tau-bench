"""Local OTLP HTTP/protobuf evidence receiver; no forwarding destination."""
import argparse,gzip,hashlib,importlib.metadata,json,os,signal,sys,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest,ExportTraceServiceResponse
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest,ExportMetricsServiceResponse

class Capture:
 def __init__(self,directory,forbidden_secret=''):
  self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=False);self.secret=forbidden_secret.encode();self.lock=threading.Lock();self.requests=0;self.spans=0;self.rejected=0
 def receive(self,path,body,encoding=''):
  if encoding=='gzip':body=gzip.decompress(body)
  if self.secret and self.secret in body:
   with self.lock:self.rejected+=1;self.status()
   raise ValueError('Forbidden model credential detected; payload not stored')
  if path=='/v1/traces':request=ExportTraceServiceRequest();response=ExportTraceServiceResponse()
  elif path=='/v1/metrics':request=ExportMetricsServiceRequest();response=ExportMetricsServiceResponse()
  else:raise ValueError('Unsupported OTLP route')
  request.ParseFromString(body)
  document=MessageToDict(request,preserving_proto_field_name=True)
  with self.lock:
   index=self.requests;self.requests+=1
   binary=f'{index:06d}.otlp.bin';(self.root/binary).write_bytes(body)
   (self.root/f'{index:06d}.otlp.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
   rows=[]
   if path=='/v1/traces':
    for resource in request.resource_spans:
     for scope in resource.scope_spans:
      for span in scope.spans:
       rows.append({'trace_id':span.trace_id.hex(),'span_id':span.span_id.hex(),'parent_span_id':span.parent_span_id.hex(),'name':span.name,'kind':span.kind,'start_time_unix_nano':span.start_time_unix_nano,'end_time_unix_nano':span.end_time_unix_nano,'status_code':span.status.code,'dropped_attributes_count':span.dropped_attributes_count,'dropped_events_count':span.dropped_events_count,'dropped_links_count':span.dropped_links_count,'resource':MessageToDict(resource.resource,preserving_proto_field_name=True),'scope_name':scope.scope.name,'attributes':[MessageToDict(value,preserving_proto_field_name=True) for value in span.attributes],'source_payload':binary})
   with (self.root/'spans.jsonl').open('a') as stream:
    for row in rows:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
   self.spans+=len(rows)
   with (self.root/'receipts.jsonl').open('a') as stream:stream.write(json.dumps({'path':path,'payload':binary,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'span_count':len(rows)})+'\n')
   self.status()
  return response.SerializeToString()
 def status(self):
  (self.root/'status.json').write_text(json.dumps({'received_requests':self.requests,'received_span_records':self.spans,'secret_payloads_rejected':self.rejected,'scope':'Actual received OTLP only; not independent span coverage or enterprise acceptance'},indent=2)+'\n')

class Receiver:
 def __init__(self,capture):
  self.capture=capture
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    try:
     size=int(self.headers.get('Content-Length','0'))
     if not 0<size<=128*1024*1024:raise ValueError('Invalid OTLP payload size')
     reply=capture.receive(self.path,self.rfile.read(size),self.headers.get('Content-Encoding',''))
     self.send_response(200);self.send_header('Content-Type','application/x-protobuf');self.send_header('Content-Length',str(len(reply)));self.end_headers();self.wfile.write(reply)
    except Exception:
     self.send_response(400);self.send_header('Content-Length','0');self.end_headers()
  self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.daemon_threads=True
  self.endpoint='http://127.0.0.1:'+str(self.server.server_address[1]);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
 def __enter__(self):self.thread.start();return self
 def __exit__(self,*args):self.server.shutdown();self.server.server_close();self.thread.join(timeout=5);self.capture.status()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--ready-file',type=Path,required=True);a=p.parse_args()
 capture=Capture(a.output,os.getenv('OPENAI_API_KEY',''))
 def stop(*args):raise KeyboardInterrupt()
 signal.signal(signal.SIGTERM,stop)
 with Receiver(capture) as receiver:
  a.ready_file.write_text(json.dumps({'pid':os.getpid(),'endpoint':receiver.endpoint,'output':str(a.output),'python':sys.version,'parser_versions':{name:importlib.metadata.version(name) for name in ['opentelemetry-proto','protobuf']},'collector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
  try:threading.Event().wait()
  except KeyboardInterrupt:pass
