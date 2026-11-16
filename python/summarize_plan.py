"""Read-only cross-directory plan summary; original attempts remain distinct."""
import argparse,json
from pathlib import Path
from repetition_stats import describe
ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'runs/enterprise-v02-20261114'

def summarize(suite=SUITE):
    SUITE=Path(suite).resolve()
    ledger=[json.loads(x) for x in (SUITE/'execution-ledger.jsonl').read_text().splitlines()]
    attempts={}
    for row in ledger:
        if row.get('output_dir'):
            key=(row.get('plan_item'),row.get('case_id'),row.get('repetition_index',0),row.get('attempt_index',0))
            attempts[str(Path(row['output_dir']).resolve())]=(key,row)
    observations=[]
    for key,row in attempts.values():
        folder=Path(row['output_dir']);folder=folder if folder.is_absolute() else ROOT/folder
        progress=json.loads((folder/'progress.json').read_text()) if (folder/'progress.json').exists() else None
        collected=json.loads((folder/'metrics-v02.json').read_text()) if (folder/'metrics-v02.json').exists() else None
        manifest=json.loads((folder/'manifest.json').read_text())
        cases={e['key']:e['task_id'] for e in manifest['episodes']}
        for ep in folder.glob('episodes/*'):
            status=json.loads((ep/'status.json').read_text()) if (ep/'status.json').exists() else None
            result=json.loads((ep/'result.json').read_text()) if (ep/'result.json').exists() else None
            sim=result['simulations'][0] if result else None
            observations.append({'plan_item':key[0],'case_id':status.get('task_id') if status else cases.get(ep.name),'repetition_index':key[2],'attempt_index':key[3],'output_dir':str(folder.relative_to(ROOT)),
                'status':status,'official_reward':sim['reward_info']['reward'] if sim and sim.get('reward_info') else None,
                'duration':sim.get('duration') if sim else None,'observed_tokens':collected['facts']['observed_token_sum'] if collected else progress.get('observed_tokens') if progress else None,'enterprise_acceptance':None})
    primary=[x for x in observations if x['attempt_index']==0]
    report={'scope':'All real-model attempts for usage; primary and retry scores separate; no enterprise acceptance inference','attempts':observations,'completed_scored':sum(x['official_reward'] is not None for x in observations),'official_reward_one_count':sum(x['official_reward']==1 for x in observations),'pending_or_unscored':sum(x['official_reward'] is None for x in observations),'primary_completed_scored':sum(x['official_reward'] is not None for x in primary),'primary_official_reward_one_count':sum(x['official_reward']==1 for x in primary),'retry_scored_count':sum(x['attempt_index']>0 and x['official_reward'] is not None for x in observations),'note':'No retries replace initial attempts. Per-case primary statistics exclude retries; all-attempt counts are not a primary accuracy rate. Repetition equivalence and safety rules require independent review.'}
    groups={}
    for observation in observations:
        group=(observation['plan_item'],observation['case_id'])
        groups.setdefault(group,[]).append(observation)
    report['per_case_observations']=[{'plan_item':stage,'case_id':case,**describe([x for x in rows if x['attempt_index']==0],3 if stage=='P06' else sum(x['attempt_index']==0 for x in rows)),'retry_observations':[x for x in rows if x['attempt_index']>0]} for (stage,case),rows in groups.items()]
    (SUITE/'stage-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--suite',type=Path,default=SUITE);args=parser.parse_args()
    print(json.dumps(summarize(args.suite),ensure_ascii=False,indent=2))
