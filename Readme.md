🚀 TaskHub API — FastAPI + MongoDB + Celery +
![CI](https://github.com/sulimankh87/taskhub-api/actions/workflows/ci.yml/badge.svg)

```markdown
> **Version:** 1.4.0  
> **Status:** Stable core + scalable API contracts  
> **Release Date:** Dec 2025
```

## 📚 Overview

A modern, containerized backend for task management with user authentication,
async background jobs, and MongoDB persistence — built using FastAPI, Motor, Celery, and Redis.

# TaskHub API

is an async backend service for managing users and tasks.  
It demonstrates:

- Secure login & token-based authentication
- Background task scheduling with Celery
- Clean separation of routes, schemas, and database logic
- Fully containerized setup using Docker Compose\
- Automated testing with Pytest
- Pydantic v2 data validation
- Modern Python 3.12 features
- Comprehensive API documentation with Swagger UI
- Environment configuration via .env files
- Redis as a message broker and result backend for Celery
- Modular project structure for maintainability
- Async I/O using FastAPI and Motor for MongoDB
- JWT tokens with python-jose
- Password hashing with bcrypt
- Health check endpoint for monitoring
- GitHub Actions CI (linting, testing, distributed service testing)
- Idempotent background jobs using Celery (NEW)
- Offset-based pagination for task listing (`limit` / `skip`)
- MongoDB compound indexes aligned with query patterns
- Authorization header–based JWT enforcement (no query/body tokens)
- Full CI coverage with real MongoDB, Redis, and Celery worker



🧱 Tech Stack
Python 3.12
FastAPI
MongoDB (Motor)
Redis / Celery
Docker & Docker Compose
Pydantic v2
Pytest / HTTPX
JWT (python-jose)
bcrypt

## 📈 Scalability Improvements (NEW) 
After stabilizing the core system, TaskHub was enhanced to support scale.

### Pagination
Task listing endpoints support offset-based pagination:
GET /tasks?limit=20&skip=0
- `limit`: number of tasks returned (1–100)
- `skip`: offset into the result set
- Results are deterministically ordered by `created_at DESC`

This prevents large responses and keeps performance predictable as data grows.

### Indexing
To support pagination at scale, TaskHub creates a MongoDB compound index on startup:
tasks(owner ASC, created_at DESC)
This index matches the query pattern used by `/tasks` and prevents collection scans.

---------------------------------

## 🔄 Idempotent Background Jobs (NEW)

TaskHub API now supports idempotent Celery background jobs.

This ensures:

- No background job runs twice
- Retries do not duplicate work
- Worker restarts and crashes are safe
- Email sending and heavy operations are retry-safe
- Mongo-backed `job_log` prevents duplicate executions

A new file `app/idempotency.py` manages job state using:

- job_id  
- status (in_progress / completed)  
- result  
- created_at  

Before a task runs, Celery checks if the job was already completed and returns the saved result.


## 🔍 Continuous Integration & Code Quality (NEW)

TaskHub API now includes a complete CI pipeline powered by GitHub Actions.

CI runs on every push and pull request across all branches, ensuring pagination,
indexing, and API contract changes do not regress.


### ✔ What CI Runs Automatically

| **Step**   | **Tool**  | **Purpose**                             |
|------------|-----------|-----------------------------------------|
| Linting    | Ruff      | Clean, error-free Python code           |
| Formatting | Black     | Enforced consistent code style          |
| Unit Tests | Pytest    | Validates API behavior                  |
| DB Service | MongoDB 7 | Real DB ensures reliable test execution |

### ✔ Distributed Services Added to CI (NEW)

The CI workflow now launches:

- **MongoDB 7** — real database for tests  
- **Redis 7** — Celery broker + result backend  
- **Celery Worker** — runs background tasks during CI  

This allows end-to-end testing of:

- Async routes
- Database operations
- Celery tasks
- Idempotent background jobs

### ✔ CI Checks

- `ruff check .`
- `black --check .`
- `pytest -v`

CI status badge is displayed at the top of the README.

🧭 System Architecture

``` mermaid
graph TD

    %% CLIENT LAYER
    A[🧑‍💻 Client / Swagger UI / Frontend] -->|HTTP / JSON| B[🚀 FastAPI API Service]

    %% API LAYER
    subgraph B[FastAPI Application Layer]
        B1[🔐 JWT Authentication<br/>bcrypt password hashing]
        B2[📋 Task CRUD Endpoints<br/>Async I/O via Uvicorn]
        B3[🧩 Pydantic Validation<br/>and Config Management]
    end

    %% CONNECTIONS
    B -->|Async Motor Client| C[(🗄️ MongoDB)]
    B -->|Publishes Tasks| D[(🧩 Redis Broker)]
    D --> E[⚙️ Celery Worker]
    E -->|Stores Results| D

    %% DATABASES
    subgraph C_DB[MongoDB Storage]
        C1[(👤 Users Collection)]
        C2[(✅ Tasks Collection)]
    end
    C --> C1
    C --> C2

    %% REDIS / CELERY
    subgraph D_REDIS[Redis & Celery System]
        D1[(📨 Task Queue)]
        D2[(📦 Result Backend)]
    end
    D --> D1
    D --> D2

    %% FLOW DIRECTION
    A --> B
    B --> C
    B --> D
    D --> E
    E --> D
```

⚙️ Workflow Summary
Client → FastAPI
The user (or Swagger UI) sends authenticated HTTP requests.
FastAPI → MongoDB
Handles persistent storage for users and task documents.
FastAPI → Redis → Celery
Background or delayed tasks are queued via Redis, executed by Celery workers.
Celery Worker → Redis
Stores task results and execution states in Redis for retrieval.

🧱 Service Overview
Service Description Docker Container
FastAPI REST API handling authentication and tasks taskhub-api
MongoDB Stores users and tasks (NoSQL)    taskhub-mongo
Redis Message broker & Celery result backend redis
Celery Worker Executes background jobs asynchronously celery-worker

Project Structure:

📁 Project Structure

📦 taskhub-api/ — FastAPI backend with MongoDB, Redis & Celery
```text
taskhub-api/
│
├── app/                          # Application Source Code
│   │
│   ├── main.py                   # FastAPI entrypoint (routes, middleware)
│   ├── config.py                 # Global settings via pydantic-settings
│   ├── database.py               # MongoDB async client (Motor)
│   ├── security.py               # Password hashing + JWT helpers
│   ├── idempotency.py            # Mongo-backed job_log + idempotent helpers
│   ├── routes/                   # API Route Modules
│   │   ├── auth.py               # User registration + login
│   │   └── tasks.py              # Task CRUD, JWT-protected
│   │
│   ├── schemas/                  # Pydantic Request/Response Schemas
│   │   ├── user_schema.py        # User create/login/public models
│   │   ├── task_schema.py        # Task create/response schemas
│   │   ├── pagination_schema.py   # Pagination contracts 
│   │   └── token_schema.py       # JWT token models
│   │
│   ├── workers/               # Celery Worker + Background Jobs
│   │   ├── celery_app.gpy
│   │   ├── __init__.py
│   │   └── tasks/             # Celery task modules
│   │       └── email_tasks.py # send_welcome_email, email notifications, etc.
│   │
│   ├── models/                   # MongoDB Document Models (Pydantic)
│   │   ├── user_model.py
│   │   └── task_model.py
│   │
│   └── tests/                    # Automated Test Suite
│       ├── test_api.py           # Health check & API tests
│       ├── test_tasks.py           # Task CRUD + pagination tests 
│       └── test_idempotency.py   # Idempotent job execution tests
│
├── docker-compose.yml            # Orchestration (API + MongoDB + Redis + Celery)
├── Dockerfile                    # API image build instructions
├── requirements.txt               # Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignored files
└── README.md                     # Project documentation
```


---

## ⚙️ Environment Configuration

Example `.env` file:

```bash
# App
SECRET_KEY=replace_me_with_secure_hex_key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# MongoDB
MONGO_USER=taskhub_user
MONGO_PASSWORD=StrongPassword123
MONGODB_URI=mongodb://taskhub_user:StrongPassword123@taskhub-mongo:27017/taskhub_db?authSource=admin

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

🚀 Quick Start

1. Clone & Build
   git clone https://github.com/sulimankh87/taskhub-api.git
   cd taskhub-api
   docker compose up -d --build

✅ This launches:
FastAPI – Swagger UI → http://localhost:8000
MongoDB - quick API health check → mongodb://localhost:27017
Redis (Celery broker)
Celery worker

2. Run Tests
   docker compose exec api pytest -v
   Expected:
   app/tests/test_api.py::test_health_check PASSED

3. API Documentation
   Open your browser:
   👉 http://localhost:8000/docs

Interactive Swagger UI for all endpoints.

4. Example Workflow
   🧪 Example API Usage

# Register a new user

POST /auth/register
{
"username": "sami",
"email": "sami@example.com",
"password": "MySecurePassword123"
}

✅ Response:
{
"id": "66f91a3d8c0b5aef0d123abc",
"username": "sami",
"email": "sami@example.com"
}

# Login

POST /auth/login
(Form data → not JSON)

# Field	Example

username username@example.com
password MySecurePassword123

✅ Response:
{
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
"token_type": "bearer"
}

# Create a new task

POST /tasks/
Use your Authorization: Bearer <access_token> header.
{
"title": "Prepare deployment report",
"description": "Write Docker + CI/CD summary"
}

✅ Response:
{
"id": "66f91b1f0f0a5bde01abcd99",
"title": "Prepare deployment report",
"status": "pending",
"owner_id": "66f91a3d8c0b5aef0d123abc"
}

# Health check

GET /health
curl http://localhost:8000/health

🧾 List Tasks
GET /tasks/

💀 Delete Task
DELETE /tasks/{task_id}

✅ Response:
{"status": "ok", "app": "taskhub-api"}

🧪 Testing
▶️ Run tests locally
pytest -v --disable-warnings

▶️ Run tests inside Docker
docker compose exec api pytest -v

✔ Expected Output
app/tests/test_api.py::test_health_check PASSED

🧠 Testing Notes (Updated)
TaskHub API uses Pytest together with Ruff (linting), Black (formatting), and GitHub Actions CI.

### ✔ Test Coverage Details (NEW)
Tests also verify:
- JWT authorization via `Authorization: Bearer <token>` header
- Paginated task listing using `limit` and `skip` query parameters
- Stable ordering of paginated results (`created_at DESC`)


CI automatically runs:
ruff check .
black --check .
pytest -v
A real MongoDB 7 service for DB-backed tests

🗄 Database Initialization in Tests
Tests now manually initialize and close MongoDB connections to prevent NoneType db issues.

Example:
from app.database import connect_to_mongo, close_mongo_connection

@pytest.mark.asyncio
async def test_health_check():
await connect_to_mongo()

    async with AsyncClient(app=app, base_url="http://test") as client:
        res = await client.get("/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    await close_mongo_connection()

🛡️ Security
JWT authentication with bcrypt password hashing
TrustedHostMiddleware to block Host header attacks
.env secrets never committed

👷‍ Deployment
docker compose -f docker-compose.yml up -d --build

Or on Kubernetes (future step):
kubectl apply -f k8s/

🧠 Developer Quick Commands
Command Description
docker compose logs -f api Stream FastAPI logs
docker compose logs -f celery-worker Watch Celery tasks
docker compose down Stop all services
docker compose up -d Restart in background
docker compose exec api pytest -v Run tests

### ⚙️ Application Startup & Shutdown

TaskHub API now uses FastAPI event hooks to manage the MongoDB connection lifecycle.

```python
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
```

🌐 API Documentation
After running the containers:
Swagger UI → http://localhost:8000/docs
ReDoc → http://localhost:8000/redoc

## 🧾 Recent Updates (vNext)

```markdown 

### 📈 Scale Readiness Improvementsg
- Added offset-based pagination to task listing
- Added MongoDB compound index for owner-based queries
- Enforced Authorization header JWT contracts
- Added integration tests covering pagination and authentication


### 🔧 CI & Code Quality Enhancements
- Added full GitHub Actions CI workflow
- Integrated Ruff linting (static analysis)
- Added Black formatting enforcement
- Cleaned unused imports and improved module structure
- Ensures every push/PR passes quality checks before merging


### Database Connection Lifecycle
- **database.py**: Added explicit connection lifecycle functions  
  → Prevents premature DB connections and ensures clean shutdown
- **main.py**: Added startup/shutdown event handlers  
  → Automatically calls `connect_to_mongo()` and `close_mongo_connection()`
- **test_api.py**: Handles database initialization and teardown in tests  
  → Prevents `NoneType db` errors during isolated test runs

### 🔄 Idempotent Background Jobs (NEW)
- Added Mongo-backed `job_log` to prevent duplicate background job execution  
- Implemented idempotent layer in `app/idempotency.py`  
- Updated Celery tasks to check for previous results before running  
- Ensures email tasks and future workloads run **exactly once**, even under retries  
- Production-safe behavior for distributed workers  

### 🐇 Celery Worker Integration (NEW)
- CI now runs a full Celery worker  
- Ensures background jobs are tested end-to-end  
- Worker bootstraps automatically inside GitHub Actions  

### 🧪 New Idempotency Test
- Added `test_idempotency.py`  
- Verifies Celery results are identical across multiple runs  
- Ensures `job_log` stores only one record  
- Prevents duplicate sends and duplicate DB writes  

### 🔧 CI Enhancements (Updated)
- Added Redis 7 service for Celery broker + result backend  
- Added Celery worker startup step  
- Added PYTHONPATH fix to prevent import errors in CI  
- Added full distributed environment testing (API + DB + Redis + Worker)  


📄 License
MIT License © 2025 Suleiman Khasheboun suli.tempmail2022@gmail.com
Backend Developer | FastAPI · Docker · MongoDB · Celery
