# Student Management System — REST API

A role-based backend service for managing students, courses, and enrollments,
built with **FastAPI**, **SQLAlchemy**, and **JWT authentication**.

Unlike a script that talks to a local database, this is a proper client-server
API: any frontend, mobile app, or another service can consume it over HTTP.

## Features

- **JWT authentication** with three roles — `admin`, `teacher`, `student` —
  enforced per-endpoint (e.g. only admins/teachers can create students; only
  admins can delete them).
- **Student, Course, and Enrollment management** with full CRUD.
- **Transcript & GPA endpoint** — computes credit-weighted GPA on the fly
  from a student's graded enrollments.
- **Search, filtering, and pagination** on the student list endpoint.
- **Layered architecture** — routers (HTTP) → services (business logic) →
  models (data), so logic is testable independent of the web framework.
- **Input validation** via Pydantic (e.g. grades must be 0–100, years 1–6).
- **Centralized error handling** — a global exception handler + explicit
  4xx responses (404 not found, 409 conflict, 403 forbidden) instead of
  raw stack traces.
- **14 automated tests** (pytest) covering auth, permissions, validation,
  and business logic (GPA calculation), run against an isolated in-memory DB.
- **Dockerized**, with a `docker-compose.yml` wiring the API to Postgres.
- **Auto-generated interactive API docs** (Swagger UI + ReDoc).

## Tech Stack

| Layer          | Choice                                   |
|----------------|-------------------------------------------|
| Framework      | FastAPI                                   |
| ORM            | SQLAlchemy 2.0                            |
| Validation     | Pydantic v2                               |
| Auth           | OAuth2 password flow + JWT (python-jose)  |
| Password hash  | bcrypt (passlib)                          |
| Database       | SQLite (dev) / PostgreSQL (docker-compose)|
| Testing        | pytest + FastAPI TestClient               |
| Containerization | Docker / docker-compose                 |

## Architecture

```
app/
├── main.py            # App entrypoint, middleware, global exception handler
├── config.py           # Environment-driven settings
├── database.py         # Engine/session factory
├── models.py            # SQLAlchemy ORM models (User, Student, Course, Enrollment)
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # Password hashing, JWT issuing/decoding, role guards
├── routers/              # HTTP layer — one router per resource
│   ├── auth.py
│   ├── students.py
│   ├── courses.py
│   └── enrollments.py
└── services/             # Business logic layer, framework-agnostic
    ├── student_service.py
    ├── course_service.py
    └── enrollment_service.py
tests/                    # pytest suite, isolated in-memory DB per run
```

**Why this layering?** Routers only handle HTTP concerns (status codes,
request/response shapes). All business rules — duplicate checks, GPA math,
"does this student exist" — live in the service layer, so they can be unit
tested without spinning up HTTP, and reused if a second interface (e.g. a
CLI or admin script) is ever added.

## Data Model

- **User** — login identity (email + hashed password + role). Kept separate
  from `Student` because not every user is a student (admins/teachers aren't),
  and this avoids coupling auth concerns to academic records.
- **Student** — academic profile (roll number, name, department, year).
- **Course** — a course with a code, title, and credit value.
- **Enrollment** — join entity between Student and Course carrying the
  grade; a unique constraint on `(student_id, course_id)` prevents duplicate
  enrollment, and cascading deletes keep the data consistent.

## Getting Started

### Option A — Local (SQLite, zero setup)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # defaults already work out of the box
python seed.py                   # optional: adds demo students/courses/admin
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs
Demo admin login (after seeding): `admin@sms.com` / `admin123`

### Option B — Docker (API + PostgreSQL)

```bash
docker-compose up --build
```

### Running tests

```bash
pytest -v
```

## Example Usage

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sms.com","password":"admin123","role":"admin"}'

# Login (OAuth2 form fields)
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=admin@sms.com&password=admin123"

# Create a student (use the access_token from login)
curl -X POST http://127.0.0.1:8000/students \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"roll_number":"SVIT001","first_name":"Manjunath","last_name":"KR","email":"manjunath@sms.com","department":"CSE","year_of_study":3}'
```

## Frontend

A lightweight vanilla HTML/CSS/JS frontend lives in `app/static/` and is served
directly by FastAPI at `/` (via `StaticFiles`) — no separate frontend server,
build step, or `npm install` needed. It covers registration/login, student
CRUD with search & pagination, course management, enrollment + grading, and
a transcript/GPA view, all against the same REST API described below.

**Route precedence matters here:** in `app/main.py`, the API routers
(`/auth`, `/students`, `/courses`, `/enrollments`, `/health`) are registered
*before* the static mount at `/`. Starlette matches routes in registration
order, so API paths resolve to the API and everything else falls through to
the static files — that's what makes both "the frontend loads at `/`" and
"the API still works" true at once. If you ever see `{"detail":"Not Found"}`
at `/`, it means either the static mount is missing/misordered, or the
`app/static/index.html` file didn't make it into the deployed build.

## Deploying to Render

This repo includes a `render.yaml` Blueprint, so the easiest path is:
**New → Blueprint** in the Render dashboard, point it at this repo, and Render
reads the config automatically.

If configuring manually instead (New → Web Service), set:

| Setting | Value |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

**The two things that most commonly break this on Render:**
1. **Binding to the wrong host/port.** Render assigns a port at runtime via
   the `$PORT` environment variable and routes traffic to it — the app must
   bind to `0.0.0.0:$PORT`, not `127.0.0.1` or a hardcoded port, or Render's
   health checks and routing can't reach it.
2. **The static frontend not being present in the deployed build.** Since
   `app/static/` is committed to the repo, this isn't an issue as long as
   you're deploying from this repo as-is — but if you regenerate or `.gitignore`
   that folder later, the root route will 404 again.

**Database note:** the default `sqlite:///./sms.db` works for a demo, but
Render's free-tier filesystem is ephemeral — data is wiped on every redeploy
or restart. For anything you want to persist, either add a
[Render Disk](https://render.com/docs/disks) mounted at the app's working
directory, or point `DATABASE_URL` at a managed Postgres instance (Render
offers this natively; SQLAlchemy needs no code changes, just the connection
string and `psycopg2-binary` added to `requirements.txt`).

## Possible Extensions

- Alembic migrations for schema versioning in production.
- Attendance tracking module.
- Refresh tokens + token revocation.
- Rate limiting on the auth endpoints.
- CI pipeline (GitHub Actions) running `pytest` on every push.

## Author

Manjunath K R — B.E. Computer Science and Engineering, Sai Vidya Institute of Technology.
