"""P06 planned-sample report with exact tool-sequence diagnostics, not semantic equivalence."""
import argparse,hashlib,json,itertools
from pathlib import Path
from repetition_stats import describe
from study_contract import compare
ROOT=Path(__file__).resolve().parents[1];SUITE=ROOT/'runs/enterprise-v02-20261114'

def canonical(value):
 if isinstance(value,dict):
  result={}
  for key,item in sorted(value.items()):
   if key=='arguments' and isinstance(item,str):
    try:item=json.loads(item)
    except ValueError:pass
   result[key]=canonical(item)
  return result
 if isinstance(value,list):return [canonical(x) for x in value]
 if isinstance(value,float) and value.is_integer():return int(value)
 return value

def report(suite=SUITE):
 SUITE=Path(suite).resolve()
 rules=json.loads((ROOT/'config/repetition-study-v1.json').read_text())['P06'];cases=[]
 for case in rules['cases']:
  rows=[];manifests=[];sequences=[]
  for index in range(rules['independent_runs_per_case']):
   folder=SUITE/f'P06-{case}-r{index:02d}-a00';manifest=folder/'manifest.json';results=list(folder.glob('episodes/*/result.json'))
   if manifest.exists():manifests.append(json.loads(manifest.read_text()))
   row={'repetition_index':index,'official_reward':None,'duration':None,'state':'NOT_STARTED' if not manifest.exists() else 'RUNNING_OR_UNSCORED'}
   if results:
    simulation=json.loads(results[0].read_text())['simulations'][0]
    row.update(official_reward=simulation['reward_info']['reward'],duration=simulation['duration'],state='SCORED')
    sequence=[]
    for message in simulation['messages']:
     for call in message.get('tool_calls') or []:
      sequence.append(json.dumps(canonical({'actor':message['role'],'name':call['name'],'arguments':call['arguments']}),sort_keys=True,separators=(',',':')))
    sequences.append(tuple(sequence));row['tool_sequence_sha256']=hashlib.sha256(json.dumps(sequence).encode()).hexdigest()
   rows.append(row)
  pairs=list(itertools.combinations(sequences,2))
  cases.append({'case_id':case,**describe(rows,rules['independent_runs_per_case']),'runs':rows,'execution_contract':compare(manifests),
                'exact_tool_sequence_pairs':len(pairs),'exact_tool_sequence_agreement':sum(a==b for a,b in pairs)/len(pairs) if pairs else None,
                'scope':'Exact ordered tool requests only; not K01 semantic result or K04 slot equivalence. No inference of future deterministic behavior.'})
 result={'stage':'P06','cases':cases,'formal_K05':None,'safety_acceptance':'unknown','note':'Planned runs remain in denominator; no retry selection.'}
 (SUITE/'P06-repetition-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--suite',type=Path,default=SUITE);args=parser.parse_args()
 print(json.dumps(report(args.suite),ensure_ascii=False,indent=2))
