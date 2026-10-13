"""Smart Student Planner: dependency-free Python/SQLite JSON API and web server."""
import json
import os
import sqlite3
from datetime import datetime, date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('PLANNER_DB', ROOT / 'planner.db'))
STATIC = ROOT / 'static'
MAX_BODY = 64 * 1024
STATUSES = {'todo', 'in_progress', 'done'}
PRIORITIES = {'low', 'medium', 'high'}


def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=10000')
    return con


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, course TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '', due_date TEXT,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )''')
        con.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)')


def validate(data, partial=False):
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object')
    allowed = {'title', 'course', 'notes', 'due_date', 'priority', 'status'}
    if not partial and 'title' not in data:
        raise ValueError('Title is required')
    if not data or any(k not in allowed for k in data):
        raise ValueError('Unknown or missing fields')
    out = {}
    for key, value in data.items():
        if key in {'title', 'course', 'notes'}:
            if not isinstance(value, str) or len(value) > (2000 if key == 'notes' else 120):
                raise ValueError(f'Invalid {key}')
            value = value.strip()
            if key == 'title' and not value:
                raise ValueError('Title cannot be empty')
        elif key == 'due_date':
            if value in ('', None):
                value = None
            elif not isinstance(value, str):
                raise ValueError('Invalid due date')
            else:
                try:
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError()
                except ValueError:
                    raise ValueError('Due date must be YYYY-MM-DD')
        elif key == 'priority' and value not in PRIORITIES:
            raise ValueError('Invalid priority')
        elif key == 'status' and value not in STATUSES:
            raise ValueError('Invalid status')
        out[key] = value
    return out


def list_tasks(filters=None):
    filters = filters or {}
    clauses, params = [], []
    for key in ('status', 'priority'):
        if filters.get(key):
            if filters[key] not in (STATUSES if key == 'status' else PRIORITIES):
                raise ValueError(f'Invalid {key} filter')
            clauses.append(f'{key} = ?')
            params.append(filters[key])
    if filters.get('q'):
        clauses.append('(title LIKE ? OR course LIKE ? OR notes LIKE ?)')
        needle = '%' + filters['q'][:120].replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        clauses[-1] = clauses[-1].replace('LIKE ?', "LIKE ? ESCAPE '\\'")
        params.extend([needle] * 3)
    where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
    with connect() as con:
        return [dict(row) for row in con.execute('SELECT * FROM tasks' + where + ' ORDER BY (due_date IS NULL), due_date, CASE priority WHEN \'high\' THEN 0 WHEN \'medium\' THEN 1 ELSE 2 END, id DESC', params)]


def get_task(task_id):
    with connect() as con:
        row = con.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        return dict(row) if row else None


def create_task(data):
    data = validate(data)
    with connect() as con:
        cur = con.execute('INSERT INTO tasks (title, course, notes, due_date, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
                          (data['title'], data.get('course', ''), data.get('notes', ''), data.get('due_date'), data.get('priority', 'medium'), data.get('status', 'todo')))
        task_id = cur.lastrowid
    return get_task(task_id)


def update_task(task_id, data):
    data = validate(data, partial=True)
    with connect() as con:
        if not con.execute('SELECT id FROM tasks WHERE id=?', (task_id,)).fetchone():
            return None
        sets = ', '.join(f'{key}=?' for key in data)
        con.execute(f'UPDATE tasks SET {sets}, updated_at=CURRENT_TIMESTAMP WHERE id=?', (*data.values(), task_id))
    return get_task(task_id)


def delete_task(task_id):
    with connect() as con:
        return con.execute('DELETE FROM tasks WHERE id=?', (task_id,)).rowcount > 0


def summary():
    today = date.today().isoformat()
    with connect() as con:
        row = con.execute('''SELECT COUNT(*) total,
            COALESCE(SUM(CASE WHEN status='done' THEN 1 ELSE 0 END), 0) completed,
            COALESCE(SUM(CASE WHEN status!='done' AND due_date < ? THEN 1 ELSE 0 END), 0) overdue,
            COALESCE(SUM(CASE WHEN status!='done' AND due_date = ? THEN 1 ELSE 0 END), 0) due_today
            FROM tasks''', (today, today)).fetchone()
    return dict(row)


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        if 'application/json' not in self.headers.get('Content-Type', ''):
            raise ValueError('Content-Type must be application/json')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Invalid Content-Length')
        if length <= 0 or length > MAX_BODY:
            raise ValueError('Request body missing or too large')
        try:
            return json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError('Invalid JSON')

    def route(self):
        path = urlparse(self.path)
        if path.path == '/':
            return self.static('index.html', 'text/html; charset=utf-8')
        if path.path in ('/static/style.css', '/static/app.js'):
            name = path.path.split('/')[-1]
            return self.static(name, 'text/css' if name.endswith('.css') else 'application/javascript')
        if path.path == '/api/summary' and self.command == 'GET':
            return self.respond(200, summary())
        if path.path == '/api/tasks':
            if self.command == 'GET':
                filters = {k: v[0] for k, v in parse_qs(path.query).items()}
                return self.respond(200, {'tasks': list_tasks(filters)})
            if self.command == 'POST':
                return self.respond(201, create_task(self.read_json()))
        if path.path.startswith('/api/tasks/'):
            tail = path.path.removeprefix('/api/tasks/')
            if not tail.isdigit() or int(tail) < 1:
                return self.respond(404, {'error': 'Not found'})
            task_id = int(tail)
            if self.command == 'GET':
                task = get_task(task_id)
                return self.respond(200, task) if task else self.respond(404, {'error': 'Not found'})
            if self.command == 'PATCH':
                task = update_task(task_id, self.read_json())
                return self.respond(200, task) if task else self.respond(404, {'error': 'Not found'})
            if self.command == 'DELETE':
                return self.respond(200, {'deleted': True}) if delete_task(task_id) else self.respond(404, {'error': 'Not found'})
        self.respond(404, {'error': 'Not found'})

    def static(self, filename, content_type):
        data = (STATIC / filename).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.handle_route()

    def do_POST(self):
        self.handle_route()

    def do_PATCH(self):
        self.handle_route()

    def do_DELETE(self):
        self.handle_route()

    def handle_route(self):
        try:
            self.route()
        except ValueError as e:
            self.respond(400, {'error': str(e)})
        except Exception:
            self.respond(500, {'error': 'Internal server error'})
            raise


if __name__ == '__main__':
    init_db()
    host = os.environ.get('PLANNER_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'Smart Student Planner running at http://{host}:{port}', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
