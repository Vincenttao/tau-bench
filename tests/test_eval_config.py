import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from eval_config import configure, GATEWAY, MODEL

class ConfigTest(unittest.TestCase):
    def test_defaults_shared(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(configure(),(MODEL,GATEWAY))
            self.assertEqual(os.environ['OPENAI_API_BASE'],os.environ['OPENAI_BASE_URL'])
    def test_mismatched_routes_rejected(self):
        with patch.dict(os.environ,{'OPENAI_API_BASE':GATEWAY,'OPENAI_BASE_URL':'https://other.example/v1'},clear=True):
            with self.assertRaises(ValueError):configure()
    def test_responses_route_rejected(self):
        with patch.dict(os.environ,{'OPENAI_API_BASE':GATEWAY+'/responses'},clear=True):
            with self.assertRaises(ValueError):configure()
    def test_model_override_propagates(self):
        with patch.dict(os.environ,{'OPENAI_MODEL':'test-model'},clear=True):
            self.assertEqual(configure()[0],'test-model')

if __name__=='__main__':unittest.main()
