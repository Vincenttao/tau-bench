"""Episode-local Streamable HTTP MCP facade. Only the official scheduler mutates bank state."""
import hashlib
import json
import queue
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import jsonschema


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class KnowledgeProjection:
    # Exact official BM25 formatter; unknown formats always retain the complete response.
    pattern = re.compile(r'(?m)^(\d+)\. ([^\n]*)\n   ID: ([^\n]+)\n   Score: ([^\n]+)\n   Content: ')

    def __init__(self):
        self.docs = {}
        self.stale = 0
        self.todo_version = None
        self.warned = set()

    def project(self, operation, content, todo_version):
        if operation != 'KB_search':
            return content, {}
        matches = list(self.pattern.finditer(content))
        timing = content.rfind('\n\n[Timing:')
        if not matches or matches[0].start() != 0 or timing < 0:
            return content, {'projection': 'raw_unknown_format'}
        output, new, repeats = [], 0, 0
        for i, match in enumerate(matches):
            end = matches[i+1].start() if i+1 < len(matches) else timing
            body = content[match.end():end]
            ref = 'kb:' + digest(match[3] + '\0' + body)
            header = content[match.start():match.end()]
            if ref in self.docs:
                output.append(header + '[Previously observed document: ' + ref + ']\n\n')
                repeats += 1
            else:
                self.docs[ref] = body
                output.append(header + body + '\n[doc_ref: ' + ref + ']\n')
                new += 1
        output.append(content[timing:])
        self.stale = self.stale + 1 if not new and todo_version == self.todo_version else 0
        self.todo_version = todo_version
        state = (tuple(sorted(self.docs)), todo_version)
        if self.stale >= 3 and state not in self.warned:
            output.append('\nProgress observation: three knowledge searches added no new document or Todo change. Identify the missing fact; change the query or ask the customer. This is not an instruction to skip verification.')
            self.warned.add(state)
        view = ''.join(output)
        return view, {'new_documents': new, 'repeated_documents': repeats, 'unique_documents': len(self.docs),
                      'raw_bytes': len(content.encode()), 'model_view_bytes': len(view.encode()), 'progress_hints': len(self.warned)}


