# 💰 Cost & Scaling — TaskHub AWS Infrastructure

This document breaks down what TaskHub costs to run, why each resource
costs what it does, and exactly how to reduce costs by 40-60%.

> **Interview answer:**
> "I track infrastructure costs per service so I can make informed
>  tradeoffs between reliability and spend. I know which components
>  are expensive and have a concrete plan to reduce each one."

---

## Monthly Cost Breakdown (eu-central-1 / Frankfurt)

| Resource | Type | Config | Cost/month |
|----------|------|--------|-----------|
| ECS Fargate — API | 0.25 vCPU / 512MB, 1 task | On-Demand | ~$7.50 |
| ECS Fargate — Worker | 0.25 vCPU / 512MB, 1 task | On-Demand | ~$7.50 |
| RDS PostgreSQL | db.t4g.micro, single-AZ | On-Demand | ~$15.00 |
| ElastiCache Redis | cache.t4g.micro, single node | On-Demand | ~$13.00 |
| Application Load Balancer | 1 ALB, minimal traffic | On-Demand | ~$18.00 |
| ECR | 2 repos, ~500MB storage | Per GB | ~$0.05 |
| CloudWatch | Logs + alarms + dashboard | Per GB/alarm | ~$3.00 |
| Secrets Manager | 2 secrets | Per secret/month | ~$0.80 |
| Data transfer | Minimal outbound | Per GB | ~$1.00 |
| **Total** | | | **~$66/month** |

> Prices are approximate. Use the
> [AWS Pricing Calculator](https://calculator.aws) for exact figures.

---

## Cost Drivers — Why Each Service Costs What It Does

### ALB — $18/month (27% of total)
The ALB is the most expensive single item despite doing the least "work."
AWS charges a fixed hourly rate ($0.0085/hr = ~$6/month) plus LCU
(Load Balancer Capacity Units) based on traffic. Even with near-zero
traffic the fixed cost applies.

The ALB is non-negotiable for production — it provides health checks,
SSL termination, and routing. But it's worth knowing it dominates the bill.

### RDS — $15/month
`db.t4g.micro` is the smallest available RDS instance. It provides
2 vCPU (burstable), 1GB RAM, 20GB gp2 storage, and ~85 max connections.
Single-AZ keeps costs low. Multi-AZ would double RDS cost to ~$30/month
but provides automatic failover — only worth it in production.

### ElastiCache — $13/month
`cache.t4g.micro` (1 vCPU, 512MB) used as the Celery broker.
Single node, no replication. If Redis restarts, Celery tasks pause
briefly — acceptable for dev/staging.

### ECS Fargate — $15/month (both services)
Fargate pricing = vCPU-hours + GB-hours.
At 0.25 vCPU / 512MB running 24/7:
- vCPU cost: 0.25 × 730hrs × $0.04048 = ~$7.40
- Memory cost: 0.5GB × 730hrs × $0.004445 = ~$1.62
- Per task: ~$9/month → two tasks: ~$18/month

---

## Cost Reduction Strategies

### Strategy 1 — Fargate Spot for Worker (~70% saving on worker)

**What:** Fargate Spot uses spare AWS capacity at up to 70% discount.
Spot tasks can be interrupted with a 2-minute warning.

**Why it's safe for the worker:**
- Celery tasks are retryable by design
- `job_log` table enforces idempotency — no duplicate execution on retry
- Interruption means the task returns to the queue and re-processes cleanly

**Already implemented** in `infra/terraform/ecs.tf`:
```hcl
capacity_provider_strategy {
  capacity_provider = "FARGATE_SPOT"
  weight            = 1
}
```

**Saving:** Worker drops from ~$9/month → ~$2.70/month. **Save ~$6/month.**

---

### Strategy 2 — Scale ECS to Zero After Hours (~$8/month saving)

**What:** Scale API and worker tasks to 0 outside working hours.
ECS Fargate does not charge for stopped tasks.

```bash
# Scale down at end of day (add to a cron / EventBridge schedule)
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --desired-count 0 \
  --region eu-central-1

aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-worker \
  --desired-count 0 \
  --region eu-central-1

# Scale up at start of day
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --desired-count 1 \
  --region eu-central-1
```

Note: RDS and ElastiCache keep running — they don't support pause.
Only ECS tasks stop billing when desired-count is 0.

**Saving:** 13hrs/day off × 30 days = ~53% of ECS hours saved → **~$8/month.**

---

### Strategy 3 — RDS Reserved Instance (~40% saving on RDS)

**What:** Commit to 1-year usage upfront and get a 40% discount.
Switch from On-Demand to Reserved in the RDS console — no downtime.

**When to use:** Once the environment is stable and running for 12+ months.

**Saving:** ~$15/month → ~$9/month. **Save ~$6/month.**

---

### Strategy 4 — Remove ALB for Dev (~$18/month saving)

**What:** In dev, access ECS tasks directly via their public IP.
No load balancing needed with a single task.

**Trade-off:** No health checks, no SSL, no path routing.
Only acceptable for dev — never for production.

```hcl
# In variables.tf
variable "enable_alb" {
  description = "Set false for dev to save ALB cost"
  type        = bool
  default     = true
}
```

**Saving:** Removes the single largest cost item. **Save ~$18/month.**

---

### Strategy 5 — terraform destroy When Not Working

**What:** Tear down the entire environment when not developing.
Rebuild takes ~10 minutes when needed.

```bash
# Destroy everything
cd infra/terraform
terraform destroy

# Rebuild when needed
terraform apply
./scripts/push-to-ecr.sh
./scripts/run-migrations.sh
```

**Cost while destroyed:** ~$0.05/month (ECR storage only).

**Saving:** **~$66/month → ~$0.05/month.** Best strategy for a portfolio
project that only runs during demos or active development.

---

## Combined Savings Summary

| Strategy | Applies to | Monthly saving |
|----------|-----------|---------------|
| Fargate Spot (worker) | Always | ~$6 |
| Scale to zero after hours | Dev only | ~$8 |
| RDS Reserved Instance | Long-running envs | ~$6 |
| Remove ALB in dev | Dev only | ~$18 |
| terraform destroy | Portfolio/demo | ~$66 |

Applying strategies 1 + 2 + 3 (production-safe): **~$20/month saved (30%).**
Applying all five (dev environment): **~$66/month → ~$0.05/month.**

---

## Scaling — Connection Math

Before changing `max_replicas`, `pool_size`, or `max_overflow`,
always verify this formula passes:

```
max_replicas × (pool_size + max_overflow) < rds_max_connections × 0.8
```

Current values:
```
4 tasks × (5 pool + 5 overflow) = 40 connections
RDS db.t4g.micro max = 85
Safety threshold = 85 × 0.8 = 68
40 < 68  ✅ safe
```

If autoscaling scales to 8 tasks with these settings:
```
8 × 10 = 80 > 68  ❌ risky — reduce pool_size to 3 first
```

CloudWatch alarm in `monitoring.tf` fires at 68 connections
(80% of max) to warn before exhaustion occurs.

---

## Cost vs Reliability Tradeoffs

| Decision | Dev choice | Prod choice | Monthly difference |
|----------|-----------|------------|-------------------|
| RDS availability | Single-AZ | Multi-AZ | +$15/month |
| Worker capacity | FARGATE_SPOT | FARGATE On-Demand | +$6/month |
| Redis replication | Single node | Cluster mode | +$13/month |
| ECS API replicas | 1 | 2 minimum | +$9/month |

> Rule: API stays on On-Demand (no interruptions).
> Worker uses Spot (retryable, idempotent).
> Data stores stay single in dev, replicated in prod.
