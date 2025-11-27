🚀 TaskHub API — FastAPI + MongoDB + Celery + 
![CI](https://github.com/sulimankh87/taskhub-api/actions/workflows/ci.yml/badge.svg)

```markdown
> **Version:** 1.1.0 — Database Connection Lifecycle Enhancement  & CI tests 
> *Release Date:* Nov 2025
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

## 🔍 Continuous Integration & Code Quality (NEW)

TaskHub API now includes a complete CI pipeline powered by GitHub Actions.

### ✔ What CI Runs Automatically

| **Step**    | **Tool**    | **Purpose**                              |
|-------------|-------------|-------------------------------------------|
| Linting     | Ruff        | Clean, error-free Python code            |
| Formatting  | Black       | Enforced consistent code style           |
| Unit Tests  | Pytest      | Validates API behavior                   |
| DB Service  | MongoDB 7   | Real DB ensures reliable test execution  |


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
Service	Description	Docker Container
FastAPI	REST API handling authentication and tasks	taskhub-api
MongoDB	Stores users and tasks (NoSQL)	taskhub-mongo
Redis	Message broker & Celery result backend	redis
Celery Worker	Executes background jobs asynchronously	celery-worker

taskhub-api/                                                         
│  
├── app/                                    📁 application source  
│   ├── main.py               🚀 app entrypoint (FastAPI initialization & middleware)  
│   ├── config.py             ⚙️ environment configuration (loads .env)  
│   ├── database.py           🗃️ MongoDB async client (Motor)  
│   ├── celery_app.py         🐇 Celery configuration (broker & backend)  
│   ├── tasks.py              🔄 background task definitions  
│   ├── security.py           🔐 JWT creation & bcrypt password hashing  
│   │  
│   ├── routes/               🌐 API route modules  
│   │   ├── auth.py           👤 login & registration endpoints  
│   │   └── tasks.py          ✅ CRUD endpoints for task operations  
│   │  
│   ├── schemas/              🧩 Pydantic data models  
│   │   ├── user_schema.py    👥 user data validation  
│   │   ├── task_schema.py    📋 task model definition  
│   │   └── token_schema.py   🔑 JWT token schema  
│   │  
│   └── tests/                🧪 automated tests  
│       └── test_api.py       🩺 health check & endpoint tests  
│ 
├── .env                      🗝️ environment secrets (excluded from git)  
├── .gitignore                🚫 ignored files & folders  
├── Dockerfile                🐳 build instructions for FastAPI container  
├── docker-compose.yml        ⚙️ service orchestration (API, Mongo, Redis, Celery)  
├── requirements.txt          📦 Python dependencies list  
└── README.md                 📖 project documentation  


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
username	username@example.com
password	MySecurePassword123

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
Command	Description
docker compose logs -f api	Stream FastAPI logs
docker compose logs -f celery-worker	Watch Celery tasks
docker compose down	Stop all services
docker compose up -d	Restart in background
docker compose exec api pytest -v	Run tests

### ⚙️ Application Startup & Shutdown
TaskHub API now uses FastAPI event hooks to manage the MongoDB connection lifecycle.

```python
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
✅ Ensures database connections open only when the app starts
✅ Cleanly closes all connections when the container stops
```

🌐 API Documentation
After running the containers:
Swagger UI → http://localhost:8000/docs
ReDoc → http://localhost:8000/redoc

## 🧾 Recent Updates (vNext)

```markdown 
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


📄 License
MIT License © 2025 Suleiman Khasheboun suli.tempmail2022@gmail.com
Backend Developer | FastAPI · Docker · MongoDB · Celery
