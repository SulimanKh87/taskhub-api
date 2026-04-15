# 🛠 Operations Guide — TaskHub API

Day-to-day commands for debugging, monitoring, and operating TaskHub in production.

> This is a living document. Add commands as you discover them.

---

## Debugging Flow — "The app is slow / returning errors"

Follow this order. Start broad, narrow down to root cause.

```
1. Check ALB metrics        → is traffic even reaching the app?
2. Check ECS task health    → are containers running and healthy?
3. Check application logs   → what error is the app throwing?
4. Check RDS metrics        → is the database the bottleneck?
5. Check Redis              → is the broker reachable?
6. Check Prometheus/Grafana → what do the metrics show over time?
```

---

## AWS — ECS

```bash
# List running tasks
aws ecs list-tasks \
  --cluster taskhub-dev-cluster \
  --service-name taskhub-dev-api \
  --desired-status RUNNING \
  --region eu-central-1

# Describe a specific task (CPU, memory, health, exit code)
aws ecs describe-tasks \
  --cluster taskhub-dev-cluster \
  --tasks <task-arn> \
  --region eu-central-1

# List recent STOPPED tasks (find crashes)
aws ecs list-tasks \
  --cluster taskhub-dev-cluster \
  --service-name taskhub-dev-api \
  --desired-status STOPPED \
  --region eu-central-1

# View service events (last 5 — shows deployments, health check failures)
aws ecs describe-services \
  --cluster taskhub-dev-cluster \
  --services taskhub-dev-api \
  --region eu-central-1 \
  --query 'services[0].events[:5]'

# Force new deployment (restarts all tasks with latest image)
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --force-new-deployment \
  --region eu-central-1

# Wait for service to stabilize (use after deploy)
aws ecs wait services-stable \
  --cluster taskhub-dev-cluster \
  --services taskhub-dev-api taskhub-dev-worker \
  --region eu-central-1

# Scale service manually (override autoscaling temporarily)
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --desired-count 2 \
  --region eu-central-1

# Execute a command inside a running container (ECS Exec — must be enabled)
aws ecs execute-command \
  --cluster taskhub-dev-cluster \
  --task <task-arn> \
  --container api \
  --interactive \
  --command "/bin/sh"
```

---

## AWS — CloudWatch Logs

```bash
# Tail API logs live
aws logs tail /ecs/taskhub-dev-api \
  --follow \
  --region eu-central-1

# Tail worker logs live
aws logs tail /ecs/taskhub-dev-worker \
  --follow \
  --region eu-central-1

# Tail with since filter (last 30 minutes)
aws logs tail /ecs/taskhub-dev-api \
  --since 30m \
  --region eu-central-1

# Search logs for a specific error pattern
aws logs filter-log-events \
  --log-group-name /ecs/taskhub-dev-api \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000) \
  --region eu-central-1

# Search for a specific exception
aws logs filter-log-events \
  --log-group-name /ecs/taskhub-dev-api \
  --filter-pattern "sqlalchemy" \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --region eu-central-1

# CloudWatch Insights query (more powerful — use in console)
# fields @timestamp, @message
# | filter @message like /ERROR/
# | sort @timestamp desc
# | limit 50
```

---

## AWS — RDS PostgreSQL

```bash
# Check DB instance status
aws rds describe-db-instances \
  --db-instance-identifier taskhub-dev-postgres \
  --region eu-central-1 \
  --query 'DBInstances[0].{Status: DBInstanceStatus, Endpoint: Endpoint.Address}'

# Get current connection count
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=taskhub-dev-postgres \
  --start-time $(date -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date --iso-8601=seconds) \
  --period 60 \
  --statistics Maximum \
  --region eu-central-1

# Get CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=taskhub-dev-postgres \
  --start-time $(date -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date --iso-8601=seconds) \
  --period 60 \
  --statistics Average \
  --region eu-central-1
```

---

## AWS — ECR Images

```bash
# List recent images (check what's deployed)
aws ecr describe-images \
  --repository-name taskhub-dev-api \
  --region eu-central-1 \
  --query 'sort_by(imageDetails, &imagePushedAt)[-5:].{Tag: imageTags[0], Pushed: imagePushedAt}'

# Get the currently deployed image tag
aws ecs describe-task-definition \
  --task-definition taskhub-dev-api \
  --region eu-central-1 \
  --query 'taskDefinition.containerDefinitions[0].image'
```

---

## AWS — Secrets Manager

