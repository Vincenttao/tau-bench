import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from planner_client import PlannerClient

class PlannerTests(unittest.TestCase):
    def test_validates_output_and_reserves_before_send(self):
        class Task:
            def __init__(self): self.calls=[]
            def call(self, method, **values): self.calls.append((method,values))
        task=Task()
        response={'model':'fixture','choices':[{'message':{'content':json.dumps({'value':1})}}], 'usage':{'prompt_tokens':3,'completion_tokens':2}}
        class Reply:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return json.dumps(response).encode()
        with tempfile.TemporaryDirectory() as directory:
            client=PlannerClient(task,Path(directory),'synthetic-key','https://example.invalid/v1','fixture')
            def sent(*args,**kwargs):
                self.assertEqual(task.calls[0][1]['kind'],'execution')
                return Reply()
            with patch.object(client.opener,'open',side_effect=sent):
                result=client.complete('fixture',{}, {'type':'object','properties':{'value':{'type':'integer'}},'required':['value'],'additionalProperties':False})
                self.assertEqual(result,{'value':1})
            response['choices'][0]['message']['content']='{"value":"bad"}'
            with patch.object(client.opener,'open',side_effect=sent):
                with self.assertRaises(ValueError): client.complete('fixture',{}, {'type':'object','properties':{'value':{'type':'integer'}}})
