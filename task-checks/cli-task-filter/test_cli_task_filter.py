"""Run both CLI binaries against a loopback-only, non-empty task-feed fixture."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

assert os.environ.get('BOUNTY_REPO'), 'Set BOUNTY_REPO to your agentswarm-cli branch checkout.'
REPO = Path(os.environ['BOUNTY_REPO']).resolve()
assert (REPO / 'node/bin/agentswarm.js').is_file(), 'BOUNTY_REPO must contain node/bin/agentswarm.js'
assert (REPO / 'python/src/agentswarm_cli/__main__.py').is_file(), 'BOUNTY_REPO must contain the Python CLI'

# The API selects type/parent; the existing CLI selects open/accepted statuses.
# Mixed types make missing type=task meaningful without inventing client-side type filtering.
ROWS = [
    {'id': 'task_one', 'type': 'task', 'underTaskId': 'post_parent', 'title': 'First útil', 'status': 'open'},
    {'id': 'note_one', 'type': 'note', 'underTaskId': 'post_parent', 'title': 'Not a task', 'status': 'open'},
    {'id': 'task_two', 'type': 'task', 'underTaskId': 'post_parent', 'title': 'Accepted', 'status': 'accepted'},
    {'id': 'task_closed', 'type': 'task', 'underTaskId': 'post_parent', 'title': 'Closed', 'status': 'closed'},
    {'id': 'task_other', 'type': 'task', 'underTaskId': 'other_parent', 'title': 'Another parent', 'status': 'open'},
    {'id': 'result_one', 'type': 'result', 'underTaskId': 'post_parent', 'title': 'Result', 'status': 'open'},
    {'id': 'task_three', 'type': 'task', 'underTaskId': 'post_parent', 'title': 'Last 第二', 'status': 'open'},
]
FOLLOWUP = [
    {'id': 'task_four', 'type': 'task', 'underTaskId': 'post_parent', 'title': 'Next page', 'status': 'open'},
    {'id': 'offer_one', 'type': 'offer', 'underTaskId': 'post_parent', 'title': 'Offer', 'status': 'open'},
]
CURSOR = 'page:two/with+symbols'

@contextmanager
def feed():
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query)
            calls.append((parsed.path, query))
            rows = FOLLOWUP if 'before' in query else ROWS
            if query.get('type'):
                rows = [r for r in rows if r['type'] == query['type'][0]]
            if query.get('task'):
                rows = [r for r in rows if r['underTaskId'] == query['task'][0]]
            payload = json.dumps({'items': rows, 'nextCursor': None if 'before' in query else CURSOR}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

def run(language, args, tmp_path, base='http://127.0.0.1:1'):
    env = dict(os.environ, NODE_NO_WARNINGS='1', AGENTSWARM_BASE_URL=base, AGENTSWARM_API_KEY='',
               AGENTSWARM_CONFIG_DIR=str(tmp_path), PYTHONPATH=str(REPO / 'python/src'))
    command = ['node', str(REPO / 'node/bin/agentswarm.js')] if language == 'node' else [sys.executable, '-m', 'agentswarm_cli']
    return subprocess.run(command + args, env=env, capture_output=True, text=True, timeout=5)

CASES = [
    ('parent', ['--task', 'post_parent'], {'task': ['post_parent']}, [ROWS[0], ROWS[2], ROWS[6]], CURSOR),
    ('followup', ['--task', 'post_parent', '--before', CURSOR], {'task': ['post_parent'], 'before': [CURSOR]}, [FOLLOWUP[0]], None),
    ('plain', [], {}, [ROWS[0], ROWS[2], ROWS[4], ROWS[6]], CURSOR),
    ('other-filters', ['--task', 'post_parent', '--sort', 'top', '--bounties', 'only', '--limit', '7'],
     {'task': ['post_parent'], 'sort': ['top'], 'bounties': ['only'], 'limit': ['7']}, [ROWS[0], ROWS[2], ROWS[6]], CURSOR),
    ('all', ['--task', 'post_parent', '--all'], {'task': ['post_parent']}, [ROWS[0], ROWS[2], ROWS[3], ROWS[6]], CURSOR),
    ('empty', ['--task', 'missing_parent'], {'task': ['missing_parent']}, [], CURSOR),
]

@pytest.mark.parametrize('language', ['node', 'python'])
@pytest.mark.parametrize('name,args,query,items,cursor', CASES, ids=[c[0] for c in CASES])
def test_tasks_preserves_items_and_manual_paging(language, name, args, query, items, cursor, tmp_path):
    with feed() as (base, calls):
        result = run(language, ['tasks', *args, '--json'], tmp_path, base)
    assert result.returncode == 0, f'{language} {name}: {result.stderr}'
    assert calls == [('/api/feed', {'type': ['task'], **query})], 'Exactly one page per invocation; preserve filters'
    actual = json.loads(result.stdout)
    assert actual['items'] == items, 'Return the actual page items in feed order, preserving existing status filtering'
    assert 'nextCursor' in actual, 'Preserve the cursor, including explicit null'
    assert actual['nextCursor'] == cursor

@pytest.mark.parametrize('language', ['node', 'python'])
def test_tasks_rejects_retired_mission_before_http(language, tmp_path):
    with feed() as (base, calls):
        result = run(language, ['tasks', '--mission', 'post_parent', '--json'], tmp_path, base)
    assert result.returncode == 2, f'{language}: {result.stderr}'
    assert calls == [], 'Retired --mission must fail locally before HTTP'

@pytest.mark.parametrize('language', ['node', 'python'])
def test_tasks_help_names_parent_filter(language, tmp_path):
    result = run(language, ['--help'], tmp_path)
    assert result.returncode == 0
    task_help = result.stdout.split('  tasks ', 1)[1].split('  read ', 1)[0]
    assert '--task' in task_help and '--mission' not in task_help
