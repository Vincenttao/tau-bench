import contextlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import httpx
from fixed_response_gateway import Transcript,LocalGateway

class FixedResponseGatewayTest(unittest.TestCase):
 def test_exact_replay_twice_and_mismatch_stops(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'capture';calls=[]
   @contextlib.contextmanager
   def local_fixture(body,key):
    calls.append(json.loads(body));yield 200,{'content-type':'text/event-stream'},iter([b'data: {"choices":[]}\n\n',b'data: [DONE]\n\n'])
   body={'model':'deepseek-v4-flash','messages':[{'role':'user','content':'fixture input'}],'stream':True}
   capture=Transcript(folder,'capture','fixture-capture-key')
   with httpx.Client(trust_env=False) as client,LocalGateway(capture,local_fixture) as gateway:
    response=client.post(gateway.base_url+'/chat/completions',json=body,headers={'Authorization':'Bearer fixture-capture-key'})
    self.assertEqual(response.status_code,200);self.assertIn('[DONE]',response.text)
   capture.seal();self.assertEqual(len(calls),1)
   self.assertNotIn('fixture-capture-key',''.join(p.read_text() for p in folder.iterdir() if p.is_file()))
   for repetition in range(2):
    replay=Transcript(folder,'replay','fixture-replay-key')
    def forbidden(*args):raise AssertionError('Replay contacted upstream')
    with httpx.Client(trust_env=False) as client,LocalGateway(replay,forbidden) as gateway:
     response=client.post(gateway.base_url+'/chat/completions',json=body,headers={'Authorization':'Bearer fixture-replay-key'})
     self.assertEqual(response.status_code,200)
    self.assertTrue(replay.verdict()['strict_match_complete']);self.assertEqual(replay.verdict()['real_gateway_call_count'],0)
   replay=Transcript(folder,'replay','fixture-replay-key')
   with httpx.Client(trust_env=False) as client,LocalGateway(replay,forbidden) as gateway:
    wrong={**body,'messages':[{'role':'user','content':'different request'}]}
    for request in [wrong,body]:
     response=client.post(gateway.base_url+'/chat/completions',json=request,headers={'Authorization':'Bearer fixture-replay-key'})
     self.assertEqual(response.status_code,409)
   self.assertFalse(replay.verdict()['strict_match_complete']);self.assertEqual(replay.position,0)
   self.assertEqual(replay.verdict()['failure'],'strict_request_mismatch_at_index_0')

 def test_unsealed_or_tampered_transcript_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'capture';capture=Transcript(folder,'capture','fixture-key')
   with self.assertRaises(ValueError):Transcript(folder,'replay','local-key')
   body=json.dumps({'model':'deepseek-v4-flash','messages':[]}).encode();index=capture.begin(body);capture.complete(index,200,{},b'{}');capture.seal()
   (folder/'000000.response.bin').write_bytes(b'tampered')
   with self.assertRaises(ValueError):Transcript(folder,'replay','local-key')

if __name__=='__main__':unittest.main()
