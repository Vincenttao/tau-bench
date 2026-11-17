"""Read-only verification of one completed English baseline; writes a separate report."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    run = args.run.resolve()
    banking = run / 'banking'
    manifest = read(banking / 'manifest.json')
    assert len(manifest['episodes']) == 1
    episode = banking / 'episodes' / manifest['episodes'][0]['key']
    result = read(episode / 'result.json')
    simulation = result['simulations'][0]
    messages = simulation['messages']
    status = read(episode / 'status.json')
    workspace, = (episode / 'deepagent').iterdir()
    events = records(workspace / 'deepagent-events.jsonl')
    receipts = records(workspace / 'mcp/evidence.jsonl')
    protocol = read(run / 'protocol/result.json')
    freeze = read(run / 'source-freeze.json')
    checks = {}
    checks['single_english_task'] = manifest['episodes'][0]['task_id'] == 'task_054' and manifest['trials'] == manifest['concurrency'] == 1
    checks['official_commit'] = manifest['benchmark_commit'] == 'fc0055dc4e0a316c3f83133267fbd6faaa770992'
    checks['skill_release'] = manifest['skill_release']['version'] == '3.2.0'
    checks['protocol_passed'] = protocol['status'] == 'passed' and protocol['external_model_calls'] == 0
    language = [r['data'] for r in events if r['event'] == 'language']
    prompts = [r['data'] for r in events if r['event'] == 'system_prompt']
    checks['runtime_language_en'] = language == [{'benchmark_language': 'en', 'core_language': 'en'}]
    checks['runtime_prompt'] = len(prompts) == 1 and prompts[0]['version'] == 'evidence-todo-v1'
    checks['no_cjk_in_customer_dialogue'] = not any(re.search(r'[\u3400-\u9fff]', m.get('content') or '') for m in messages if m['role'] in ('assistant', 'user'))
    checks['frozen_sources_intact'] = all(sha(run / 'frozen' / name) == digest for name, digest in freeze['files'].items())
    checks['deployed_skill_matches_release'] = all(sha(workspace / 'skills' / name) == digest for name, digest in manifest['skill_release']['files'].items() if name.startswith('banking-mcp/') and name.endswith('.md'))
    checks['mcp_raw_receipt_hashes'] = bool(receipts) and all(hashlib.sha256(r['raw'].encode()).hexdigest() == r['result']['raw_sha256'] for r in receipts)
    checks['officially_scored'] = status['status'] == 'scored'
    checks['business_reward_passed'] = status.get('reward') == 1
    checks['strict_offline_reconstruction'] = read(run / 'strict-state-reconstruction.json')['strict_reconstruction'] is True
    actions = []
    dialogue = []
    for index, message in enumerate(messages):
        if message['role'] in ('assistant', 'user') and message.get('content'):
            dialogue.append({'message_index': index, 'role': message['role'], 'content': message['content']})
        for call in message.get('tool_calls') or []:
            name, arguments = call['name'], call.get('arguments', {})
            if name in ('call_discoverable_agent_tool', 'call_discoverable_user_tool'):
                name = arguments.get('agent_tool_name') or arguments.get('user_tool_name')
                arguments = arguments.get('arguments', {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
            actions.append({'message_index': index, 'actor': message['role'], 'name': name, 'arguments': arguments})
    writes = [a for a in actions if a['name'] in ('submit_credit_limit_increase_request_7392', 'approve_credit_limit_increase_5847', 'order_replacement_credit_card_7291', 'file_credit_card_transaction_dispute_4829')]
    names = [a['name'] for a in writes]
    expected = ['submit_credit_limit_increase_request_7392', 'approve_credit_limit_increase_5847', 'order_replacement_credit_card_7291', 'file_credit_card_transaction_dispute_4829']
    checks['one_each_expected_write'] = len(names) == 4 and sorted(names) == sorted(expected)
    by_name = {a['name']: a for a in writes}
    checks['cli_before_replacement_and_dispute'] = all(n in by_name for n in expected) and by_name[expected[0]]['message_index'] < by_name[expected[1]]['message_index'] < min(by_name[expected[2]]['message_index'], by_name[expected[3]]['message_index'])
    checks['adjusted_cli_amount'] = by_name.get(expected[0], {}).get('arguments', {}).get('requested_increase_amount') == 2500 and by_name.get(expected[1], {}).get('arguments', {}).get('new_credit_limit') == 7500
    response_events = [e['data'] for e in events if e['event'] == 'model_response']
    usage = [r['usage_metadata'] for r in response_events if r.get('usage_metadata')]
    user_usage = records(episode / 'user-usage.jsonl')
    evidence_hashes = {str(f.relative_to(run)): sha(f) for f in run.rglob('*') if f.is_file()}
    report = {'scope': 'Existing baseline only; agent-hub enhancement is not installed; N=1 is not a general performance claim.',
              'status': status, 'reward_info': simulation['reward_info'], 'checks': checks,
              'all_checks_passed': all(checks.values()), 'language': language, 'system_prompt': prompts,
              'messages': len(messages), 'assistant_tool_calls': sum(a['actor'] == 'assistant' for a in actions),
              'user_tool_calls': sum(a['actor'] == 'user' for a in actions),
              'user_tool_scope': 'task_054 has an empty user_tools list; user-simulator dialogue is exercised, user-side business writes are not covered.',
              'mcp_receipts': len(receipts), 'mcp_error_receipts': sum(not r['result']['success'] for r in receipts),
              'java_model_responses': len(response_events), 'java_usage_records': len(usage),
              'java_observed_tokens': sum(r.get('total_tokens', 0) for r in usage),
              'simulator_or_judge_observed_tokens': sum(r.get('total_tokens', 0) for r in user_usage),
              'gateway_probe_tokens': read(run / 'gateway.log').get('usage', {}).get('total_tokens'),
              'gateway_returned_models': sorted({r['model'] for r in user_usage}),
              'business_writes': writes, 'official_actions': actions, 'customer_dialogue': dialogue,
              'evidence_sha256': evidence_hashes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as target:
        target.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'checks', 'all_checks_passed', 'messages', 'mcp_receipts', 'mcp_error_receipts', 'java_observed_tokens', 'simulator_or_judge_observed_tokens')}, indent=2))


if __name__ == '__main__':
    main()
