"""Real MOA and domain Runtime with scripted local models; no banking score claim."""
import argparse
from contextlib import ExitStack
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import uuid
from urllib.request import Request, urlopen

ARM = Path(__file__).resolve().parents[1]
ROOT = ARM.parents[1]
sys.path.insert(0, str(ROOT / 'shared/python'))
from benchmark_mcp import BenchmarkMcpFacade
from process_tree import terminate_tree
from skill_assets import skill_init_payload
from runtime_protocol import customer_reply
from domain_boundary import DomainBoundary
from receipt_context import ReceiptContext


def run(output, timeout_fault=False, receipt_flow=False, parent_wait_fault=False):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ['TAU3_SKILL_VERSION'] = json.loads((ARM / 'config/diagnostic-runtime.json').read_text())['skill_release']
    query = 'Compare fixture products X and Y for travel with a possible limit of at least 200.'
    if receipt_flow:
        query += ' Record my initial selection and perform the separate fulfillment if authorized.'
    candidate_id = 'card-application-agent'
    owner_id = 'fulfillment-agent'
    follow_up = 'Perform the outstanding fixture fulfillment once. Keep the existing selection.'
    scripts = {
        'fixture-main': [
            ('stage_plan', {'tasks': [{'query': query, 'candidate_ids': [candidate_id]}]}),
            ('stage_bind_next', {}), ('stage_finalize', {}), ('stage_execute_next', {}),
            (None, 'Fixture X meets the possible limit of 200 and has the better travel rate. Approval is not guaranteed.'),
        ],
        'fixture-domain': [
            ('ask_user', {'questions': [{'header': 'Subscription',
                'question': 'Do you have the fixture subscription?',
                'options': [{'label': 'Yes', 'description': 'I have it'},
                            {'label': 'No', 'description': 'I do not have it'}]}]}),
            (None, 'With the confirmed fixture subscription, X has a possible limit up to 200, fee 0 and travel rate 3%; Y up to 250, fee 0 and travel rate 1%. X fits the stated threshold and travel preference. Approval is not guaranteed.'),
        ],
    }
    official_calls = []
    receipt_context = ReceiptContext(output)
    if receipt_flow:
        def invocation(name):
            return ('invoke_skill', {'skill_id': 'banking-mcp',
                    'operation': 'call_discoverable_agent_tool',
                    'arguments': {'agent_tool_name': name, 'arguments': '{}'}})
        scripts['fixture-domain'][1:1] = [invocation('fixture_owned'), invocation('fixture_other')]
        scripts['fixture-main'][-1] = (None, 'Fixture X meets the threshold. The selection was recorded; '
                                       'fulfillment was refused before submission. You may request fulfillment.')
        for approved in (False, True):
            scripts['fixture-main'].extend([
                ('stage_plan', {'tasks': [{'query': follow_up, 'candidate_ids': [owner_id]}]}),
                ('stage_bind_next', {}), ('stage_finalize', {})])
            if approved:
                scripts['fixture-main'].append(('stage_execute_next', {}))
            scripts['fixture-main'].append((None, 'Fulfillment confirmed.' if approved else 'Request withdrawn.'))
        scripts['fixture-owner'] = [invocation('fixture_other'), (None, 'Fulfillment confirmed.')]
    requests = {key: [] for key in scripts}
    errors = []
    a2a = []
    descriptors = []
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            try:
                request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                model = request['model']
                with lock:
                    index = len(requests[model])
                    requests[model].append(request)
                name, value = scripts[model][index]  # Extra calls fail, never invent a fallback answer.
                if (timeout_fault or parent_wait_fault) and model == 'fixture-domain' and index == 1:
                    time.sleep(4)  # Remote execution continues beyond the caller's deadline.
                if name:
                    available = {tool['function']['name'] for tool in request.get('tools', [])}
                    assert name in available, (name, available)
                message = {'role': 'assistant', 'content': '' if name else value}
                if name:
                    message['tool_calls'] = [{'index': 0, 'id': model + '-' + str(index), 'type': 'function',
                        'function': {'name': name, 'arguments': json.dumps(value)}}]
                response = {'id': model + '-' + str(index), 'created': 1, 'model': model,
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 3, 'total_tokens': 13},
                    'choices': [{'index': 0, 'finish_reason': 'tool_calls' if name else 'stop'}]}
                if request.get('stream'):
                    response['object'] = 'chat.completion.chunk'
                    response['choices'][0]['delta'] = message
                    body = ('data: ' + json.dumps(response) + '\n\ndata: [DONE]\n\n').encode()
                    content_type = 'text/event-stream'
                else:
                    response['object'] = 'chat.completion'
                    response['choices'][0]['message'] = message
                    body = json.dumps(response).encode()
                    content_type = 'application/json'
                self.send_response(200)
            except Exception as error:
                errors.append(repr(error))
                body = json.dumps({'error': str(error)}).encode()
                content_type = 'application/json'
                self.send_response(500)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def host(stack, role, identity, candidates, model_url):
        workspace = output / identity
        workspace.mkdir()
        tools = []
        if receipt_flow and role == 'domain':
            tools = [{'type': 'function', 'function': {'name': 'call_discoverable_agent_tool',
                'description': 'Synthetic operation', 'parameters': {'type': 'object', 'properties': {
                'agent_tool_name': {'type': 'string'}, 'arguments': {'type': 'string'}}}}}]
        facade = BenchmarkMcpFacade(tools, identity + '-fixture', queue.Queue(), workspace / 'mcp')
        if tools:
            rules = {'call_discoverable_agent_tool': {'access': 'write', 'allowed_requesters': [candidate_id, owner_id]},
                     'fixture_owned': {'access': 'write', 'allowed_requesters': [candidate_id]},
                     'fixture_other': {'access': 'write', 'allowed_requesters': [owner_id]}}
            callbacks = {}
            events = queue.Queue()
            facade.events = DomainBoundary(identity, rules, events, callbacks, facade.deliver_if_waiting,
                                          context=receipt_context)

            def serve_one():
                try:
                    call = events.get(timeout=90)['tool_calls'][0]
                    official_calls.append(call)
                    receipt_context.reply(call['id'], 'Synthetic receipt R-471', False)
                    deliver, local_id = callbacks.pop(call['id'])
                    deliver(local_id, 'Synthetic receipt R-471', False)
                except Exception as error:
                    errors.append(repr(error))
            threading.Thread(target=serve_one, daemon=True).start()
        stack.callback(facade.close)
        cp = ':'.join([str(ARM / 'java/target/classes'), str(ROOT / 'shared/java/target/classes'),
                      (ROOT / 'shared/java/classpath.txt').read_text().strip()])
        log = stack.enter_context((output / (identity + '.stderr.log')).open('w'))
        env = {**os.environ, 'OPENAI_API_KEY': 'synthetic-local-key', 'OPENAI_BASE_URL': model_url}
        proc = subprocess.Popen(['java', '-Xmx384m', '-cp', cp, 'eval.BankingRuntimeHost'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True,
            start_new_session=True, cwd=workspace, env=env)
        stack.callback(proc.stdout.close)
        stack.callback(proc.stdin.close)
        stack.callback(terminate_tree, proc)
        mailbox = queue.Queue()

        def reader():
            for line in proc.stdout:
                if line.startswith('TAU2_JSON:'):
                    mailbox.put(json.loads(line.removeprefix('TAU2_JSON:')))
            mailbox.put({'type': 'closed'})

        threading.Thread(target=reader, daemon=True).start()
        init = {'role': role, 'agent_id': identity, 'session_id': identity + '-fixture',
            'workspace': str(workspace), 'model': 'fixture-owner' if identity == owner_id else 'fixture-' + role,
            'domain_policy': 'Synthetic protocol fixture; no real bank operations.',
            'candidates': candidates, 'tools': tools, 'mcp_url': facade.url, 'mcp_token': facade.token,
            'language': 'en', 'system_prompt_version': 'evidence-todo-v1', **skill_init_payload()}
        if receipt_flow and role == 'main':
            init['receipt_context'] = str(receipt_context.path)
        if parent_wait_fault:
            init['parent_wait_seconds'] = 2
        if timeout_fault:
            init['remote_timeout_seconds'] = 2
        proc.stdin.write(json.dumps(init) + '\n')
        proc.stdin.flush()
        descriptor = mailbox.get(timeout=90)
        assert descriptor.get('type') == 'ready', descriptor
        descriptors.append(descriptor)
        return descriptor

    result = {'passed': False, 'external_model_calls': 0, 'business_scoring': 'not_applicable',
              'full_moa_acceptance': False, 'fixture': 'real MAIN/domain Runtime, scripted models, synthetic facts'}
    try:
        with ExitStack() as stack:
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            stack.callback(server.server_close)
            stack.callback(server.shutdown)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            model_url = f'http://127.0.0.1:{server.server_port}/v1'
            candidates = [{'id': candidate_id, 'description': 'Compare fixture card products', 'url': 'http://127.0.0.1:1'}]
            domain = host(stack, 'domain', candidate_id, candidates, model_url)
            candidates[0]['url'] = domain['url']
            if receipt_flow:
                candidates.append({'id': owner_id, 'description': 'Fixture fulfillment', 'url': 'http://127.0.0.1:1'})
                candidates[-1]['url'] = host(stack, 'domain', owner_id, candidates, model_url)['url']
            main = host(stack, 'main', 'banking-moa', candidates, model_url)
            context = uuid.uuid4().hex
            task_id = None

            def send(content):
                nonlocal task_id
                message = {'role': 'ROLE_USER', 'messageId': uuid.uuid4().hex, 'contextId': context,
                           'parts': [{'text': content}]}
                if task_id:
                    message['taskId'] = task_id
                request = {'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'SendMessage',
                           'params': {'message': message}}
                with urlopen(Request(main['url'] + '/a2a/', data=json.dumps(request).encode(),
                        headers={'Content-Type': 'application/json'}), timeout=60) as response:
                    raw = json.load(response)
                a2a.append({'request': request, 'response': raw})
                assert 'error' not in raw, raw
                reply = customer_reply(raw['result'].get('task', raw['result']))
                task_id = reply['runtime_task_id'] if reply['waiting'] else None
                assert not any('\u4e00' <= char <= '\u9fff' for char in reply['content']), reply
                return reply

            confirmation = send(query)
            assert confirmation['waiting'] and 'Yes or No' in confirmation['content'], confirmation
            assert query in confirmation['content'], confirmation
            question = send('Yes')
            assert question['waiting'] and 'fixture subscription' in question['content'], question
            if parent_wait_fault:
                start = time.monotonic()
                try:
                    send('Yes, I have the fixture subscription.')
                except ValueError:
                    state = a2a[-1]['response']['result']
                    assert state.get('task', state)['status']['state'] == 'TASK_STATE_FAILED'
                else:
                    raise AssertionError('Parent did not enforce the configured child wait budget')
                assert time.monotonic() - start < 4, 'Parent waited for child rather than the deadline'
                assert len(requests['fixture-domain']) == 2
                result.update(passed=True, checks=['parent propagates bounded wait failure on child resume',
                                                  'no duplicate child invocation'])
                return
            final = send('Yes, I have the fixture subscription.')
            assert not final['waiting'] and 'Fixture X' in final['content'], final
            if timeout_fault:
                time.sleep(5)
                domain_log = (output / (candidate_id + '.stderr.log')).read_text()
                main_log = (output / 'banking-moa.stderr.log').read_text()
                assert 'response watchdog fired' in main_log, 'Fault did not trigger'
                assert 'retryIn=' not in main_log, 'Uncertain invocation replayed'
                assert 'CONVERSATION_BUSY' not in domain_log + main_log, 'Overlapping execution'
                assert domain_log.count('A2A execute START') == 2, 'Unexpected domain invocation'
                result.update(passed=True, checks=['actual response timeout', 'no automatic resend',
                    'no conversation busy', 'exactly initial invocation plus one resume'],
                    fixture='transport failure injection; scripted MAIN output is not a business result')
                return
            if receipt_flow:
                assert len(official_calls) == 1
                for answer, expected_count in [('No.', 1), ('Yes.', 2)]:
                    confirm = send(follow_up)
                    assert confirm['waiting'] and owner_id in confirm['content'], confirm
                    decision = send(answer)
                    assert not decision['waiting'], decision
                    assert len(official_calls) == expected_count, (answer, official_calls)
                assert [c['id'].split('-skill-')[0] for c in official_calls] == [candidate_id, owner_id]
            assert not errors, errors
            assert all(len(requests[key]) == len(script) for key, script in scripts.items()), {k: len(v) for k, v in requests.items()}
            records = [json.loads(line) for line in (output / 'banking-moa/main-model-events.jsonl').read_text().splitlines()]
            captured = [r for r in records if r['event'] == 'model_request']
            assert len(captured) == len(requests['fixture-main']), len(captured)
            # Core stores metadata and flattened tools; normalize only those representation differences.
            def wire_message(message):
                # BaseModelClient sends a ToolMessage's call ID but omits its internal name.
                normalized = {key: message[key] for key in ('role', 'content', 'tool_call_id')
                              if message.get(key) is not None}
                if message.get('toolCalls'):
                    normalized['tool_calls'] = [
                        {'id': call['id'], 'type': call['type'],
                         'function': {'name': call['name'], 'arguments': call['arguments']}}
                        for call in message['toolCalls']]
                return normalized

            for record, actual in zip(captured, requests['fixture-main']):
                assert [wire_message(m) for m in record['data']['messages']] == actual['messages'], 'MAIN messages differ from wire'
                assert [{'type': tool['type'], 'function': {k: v for k, v in tool.items() if k != 'type'}}
                        for tool in record['data']['tools']] == actual['tools'], 'MAIN tools differ from wire'
            if receipt_flow:
                assert len(official_calls) == 2
                assert official_calls[0]['arguments']['agent_tool_name'] == 'fixture_owned'
                assert 'DOMAIN_NOT_AUTHORIZED' in json.dumps(requests['fixture-domain'][-1])
                main_input = json.dumps(requests['fixture-main'][-1])
                assert 'Synthetic receipt R-471' in main_input and 'refused before submission' in main_input
                result['receipt_flow_verified'] = True
            responses = [r for r in records if r['event'] == 'model_response']
            assert [r['call_id'] for r in captured] == [r['call_id'] for r in responses], 'Incomplete MAIN response capture'
            assert 'With the confirmed fixture subscription' in json.dumps(captured), 'Domain evidence missing at MAIN'
            assert "'At least' includes equality" in json.dumps(requests['fixture-main'][0]), 'Updated prompt did not reach model'
            domain_context = json.dumps(requests['fixture-domain'][-1])
            assert 'Yes, I have the fixture subscription.' in domain_context, 'Customer answer not forwarded'
            meta = json.loads((output / 'banking-moa/main-prompt-meta.json').read_text())
            assert meta['sha256'] == hashlib.sha256((output / 'banking-moa/main-prompt.md').read_bytes()).hexdigest()
            result.update(passed=True, main_model_calls=len(captured), domain_model_calls=len(requests['fixture-domain']),
                checks=['native plan/bind/finalize/execute', 'English confirmation', 'real A2A domain delegation',
                        'domain INPUT_REQUIRED and associated answer', 'domain facts reach MAIN',
                        'updated prompt reaches model', 'MAIN messages, tool calls and schemas match HTTP model inputs',
                        'MAIN input/output call IDs match'],
                prompt_version=meta['version'])
    except Exception as error:
        result['error'] = repr(error)
        raise
    finally:
        (output / 'model-requests.json').write_text(json.dumps(requests, indent=2))
        (output / 'a2a.json').write_text(json.dumps(a2a, indent=2))
        (output / 'runtime-descriptors.json').write_text(json.dumps(descriptors, indent=2))
        result['model_fixture_errors'] = errors
        result['sources_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), *sorted((ARM / 'java/src/eval').glob('*.java')),
                      *sorted((ARM / 'java/patches').glob('*'))]}
        artifacts = [*sorted((ARM / 'java/target/classes').rglob('*.class')),
                     *sorted((ROOT / 'shared/java/target/classes').rglob('*.class'))]
        artifacts += [Path(name) for name in (ROOT / 'shared/java/classpath.txt').read_text().strip().split(os.pathsep)]
        result['artifacts_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout-fault', action='store_true')
    parser.add_argument('--receipt-flow', action='store_true')
    parser.add_argument('--parent-wait-fault', action='store_true')
    args = parser.parse_args()
    run(args.output, args.timeout_fault, args.receipt_flow, args.parent_wait_fault)
