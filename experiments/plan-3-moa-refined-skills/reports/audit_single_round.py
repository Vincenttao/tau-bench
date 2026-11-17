"""Audit a completed one-start-per-task batch and export official results."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.run = args.run.resolve()
    args.output = args.output.resolve()
    root = Path(__file__).resolve().parents[3]
    progress = json.loads((args.run / 'progress.json').read_text())
    cohort = json.loads((root / 'studies/banking-architecture-comparison/cohort.json').read_text())
    expected = [case['task_id'] for case in cohort['cases']]
    checks = {'batch_finished': progress['status'] == 'finished',
              'task_ids_and_order': [row['task_id'] for row in progress['cases']] == expected,
              'exactly_22': len(progress['cases']) == 22,
              'all_started_once': all(row['starts'] == 1 for row in progress['cases'])}
    rows, identities, prompt_hashes = [], set(), set()
    for row in progress['cases']:
        task = row['task_id']
        directory = args.run / task
        manifest = json.loads((directory / 'manifest.json').read_text())
        checks[task + '_source_identity'] = all(digest(root / name) == sha
            for name, sha in manifest['implementation_files'].items())
        checks[task + '_dependency_identity'] = all(digest(Path(name)) == sha
            for name, sha in manifest['dependency_files'].items())
        identities.add(json.dumps({key: manifest[key] for key in ('implementation_files',
            'dependency_files', 'skill_release', 'limits', 'model', 'api_base', 'language')}, sort_keys=True))
        episode = manifest['episodes'][0]
        checks[task + '_seed_trial'] = episode['seed'] == 300 and episode['trial'] == 0
        summary = json.loads((directory / 'summary.json').read_text())
        checks[task + '_summary_matches_ledger'] = summary == row['result']
        checks[task + '_terminal'] = summary['status'] not in ('planned', 'started')
        prompt = directory / 'episodes' / task / 'moa/main/main-prompt-meta.json'
        if prompt.exists():
            meta = json.loads(prompt.read_text())
            checks[task + '_v9'] = meta['version'] == 'moa-banking-v9-delegation-context'
            prompt_hashes.add(meta['sha256'])
        record = directory / 'episodes' / task / 'result.json'
        db_match, unmatched = None, None
        if record.exists() and summary['status'] == 'scored':
            sim = json.loads(record.read_text())['simulations'][0]
            reward = sim['reward_info']['reward']
            checks[task + '_official_reward'] = reward == summary.get('reward')
            db_match = (sim['reward_info'].get('db_check') or {}).get('db_match')
            unmatched = sum(not entry['action_match'] for entry in sim['reward_info'].get('action_checks') or [])
        review = args.run / 'review' / (task + '-evidence.json')
        checks[task + '_offline_evidence'] = review.exists()
        rows.append({'task_id': task, 'status': summary['status'], 'reward': summary.get('reward'),
                     'db_match': db_match, 'unmatched_reference_actions': unmatched,
                     'termination_reason': summary.get('termination_reason'),
                     'duration_seconds': summary.get('duration'),
                     'error_type': summary.get('error_type'), 'starts': row['starts'],
                     'evidence': str(directory.relative_to(root))})
    checks['single_configuration'] = len(identities) == 1
    checks['frozen_batch_inputs'] = all(digest(root / name) == sha
        for name, sha in progress['frozen_inputs'].items())
    passed = sum(row['status'] == 'scored' and row['reward'] == 1 for row in rows)
    scored = sum(row['status'] == 'scored' for row in rows)
    failed = scored - passed
    unscored = sum(row['status'] not in ('scored', 'planned', 'started') for row in rows)
    result = {'scope': 'single MOA diagnostic, not formal architecture acceptance',
              'batch_status': progress['status'], 'passed': passed, 'failed': failed,
              'unscored': unscored, 'not_started': sum(row['starts'] == 0 for row in rows),
              'fixed_denominator': 22, 'success_rate': passed / 22,
              'scored_success_rate': passed / scored if scored else None,
              'scoring_coverage': scored / 22, 'checks': checks,
              'audit_pass': all(checks.values()), 'rows': rows,
              'observed_prompt_hashes': sorted(prompt_hashes)}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'batch-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    (args.output / 'case-results.csv').write_text(stream.getvalue())
    print(json.dumps({key: value for key, value in result.items() if key not in ('checks', 'rows')}))


if __name__ == '__main__':
    main()
