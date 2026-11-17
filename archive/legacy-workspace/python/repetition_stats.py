"""Descriptive repeated-run statistics; no inferred enterprise safety acceptance."""
import statistics

def describe(rows, planned):
    rewards=[r['official_reward'] for r in rows if r.get('official_reward') is not None]
    durations=[r['duration'] for r in rows if r.get('duration') is not None]
    return {'planned':planned,'observed':sum(r.get('state')!='NOT_STARTED' for r in rows),'scored':len(rewards),'missing_score':planned-len(rewards),
            'official_reward_one_count':sum(x==1 for x in rewards),
            'official_pass_fraction_planned':sum(x==1 for x in rewards)/planned if planned and len(rewards)==planned else None,
            'confirmed_success_fraction_lower_bound':sum(x==1 for x in rewards)/planned if planned else None,
            'possible_success_fraction_upper_bound':(sum(x==1 for x in rewards)+planned-len(rewards))/planned if planned else None,
            'quality_stdev_scored_subset':statistics.stdev(rewards) if len(rewards)>=2 else None,
            'duration_stdev_observed_subset':statistics.stdev(durations) if len(durations)>=2 else None,
            'duration_sample_size':len(durations),'enterprise_K05':None,
            'tail_quantiles':None,'limitation':'Missing scores remain unknown; planned-sample success fraction is null until fully scored. Bounds reflect only missing outcomes and are not confidence intervals. Official success is not safety-complete K05. Small samples do not establish tail behavior.'}