```bash
# List all TaskHub secrets
aws secretsmanager list-secrets \
  --region eu-central-1 \
  --query 'SecretList[?starts_with(Name, `taskhub`)].Name'

# Verify a secret exists (never print the value in terminal)
aws secretsmanager describe-secret \
  --secret-id taskhub/dev/db-password \
  --region eu-central-1 \
  --query '{Name: Name, LastChanged: LastChangedDate}'

# Rotate a secret (update the value)
aws secretsmanager put-secret-value \
  --secret-id taskhub/dev/jwt-secret \
  --secret-string "new-secret-value-here" \
  --region eu-central-1
```

---

## Kubernetes — kubectl Quick Reference

```bash
# Get all resources in the taskhub namespace
kubectl get all -n taskhub

# Watch pods in real time (see restarts, status changes)
kubectl get pods -n taskhub -w

# Describe a pod (events, resource usage, probe results)
kubectl describe pod <pod-name> -n taskhub

# Get logs from a running pod
kubectl logs <pod-name> -n taskhub

# Get logs from a crashed pod (previous container)
kubectl logs <pod-name> -n taskhub --previous

# Follow logs live
kubectl logs <pod-name> -n taskhub -f

# Execute a command inside a pod
kubectl exec -it <pod-name> -n taskhub -- /bin/sh

# Check HPA status (is it scaling?)
kubectl get hpa -n taskhub
kubectl describe hpa taskhub-api -n taskhub

# Check events (see scheduling failures, image pull errors)
kubectl get events -n taskhub --sort-by='.lastTimestamp'
```

### Common K8s Failure States

| State | Meaning | First command to run |
|-------|---------|---------------------|
| `CrashLoopBackOff` | Pod crashes on startup, K8s retrying | `kubectl logs <pod> --previous` |
| `OOMKilled` | Pod exceeded memory limit | `kubectl describe pod <pod>` → check Last State |
| `Pending` | Pod can't be scheduled | `kubectl describe pod <pod>` → Events section |
| `ImagePullBackOff` | Can't pull Docker image | `kubectl describe pod <pod>` → check image URI |
| `CreateContainerConfigError` | Missing Secret or ConfigMap | `kubectl describe pod <pod>` → Events section |
| `Terminating` (stuck) | Pod won't die gracefully | `kubectl delete pod <pod> --force --grace-period=0` |

---

## Linux — Process and Network

```bash
# What process is listening on port 8000?
ss -tulpn | grep 8000
# or
lsof -i :8000

# Check all listening ports
ss -tulpn

# Check outbound connections (is app reaching DB?)
ss -tn | grep 5432    # PostgreSQL
ss -tn | grep 6379    # Redis

# Check DNS resolution
dig taskhub-dev-postgres.xxx.eu-central-1.rds.amazonaws.com

# Test HTTP endpoint
curl -v http://localhost:8000/health
curl -v -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"

# Check system resource usage
top                  # real-time CPU and memory
htop                 # better interactive version
free -h              # memory summary
df -h                # disk usage

# Check process resource usage
ps aux | grep uvicorn
ps aux | grep celery

# View system logs
journalctl -u docker --since "1 hour ago"
journalctl -f        # follow all system logs
```

---

## Docker — Local Debugging

```bash
# View running containers
docker ps

# View logs from a container
docker logs taskhub-api -f
docker logs taskhub-celery-worker -f

# Get container resource usage
docker stats

# Execute a command inside a running container
docker exec -it taskhub-api /bin/sh

# Check environment variables inside container
docker exec taskhub-api env | grep -v PASSWORD | grep -v SECRET

# Restart a single service
docker compose restart api

# Rebuild and restart (after code change)
docker compose up --build api

# Check network connectivity between containers
docker exec taskhub-api curl -v http://taskhub-postgres:5432
docker exec taskhub-api curl -v http://taskhub-redis:6379
```

---

## Prometheus Queries — Useful PromQL

```promql
# Request rate (req/sec, last 5 minutes)
sum(rate(http_requests_total{job="taskhub-api"}[5m]))

# Error rate percentage
100 * sum(rate(http_requests_total{job="taskhub-api", status=~"5.."}[5m]))
    / sum(rate(http_requests_total{job="taskhub-api"}[5m]))

# p99 latency
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{job="taskhub-api"}[5m])) by (le)
)

# Slowest endpoints (p95 latency, last 5 min)
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="taskhub-api"}[5m])) by (le, handler)
)

# In-flight requests (are we processing a lot right now?)
sum(http_requests_in_progress{job="taskhub-api"})
```
