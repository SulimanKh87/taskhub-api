# TaskHub API — Production-Grade Backend + DevOps

![CI](https://github.com/sulimankh87/taskhub-api/actions/workflows/ci.yml/badge.svg?branch=devops-sql-aws)
![Deploy](https://img.shields.io/badge/deploy-pending%20AWS%20setup-yellow)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Terraform](https://img.shields.io/badge/Terraform-1.6-purple)
![Kubernetes](https://img.shields.io/badge/Kubernetes-manifests-blue)

> Backend engineer with end-to-end ownership: API design → containerization
> → CI/CD → AWS deployment → Kubernetes → monitoring → incident response.

---

## What This Project Demonstrates

This is not a tutorial project. It is a production-style backend system
built and operated the way a DevOps-aware backend engineer would in a
real company.

**Backend:** FastAPI, PostgreSQL, Celery, Redis, JWT auth, idempotent
background jobs, paginated API responses, async SQLAlchemy, Alembic migrations.

**DevOps and Infrastructure:**
- Multi-stage Docker build — image ~180MB vs ~450MB naive single-stage
- GitHub Actions CI/CD: test → Trivy security scan → ECR push → ECS deploy → auto-rollback
- Terraform: VPC, ECS Fargate, RDS, ElastiCache, ALB, ECR, Secrets Manager, CloudWatch alarms, S3 remote state, DynamoDB locking
- Kubernetes manifests and Helm chart: readiness/liveness probes, HPA, Ingress
- Prometheus + Grafana: request rate, latency p50/p95/p99, error rate
- Incident runbooks with exact AWS CLI diagnosis commands
- Cost analysis with 5 concrete reduction strategies (~$66/month → ~$0.05 when idle)

---

## Architecture

```
Internet
  │
  ▼
Application Load Balancer (HTTPS)
  │
  ├──▶ ECS Fargate — API (FastAPI, port 8000)
  │         │
  │         ├──▶ RDS PostgreSQL     (private subnet)
  │         ├──▶ ElastiCache Redis  (private subnet)
  │         └──▶ EventBridge ──▶ Lambda (TaskCreated events)
  │
  └──▶ ECS Fargate — Worker (Celery, FARGATE_SPOT)
            │
            ├──▶ RDS PostgreSQL
            └──▶ ElastiCache Redis
```

All secrets (DB password, JWT secret) stored in AWS Secrets Manager.
ECS fetches them at container startup — never plaintext in task definitions.

All infrastructure defined in Terraform with S3 remote state and DynamoDB
locking — reproducible from any machine in ~10 minutes.

---

## CI/CD Pipeline

```
Push to devops-sql-aws
  │
  ├──▶ CI (runs on every branch — no AWS credentials needed)
  │       ├── black + ruff lint
  │       ├── pytest with real PostgreSQL + Redis
  │       └── terraform fmt + validate
  │
  └──▶ Deploy (devops-sql-aws only, after CI passes)
            ├── Build Docker image (multi-stage)
            ├── Trivy scan → block on CRITICAL CVEs
            ├── Push to ECR (git SHA + latest tags)
            ├── Deploy ECS API + Worker services
            ├── Wait for services-stable
            └── Auto-rollback → restore previous task definition on failure
```

`ci.yml` and `deploy.yml` are split deliberately — CI runs cheaply on all
branches with no secrets. Deploy only runs on the protected branch.
A `Jenkinsfile` mirrors the same pipeline for Jenkins environments.

---

## Key Engineering Decisions

**Why ECS over EKS?**
ECS is simpler and ~$10/month cheaper (no control plane cost) for a single
service. EKS manifests and a Helm chart exist in `k8s/` and `helm/` to
demonstrate Kubernetes fluency. The same app deploys to EKS with one command:
`helm install taskhub ./helm/taskhub`.

**Why Fargate Spot for the worker?**
Celery tasks are retryable and the `job_log` table enforces idempotency via
`INSERT ... ON CONFLICT DO NOTHING`. Spot interruption is safe — the task
returns to the queue and replays without duplication. Saves ~70% on worker
compute (~$6/month).

**Why split CI and deploy workflows?**
CI runs on every push with zero AWS credentials — fast, cheap, no blast radius.
Deploy runs only on the main branch and needs production secrets. Each file
is simpler to debug and reason about independently.

**Why Secrets Manager over task definition env vars?**
Plaintext env vars appear in the AWS Console, CloudTrail logs, and Terraform
state. Secrets Manager ARNs reveal nothing — ECS fetches values at container
startup using the task execution role. Zero code changes required in the app.

**Why multi-stage Dockerfile?**
The builder stage installs gcc and compiles asyncpg/psycopg. The runtime stage
copies only the compiled packages. Build tools, pip cache, and gcc never reach
the production image. Result: ~180MB vs ~450MB.

---

## Monitoring

Prometheus scrapes `/metrics` every 15 seconds via
`prometheus-fastapi-instrumentator`. Grafana dashboard includes 7 panels:
request rate, error rate (%), active in-flight requests, p50/p95/p99 latency,
latency by endpoint, request volume by endpoint, status code breakdown.

CloudWatch alarms: ECS CPU > 80%, ECS memory > 80%, ALB 5xx > 10 in 5 min,
unhealthy host count > 0, RDS CPU > 70%, RDS connections > 68.

```bash
# Run the monitoring stack locally alongside the app
docker compose up -d
docker compose -f monitoring/docker-compose.monitoring.yml up -d
open http://localhost:3000   # Grafana: admin / admin
open http://localhost:9090   # Prometheus
```

---

## Running Locally

```bash
# 1. Clone and configure
git clone https://github.com/sulimankh87/taskhub-api.git
cd taskhub-api
cp .env.example .env

# 2. Start all services
docker compose up --build

# 3. Run migrations
docker compose exec api alembic upgrade head

# 4. Verify
curl http://localhost:8000/health
# {"status": "ok", "app": "TaskHub API"}

# 5. Run tests
pytest -v app/tests
```

---

## AWS Deployment

See `docs/AWS_DEPLOY.md` for the complete step-by-step deployment checklist.
All AWS steps are deferred to a single document to avoid accidental charges
during development.

Quick summary:
```bash
# Bootstrap remote state (one time only)
aws s3 mb s3://taskhub-terraform-state --region eu-central-1
aws dynamodb create-table --table-name taskhub-terraform-locks ...

# Deploy infrastructure
cd infra/terraform && terraform init && terraform apply

# Push images and run migrations
./scripts/push-to-ecr.sh
./scripts/run-migrations.sh
```

---

## Project Structure

```
taskhub-api/
│
├── app/                         FastAPI application
│   ├── main.py                  Entrypoint + middleware + /metrics
│   ├── routes/                  auth.py, tasks.py
│   ├── models/                  User, Task, JobLog (SQLAlchemy ORM)
│   ├── schemas/                 Pydantic v2 contracts
│   ├── workers/                 Celery app + email tasks
│   └── tests/                   pytest async, real DB, Celery mocked
│
├── infra/terraform/             Full AWS stack as code
│   ├── provider.tf              S3 remote state + DynamoDB locking
│   ├── main.tf                  VPC, subnets, SGs, RDS, Redis, ALB
│   ├── ecs.tf                   ECS cluster + Secrets Manager injection
│   ├── secrets.tf               Secrets Manager resources
│   ├── monitoring.tf            CloudWatch alarms + SNS + dashboard
│   └── eks.tf                   EKS cluster (Kubernetes reference)
│
├── k8s/                         Kubernetes raw manifests
│   ├── deployment-api.yaml      Probes, resource limits, topology spread
│   ├── deployment-worker.yaml   Celery exec liveness probe
│   ├── service.yaml             ClusterIP + ALB Ingress
│   └── hpa.yaml                 CPU 70% + memory 80% autoscaling
│
├── helm/taskhub/                Helm chart
│   ├── values.yaml              All defaults, overridable per environment
│   └── templates/               Templated versions of k8s/ manifests
│
├── monitoring/                  Prometheus + Grafana stack
│   ├── prometheus.yml           Scrape config
│   ├── grafana-dashboard.json   7-panel dashboard (auto-loaded)
│   └── docker-compose.monitoring.yml
│
├── docs/
│   ├── INCIDENTS.md             3 runbooks with exact CLI commands
│   ├── OPERATIONS.md            AWS/K8s/Linux/Prometheus cheat sheet
│   ├── COST.md                  ~$66/month breakdown + 5 reduction strategies
│   ├── ARCHITECTURE.md          System design + data flow
│   ├── SECURITY.md              Auth, secrets, OWASP headers
│   ├── FAILURE_MODES.md         Per-layer failure + recovery
│   └── AWS_DEPLOY.md            Final AWS deployment checklist
│
├── .github/workflows/
│   ├── ci.yml                   Test + lint + terraform validate
│   └── deploy.yml               Build → scan → push → deploy → rollback
│
├── Jenkinsfile                  Jenkins pipeline (interview reference)
├── Dockerfile                   Multi-stage: builder + runtime
├── .dockerignore                Excludes secrets, infra, tests, git
├── docker-compose.yml           Local stack (API, worker, PG, Redis)
└── docker-compose.override.yml  Hot reload + Flower UI (dev only)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API framework | Python 3.12, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy 2.0 async, Alembic |
| Background jobs | Celery 5, Redis |
| Containerization | Docker multi-stage, Docker Compose |
| CI/CD | GitHub Actions, Trivy image scanning, Jenkinsfile |
| Infrastructure (IaC) | Terraform, AWS ECS Fargate, RDS, ElastiCache, ALB, ECR |
| Secrets | AWS Secrets Manager |
| Kubernetes | K8s manifests, Helm chart, HPA, EKS Terraform |
| Monitoring | Prometheus, Grafana, CloudWatch alarms, SNS |
| Security | JWT, bcrypt, OWASP headers, non-root containers |

---

## Documentation

- [Incident Runbooks](docs/INCIDENTS.md) — how to diagnose and fix production failures
- [Operations Cheat Sheet](docs/OPERATIONS.md) — AWS/K8s/Linux commands
- [Cost Analysis](docs/COST.md) — monthly breakdown and reduction strategies
- [AWS Deployment Guide](docs/AWS_DEPLOY.md) — step-by-step with exact commands
- [Architecture](docs/ARCHITECTURE.md) — system design and data flow
- [Security Model](docs/SECURITY.md) — auth, secrets, headers
- [Failure Modes](docs/FAILURE_MODES.md) — per-layer failure and recovery

---

MIT License © 2025–2026 Suleiman Khasheboun
