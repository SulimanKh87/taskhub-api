# 🧩 Terraform Alignment — Infrastructure as Code Mapping

This document maps **architecture components** to **Terraform-managed resources**.

Terraform is used to:
- Version infrastructure
- Enable reproducible environments
- Prevent configuration drift

> **Status:**  
> Terraform resources listed in this document represent the **planned infrastructure**.
> Initial Terraform skeletons will be introduced incrementally, starting with
> networking, ECS, and RDS.

---

## 1️⃣ Networking

Terraform resources:
- aws_vpc
- aws_subnet (public / private)
- aws_security_group
- aws_internet_gateway
- aws_nat_gateway

Purpose:
- Isolate services
- Control traffic
- Secure databases

---

## 2️⃣ Compute (ECS)

Terraform resources:
- aws_ecs_cluster
- aws_ecs_task_definition
- aws_ecs_service
- aws_iam_role (task execution)

Purpose:
- Run stateless containers
- Enable scaling
- Isolate workloads

---

## 3️⃣ Load Balancing

Terraform resources:
- aws_lb
- aws_lb_listener
- aws_lb_target_group

Purpose:
- HTTPS termination
- Traffic distribution
- Health checks

---

## 4️⃣ Databases

### PostgreSQL (RDS)
Terraform resources:
- aws_db_instance
- aws_db_subnet_group
- aws_db_parameter_group

Purpose:
- Managed persistence
- Backups & failover
- Strong consistency

---

### Redis (ElastiCache)
Terraform resources:
- aws_elasticache_cluster
- aws_elasticache_subnet_group

Purpose:
- Caching
- Async brokering

---

## 5️⃣ Messaging

### SQS
Terraform resources:
- aws_sqs_queue
- aws_sqs_queue_policy

Purpose:
- Durable async events
- Decoupling services

---

## 6️⃣ Search

### Elasticsearch / OpenSearch
Terraform resources:
- aws_opensearch_domain

Purpose:
- Search optimization
- Read-heavy workloads

---

## 7️⃣ Observability

Terraform resources:
- aws_cloudwatch_log_group
- aws_cloudwatch_metric_alarm

Purpose:
- Logging
- Alerting
- Operational visibility

---

## 🎯 Why Terraform Matters

Infrastructure is code.
Code is reviewable.
Reviewable systems are reliable.

Terraform turns architecture into **repeatable reality**.