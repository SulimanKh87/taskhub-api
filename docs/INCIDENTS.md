# 🚨 Incident Response — TaskHub API

This document describes real failure scenarios for TaskHub API:
**how they're detected, diagnosed, fixed, and prevented.**

Production systems don't fail cleanly. This doc exists so that when
something breaks, the diagnosis path is already mapped out.

> **Interview answer:**
> "I document incident patterns because the worst time to figure out
>  how to debug a system is when it's actually down."

---

## Incident Template

Every incident follows this structure:

| Field       | Description                                      |
|-------------|--------------------------------------------------|
| Symptom     | What the user or monitor sees                    |
| Detection   | Which alarm or command reveals it                |
| Diagnosis   | Step-by-step commands to find root cause         |
| Fix         | Exact commands to restore service                |
| Prevention  | What change stops this from happening again      |

---

## Incident 1 — ECS Task Keeps Restarting (CrashLoopBackOff equivalent)

### Symptom
- ALB health checks failing
- ECS console shows tasks stopping and starting every 2 minutes
- Users getting `502 Bad Gateway` from the ALB

### Detection
```bash
# CloudWatch alarm fires: UnHealthyHostCount > 0
# Check ECS service events
aws ecs describe-services \
  --cluster taskhub-dev-cluster \
  --services taskhub-dev-api \
  --region eu-central-1 \
  --query 'services[0].events[:5]'

# Expected output when crashing:
# "service taskhub-dev-api has reached a steady state."
# "service taskhub-dev-api (port 8000) is unhealthy in target-group..."
```

### Diagnosis

**Step 1 — Find the failing task**
```bash
# List stopped tasks to see the most recent failure
aws ecs list-tasks \
  --cluster taskhub-dev-cluster \
  --service-name taskhub-dev-api \
  --desired-status STOPPED \
  --region eu-central-1
```

**Step 2 — Get exit code and stop reason**
```bash
aws ecs describe-tasks \
  --cluster taskhub-dev-cluster \
  --tasks <task-arn-from-above> \
  --region eu-central-1 \
  --query 'tasks[0].{StopCode: stopCode, StopReason: stoppedReason, ExitCode: containers[0].exitCode}'

# Exit code 1 = application crash (check logs)
# Exit code 137 = OOMKilled (out of memory)
# Exit code 143 = SIGTERM (graceful shutdown, expected during deploy)
```

**Step 3 — Read application logs**
```bash
# Get logs from the stopped container
aws logs tail /ecs/taskhub-dev-api \
  --since 30m \
  --follow \
  --region eu-central-1

# Common root causes found in logs:
# - "could not connect to server" → RDS unreachable (security group issue)
# - "password authentication failed" → wrong DATABASE_URL secret
# - "ModuleNotFoundError" → bad Docker image (missing dependency)
```

**Step 4 — Check security groups if DB connection error**
```bash
# Verify RDS security group allows inbound from ECS security group
aws ec2 describe-security-groups \
  --group-ids <rds-security-group-id> \
  --query 'SecurityGroups[0].IpPermissions'

# Should see port 5432 allowed from api-security-group
# If missing, that's your root cause
```

### Fix

**If security group missing:**
```bash
# Get the API security group ID
API_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=taskhub-dev-api-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)

# Allow port 5432 from API SG to RDS SG
aws ec2 authorize-security-group-ingress \
  --group-id <rds-security-group-id> \
  --protocol tcp \
  --port 5432 \
  --source-group $API_SG \
  --region eu-central-1
```

**If wrong secret value:**
```bash
# Update the secret in Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id taskhub/dev/db-password \
  --secret-string "correct-password-here" \
  --region eu-central-1

# Force new ECS deployment to pick up new secret
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --force-new-deployment \
  --region eu-central-1
```

### Prevention
- Terraform security group rules tested in CI via `terraform validate`
- Add DB connectivity smoke test to startup (try connecting before serving traffic)
- CloudWatch alarm on `UnHealthyHostCount` fires within 60 seconds of crash
- Set ECS `deployment_circuit_breaker` with `rollback = true` (already in ecs.tf)

---

## Incident 2 — Celery Tasks Silently Failing (No Emails Sent)

### Symptom
- Welcome emails not arriving after user registration
- No errors visible in API logs (API returned 201 successfully)
- Users complaining but API appears healthy

### Detection
```bash
# API looks fine — check the WORKER logs
aws logs tail /ecs/taskhub-dev-worker \
  --since 1h \
  --region eu-central-1

# Look for:
# [ERROR] consumer: Cannot connect to redis://...
# ConnectionRefusedError: [Errno 111] Connection refused
```

### Diagnosis

**Step 1 — Verify Redis endpoint is reachable from ECS**
```bash
# Check ElastiCache cluster status
aws elasticache describe-cache-clusters \
  --region eu-central-1 \
  --query 'CacheClusters[?CacheClusterId==`taskhub-dev-redis`].[CacheClusterId, CacheClusterStatus, RedisConfiguration.PrimaryEndpoint]'

# Status should be "available"
# If "modifying" or "rebooting" → wait for it to complete
```

