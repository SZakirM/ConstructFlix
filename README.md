# ConstructFlix

A Flask-based construction project scheduling and team collaboration application.

## Overview

ConstructFlix provides project tracking, task management, scheduling, team invites, and API access for construction teams. It is built on Flask with server-rendered UI templates, SQLAlchemy models, and optional PostgreSQL support.

## Key Features

- User authentication: register, login, logout, profile, forgot password
- Dashboard with project, task, milestone, and budget summary cards
- Project management: create, view, start, delete
- Project-level team invitations and WhatsApp share link
- Schedule and report views for each project
- REST API endpoints for projects, tasks, documents, resources, and imports
- Admin blueprint for user and project management
- File upload and import support for CSV/XLSX/XLS
- PostgreSQL support through `DATABASE_URL`, with SQLite fallback
- Rate limiting and security-focused cookie settings

## Requirements

- Python 3.11+
- pip
- PostgreSQL (optional, recommended for production)

## Installation

```powershell
git clone https://github.com/yourusername/construction-scheduler.git
cd construction-scheduler
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the repository root and set the values you need.

```env
SECRET_KEY=change-this
DATABASE_URL=postgresql://user:password@localhost:5432/constructflix_dev
SQLALCHEMY_TRACK_MODIFICATIONS=False
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@constructflix.local
DOMAIN=localhost:5000
HOST=127.0.0.1
PORT=5000
FLASK_DEBUG=True
```

> Note: If `DATABASE_URL` starts with `postgres://`, the app will transparently convert it to `postgresql://`.

## Initialize the database

Run the initializer to create tables and seed sample accounts:

```powershell
python init_db.py
```

This script will create:

- Admin account: `admin` / `admin@example.com` / `AdminPass123`
- Test user: `testuser` / `test@example.com` / `password123`
- Sample project and task

## Running the application

Run the Flask app with:

```powershell
python run.py
```

Or set environment variables first:

```powershell
set PORT=5402&& set HOST=127.0.0.1&& python run.py
```

Then open:

```
http://127.0.0.1:5000
```

## Testing

Run the repository tests with unittest:

```powershell
python -m unittest discover -s app/tests -p "test_*.py"
```

Or use the test runner script:

```powershell
python test_app.py
```

## Project Structure

- `app/` — Flask application package
- `app/routes/` — Blueprint routes for auth, main UI, API, admin, tasks, and gantt
- `app/models/` — SQLAlchemy model definitions
- `app/templates/` — Jinja2 HTML templates
- `app/static/` — CSS, JavaScript, images, uploads
- `run.py` — Application startup script
- `init_db.py` — Database initialization and seed data
- `requirements.txt` — Python dependencies

## API Endpoints

The app exposes RESTful API endpoints under `/api` including:

- `GET /api/health`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/<id>`
- `PUT /api/projects/<id>`
- `GET /api/projects/<id>/tasks`
- `POST /api/projects/<id>/tasks`
- `POST /api/projects/<id>/import`
- `POST /api/projects/<id>/upload`
- `GET /api/projects/<id>/documents`
- `GET /api/projects/<id>/resources`
- `POST /api/projects/<id>/resources`
- `POST /api/resources/<id>/allocate`
- `POST /api/resources/<id>/release`

## Docker Deployment (Production)

### Troubleshooting Docker on Windows
- Install Docker Desktop, enable WSL2 (`wsl --install` as admin, reboot).
- Start Docker Desktop GUI (tray green).
- Verify: `docker info` no errors.
- Service: `sc start com.docker.service` (admin).

### Deploy
1. Copy `.env.example` to `.env` (edit secrets):
```
POSTGRES_DB=constructflix
POSTGRES_USER=constructflix_user
POSTGRES_PASSWORD=securepass
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=app_password
DOMAIN=http://localhost
```

2. `docker compose up --build -d`

3. http://localhost (Nginx 80/443).
4. Logs: `docker compose logs -f`.
5. Down: `docker compose down -v`.

Services: Flask (gunicorn), Postgres13, Redis6, Nginx, Celery+Beat.

## Notes

- The app automatically creates the `instance/` folder and database tables when started.
- The default database is SQLite unless `DATABASE_URL` is provided.
- Logging and rate limiting are enabled by default.
