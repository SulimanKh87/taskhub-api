# 💥 Failure Modes — How TaskHub Breaks (and Recovers)

This document explains **how the system can fail**, **what the impact is**, and **how failures are detected and mitigated**.

Understanding failure modes is critical for operating production systems.

> **Scope note:**  
> Failure scenarios described here apply both to the current local setup
> (Docker Compose) and the planned AWS deployment. Cloud-managed services
> (ECS, RDS, ElastiCache) reduce operational burden but do not eliminate failures.

---

## 🎯 Design Philosophy

Failures are inevitable.
The system is designed so that:
- Failures are isolated
- Failures are observable
- Failures degrade gracefully
- Failures do not corrupt data

---

## 1️⃣ API Container Failure (FastAPI)

### What breaks
- One or more API containers crash
- Deployment misconfiguration
- Memory / CPU exhaustion

### Impact
- Partial loss of capacity
- No data loss

### Why it’s safe
- API containers are stateless
- Requests can be served by any healthy container

### Mitigation
- ECS restarts failed tasks
- Load Balancer routes traffic to healthy tasks
- Auto-scaling replaces capacity

---

## 2️⃣ Worker Failure (Celery)

### What breaks
- Worker crashes mid-task
- Task timeout
- Code exception

### Impact
- Background job delay
- No duplicate execution

### Why it’s safe
- Tasks are retryable
- Idempotency is enforced at the database level

### Mitigation
- Celery retries
- Job state stored in PostgreSQL
- Exactly-once semantics via `job_id`

---

## 3️⃣ PostgreSQL Failure (RDS)

### What breaks
- DB instance restart
- Network partition
- Failover event

### Impact
- Temporary read/write unavailability

### Why it’s safe
- ACID transactions
- Managed backups
- Failover handled by RDS

### Mitigation
- Application-level retries
- Connection pooling
- Multi-AZ deployment

Rule:
> If PostgreSQL is down, the system is degraded but consistent.

---

## 4️⃣ Redis Failure (ElastiCache)

### What breaks
- Cache eviction
- Redis restart
- Broker unavailability

### Impact
- Background jobs paused
- Cache misses

### Why it’s safe
- Redis is not a source of truth
- Data persists in PostgreSQL

### Mitigation
- Redis cluster replication
- Task retry after broker recovery

---

## 5️⃣ SQS Failure

### What breaks
- Consumer crashes
- Message backlog

### Impact
- Event processing delay

### Why it’s safe
- Messages are durable
- At-least-once delivery

### Mitigation
- Dead-letter queues (DLQ)
- Consumer scaling

---

## 6️⃣ Elasticsearch Failure

### What breaks
- Search unavailable
- Index lag

### Impact
- Search endpoints degraded
- Core API still functional

### Why it’s safe
- Elasticsearch is a derived view
- PostgreSQL remains source of truth

### Mitigation
- Re-index from DB
- Graceful fallback

---

## 7️⃣ Load Balancer Failure

### What breaks
- ALB configuration issue
- TLS misconfiguration

### Impact
- Entry point unavailable

### Mitigation
- Infrastructure as Code (Terraform)
- Rollback via redeploy
- Monitoring & alerts

---

## 8️⃣ Observability Failure

### What breaks
- Logs missing
- Metrics unavailable

### Impact
- Harder debugging
- No direct user impact

### Mitigation
- Structured logging
- Health endpoints
- Redundant monitoring

---

## 🧠 Key Takeaway

The system is designed so that:
- Failures are isolated by layer
- State is protected by PostgreSQL
- Async processing absorbs instability
- Recovery is automated

Production systems are defined not by *avoiding* failures, but by **surviving them predictably**.