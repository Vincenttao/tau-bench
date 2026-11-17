"""Offline replay of recorded input judgments through the actual routing rules.

This verifies the input segment only, not native execution or the whole H19 contract.
There is no network client or business-tool adapter in this entry point.
"""
import argparse
import copy
import json
from pathlib import Path

from input_router import InputRouter, RoutingPolicy
from task_session import durable_json


def replay(record):
    expected_request = record['request']
    response = record['raw_response']
    if not isinstance(response, dict): raise ValueError('Recorded model response missing')

    class RecordedOnly:
        calls = 0
        def ask(self, request):
            if request != expected_request: raise ValueError('Replay input or question differs from captured request')
            self.calls += 1
            return copy.deepcopy(response)

    client = RecordedOnly()
    result = InputRouter(client, RoutingPolicy(**record['policy'])).interpret(copy.deepcopy(record['input_snapshot']))
    if client.calls != 1 or result != record: raise ValueError('Replay control result differs from captured route')
    return {'status': 'passed', 'scope': 'input-routing-segment-only', 'external_calls': 0,
            'message_id': record['message_id'], 'input_hash': record['input_hash']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.inputs.glob('*.proposal.json'))
    if not paths: raise ValueError('No recorded input routes')
    args.output.mkdir(parents=True, exist_ok=False)
    results = [replay(json.loads(path.read_text())) for path in paths]
    durable_json(args.output/'result.json', {'status': 'passed', 'scope': 'input-routing-segment-only',
                 'whole_chain_replay': False, 'external_calls': 0, 'routes': results})
    print(json.dumps({'status': 'passed', 'replayed_routes': len(results), 'whole_chain_replay': False}))
