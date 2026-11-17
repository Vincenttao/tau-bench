"""Metadata/count summary of completed strict DB replay files; no simulation edits."""
import argparse,collections,hashlib,json,re
from pathlib import Path
def summarize(root):
 root=Path(root);documents=[];counts=collections.Counter()
 for path in sorted((root/'diagnostics').glob('*-db-diff.json')):
  d=json.loads(path.read_text());fields=collections.Counter()
  for category,changes in d.get('deepdiff_gold_to_actual',{}).items():
   for key in changes:
    match=re.search(r"\['([^']+)'\]$",key);fields[match.group(1) if match else category]+=1
  counts.update(fields)
  documents.append({'file':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_result_sha256':d.get('source_result_sha256'),'task_id':d['task_id'],'trial':d['trial'],'official_reward_unchanged':d['official_reward_unchanged'],'replay_completed':d.get('replay_completed',False),'model_calls':d.get('replay',{}).get('model_calls'),'field_counts':dict(fields)})
 if not documents:raise ValueError('No strict DB diagnostic files found')
 calls=[d['model_calls'] for d in documents]
 report={'documents':documents,'replay_completed':all(d['replay_completed'] for d in documents),'model_calls':sum(calls) if all(isinstance(x,int) for x in calls) else None,'field_counts':dict(counts),'note':'Strict official DB replay diagnostic only; original scores unchanged. Counts describe observed field differences, not independent enterprise failure causes.'}
 (root/'replay-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();print(json.dumps(summarize(a.root),ensure_ascii=False,indent=2))
