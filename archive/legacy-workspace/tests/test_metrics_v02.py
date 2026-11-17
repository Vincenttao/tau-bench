import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from collect_metrics_v02 import collect, ROOT

class MetricsTest(unittest.TestCase):
    def test_all_cards_match_source(self):
        source=(ROOT/'企业任务执行效果指标卡-V0.2.md').read_text()
        cards=json.loads((ROOT/'config/metrics-v02-catalog.json').read_text())
        expected={m[1]:m[2] for m in re.finditer(r'^#{3,4} ([QRCTEKGX]\d{2}) ([^\n]+)$',source,re.M)}
        self.assertEqual(len(cards),81)
        self.assertEqual({c['id']:c['name'] for c in cards},expected)
        for card in cards:self.assertIn(card['formula'],source)
    def test_missing_evidence_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'manifest.json').write_text(json.dumps({'implementation':'native-skill-stdio','model':'test','episodes':[{'key':'case','task_id':'task_001','trial':0,'seed':300,'domain':'banking_knowledge'}]}))
            result=collect(root)
            self.assertIsNone(result['facts']['observed_token_sum'])
            self.assertEqual(result['facts']['planned_episodes'],1)
            self.assertEqual(result['facts']['officially_scored_episodes'],0)
            self.assertIsNone(result['episodes'][0]['rail_rejections'])
            self.assertTrue(all(m['value'] is None for m in result['metrics']))
            self.assertTrue(all(m['evaluation_result']=='未验证' for m in result['metrics']))
    def test_deepagent_has_no_runtime_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'manifest.json').write_text(json.dumps({'implementation':'deepagent-todo-skill-mcp','model':'test','episodes':[{'key':'case','task_id':'task_001','trial':0,'seed':300,'domain':'banking_knowledge'}]}))
            result=collect(root,'deepagent-todo-skill-mcp')
            self.assertEqual(len(result['metrics']),81)
            self.assertIn('not Runtime',result['scope'])
            self.assertTrue(all('不能替换 Runtime Task' in x['evaluation_level'] for x in result['metrics']))
            self.assertIsNone(result['episodes'][0]['runtime_task_id'])

    def test_smoke_does_not_become_enterprise_success(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            src=ROOT/'runs/smoke-20261113T154715Z'
            dst=Path(tmp)/'smoke';shutil.copytree(src,dst)
            result=collect(dst)
            self.assertEqual(result['facts']['observed_token_sum'],714038)
            self.assertEqual(result['facts']['official_reward_one_count'],1)
            self.assertIsNone(result['facts']['enterprise_accepted_count'])
            self.assertIsNone(result['episodes'][0]['runtime_task_id'])
            self.assertEqual(result['episodes'][0]['agent_tool_calls'],20)
            for ident in ('Q08','K05','K08','G01','G04','G07','X02'):
                self.assertIsNone(next(m for m in result['metrics'] if m['id']==ident)['value'])

if __name__=='__main__':unittest.main()
