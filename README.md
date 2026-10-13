[README.md](https://github.com/user-attachments/files/33405103/README.md)[U# Smart Student Planner

A responsive, full-stack academic task planner built with **Python**, **SQLite**, **JavaScript**, **HTML**, and **CSS**. Create assignments, organize them by course, set priorities and deadlines, track progress, and monitor overdue work. Designed as a software engineering portfolio project.

## Features

- Add, edit, complete, and delete tasks (CRUD)
- Course labels, notes, due dates, and priority levels
- Search tasks and filter by status or priority
- Live dashboard: total, completed, due today, and overdue
- SQLite persistence across server restarts
- Responsive layout for desktop and mobile
- JSON REST API with server-side validation and parameterized SQL
- Automated unit tests
- **No third-party packages required** (Python standard library only)

## Quick start

Requires **Python 3.10+**.

```bash
git clone https://github.com/Racks-work/smart-student-planner.git
cd smart-student-planner
python app.py
```

Open **http://127.0.0.1:8000** in your browser. A local `planner.db` is created automatically on first run. Stop with Ctrl+C.

To use another port:

```bash
PORT=8080 python app.py
```

On Windows PowerShell:

```powershell
$env:PORT = '8080'
python app.py
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/tasks` | List tasks; supports `q`, `status`, `priority` query parameters |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/{id}` | Retrieve one task |
| PATCH | `/api/tasks/{id}` | Update task fields |
| DELETE | `/api/tasks/{id}` | Delete a task |
| GET | `/api/summary` | Dashboard totals |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Finish Python lab","course":"Computer Science","due_date":"2026-12-10","priority":"high"}'
```

Task fields: `title` (required, 1–120 chars), `course` (optional), `notes` (optional), `due_date` (`YYYY-MM-DD` or null), `priority` (`low`, `medium`, `high`), and `status` (`todo`, `in_progress`, `done`). Invalid inputs return HTTP 400; unknown tasks return 404.

## Architecture

```text
Browser (HTML/CSS/JavaScript)
       |
       | fetch JSON /api/*
       v
Python ThreadingHTTPServer (app.py)
       |
       | parameterized SQL
       v
SQLite database (planner.db)
```

## Project structure

```text
smart-student-planner/
├── app.py                 # HTTP server, REST endpoints, data validation, SQLite
├── static/
│   ├── index.html         # Accessible UI and task editor
│   ├── style.css          # Responsive design
│   └── app.js             # Client-side API integration and interactions
├── tests/
│   └── test_app.py        # Unit tests for CRUD, filtering, and validation
├── .gitignore
├── LICENSE
└── README.md
```

## Security and deployment notes

This is a **single-user local demo**, not a hosted multi-user product. By default the server binds to `127.0.0.1`, so it is accessible only from your computer. It has **no authentication, user accounts, HTTPS, or rate limiting**. Do not expose it to the public internet or store sensitive information without adding those protections. SQL values use bound parameters; text entered by users is escaped before insertion into HTML. The SQLite database is excluded from Git.

## Future enhancements

- User authentication and per-user data isolation
- Recurring assignments and calendar view
- Email/push reminders
- PostgreSQL migration and cloud deployment
- CI workflow and end-to-end browser tests

## Portfolio description

> Developed a full-stack academic task manager with a Python REST API, SQLite persistence, and a responsive JavaScript interface. Implemented CRUD operations, search/filter controls, due-date analytics, input validation, and automated tests.

## Author

Built by [Racks-work](https://github.com/Racks-work) as a software engineering portfolio project.
ploading README.md…]()

