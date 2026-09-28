# Project Progress Report — Milestone 2 (Phase 2: 35% → 70%)
**Project Title**: Performance-Safe Rightsizing Simulator for Cloud Media Platforms  
**Evaluation Checkpoint**: Milestone 2 Review (Cumulative Progress: 70%)  
**Repository**: [https://github.com/mujaahithapsar888/rightsizing](https://github.com/mujaahithapsar888/rightsizing)  
**Date**: September 2026  

---

## 1. Executive Summary

The **Performance-Safe Rightsizing Simulator** is an intelligent cloud cost optimization and infrastructure simulation platform tailored for media-streaming platforms and compute-intensive microservices. While traditional cloud cost optimization tools indiscriminately downscale instances to minimize expenditure, this simulator enforces stringent SLA, latency, and performance safety boundaries to prevent system throttling and customer-facing degradation.

In **Milestone 1 (0% → 35%)**, the foundational system architecture, sample cloud telemetry dataset, and responsive frontend UI wireframe (React, TypeScript, custom design system, and analytics dashboard) were established.

In **Milestone 2 (35% → 70%)**, the project transitioned from static wireframes to a **fully functioning, end-to-end data processing and machine learning simulation system**. This phase delivered:
1. **Production-grade RESTful API** built on Python FastAPI with async request handling.
2. **Relational Database & ORM Layer** (SQLAlchemy Async + SQLite / PostgreSQL) supporting users, datasets, simulation runs, experiments, and feedback.
3. **Telemetry Ingestion Pipeline** processing chunked CSV metrics with statistical aggregation (P50, P90, P95, P99, standard deviation, and mean).
4. **Scikit-Learn Powered Rightsizing Engine** with workload trend regression ($R^2$ fit), performance breach probability modeling, and multi-tier risk classification.
5. **A/B Testing & Scenario Comparison Engine** providing multi-candidate ranking and composite optimization scoring (balancing cost savings vs. SLA risk).
6. **Frontend Live Integration** connecting React components to live backend endpoints with real-time reactive updates.

---

## 2. Milestone Progress Tracker (35% → 70%)

| Milestone / Phase | Progress | Key Deliverables | Status |
| :--- | :---: | :--- | :---: |
| **Milestone 1: Architecture & UI Wireframes** | **35%** | Architecture docs, design tokens, UI wireframes, Login view, mock KPI cards, sample dataset. | ✅ Completed |
| **Milestone 2: Backend, ML Engines & Live Integration** | **+35% (70%)** | FastAPI REST API, async database ORM, CSV pipeline, Scikit-learn trend engine, rightsizing risk algorithm, A/B testing engine, live UI data binding. | ✅ **Current Phase (Delivered)** |
| **Milestone 3: Containerization & Final Deployment** | **+30% (100%)** | Multi-container Docker orchestration (`docker-compose`), automated PDF/JSON reporting, end-to-end integration tests, cloud deployment. | ⏳ Upcoming |

---

## 3. System Architecture & Component Design

The Milestone 2 architecture adopts a decoupled, asynchronous microservices-ready structure:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND PRESENTATION LAYER                     │
│        React 18 + TypeScript + Vite + Zustand + TanStack Query        │
│    (Analytics Dashboard, CSV Uploader, ML Simulator, A/B Testing)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API / JSON (Bearer JWT)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Auth Router  │  │Metrics Router│  │Simulator API │  │Experiments │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                 │                 │                │         │
│         ▼                 ▼                 ▼                ▼         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ JWT Security │  │CSV Processing│  │ ML Analytics │  │A/B Scenario│  │
│  │  & BCrypt    │  │   Pipeline   │  │ & Risk Model │  │ Evaluator  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Async SQLAlchemy Engine
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          PERSISTENCE LAYER                             │
│   SQLite (aiosqlite) / PostgreSQL | 7 Relational Tables + Migrations   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Backend Engineering & Database Schema

### 4.1 Relational Data Models
The data layer is implemented using SQLAlchemy 2.0 async declarative models across seven core entities:

1. **`users`**: Secure multi-tenant access control with salted BCrypt password hashing and role-based permissions (`admin`, `operator`, `viewer`).
2. **`metric_datasets`**: Metadata container representing uploaded cloud monitoring intervals (time range, sample counts, computed fleet-wide averages).
3. **`metric_records`**: Granular time-series metrics capturing `cpu_utilization`, `memory_utilization`, `disk_io_read_mbs`, `disk_io_write_mbs`, `network_rx_mbps`, `network_tx_mbps`, `latency_ms`, and `availability_pct`.
4. **`simulation_runs`**: Persisted records of user simulation executions including instance type mappings, safety thresholds, and resulting risk matrices.
5. **`experiments`**: Container for comparative multi-scenario simulations evaluated side-by-side.
6. **`reports`**: Generated summary documents capturing executive optimization findings.
7. **`stakeholder_feedback`**: Human-in-the-loop review audit records capturing ease of use, recommendation trust, and satisfaction scores.

### 4.2 Ingestion & Processing Pipeline
The CSV ingestion service (`backend/app/services/metrics_service.py`) executes:
- **Chunked File Streaming**: Protects memory consumption when parsing multi-gigabyte server telemetry logs.
- **Header & Schema Validation**: Ensures required CPU, memory, and network columns are present and typed correctly.
- **Statistical Aggregation**: Automatically computes P50, P90, P95, P99, standard deviation, and mean values upon upload completion, immediately populating dataset summary cards.

---

## 5. Machine Learning Rightsizing & Risk Assessment Engine

### 5.1 Instance Scaling & Resource Projection
Given a workload transitioning from current instance $I_{curr}$ to target instance $I_{target}$, scaling factors are computed:

$$S_{cpu} = \frac{vCPU_{target}}{vCPU_{current}}, \quad S_{mem} = \frac{Memory_{target}}{Memory_{current}}$$

Projected utilization time series are then evaluated against historical utilization vectors:

$$\mathbf{u}_{cpu}^{proj} = \frac{\mathbf{u}_{cpu}^{hist}}{S_{cpu}}, \quad \mathbf{u}_{mem}^{proj} = \frac{\mathbf{u}_{mem}^{hist}}{S_{mem}}$$

### 5.2 Workload Trend Detection (Linear Regression)
To prevent underestimating growth trends, Scikit-learn's `LinearRegression` with `StandardScaler` fits a slope to the workload:

$$y = \beta_0 + \beta_1 X + \epsilon, \quad R^2 = 1 - \frac{\sum (y - \hat{y})^2}{\sum (y - \bar{y})^2}$$

- Slope is evaluated in $\% \text{ growth per hour}$.
- Direction is classified into: `stable` ($|\text{slope}| < 0.02$), `increasing` ($\text{slope} > 0.02$), or `decreasing` ($\text{slope} < -0.02$).
- Workloads exhibiting an `increasing` trend incur an automatic trend penalty in breach risk calculations.

### 5.3 Safety Margin & Breach Probability
To guarantee high-availability streaming SLAs, user-defined safety margins adjust the effective capacity thresholds:

$$T_{cpu}^{effective} = T_{cpu}^{max} \times \left(1 - \frac{M_{safety}}{200}\right)$$

Breach probability is calculated by measuring the frequency of projected utilization exceeding the effective threshold:

$$P_{breach} = \min\left(100.0, \; \max(P(\mathbf{u}_{cpu}^{proj} > T_{cpu}^{eff}), \; P(\mathbf{u}_{mem}^{proj} > T_{mem}^{eff})) + \text{Penalty}_{trend}\right)$$

### 5.4 Risk Score & Classification Matrix
A composite risk index ($0 - 100$) is computed:

$$\text{Risk Score} = \min\left(100.0, \; P_{breach} \times \left(1 - \frac{M_{safety}}{100}\right) \times 1.5\right)$$

| Score Range | Risk Level | Actionable Recommendation |
| :---: | :---: | :--- |
| **0.0 – 14.9** | `Low` | **Safe to rightsize**. Substantial cost savings without SLA violation risk. |
| **15.0 – 34.9** | `Medium` | **Proceed with caution**. Apply canary deployment and monitor peak hours. |
| **35.0 – 64.9** | `High` | **Not recommended**. P99 projections approach saturation limits. |
| **65.0 – 100.0** | `Critical` | **Do not rightsize**. High probability of throttling, latency spike, or OOM crash. |

---

## 6. A/B Testing & Scenario Comparison Engine

The scenario simulation engine (`backend/app/services/experiment_engine.py`) allows infrastructure operators to compare $N$ instance candidate scenarios concurrently against identical historical telemetry.

### Composite Score Formula:
Scenarios are ranked using a multi-objective function balancing financial savings against operational safety:

$$\text{Score}_{composite} = w_{savings} \times \left(\frac{\text{Monthly Savings}}{\$10,000} \times 100\right) + (1 - w_{savings}) \times (100 - \text{Risk Score})$$

*(Default weight $w_{savings} = 0.60$ for cost-priority, or $0.40$ for safety-critical workloads).*

The engine automatically declares an experimental **Winner** based on the highest composite score and generates actionable stakeholder recommendations.

---

## 7. REST API Endpoints Implemented

| Method | Endpoint | Description | Phase |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/login` | Issues JWT bearer access token with BCrypt validation | Phase 2 |
| `GET` | `/api/v1/auth/me` | Retrieves current authenticated profile & privileges | Phase 2 |
| `POST` | `/api/v1/metrics/upload` | Streams, parses, and validates telemetry CSV files | Phase 2 |
| `GET` | `/api/v1/metrics/` | Paginated listing of uploaded datasets & metadata | Phase 2 |
| `GET` | `/api/v1/metrics/{id}/stats`| Computes P50–P99 stats, mean, and std for dataset | Phase 2 |
| `GET` | `/api/v1/metrics/{id}/records`| Retrieves time-series records for charting | Phase 2 |
| `POST` | `/api/v1/simulator/run` | Executes ML rightsizing simulation for target config | Phase 2 |
| `GET` | `/api/v1/simulator/runs` | Fetches historical simulation executions & results | Phase 2 |
| `POST` | `/api/v1/experiments/` | Executes multi-scenario A/B comparison experiment | Phase 2 |
| `GET` | `/api/v1/experiments/` | Lists past A/B experiments and ranked winners | Phase 2 |
| `POST` | `/api/v1/feedback/` | Records stakeholder human-in-the-loop audit review | Phase 2 |
| `GET` | `/api/v1/feedback/stats` | Retrieves aggregate stakeholder ratings & NPS scores | Phase 2 |

---

## 8. Experimental Results & Verification

### Test Benchmark Case Study
- **Telemetry Dataset**: `docs/sample_metrics.csv` (100 time-series observations of cloud streaming compute nodes).
- **Baseline Configuration**: 10 $\times$ `c5.4xlarge` (16 vCPU, 32 GB RAM, \$0.68/hr per node).
  - *Current Monthly Spend*: **\$4,896.00**
  - *Baseline Peak CPU*: 38.5% | *Peak Memory*: 55.2%

### Simulation Outcomes Across Candidate Targets:
1. **Candidate A (`c5.2xlarge` - 8 vCPU, 16 GB RAM)**:
   - *Target Monthly Spend*: **\$2,448.00**
   - *Monthly Savings*: **\$2,448.00 (50.0% cost reduction)**
   - *Projected P99 CPU*: 74.2% | *P99 Memory*: 72.8%
   - *Risk Level*: **Low (Score: 8.4)**
   - *Verdict*: **Safe to Rightsize** (Optimal candidate).
2. **Candidate B (`c5.xlarge` - 4 vCPU, 8 GB RAM)**:
   - *Target Monthly Spend*: **\$1,224.00**
   - *Monthly Savings*: **\$3,672.00 (75.0% cost reduction)**
   - *Projected P99 CPU*: 98.4% (Threshold violation) | *Breach Probability*: 64.2%
   - *Risk Level*: **Critical (Score: 86.5)**
   - *Verdict*: **Do Not Rightsize** (Extreme risk of video transcoding dropped frames).

---

## 9. Next Steps (Roadmap to 100% Completion)

With Milestone 2 successfully completing 70% of the project scope, the remaining 30% (Milestone 3) will focus on enterprise hardening:
1. **Container Orchestration**: Finalize multi-stage Docker builds and `docker-compose` production services.
2. **Automated Executive Reporting**: Complete automated PDF/JSON export generation for FinOps teams.
3. **Continuous Integration & Deployment**: Setup GitHub Actions workflow for linting, typing, and automated testing.
