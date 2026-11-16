"""Inventory existing 81-card evidence without pooling formal scores or missing usage."""
import argparse,collections,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def report(suite):
 suite=Path(suite).resolve()
 catalog=json.loads((ROOT/'config/metrics-v02-catalog.json').read_text())
 expected={card['id'] for card in catalog}
 if len(catalog)!=81 or len(expected)!=81:raise ValueError('Expected unique81-card catalog')
 batches=[];cards={card['id']:{'id':card['id'],'name':card['name'],'evidence':[]} for card in catalog}
 for path in sorted(suite.glob('P*/metrics-v02.json')):
  document=json.loads(path.read_text());items=document['metrics']
  if len(items)!=81 or {item['id'] for item in items}!=expected:raise ValueError('Incomplete/duplicate card mapping: '+str(path))
  manifest=json.loads((path.parent/'manifest.json').read_text())
  reference=str(path.relative_to(suite))
  batches.append({'reference':reference,'sha256':digest(path),'implementation':manifest['implementation'],'collector_sha256':document.get('collector_sha256'),'catalog_sha256':document.get('catalog_sha256'),'metric_spec_sha256':document.get('metric_spec_sha256'),'observed_facts':document['facts']})
  for item in items:
   cards[item['id']]['evidence'].append({'reference':reference,'implementation':manifest['implementation'],'collection_status':item['collection_status'],'evaluation_result':item['evaluation_result'],'formal_value':item['value'],'reason':item['reason']})
 rows=[]
 for card in catalog:
  row=cards[card['id']]
  row['batch_count']=len(row['evidence'])
  row['collection_status_counts']=dict(collections.Counter(x['collection_status'] for x in row['evidence']))
  row['non_null_formal_value_count']=sum(x['formal_value'] is not None for x in row['evidence'])
  row['aggregate_formal_value']=None
  row['aggregate_evaluation']='未验证：仅盘点证据，不跨批次合成正式值'
  rows.append(row)
 result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'suite':str(suite),'scope':'Existing collected reports only; running/unstarted episodes not treated as completed or zero; A/B and primary/retry results not pooled','card_count':81,'batch_report_count':len(batches),'batches':batches,'cards':rows,'final_enterprise_acceptance':None}
 (suite/'metric-coverage-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 lines=['# 指标证据盘点（非最终验收）','',f'已读取 {len(batches)} 份现存批次采集报告，逐份核对81张卡。未采集或未结束的测试不计作已完成。正式值不跨批次汇总；A/B、首尝试和恢复尝试保持原始引用。','', '不同采集器、卡目录及指标原文版本的哈希保存在JSON的batches中。该盘点不追溯改写历史报告。','', '| 指标 | 报告数 | 非空正式值记录数 | 现存采集状态 |','|---|---:|---:|---|']
 for row in rows:
  states='；'.join(f'{key}：{count}' for key,count in row['collection_status_counts'].items()) or '没有采集报告'
  lines.append(f"| {row['id']} {row['name']} | {row['batch_count']} | {row['non_null_formal_value_count']} | {states} |")
 (suite/'metric-coverage-inventory.md').write_text('\n'.join(lines)+'\n')
 return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--suite',type=Path,required=True);args=parser.parse_args()
 result=report(args.suite)
 print(json.dumps({key:result[key] for key in ['generated_at_utc','card_count','batch_report_count','final_enterprise_acceptance']},ensure_ascii=False))
