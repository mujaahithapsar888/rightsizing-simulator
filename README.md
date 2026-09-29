# 🎯 Performance-Safe Rightsizing Simulator

> An enterprise-grade, machine-learning-powered cloud infrastructure simulation and rightsizing platform tailored for cloud media streaming platforms, video transcoding fleets, and latency-critical microservices.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pytest](https://img.shields.io/badge/Pytest-8.4-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)

---

## 📑 Table of Contents
1. [Overview & Key Features](#-overview--key-features)
2. [System Architecture](#-system-architecture)
3. [Quick Start (Docker & Local)](#-quick-start)
4. [Granular API Endpoints Reference](#-granular-api-endpoints-reference)
5. [Complete Relational Database Schema](#-complete-relational-database-schema)
6. [Unit Testing & Test Suites](#-unit-testing--test-suites)
7. [Error Boundaries & Fault Tolerance](#-error-boundaries--fault-tolerance)
8. [Project Structure](#-project-structure)
9. [Milestone Reports & Technical Documentation](#-milestone-reports--technical-documentation)

---

## 🌟 Overview & Key Features

Cloud media encoding pipelines (FFmpeg, ABR video packaging, live WebRTC packet relay) experience volatile, non-linear traffic surges. Conventional automated rightsizing tools downsize instances based solely on arithmetic average utilization, triggering CPU starvation, frame drops, and SLA breaches.

The **Performance-Safe Rightsizing Simulator** balances financial cost savings against Site Reliability Engineering (SRE) performance preservation by providing:
- **Streaming Telemetry Ingestion**: Chunked 64 KB streaming CSV parser extracting P50, P90, P95, and P99 percentiles without memory inflation.
- **Scikit-Learn Workload Trend Detection**: Fits Ordinary Least Squares (OLS) linear regressions with $R^2$ goodness-of-fit to penalize growing workloads.
- **Adaptive Safety Margin Buffering**: Operator-configurable margins ($0\% - 50\%$) that dynamically contract hardware thresholds before evaluating breach probabilities.
- **Multi-Scenario A/B Testing**: Simulates $N$ candidate instance configurations concurrently, generating a normalized composite score:
  $$\text{Score} = w_{savings} \times \text{Savings}_{norm} + (1 - w_{savings}) \times (100 - \text{Risk Score})$$
- **Human-in-the-Loop Feedback**: Stakeholder reviews capturing ease of use, recommendation quality, and trust.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  CLIENT APPLICATION LAYER                                    │
│                     React 18 + TypeScript + Vite + Zustand + TanStack Query                  │
│                     (Dashboard, Simulator Studio, A/B Testing, CSV Uploader)                 │
└──────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                               │ HTTPS / REST (Stateless Bearer JWT Tokens)
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  FASTAPI APPLICATION GATEWAY                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────────┐  │
│  │  Authentication Engine  │  │  Metrics Ingestion API  │  │  Simulation & Experiment API │  │
│  │  (JWT + BCrypt + RBAC)  │  │  (Streaming CSV Parser) │  │  (Asynchronous Task Handler) │  │
│  └────────────┬────────────┘  └────────────┬────────────┘  └──────────────┬───────────────┘  │
└───────────────┼────────────────────────────┼──────────────────────────────┼──────────────────┘
                │                            │                              │
                ▼                            ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐    ┌──────────────────────────────┐
│     SECURITY SERVICE    │    │   DATA STREAM ENGINE    │    │      ML ANALYTICS ENGINE     │
│  - Salted BCrypt (12 rd)│    │  - Chunked validation   │    │  - Scikit-Learn OLS Trend    │
│  - HS256 Token Signing  │    │  - Anomaly filtering    │    │  - Percentile Scaling Model  │
│  - Dependency Injection │    │  - P50-P99 Aggregator   │    │  - Risk Classification Matrix│
└───────────────┬─────────┘    └─────────────┬───────────┘    └──────────────┬───────────────┘
                │                            │                               │
                └────────────────────────────┼───────────────────────────────┘
                                             │ Async SQLAlchemy 2.0 Engine
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   DATABASE PERSISTENCE LAYER                                 │
│                                SQLite (aiosqlite) / PostgreSQL                               │
│      [Users] ──< [MetricDatasets] ──< [MetricRecords] ──< [SimulationRuns] ──< [Experiments] │
│                                         ▲                                                    │
│                               [StakeholderFeedback]                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker (Single Command)
```bash
# 1. Clone repository
git clone https://github.com/mujaahithapsar888/rightsizing-simulator.git
cd rightsizing-simulator

# 2. Setup environment configuration
cp .env.example .env

# 3. Build and launch all services
docker-compose up --build
```
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Interactive OpenAPI/Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Default Credentials**: `admin` / `admin123`

### Option 2: Local Development

#### Backend (Python 3.9+)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend (Node.js 18+)
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 Granular API Endpoints Reference

All routes are versioned under `/api/v1/`. Protected endpoints require an `Authorization: Bearer <token>` header.

### 1. Authentication (`/api/v1/auth`)

| Method | Route | Access | Request Body | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Public | `{ username, password }` | `{ access_token, token_type }` | Authenticates user against BCrypt hash, issues 24-hr JWT token. |
| `GET` | `/api/v1/auth/me` | User | *None* | `{ id, username, email, role }` | Returns current authenticated user profile. |

### 2. Telemetry Ingestion (`/api/v1/metrics`)

| Method | Route | Access | Request Parameters | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/metrics/upload` | User | `multipart/form-data` (`file`) | `MetricDataset` object | Streams CSV file in 64 KB chunks, executes anomaly filtering and statistical extraction. |
| `GET` | `/api/v1/metrics/` | User | `skip=0&limit=20` (Query) | `{ items: MetricDataset[], total }` | Paginated listing of uploaded datasets with pre-computed averages. |
| `GET` | `/api/v1/metrics/{id}/stats` | User | `id: int` (Path) | `{ p50, p90, p95, p99, mean, std }` | Returns deep statistical distributions across all metrics. |
| `GET` | `/api/v1/metrics/{id}/records`| User | `id: int, skip=0, limit=100` | `{ items: MetricRecord[], total }` | Returns granular time-series samples for Chart.js rendering. |

### 3. ML Rightsizing Simulator (`/api/v1/simulator`)

| Method | Route | Access | Request Body | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/simulator/run` | User | `SimulationConfig` JSON | `SimulationRun` JSON | Runs Scikit-learn trend analysis, computes breach risk, scaling ratios, and cost savings. |
| `GET` | `/api/v1/simulator/runs` | User | `skip=0&limit=20` (Query) | `{ items: SimulationRun[], total }` | Historical log of executed simulations. |

**Example Simulation Request Body**:
```json
{
  "name": "Production Transcoding Cluster Rightsizing",
  "dataset_id": 1,
  "current_instance_type": "c5.4xlarge",
  "target_instance_type": "c5.2xlarge",
  "current_vcpu": 16,
  "current_memory_gb": 32.0,
  "target_vcpu": 8,
  "target_memory_gb": 16.0,
  "current_cost_per_hour_usd": 0.68,
  "target_cost_per_hour_usd": 0.34,
  "max_cpu_threshold_pct": 80.0,
  "max_memory_threshold_pct": 85.0,
  "safety_margin_pct": 15.0,
  "instance_count": 10,
  "time_window_hours": 24
}
```

### 4. A/B Testing & Experiments (`/api/v1/experiments`)

| Method | Route | Access | Request Body | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/experiments/` | User | `{ title, dataset_id, scenarios }` | `ExperimentResult` JSON | Simulates $N$ candidate instance targets concurrently, ranks by composite utility score. |
| `GET` | `/api/v1/experiments/` | User | `skip=0&limit=20` | `{ items: Experiment[], total }` | Retrieves past comparative experiment results. |

### 5. Stakeholder Feedback (`/api/v1/feedback`)

| Method | Route | Access | Request Body | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/feedback/` | User | `{ ease_of_use, recommendation_quality, trust, overall_satisfaction, comments }` | `{ status: "success" }` | Records human-in-the-loop review ratings (1 - 5 stars). |
| `GET` | `/api/v1/feedback/stats`| User | *None* | `{ avg_ease, avg_quality, avg_trust, avg_satisfaction, total_reviews }` | Aggregates stakeholder consensus and NPS ratings. |

---

## 🗄️ Complete Relational Database Schema

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ENTITY RELATIONSHIP DIAGRAM                               │
└────────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────┐
  │       users       │
  ├───────────────────┤
  │ id (PK)           │
  │ username          │
  │ email             │
  │ hashed_password   │
  │ role              │
  │ is_active         │
  │ created_at        │
  └─────────┬─────────┘
            │
            ├─── 1:N ───► [metric_datasets]
            │                   │
            │                   └─── 1:N (Cascade) ───► [metric_records]
            │
            ├─── 1:N ───► [simulation_runs]
            │
            ├─── 1:N ───► [experiments]
            │
            └─── 1:N ───► [stakeholder_feedback]
```

### Table Definitions & Constraints

#### 1. `users`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `username` (VARCHAR(64), UNIQUE, NOT NULL, INDEXED)
- `email` (VARCHAR(128), UNIQUE, NOT NULL, INDEXED)
- `hashed_password` (VARCHAR(255), NOT NULL) — Salted BCrypt hash (12 work rounds)
- `role` (VARCHAR(32), NOT NULL, DEFAULT 'operator') — Enum: `admin`, `operator`, `viewer`
- `is_active` (BOOLEAN, NOT NULL, DEFAULT TRUE)
- `created_at` (DATETIME, NOT NULL, DEFAULT UTC)

#### 2. `metric_datasets`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `user_id` (INTEGER, FK -> `users.id`, NOT NULL)
- `name` (VARCHAR(128), NOT NULL)
- `description` (TEXT, NULLABLE)
- `filename` (VARCHAR(255), NOT NULL)
- `total_records` (INTEGER, NOT NULL, DEFAULT 0)
- `time_window_start` / `time_window_end` (DATETIME, NULLABLE)
- `avg_cpu_utilization` (FLOAT, DEFAULT 0.0) — Pre-aggregated mean
- `avg_memory_utilization` (FLOAT, DEFAULT 0.0) — Pre-aggregated mean
- `avg_latency_ms` (FLOAT, DEFAULT 0.0) — Pre-aggregated mean
- `avg_availability` (FLOAT, DEFAULT 100.0) — Pre-aggregated mean
- `status` (VARCHAR(32), DEFAULT 'processing') — Enum: `processing`, `ready`, `error`
- `created_at` (DATETIME, NOT NULL, DEFAULT UTC)

#### 3. `metric_records`
- `id` (BIGINT, PK, AUTOINCREMENT)
- `dataset_id` (INTEGER, FK -> `metric_datasets.id`, NOT NULL, INDEXED)
- `timestamp` (DATETIME, NOT NULL, INDEXED)
- `node_id` (VARCHAR(64), NOT NULL, INDEXED)
- `cpu_utilization` (FLOAT, NOT NULL) — Clamped $[0.0, 100.0]\%$
- `memory_utilization` (FLOAT, NOT NULL) — Clamped $[0.0, 100.0]\%$
- `disk_io_read_mbs` / `disk_io_write_mbs` (FLOAT, DEFAULT 0.0)
- `network_rx_mbps` / `network_tx_mbps` (FLOAT, DEFAULT 0.0)
- `latency_ms` (FLOAT, DEFAULT 0.0)
- `availability_pct` (FLOAT, DEFAULT 100.0)

#### 4. `simulation_runs`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `user_id` (INTEGER, FK -> `users.id`, NOT NULL)
- `dataset_id` (INTEGER, FK -> `metric_datasets.id`, NOT NULL)
- `name` (VARCHAR(128), NOT NULL)
- `current_instance_type` / `target_instance_type` (VARCHAR(64), NOT NULL)
- `instance_count` (INTEGER, DEFAULT 1)
- `safety_margin_pct` (FLOAT, DEFAULT 15.0)
- `max_cpu_threshold_pct` (FLOAT, DEFAULT 80.0)
- `max_memory_threshold_pct` (FLOAT, DEFAULT 85.0)
- `risk_score` (FLOAT, NOT NULL) — Clamped $[0.0, 100.0]$
- `risk_level` (VARCHAR(32), NOT NULL) — `low`, `medium`, `high`, `critical`
- `monthly_savings` (FLOAT, NOT NULL) — USD
- `results_json` (TEXT / JSON, NOT NULL)
- `status` (VARCHAR(32), DEFAULT 'completed')
- `created_at` (DATETIME, NOT NULL, DEFAULT UTC)

#### 5. `experiments`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `user_id` (INTEGER, FK -> `users.id`, NOT NULL)
- `dataset_id` (INTEGER, FK -> `metric_datasets.id`, NOT NULL)
- `title` (VARCHAR(128), NOT NULL)
- `scenarios_config` (TEXT / JSON, NOT NULL)
- `ranked_results` (TEXT / JSON, NOT NULL)
- `winning_scenario` (VARCHAR(64), NOT NULL)
- `created_at` (DATETIME, NOT NULL, DEFAULT UTC)

#### 6. `stakeholder_feedback`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `user_id` (INTEGER, FK -> `users.id`, NOT NULL)
- `ease_of_use` (INTEGER, NOT NULL) — $1 - 5$ stars
- `recommendation_quality` (INTEGER, NOT NULL) — $1 - 5$ stars
- `trust` (INTEGER, NOT NULL) — $1 - 5$ stars
- `overall_satisfaction` (INTEGER, NOT NULL) — $1 - 5$ stars
- `comments` (TEXT, NULLABLE)
- `submitted_at` (DATETIME, NOT NULL, DEFAULT UTC)

---

## 🧪 Unit Testing & Test Suites

The backend features test suites implemented in **Pytest** verifying analytical invariants, Scikit-learn regression models, and boundary conditions.

### Running Unit Tests:
```bash
cd backend
python -m pytest -v
```

### Verified Test Matrix (100% Pass Rate):
- ✅ `test_percentile_safe_empty_and_valid`: Asserts graceful handling of empty telemetry vectors.
- ✅ `test_pct_above_threshold`: Verifies threshold breach frequency estimation.
- ✅ `test_risk_score_and_classification_boundaries`: Validates 4-tier risk classification taxonomy.
- ✅ `test_linear_regression_trend_detection`: Tests Scikit-learn linear trend slope and $R^2$ fit.
- ✅ `test_resource_scaling_and_projection`: Validates instance capacity scaling ratios.
- ✅ `test_full_rightsizing_simulation_run`: End-to-end execution of simulation analytical pipeline.
- ✅ `test_composite_score_weighting`: Validates multi-objective utility balance (cost vs safety).
- ✅ `test_verdict_mapping`: Validates recommendation verdict mapping.
- ✅ `test_multi_scenario_experiment_execution`: Tests A/B scenario comparison and winner ranking.

For complete test specifications, see [`docs/testing_and_error_boundaries.md`](docs/testing_and_error_boundaries.md).

---

## 🛡️ Error Boundaries & Fault Tolerance

### Frontend Error Boundary (`frontend/src/components/ErrorBoundary.tsx`)
- **React Class Lifecycle**: Implements `getDerivedStateFromError` and `componentDidCatch` to prevent runtime component crashes from unmounting the SPA.
- **Glassmorphic Fallback UI**: Displays user-friendly diagnostics with collapsible error stack inspection and application reload buttons.
- **Root Mounting**: Wraps all router trees in `frontend/src/App.tsx`.

### Backend Exception Boundaries (`backend/app/main.py`)
- **`StarletteHTTPException` Handler**: Returns uniform RFC-compliant JSON payloads for 4xx/5xx errors.
- **`RequestValidationError` Handler**: Catches Pydantic schema validation failures, returning structured 422 Unprocessable Entity responses with parameter-level error pointers.
- **Generic `Exception` Catch-All Handler**: Logs unhandled exceptions with full tracebacks to server logs while returning sanitized 500 Internal Server Error payloads to the client.
- **Transactional Rollbacks**: All database write operations utilize asynchronous session context managers, automatically rolling back partial writes upon encountering unhandled exceptions.

---

## 📁 Project Structure

```
rightsizing-simulator/
├── docker-compose.yml              # Multi-container orchestration (FastAPI + React + DB)
├── README.md                       # Comprehensive project documentation
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git exclusion rules
│
├── backend/                        # Complete FastAPI Application Layer
│   ├── Dockerfile                  # Production container definition for backend
│   ├── requirements.txt            # Python dependencies (FastAPI, Scikit-learn, SQLAlchemy, etc.)
│   ├── pytest.ini                  # Pytest configuration
│   ├── alembic.ini                 # DB migration configuration
│   ├── app/
│   │   ├── main.py                 # App entrypoint, routers, CORS & global error boundaries
│   │   ├── core/                   # Database (SQLite / Postgres), security (JWT, BCrypt), config
│   │   ├── models/                 # SQLAlchemy 2.0 async models (7 entities)
│   │   ├── schemas/                # Pydantic v2 validation contracts
│   │   ├── api/v1/                 # REST endpoints (auth, metrics, simulator, experiments, feedback)
│   │   └── services/               # Rightsizing ML engine, trend regression, A/B testing, ingestion
│   └── tests/                      # Pytest unit testing suites
│
├── frontend/                       # Complete React 18 + Vite + TypeScript Application
│   ├── Dockerfile                  # Production container definition for frontend
│   ├── package.json                # Dependencies & build scripts
│   ├── vite.config.ts              # Vite configuration
│   ├── tsconfig.json               # TypeScript strict configuration
│   └── src/
│       ├── main.tsx & App.tsx      # Routing & ErrorBoundary root mounting
│       ├── index.css               # 800+ lines custom dark/glassmorphic design system
│       ├── types/index.ts          # Central TypeScript interfaces
│       ├── api/                    # Axios API client & endpoints integration
│       ├── context/AuthContext.tsx # JWT authentication provider & session persistence
│       ├── store/                  # Zustand state stores
│       ├── components/             # ErrorBoundary, Layout, Navbar, Sidebar, Chart.js components
│       └── pages/                  # Dashboard, Simulator, Experiments, Reports, UploadData, Settings, Login
│
└── docs/                           # Technical Documentation & Datasets
    ├── architecture.md             # System design & data flow specifications
    ├── milestone_2_report.md       # Phase 2 (35% → 70%) Progress Report
    ├── milestone_2_comprehensive_report.md # 8,000-word comprehensive technical report
    ├── testing_and_error_boundaries.md     # Testing strategy & Error boundary architecture
    └── sample_metrics.csv          # Benchmark cloud streaming node telemetry dataset
```

---

## 📚 Milestone Reports & Technical Documentation

- 📄 [System Architecture Specification](docs/architecture.md)
- 📄 [Testing & Error Boundary Architecture](docs/testing_and_error_boundaries.md)
- 📄 [Milestone 2 (35% → 70%) Progress Report](docs/milestone_2_report.md)
- 📄 [Milestone 2 Comprehensive 4-Chapter Technical Report (8,000 Words)](docs/milestone_2_comprehensive_report.md)
- 📊 [Benchmark Telemetry Dataset (`sample_metrics.csv`)](docs/sample_metrics.csv)

---

## 📄 License
Academic and Evaluation Rightsizing Simulator Project. MIT License.
