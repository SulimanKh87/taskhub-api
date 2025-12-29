# 📈 Scaling Strategy — What Scales and How
This document explains **how TaskHub scales**, **which components scale independently**, and **why scaling decisions were made**.

## 🟡 Current Scaling Baseline

In the current local setup:
- FastAPI runs as a single container
- Celery workers scale manually
- PostgreSQL runs as a single instance
- Redis runs as a single node

The scaling strategies described below represent the **intended AWS deployment**
and guide future infrastructure work.


---

## 🎯 Scaling Principles

- Scale horizontally, not vertically
- Scale stateless services first
- Protect the database
- Prefer async over sync under load

---

## 1️⃣ API Layer Scaling (FastAPI)

### What scales
- ECS API tasks

### How
- Horizontal scaling via ECS Service
- CPU-based auto-scaling
- Load Balancer distributes traffic

### Why
- Stateless containers
- No session affinity
- Linear scaling behavior

---

## 2️⃣ Worker Scaling (Celery)

### What scales
- Background workers

### How
- Separate ECS service
- Scale based on queue depth or CPU

### Why
- Async workloads are bursty
- Isolation from API latency

---

## 3️⃣ PostgreSQL Scaling

### What scales
- Read replicas (optional)

### What does NOT scale easily
- Writes

### Strategy
- Strong schema design
- Indexed queries
- Pagination enforcement

Rule:
> Databases scale through design, not brute force.

---

## 4️⃣ Redis Scaling

### What scales
- Redis clusters
- Partitioned caches

### Use cases
- Rate limiting
- Task brokering
- Hot data caching

Redis is optimized for **speed**, not durability.

---

## 5️⃣ SQS Scaling

### What scales
- Virtually unlimited throughput

### Why
- Fully managed
- Automatic scaling
- Decouples producers and consumers

SQS absorbs traffic spikes without system overload.

---

## 6️⃣ Elasticsearch Scaling

### What scales
- Index shards
- Query nodes

### Strategy
- Scale reads independently
- Rebuild indexes asynchronously

---

## 7️⃣ Load Balancer Scaling

### What scales
- Connection handling
- TLS termination

### Why
- Shields backend services
- Simplifies client logic

---

## 🔁 Scaling Flow Summary

Traffic spike
→ ALB absorbs connections
→ ECS scales API tasks
→ Async tasks queued
→ Workers scale
→ DB protected by limits

---

## 🧠 Key Takeaway

Scaling is **not adding servers**.
Scaling is **designing systems that remain predictable under load**.