**Step 2 — Check REDIS_BROKER env var in ECS task definition**
```bash
# Get the current task definition
aws ecs describe-task-definition \
  --task-definition taskhub-dev-worker \
  --region eu-central-1 \
  --query 'taskDefinition.containerDefinitions[0].environment'

# Verify REDIS_BROKER matches the current ElastiCache endpoint
# ElastiCache endpoints change if the cluster is recreated
```

**Step 3 — Verify worker is actually running**
```bash
aws ecs list-tasks \
  --cluster taskhub-dev-cluster \
  --service-name taskhub-dev-worker \
  --desired-status RUNNING \
  --region eu-central-1

# If empty: no running tasks → service crashed silently
```

**Step 4 — Check job_log table for stuck jobs**
```bash
# Connect to RDS and check job state
# (via bastion or ECS exec)
aws ecs execute-command \
  --cluster taskhub-dev-cluster \
  --task <running-api-task-arn> \
  --container api \
  --interactive \
  --command "python -c \"
import asyncio
from app.db import SessionLocal
from app.models.job_log import JobLog
from sqlalchemy import select

async def check():
    async with SessionLocal() as db:
        result = await db.execute(
            select(JobLog).where(JobLog.status == 'in_progress')
        )
        jobs = result.scalars().all()
        for j in jobs:
            print(j.job_id, j.created_at)

asyncio.run(check())
\""
```

### Fix

**If Redis endpoint changed (ElastiCache recreated):**
```bash
# Get new endpoint
NEW_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id taskhub-dev-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

# Update the environment variable in ECS task definition
# Then force new deployment
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-worker \
  --force-new-deployment \
  --region eu-central-1
```

**If worker simply crashed — restart it:**
```bash
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-worker \
  --force-new-deployment \
  --region eu-central-1
```

### Prevention
- Worker health check (liveness probe in K8s, see `k8s/deployment-worker.yaml`)
- CloudWatch alarm on worker `CPUUtilization` — zero CPU for > 5 min = worker dead
- Celery task retry with exponential backoff (already configured in `email_tasks.py`)
- Dead letter queue for failed tasks (future improvement)
- Idempotency via `job_log` table means replaying stuck jobs is safe

---

## Incident 3 — PostgreSQL Connection Pool Exhausted

### Symptom
- API returns `500 Internal Server Error` intermittently under load
- Errors are not constant — some requests succeed, others fail
- Errors appear more during traffic spikes

### Detection
```bash
# CloudWatch alarm fires: RDS DatabaseConnections > 68
# Check API logs for the specific error
aws logs filter-log-events \
  --log-group-name /ecs/taskhub-dev-api \
  --filter-pattern "QueuePool" \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --region eu-central-1

# You'll see:
# sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 5 reached,
# connection timed out, timeout 30
```

### Diagnosis

**Step 1 — Check current connection count vs max**
```bash
# RDS max connections for db.t4g.micro = 85
# Check current usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=taskhub-dev-postgres \
  --start-time $(date -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date --iso-8601=seconds) \
  --period 60 \
  --statistics Maximum \
  --region eu-central-1
```

**Step 2 — Calculate connections in use**
```bash
# Formula:
# Total connections = ECS tasks × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
# Example: 4 API tasks × (5 + 5) = 40 connections
# Plus: 1 worker task × (5 + 5) = 10 connections
# Total: 50 / 85 max = 59% — should be fine

# If autoscaling kicked in and spun up 8 tasks:
# 8 × 10 + 1 × 10 = 90 > 85 max → EXHAUSTED

# Check current running task count
aws ecs describe-services \
  --cluster taskhub-dev-cluster \
  --services taskhub-dev-api \
  --query 'services[0].runningCount' \
  --region eu-central-1
```

**Step 3 — Check if autoscaling over-scaled**
```bash
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --resource-id service/taskhub-dev-cluster/taskhub-dev-api \
  --region eu-central-1 \
  --query 'ScalingActivities[:3]'
```

### Fix

**Immediate — reduce pool size to stop the bleeding:**
```bash
# Update environment variable in ECS task definition
# Reduce DB_MAX_OVERFLOW from 5 to 2
# Then force redeploy (new tasks pick up new env var)
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --force-new-deployment \
  --region eu-central-1
```

**Proper fix — cap autoscaling max replicas:**
```bash
# In infra/terraform/ecs.tf (already set):
# maxReplicas = 8
#
# With DB_POOL_SIZE=5, DB_MAX_OVERFLOW=5:
# 8 tasks × 10 connections = 80 < 85 max
# Reduce maxReplicas to 6 OR reduce pool size to 3+2
```

### Prevention
- Set `DB_MAX_OVERFLOW = 5` (already set in `ecs.tf` and `k8s/configmap.yaml`)
- CloudWatch alarm on `DatabaseConnections > 68` (80% of max) already in `monitoring.tf`
- Formula to always check before changing pool size or replica count:
  `max_replicas × (pool_size + max_overflow) < rds_max_connections × 0.8`
- Consider PgBouncer connection pooler for production scale (future improvement)
