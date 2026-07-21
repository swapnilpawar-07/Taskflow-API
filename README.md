# TaskFlow API

A production-style Task Management REST API built with FastAPI, demonstrating the patterns recruiters and interviewers expect from a backend/full-stack SDE candidate: JWT authentication, per-user data isolation, pagination and filtering, rate limiting, input validation, auto-generated API docs, Docker packaging, and a tested CI pipeline.

Built as a portfolio project to demonstrate production API design — not tied to a specific business domain, so the same patterns apply directly to real-world backend work.

---

## Why This Project

Most portfolio API projects stop at "CRUD works." This one focuses on what separates a toy project from a production-minded one:

- **Auth done properly** — JWT with expiry, hashed passwords (bcrypt), no plaintext or hash leakage in responses
- **Authorization, not just authentication** — every task is scoped to its owner; users cannot read, edit, or delete each other's data (verified by test, not just assumed)
- **Abuse protection** — rate limiting on auth endpoints to blunt brute-force attempts
- **API contract discipline** — Pydantic validation on every input, consistent error responses, auto-generated OpenAPI/Swagger docs
- **Test discipline** — 96% test coverage, including negative cases (bad tokens, duplicate emails, cross-user access attempts), enforced in CI
- **Deployability** — Dockerized with a Postgres-backed `docker-compose.yml`, plus a zero-setup SQLite fallback for local development

---

## Tech Stack

| Category         | Technology                                  |
|--------------------|-----------------------------------------------|
| Language           | Python 3.12                                   |
| Framework          | FastAPI                                       |
| ORM                | SQLAlchemy 2.0                                |
| Validation         | Pydantic v2                                   |
| Auth               | JWT (`python-jose`) + bcrypt (`passlib`)      |
| Rate Limiting      | `slowapi`                                     |
| Database           | PostgreSQL (production/Docker), SQLite (local dev/tests) |
| Testing            | `pytest`, `pytest-cov`, `httpx` (via `TestClient`) |
| Containerization   | Docker, Docker Compose                        |
| CI                 | GitHub Actions                                |

---

## Project Structure

```
taskflow-api/
├── app/
│   ├── main.py              # FastAPI app, middleware, exception handlers
│   ├── config.py             # Settings (env-driven, pydantic-settings)
│   ├── database.py           # SQLAlchemy engine/session setup
│   ├── models.py             # User, Task ORM models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── security.py            # Password hashing, JWT encode/decode
│   ├── crud.py                # DB access layer (no request/response logic)
│   ├── dependencies.py        # Shared FastAPI dependencies (current-user auth)
│   ├── rate_limiter.py         # Shared slowapi Limiter instance
│   └── routers/
│       ├── auth.py             # /auth/register, /auth/login
│       ├── users.py            # /users/me
│       └── tasks.py            # /tasks CRUD + pagination + filtering
│
├── tests/
│   ├── conftest.py            # Isolated in-memory DB + client fixtures per test
│   ├── test_auth.py            # Registration, login, token validation
│   ├── test_tasks.py            # CRUD, pagination, filtering, cross-user isolation
│   └── test_health.py           # Liveness endpoint
│
├── .github/workflows/ci.yml    # Test + coverage gate + Docker build on every push/PR
├── Dockerfile
├── docker-compose.yml           # API + Postgres, for local "prod-like" runs
├── requirements.txt
├── requirements-dev.txt          # requirements.txt + test tooling
├── .env.example
├── pytest.ini
└── .gitignore
```

---

## Getting Started (Local, No Docker)

Requires Python 3.12+.

```bash
git clone <your-repo-url>
cd taskflow-api

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements-dev.txt
cp .env.example .env           # defaults work out of the box (SQLite)

uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`.

---

## Getting Started (Docker)

```bash
docker compose up --build
```

This starts the API (port `8000`) backed by a Postgres container, with a persistent volume for data. Set a real `SECRET_KEY` via an environment variable before deploying anywhere beyond your own machine:

```bash
SECRET_KEY=$(openssl rand -hex 32) docker compose up --build
```

---

## Running Tests

```bash
pytest --cov=app --cov-report=term-missing
```

Tests run against an isolated in-memory SQLite database per test (see `tests/conftest.py`) — no external services required. The same suite runs automatically in CI on every push and pull request, with a coverage gate (`--cov-fail-under=80`, currently sitting at 96%).

