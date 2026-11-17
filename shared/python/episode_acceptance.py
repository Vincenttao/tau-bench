"""Inspect live episode evidence, independently of the official business reward."""
import json
from pathlib import Path
from skill_assets import sha


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def inspect_deepagent(manifest):
    checks = {}
    output = Path(manifest['output'])
    episode = output / 'episodes' / manifest['episodes'][0]['key']
    try:
        sessions = list((episode / 'deepagent').glob('*'))
        checks['one_session'] = len(sessions) == 1
        if not checks['one_session']:
            raise ValueError('Expected exactly one DeepAgent workspace')
        workspace = sessions[0]
        events = rows(workspace / 'deepagent-events.jsonl')
        assembly = next(e['data'] for e in events if e['event'] == 'assembly')
        language = next(e['data'] for e in events if e['event'] == 'language')
        prompt = next(e['data'] for e in events if e['event'] == 'system_prompt')
        checks['skill_identity'] = assembly['skill_release'] == manifest['skill_release']
        checks['skill_bytes'] = all(sha(workspace / 'skills' / name) == digest
                                   for name, digest in manifest['skill_release']['files'].items()
                                   if name.startswith('banking-mcp/') and name.endswith('.md'))
        checks['native_task_loop'] = assembly['task_loop'] is True and assembly['task_planning'] is True
        checks['no_general_purpose_agent'] = assembly['general_purpose_agent'] is False
        checks['language'] = language['benchmark_language'] == manifest['language']
        checks['system_prompt'] = prompt['version'] == manifest['system_prompt_version']
        bridge = rows(episode / 'java' / (workspace.name + '.jsonl'))
        ready = [r['data'] for r in bridge if r['direction'] == 'from_java' and r['data']['type'] == 'ready']
        checks['actual_driver'] = len(ready) == 1 and ready[0]['implementation'] == 'DeepAgent-Todo-Skill-MCP'
        mcp_calls = rows(workspace / 'mcp/skill.jsonl')
        official = rows(episode / 'official-trajectory.jsonl')
        calls = {c['id']: c for msg in official if msg.get('role') == 'assistant'
                 for c in msg.get('tool_calls') or []}
        receipts = {msg['id'] for msg in official if msg.get('role') == 'tool'}
        checks['mcp_official_binding'] = bool(mcp_calls) and all(
            call['id'] in calls and call['id'] in receipts
            and calls[call['id']]['name'] == call['operation']
            and calls[call['id']]['arguments'] == call['arguments'] for call in mcp_calls)
        checks['no_official_tool_bypass'] = set(calls) == {call['id'] for call in mcp_calls}
        result = json.loads((episode / 'result.json').read_text())
        status = json.loads((episode / 'status.json').read_text())
        checks['official_score_preserved'] = status['status'] == 'scored' and (
            status['reward'] == result['simulations'][0]['reward_info']['reward'])
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as error:
        checks['complete_evidence'] = False
        error_type = type(error).__name__
    else:
        error_type = None
    return {'status': 'passed' if checks and all(checks.values()) else 'failed',
            'scope': 'single DeepAgent episode wiring; not full study release or paired equivalence',
            'checks': checks, 'error_type': error_type, 'business_reward_is_not_architecture_oracle': True}
