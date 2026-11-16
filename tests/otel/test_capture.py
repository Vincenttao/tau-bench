import json,sys,tempfile,unittest,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'python'))
from otlp_capture import Capture,Receiver,ExportTraceServiceRequest
from collect_metrics_v02 import collect
class CaptureTest(unittest.TestCase):
 def payload(self):
  request=ExportTraceServiceRequest();resource=request.resource_spans.add();scope=resource.scope_spans.add();scope.scope.name='local-fixture';span=scope.spans.add();span.trace_id=bytes.fromhex('ab'*16);span.span_id=bytes.fromhex('cd'*8);span.name='fixture-only';span.start_time_unix_nano=10;span.end_time_unix_nano=20
  return request,span
 def test_real_otlp_wire_and_identifiers(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'experiment';root.mkdir()
   (root/'manifest.json').write_text(json.dumps({'implementation':'runtime-moa-main-local-skill','model':'fixture','token_limit':None,'episodes':[{'key':'case','task_id':'task_001','trial':0,'seed':300,'domain':'banking_knowledge'}]}))
   capture=Capture(root/'episodes/case/java/otel/capture');request,span=self.payload()
   with Receiver(capture) as receiver:
    req=urllib.request.Request(receiver.endpoint+'/v1/traces',data=request.SerializeToString(),headers={'Content-Type':'application/x-protobuf'})
    with urllib.request.urlopen(req) as response:self.assertEqual(response.status,200)
   row=json.loads((capture.root/'spans.jsonl').read_text());self.assertEqual(row['trace_id'],'ab'*16);self.assertEqual(row['span_id'],'cd'*8);self.assertEqual(row['name'],'fixture-only');self.assertEqual(capture.spans,1)
   report=collect(root,implementation='runtime-moa-main-local-skill')
   self.assertEqual(report['episodes'][0]['observed_unique_otel_spans'],1)
   self.assertIn('已读取真实OTLP',report['otel_status'])
   self.assertIsNone(report['facts']['runtime_task_count'])
   self.assertTrue(all(metric['value'] is None and metric['evidence_coverage'] is None for metric in report['metrics']))
 def test_credential_payload_not_persisted(self):
  with tempfile.TemporaryDirectory() as tmp:
   capture=Capture(Path(tmp)/'otlp','fixture-forbidden-credential');request,span=self.payload();attribute=span.attributes.add();attribute.key='forbidden';attribute.value.string_value='fixture-forbidden-credential'
   with self.assertRaises(ValueError):capture.receive('/v1/traces',request.SerializeToString())
   self.assertEqual(capture.rejected,1);self.assertFalse(list(capture.root.glob('*.bin')))
   self.assertNotIn('fixture-forbidden-credential',''.join(p.read_text() for p in capture.root.iterdir()))
if __name__=='__main__':unittest.main()