---

## API Reference

Full interactive documentation is auto-generated at `/docs` (Swagger UI) and `/redoc`. Summary below:

### Auth

| Method | Endpoint          | Description                          | Rate Limit |
|--------|--------------------|-----------------------------------------|------------|
| POST   | `/auth/register`   | Create a new user account                | 5/minute   |
| POST   | `/auth/login`       | Exchange email + password for a JWT       | 5/minute   |

`/auth/login` uses the OAuth2 password flow — send `username` (your email) and `password` as form data, not JSON.

### Users

| Method | Endpoint     | Description                  | Auth Required |
|--------|---------------|---------------------------------|----------------|
| GET    | `/users/me`    | Get the current user's profile   | Yes            |

### Tasks

All task endpoints require a valid JWT (`Authorization: Bearer <token>`) and are scoped to the authenticated user — you can only see and modify your own tasks.

| Method | Endpoint         | Description                                   |
|--------|-------------------|---------------------------------------------------|
| POST   | `/tasks`           | Create a task                                       |
| GET    | `/tasks`            | List tasks (paginated, filterable)                    |
| GET    | `/tasks/{id}`        | Get a single task                                     |
| PUT    | `/tasks/{id}`         | Update a task (partial updates supported)               |
| DELETE | `/tasks/{id}`          | Delete a task                                            |

**Pagination & filtering** (`GET /tasks`):

```
GET /tasks?skip=0&limit=20&status=todo&priority=high
```

- `skip` — records to skip (default `0`)
- `limit` — max records to return, 1–100 (default `20`)
- `status` — optional filter: `todo`, `in_progress`, `done`
- `priority` — optional filter: `low`, `medium`, `high`

Response shape:

```json
{
  "total": 42,
  "skip": 0,
  "limit": 20,
  "items": [ ... ]
}
```

### Health

| Method | Endpoint   | Description                              |
|--------|-------------|----------------------------------------------|
| GET    | `/health`    | Liveness probe for load balancers/orchestrators |

---

## Example Walkthrough

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demopass123","full_name":"Demo User"}'

# Login (note: form data, not JSON)
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=demo@example.com&password=demopass123"
# → {"access_token": "...", "token_type": "bearer"}

# Create a task
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Ship the API","priority":"high"}'

# List tasks
curl "http://127.0.0.1:8000/tasks?limit=5" \
  -H "Authorization: Bearer <token>"
```

---

## Design Notes

- **Layered structure** — routers handle HTTP concerns only; `crud.py` owns all database access; `schemas.py` defines the API contract independently of the ORM models in `models.py`. This keeps request/response shapes decoupled from storage schema.
- **SQLite for dev, Postgres for prod** — `DATABASE_URL` is the single source of truth; switching backends requires no code changes, only an env var.
- **In-memory rate limiting by default** — fine for a single-instance deployment. For multi-instance production deployments, swap `Limiter`'s storage backend to Redis (one-line change in `app/rate_limiter.py`).
- **Schema managed via `create_all` for now** — appropriate for a project at this stage; a real production system with evolving schema would move to Alembic migrations (see Future Enhancements).

---

## Known Limitations

- Schema changes currently require re-creating tables — no migration tooling wired up yet (see Future Enhancements)
- Rate limiting is in-memory, so limits reset if the process restarts and aren't shared across multiple instances/workers
- No refresh-token flow — access tokens are valid for a fixed window (default 60 minutes) with no silent renewal
- No role-based access control — all authenticated users have identical permissions over their own data

---

## Future Enhancements

- Add Alembic for versioned database migrations
- Refresh token flow with rotation
- Role-based access control (e.g., admin vs. standard user)
- Redis-backed rate limiting for multi-instance deployments
- Structured logging + request tracing (e.g., `structlog`, OpenTelemetry)
- Optional full-text search / sorting on task lists
- Webhooks or WebSocket support for real-time task updates

---

## Learning Outcomes

Building this project reinforced:

- Designing a layered FastAPI application (routers → dependencies → CRUD → ORM)
- JWT-based authentication and per-resource authorization
- Writing isolated, deterministic tests against a stateful API (fixtures, DB isolation, rate-limiter resets)
- Containerizing a Python web service and wiring it to a real database via Docker Compose
- Setting up CI with a test and coverage gate