class BenchmarkMcpFacade:
    def __init__(self, schemas, session_id, events, directory, timeout=120):
        self.schemas = {t['function']['name']: t['function'] for t in schemas}
        self.session_id, self.events = session_id, events
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_urlsafe(32)
        self.protocol_session = secrets.token_urlsafe(24)
        self.timeout = timeout
        self.lock = threading.RLock()
        self.pending, self.invocations = {}, {}
        self.projection = KnowledgeProjection()
        self.closed = False
        facade = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, value=None, initialize=False):
                body = b'' if value is None else json.dumps(value, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                if initialize:
                    self.send_header('Mcp-Session-Id', facade.protocol_session)
                self.end_headers()
                self.wfile.write(body)

            def authorized(self):
                return self.path == '/mcp' and self.headers.get('Authorization') == 'Bearer ' + facade.token

            def do_GET(self):
                self.reply(405 if self.authorized() else 403)

            def do_DELETE(self):
                self.reply(200 if self.authorized() and self.headers.get('Mcp-Session-Id') == facade.protocol_session else 403)

            def do_POST(self):
                if not self.authorized():
                    self.reply(403)
                    return
                request = {}
                start = time.time()
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    if not 0 < size <= 4_000_000:
                        raise ValueError('Invalid request size')
                    request = json.loads(self.rfile.read(size))
                    method = request.get('method')
                    if method != 'initialize' and self.headers.get('Mcp-Session-Id') != facade.protocol_session:
                        self.reply(404)
                        return
                    if method == 'initialize':
                        version = request.get('params', {}).get('protocolVersion')
                        if version not in ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'):
                            version = '2025-03-26'
                        result = {'protocolVersion': version, 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'tau3-episode-facade', 'version': '0.3.2'}}
                    elif method.startswith('notifications/'):
                        self.reply(202)
                        return
                    elif method == 'ping':
                        result = {}
                    elif method == 'tools/list':
                        result = {'tools': [facade.mcp_tool(name, spec) for name, spec in facade.schemas.items()]}
                    elif method == 'tools/call':
                        params = request['params']
                        name = params['name']
                        if name not in facade.schemas:
                            raise ValueError('Unknown MCP tool')
                        value = facade.invoke(name, params['arguments'], request.get('id'))
                        result = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}], 'isError': not value['success']}
                    else:
                        raise ValueError('Unsupported MCP method')
                    self.reply(200, {'jsonrpc': '2.0', 'id': request['id'], 'result': result}, method == 'initialize')
                except (ValueError, KeyError, jsonschema.ValidationError) as ex:
                    self.reply(200, {'jsonrpc': '2.0', 'id': request.get('id'), 'error': {'code': -32602, 'message': str(ex)[:1000]}})
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    facade.log('mcp', {'method': request.get('method'), 'request_id': request.get('id'), 'tool_name': request.get('params', {}).get('name'), 'start': start, 'end': time.time()})

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:%d/mcp' % self.server.server_port

    @staticmethod
    def mcp_tool(name, spec):
        original = spec.get('parameters', {'type': 'object', 'properties': {}})
        return {'name': name, 'description': spec.get('description', name), 'inputSchema': {
            'type': 'object', 'properties': {
                'skill_id': {'type': 'string'}, 'arguments': original,
                'session_id': {'type': 'string'}, 'invocation_id': {'type': 'string'},
                'todo_version': {'type': 'integer'}},
            'required': ['skill_id', 'arguments', 'session_id', 'invocation_id'],
            'additionalProperties': False}}

    def log(self, kind, data):
        with self.lock:
            with (self.directory / (kind + '.jsonl')).open('a') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')

    def invoke(self, operation, args, mcp_id=None):
        if args.get('session_id') != self.session_id or args.get('skill_id') not in ('banking-mcp', 'dispute-processing'):
            raise ValueError('Skill/session not authorized')
        if operation not in self.schemas and operation != 'evidence_read':
            raise ValueError('Unknown MCP tool')
        if 'operation' in args:
            raise ValueError('Operation must be supplied as the MCP tool name')
        parameters, call_id = args['arguments'], args['invocation_id']
        if not isinstance(call_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,150}', call_id):
            raise ValueError('Invalid invocation id')
        if operation == 'evidence_read':
            jsonschema.validate(parameters, {'type': 'object', 'properties': {'doc_ref': {'type': 'string'}, 'start': {'type': 'integer', 'minimum': 0}, 'length': {'type': 'integer', 'minimum': 1, 'maximum': 24000}}, 'required': ['doc_ref'], 'additionalProperties': False})
            text = self.projection.docs.get(parameters['doc_ref'])
            if text is None:
                raise ValueError('Unknown episode evidence reference')
            start, length = parameters.get('start', 0), parameters.get('length', 12000)
            self.log('evidence-read', {'id': call_id, 'arguments': parameters})
            return {'success': True, 'content': text[start:start+length], 'total_characters': len(text)}
        if operation not in self.schemas:
            raise ValueError('Operation is not in the deployed catalog')
        jsonschema.validate(parameters, self.schemas[operation]['parameters'])
        signature = json.dumps([operation, parameters], sort_keys=True)
        with self.lock:
            if self.closed:
                raise ValueError('Episode closed')
            if call_id in self.invocations:
                record = self.invocations[call_id]
                if record['signature'] != signature:
                    raise ValueError('Invocation id reused with different arguments')
                # Fail closed: no automatic business replay, including transport retries.
                return {'success': False, 'error': 'DUPLICATE_INVOCATION_NOT_REEXECUTED', 'official_call_id': call_id}
            slot = queue.Queue(maxsize=1)
            self.invocations[call_id] = {'signature': signature}
            self.pending[call_id] = slot
            self.log('skill', {'id': call_id, 'mcp_request_id': mcp_id, 'operation': operation, 'arguments': parameters, 'start': time.time()})
            self.events.put({'type': 'tool_calls', 'tool_calls': [{'id': call_id, 'name': operation, 'arguments': parameters}]})
        try:
            response = slot.get(timeout=self.timeout)
        except queue.Empty:
            response = {'content': 'Official scheduler did not return before timeout; do not retry an uncertain write.', 'error': True}
        finally:
            with self.lock:
                self.pending.pop(call_id, None)
        raw = response['content']
        view, metrics = self.projection.project(operation, raw, args.get('todo_version', 0))
        result = {'success': not response.get('error', False), 'official_call_id': call_id, 'content': view, 'raw_sha256': digest(raw)}
        self.log('evidence', {'id': call_id, 'operation': operation, 'raw': raw, 'model_view': view, 'result': result, 'metrics': metrics, 'end': time.time()})
        return result

    def deliver(self, call_id, content, error):
        with self.lock:
            slot = self.pending.get(call_id)
            if slot is None:
                raise ValueError('Unknown or expired official call id: ' + call_id)
            slot.put_nowait({'content': content, 'error': error})

    def close(self):
        with self.lock:
            self.closed = True
            for slot in self.pending.values():
                try:
                    slot.put_nowait({'content': 'Episode closed', 'error': True})
                except queue.Full:
                    pass
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
