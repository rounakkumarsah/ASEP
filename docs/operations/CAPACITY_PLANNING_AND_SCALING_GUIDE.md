# ASEP — Capacity Planning & Horizontal Scaling Guide
**Document ID:** ASEP-OPS-DOC-003  
**Version:** 1.0 (Enterprise Scaling Architecture)  
**Author:** Principal Infrastructure Architect (Rounak Kumar Sah)  
**Date:** August 24, 2026  

---

## 1. Resource Consumption Formulas per Active Agent Run

To size enterprise clusters accurately, use the following resource sizing math:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RESOURCE ALLOCATION PER CONCURRENT RUN                 │
├─────────────────────────────┬───────────────────────────┬───────────────────┤
│ Resource Dimension          │ Average Load              │ Peak Allocation   │
├─────────────────────────────┼───────────────────────────┼───────────────────┤
│ API Worker Memory (FastAPI) │ 45 MB / session           │ 80 MB / session   │
│ Sandbox Container RAM       │ 128 MB / active container │ 512 MB (Capped)   │
│ Sandbox CPU Allocation      │ 0.15 vCPU                 │ 1.0 vCPU (Capped) │
│ Database Connection Pool    │ 1 connection / run        │ 2 connections     │
│ Redis Memory (Working State)│ 25 KB / session           │ 100 KB / session  │
│ Vector Store (Qdrant)       │ 50 KB / indexed document  │ 1.5 KB / vector   │
└─────────────────────────────┴───────────────────────────┴───────────────────┘
```

### Sizing Calculation Example

For an enterprise cluster supporting **100 Concurrent Active Agent Runs**:
* **Backend API Nodes:** $100 \times 65\text{MB} \approx 6.5\text{GB RAM}$ + 4 vCPU.
* **Sandbox Container Host:** $100 \times 256\text{MB} \approx 25.6\text{GB RAM}$ + 16 vCPU (e.g. AWS `c6i.4xlarge` or `m6i.4xlarge`).
* **PostgreSQL Database:** Minimum 150 connection pool capacity, 8GB RAM, SSD NVMe storage.
* **Redis Cluster:** 4GB RAM with RDB/AOF persistence enabled.

---

## 2. Horizontal Scaling Topology (Kubernetes / AWS ECS)

```
                       [ AWS Application Load Balancer ]
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
   [ FastAPI Worker Pod 1 ]                        [ FastAPI Worker Pod N ]
   (Auto-scaling: CPU > 70%)                       (Auto-scaling: CPU > 70%)
              │                                               │
              └───────────────────────┬───────────────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
           [ Redis Cluster 7.x ]             [ PostgreSQL 16 (RDS/Neon) ]
           (PubSub / State Cache)            (Connection Pool: PgBouncer)
                     │                                 │
                     ▼                                 ▼
           [ Qdrant Vector Cluster ]         [ Neo4j Enterprise Cluster ]
```

### Auto-Scaling Triggers & Thresholds

| Metric | Target Metric Source | Scaling Threshold | Scale-Out Action |
|---|---|---|---|
| **CPU Utilization** | `container_cpu_usage_seconds_total` | **> 70% for 3 mins** | +2 Pods (Max: 50) |
| **Active Runs Queue** | `asep_active_runs_gauge` | **> 15 runs per Pod** | +1 Pod per 10 runs |
| **P95 Request Latency**| `http_request_duration_seconds{quantile="0.95"}` | **> 400ms for 2 mins** | +2 Pods |
| **Terminal Connections**| `asep_active_pty_sessions` | **> 20 per node** | Route to adjacent node |

---

## 3. Database Connection Pooling Math

When scaling horizontally across $N$ API pods:
$$\text{Max DB Connections} = (N_{\text{pods}} \times \text{DATABASE\_POOL\_SIZE}) + \text{DATABASE\_MAX\_OVERFLOW} + \text{Admin Margin}$$

* **Default Config:** `DATABASE_POOL_SIZE = 20`, `DATABASE_MAX_OVERFLOW = 10`.
* For a 5-pod cluster: $(5 \times 20) + 10 + 20 = 130$ connections (Well within standard PostgreSQL 300–500 max connection caps).
* For >10 pods: Implement **PgBouncer** in transaction pooling mode.

---
*Verified for high-throughput enterprise deployments.*
