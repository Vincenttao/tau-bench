"""Read-only local viewer for benchmark conversations and internal agent events."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'viewer'


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def records(path, warnings):
    rows = []
    try:
        with path.open(encoding='utf-8') as stream:
            for line, value in enumerate(stream, 1):
                if not value.strip():
                    continue
                try:
                    item = json.loads(value)
                    if not isinstance(item, dict):
                        raise ValueError('expected object')
                    rows.append((line, item))
                except ValueError:
                    warnings.append(f'{path.name}:{line} 无法解析，已跳过（文件可能仍在写入）')
    except OSError:
        warnings.append(f'{path.name} 无法读取')
    return rows


def inside(path, root):
    return path.resolve().is_relative_to(root.resolve())


def catalog(root=ROOT):
    paths = set()
    for pattern in ('runs/manifest.json', 'runs/*/manifest.json', 'experiments/*/runs/*/manifest.json'):
        paths.update(p.resolve() for p in root.glob(pattern) if inside(p, root))
    result = {}
    for path in sorted(paths):
        manifest = read_json(path, {})
        if not isinstance(manifest, dict) or not isinstance(manifest.get('episodes'), list):
            continue
        relative = path.parent.relative_to(root.resolve()).as_posix()
        ident = hashlib.sha256(relative.encode()).hexdigest()[:16]
        result[ident] = (path.parent, manifest, relative)
    return result


def episode_folder(folder, episode):
    key = episode.get('key', '')
    path = folder / 'episodes' / key
    if not key or not inside(path, folder / 'episodes'):
        raise ValueError('invalid episode key')
    return path


def run_summary(ident, item):
    folder, manifest, relative = item
    episodes = []
    for index, episode in enumerate(manifest['episodes']):
        path = episode_folder(folder, episode)
        status = read_json(path / 'status.json', {}) or {}
        episodes.append({'id': str(index), 'task_id': episode.get('task_id', episode['key']),
                         'trial': episode.get('trial'), 'status': status.get('status', 'unknown'),
                         'reward': status.get('reward'), 'duration': status.get('duration'),
                         'termination_reason': status.get('termination_reason')})
    return {'id': ident, 'name': folder.name, 'path': relative, 'model': manifest.get('model'),
            'implementation': manifest.get('implementation'), 'episodes': episodes}


def text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)


def timestamp(record):
    # ISO timestamps in the official journal have no zone. Do not infer one.
    if record.get('time_ms') is not None:
        return str(record['time_ms']) + ' ms Unix'
    if record.get('start') is not None:
        return datetime.fromtimestamp(record['start']).astimezone().isoformat(timespec='milliseconds')
    return record.get('timestamp') or ''


def error_record(record):
    if not isinstance(record, dict):
        return False
    if record.get('success') is False or record.get('isError') is True or record.get('error') not in (None, False, ''):
        return True
    return any(error_record(record.get(key)) for key in ('data', 'result'))


def load_episode(folder, episode):
    path = episode_folder(folder, episode)
    warnings, events, raw = [], [], {}
    sources = []

    def add(source, locator, stream, category, title, body, record, *, error=False, call_id=None):
        ident = str(len(events))
        raw[ident] = record
        events.append({'id': ident, 'source': source.relative_to(folder).as_posix(),
                       'locator': locator, 'stream': stream, 'category': category,
                       'title': title, 'preview': text(body)[:650], 'time': timestamp(record),
                       'error': error or error_record(record), 'call_id': call_id})

    journal = path / 'official-trajectory.jsonl'
    if journal.exists():
        messages = records(journal, warnings)
        source = journal
        locator = lambda n: f'行 {n}'
    else:
        source = path / 'result.json'
        result = read_json(source, {}) or {}
        sims = result.get('simulations') or []
        values = sims[0].get('messages', []) if sims else []
        if not values:
            source = path / 'trajectory-unscored.json'
            partial = read_json(source, {}) or {}
            values = partial.get('messages', []) if isinstance(partial, dict) else []
        messages = list(enumerate(values, 1))
        locator = lambda n: f'messages[{n - 1}]'
    if source.exists():
        sources.append(source.relative_to(folder).as_posix())
    for number, message in messages:
        role = message.get('role', 'unknown')
        calls = message.get('tool_calls') or []
        category = 'conversation' if role in ('assistant', 'user') and not calls else 'tool'
        names = [c.get('name') or c.get('function', {}).get('name', '') for c in calls]
        title = {'assistant': 'Agent', 'user': '用户', 'tool': '官方工具返回'}.get(role, role)
        if names:
            title += ' → ' + ', '.join(names)
        body = message.get('content') or calls or message
        add(source, locator(number), 'official', category, title, body, message,
            call_id=message.get('tool_call_id') or (calls[0].get('id') if len(calls) == 1 else None))

    for source in sorted(path.glob('deepagent/*/deepagent-events.jsonl')):
        if not inside(source, path):
            continue
        sources.append(source.relative_to(folder).as_posix())
        for number, record in records(source, warnings):
            kind = record.get('event', 'unknown')
            data = record.get('data') or {}
            name = data.get('name', '') if isinstance(data, dict) else ''
            category = 'system'
            if kind.startswith('model_'):
                category = 'model'
            elif name in ('skill_tool', 'list_skill', 'invoke_skill') or kind == 'skill_result':
                category = 'skill'
            elif name.startswith('todo_'):
                category = 'todo'
            elif kind.startswith('tool_'):
                category = 'tool'
            elif kind.startswith('mcp_'):
                category = 'mcp'
            title = kind + (' · ' + name if name else '')
            # Keep full model context out of the list; raw source is available on demand.
            body = data
            if kind == 'model_request':
                body = '模型请求上下文（展开查看原始记录）'
            elif kind == 'model_response':
                body = {'content': data.get('content'), 'tool_calls': data.get('tool_calls'),
                        'usage_metadata': data.get('usage_metadata')}
            add(source, f'行 {number}', 'internal', category, title, body, record)

    for source in sorted(path.glob('deepagent/*/mcp/mcp.jsonl')):
        if not inside(source, path):
            continue
        sources.append(source.relative_to(folder).as_posix())
        skill_source = source.with_name('skill.jsonl')
        links = {}
        if skill_source.exists() and inside(skill_source, path):
            for number, row in records(skill_source, warnings):
                if row.get('mcp_request_id'):
                    links[row['mcp_request_id']] = (number, row)
        for number, record in records(source, warnings):
            linked = links.get(record.get('request_id'))
            detail = dict(record)
            if linked:
                detail['skill_record'] = linked[1]
                detail['skill_source'] = skill_source.relative_to(folder).as_posix()
                detail['skill_line'] = linked[0]
            title = record.get('method', 'MCP') + (' · ' + record['tool_name'] if record.get('tool_name') else '')
            add(source, f'行 {number}', 'mcp', 'mcp', title, detail, detail,
                call_id=linked[1].get('id') if linked else record.get('request_id'))
    counts = dict(Counter(e['category'] for e in events))
    if not events:
        warnings.append('此尝试尚无可读取轨迹，或文件格式暂不支持。')
    return {'events': events, 'counts': counts, 'warnings': warnings, 'sources': sources}, raw


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        try:
            if url.path in ('/', '/app.js', '/style.css'):
                name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[url.path]
                mime = {'index.html': 'text/html', 'app.js': 'text/javascript', 'style.css': 'text/css'}[name]
                self.send_data((ASSETS / name).read_bytes(), mime)
                return
            query = parse_qs(url.query)
            runs = catalog()
            if url.path == '/api/runs':
                value = {'runs': [run_summary(key, item) for key, item in runs.items()]}
            elif url.path in ('/api/episode', '/api/event'):
                folder, manifest, _ = runs[query['run'][0]]
                index = int(query['episode'][0])
                if index < 0:
                    raise KeyError('episode')
                episode = manifest['episodes'][index]
                bundle, raw = load_episode(folder, episode)
                value = bundle if url.path == '/api/episode' else raw[query['event'][0]]
            else:
                self.send_json({'error': 'Not found'}, 404)
                return
            self.send_json(value)
        except (KeyError, IndexError, ValueError):
            self.send_json({'error': '记录不存在或参数无效'}, 404)
        except OSError:
            self.send_json({'error': '文件读取失败，请刷新后重试'}, 500)

    def send_json(self, value, status=200):
        self.send_data(json.dumps(value, ensure_ascii=False).encode(), 'application/json', status)

    def send_data(self, body, mime, status=200):
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8877)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Trace viewer: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
