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

## Possible Extensions

- Alembic migrations for schema versioning in production.
- Attendance tracking module.
- Refresh tokens + token revocation.
- Rate limiting on the auth endpoints.
- CI pipeline (GitHub Actions) running `pytest` on every push.

## Author

Manjunath K R — B.E. Computer Science and Engineering, Sai Vidya Institute of Technology.
