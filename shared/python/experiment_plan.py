"""Validate independent experiment inputs without starting models or runtimes."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate(plan_directory, root=ROOT):
    import jsonschema

    directory, root = Path(plan_directory).resolve(), Path(root).resolve()

    def within(base, name):
        candidate = (base / name).resolve()
        if not candidate.is_relative_to(base.resolve()):
            raise ValueError('Path escapes input root: ' + name)
        return candidate

    def require(condition, reason):
        if not condition:
            raise ValueError(reason)

    schema_root = root / 'studies/banking-architecture-comparison/schemas'
    plan_path = directory / 'plan.json'
    plan = read(plan_path)
    try:
        jsonschema.validate(plan, read(schema_root / 'plan.schema.json'))
        study_path = within(root, plan['comparison_study'])
        study = read(study_path)
        jsonschema.validate(study, read(schema_root / 'study.schema.json'))
    except jsonschema.ValidationError as error:
        raise ValueError('Experiment schema: ' + error.message) from error
    require(directory == root / 'experiments' / plan['plan_id'], 'Experiment identity differs')
    require(study['profile'] == plan['comparison_profile'], 'Study profile differs')
    require(len(study['arms']) == len(set(study['arms'])) == 4, 'Expected four unique arms')
    require(set(study['arms']) == {'experiments/' + k for k in study['arm_bindings']}, 'Arm registry differs')
    require('experiments/' + plan['plan_id'] in study['arms'], 'Unregistered experiment')
    binding = study['arm_bindings'][plan['plan_id']]
    for key, expected in binding.items():
        require(plan[key] == expected, 'Arm binding differs: ' + key)
    for field, study_field in [('comparison_language', 'language'), ('comparison_cases', 'tasks_per_arm'),
                               ('comparison_trials', 'trials_per_task'), ('seed', 'seed'),
                               ('limits', 'limits'), ('model_profile', 'model_profile')]:
        require(plan[field] == study[study_field], 'Shared condition differs: ' + field)
    for key in ('episode_timeout_seconds', 'batch_timeout_seconds', 'max_steps', 'max_errors',
                'cumulative_token_limit', 'global_concurrency', 'automatic_episode_retries',
                'automatic_business_write_retries'):
        require(study[key] == study['limits'][key], 'Duplicated budget differs: ' + key)
    require(study['total_formal_episodes'] == 4 * study['tasks_per_arm'] * study['trials_per_task'] == 88,
            'Formal position count differs')
    pair = sorted(study['arm_bindings'].values(), key=lambda b: b['display_number'])
    require([b['display_number'] for b in pair] == [1, 2, 3, 4], 'Arm numbering differs')
    require(pair[0]['system_prompt_version'] == pair[1]['system_prompt_version'] ==
            study['system_prompt_for_deepagent_pair'], 'DeepAgent prompts differ')
    require(pair[0]['implementation'] == pair[1]['implementation'], 'DeepAgent implementations differ')
    require(pair[3]['mode'] == study['agent_hub_mode'] == 'enforce', 'Hub mode differs')
    require(len({b['skill_manifest_sha256'] for b in pair[1:]}) == 1, 'Refined releases differ')
    require(pair[0]['skill_manifest_sha256'] != pair[1]['skill_manifest_sha256'], 'Original release lost')
    for name, expected in study['contracts'].items():
        require(sha(within(study_path.parent, name)) == expected, 'Contract file changed: ' + name)
    cohort_path = within(study_path.parent, study['cohort'])
    require(sha(cohort_path) == study['cohort_sha256'], 'Cohort file changed')
    cohort = read(cohort_path)
    require(cohort['language'] == study['language'] and cohort['benchmark_commit'] == study['benchmark_commit'],
            'Benchmark conditions differ')
    require(sha(within(root, cohort['selection_source'])) == cohort['selection_source_sha256'],
            'Selection source changed')
    cases = cohort['cases']
    require(cohort['task_count'] == len(cases) == len({c['task_id'] for c in cases}) == study['tasks_per_arm'],
            'Case count differs')
    for order, case in enumerate(cases, 1):
        require(case['order'] == order and case['seed'] == study['seed'] and case['trial'] == 0,
                'Case seed/order/trial differs')
        require(case['arm_order'] == [1 + (order - 1 + j) % 4 for j in range(4)], 'Arm rotation differs')
        task_path = within(root, case['task_file'])
        require(sha(task_path) == case['task_file_sha256'], 'Task bytes changed: ' + case['task_id'])
        require(read(task_path)['id'] == case['task_id'], 'Task content identity differs')
    release_path = within(root, plan['skill_manifest'])
    expected_path = root / 'shared/skills/releases' / plan['skill_release'] / 'release.json'
    require(release_path == expected_path.resolve(), 'Skill version/path differs')
    require(sha(release_path) == binding['skill_manifest_sha256'], 'Skill manifest changed')
    metadata = read(release_path)
    require(metadata['version'] == plan['skill_release'] and metadata['schema_version'] == 1,
            'Skill metadata identity differs')
    folder = release_path.parent
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p != release_path}
    require(actual == set(metadata['files']), 'Skill inventory differs')
    for name, expected in metadata['files'].items():
        require(sha(within(folder, name)) == expected, 'Skill document changed: ' + name)
    from study_contracts import verify
    contract_check = verify(root)
    return {
        'schema_version': 1,
        'record_type': 'experiment-preparation-not-execution-manifest',
        'plan_id': plan['plan_id'], 'executable': False, 'execution_started': False,
        'implementation_status': plan['status'], 'plan_sha256': sha(plan_path),
        'study_sha256': sha(study_path), 'cohort_sha256': sha(cohort_path),
        'skill_release': plan['skill_release'], 'skill_manifest_sha256': sha(release_path),
        'benchmark_commit': study['benchmark_commit'], 'language': cohort['language'],
        'task_ids': [case['task_id'] for case in cases], 'task_count': len(cases),
        'trials': study['trials_per_task'], 'seed': study['seed'],
        'mode': plan['mode'], 'system_prompt_version': plan['system_prompt_version'],
        'limits': plan['limits'], 'model_profile': plan['model_profile'],
        'contract_hashes': study['contracts'], 'contract_inventory': contract_check, 'blocking_gaps': study['blocking_gaps'],
        'limits_of_validation': ['Input preparation only; runtime, binaries and model routing not verified.'],
    }


def main(plan_directory):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory for preparation.json; no models are called')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output must not exist; existing records are immutable')
    result = validate(plan_directory)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'preparation.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'plan_id': result['plan_id'], 'task_count': result['task_count'],
                      'executable': False, 'output': str(args.output)}, ensure_ascii=False))
