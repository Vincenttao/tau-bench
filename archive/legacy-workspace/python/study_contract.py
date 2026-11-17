"""Frozen execution conditions for repeated benchmarking, excluding reporting code."""
import hashlib,json

def execution_contract(manifest):
    fields=['core_completion_timeout','model','api_base','api_protocol','retrieval_config','benchmark_commit','dataset_sha256','max_steps','max_errors','episode_timeout','event_timeout','concurrency','java_source_sha256','artifact_sha256','source_repositories']
    result={k:manifest.get(k) for k in fields}
    if 'main_core_completion_timeout' in manifest:result['main_core_completion_timeout']=manifest['main_core_completion_timeout']
    result['execution_adapters']={k:manifest.get('adapter_sha256',{}).get(k) for k in ['episode.py','java_agent.py','eval_config.py']}
    result['trial_seed_mode']=manifest.get('trial_seed_mode')
    result['episode_seeds']=sorted({e['seed'] for e in manifest['episodes']})
    return result

def contract_hash(manifest):
    return hashlib.sha256(json.dumps(execution_contract(manifest),sort_keys=True).encode()).hexdigest()

def compare(manifests):
    contracts=[execution_contract(m) for m in manifests]
    if not contracts:return {'comparable':False,'reason':'no manifests'}
    keys=set().union(*(c.keys() for c in contracts))
    changed=sorted({k for c in contracts[1:] for k in keys if c.get(k)!=contracts[0].get(k)})
    return {'comparable':not changed,'changed_fields':changed,'contract_hashes':[contract_hash(m) for m in manifests]}
