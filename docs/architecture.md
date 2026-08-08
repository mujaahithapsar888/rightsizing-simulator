# Performance-Safe Rightsizing Simulator — Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser Client                           │
│   React 18 + TypeScript + Vite                                  │
│   ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐   │
│   │Dashboard │ │  Simulator │ │Experiments│ │   Reports    │   │
│   └──────────┘ └────────────┘ └──────────┘ └──────────────┘   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  AuthContext · Zustand · TanStack Query · Chart.js       │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST (JSON)
                          │ Bearer JWT
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                            │
│   ┌──────────┐ ┌─────────┐ ┌───────────┐ ┌────────────────┐   │
│   │ /auth    │ │/metrics │ │/simulator │ │/experiments    │   │
│   └──────────┘ └─────────┘ └───────────┘ └────────────────┘   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │          Security · Config · DB Session Mgmt             │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ asyncpg
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 15                                │
│   users · metric_datasets · metric_records                       │
│   simulation_runs · experiments · reports                        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Authentication
```
Browser → POST /api/v1/auth/login (form: username/password)
       ← JWT access_token
Browser → stores token in localStorage
Browser → All subsequent requests include: Authorization: Bearer <token>
```

### 2. Metrics Upload
```
Browser → POST /api/v1/metrics/upload (multipart: file + name)
Backend → validates file type (CSV/Parquet)
        → saves to disk (./uploads/)
        → parses with Pandas → row_count
        → creates MetricDataset record
       ← UploadResponse (dataset_id, row_count)
```

### 3. Simulation Run
```
Browser → POST /api/v1/simulator/run (JSON: SimulationConfig)
Backend → validates config
        → calls _build_stub_results() [ML placeholder]
        → persists SimulationRun with results
       ← SimulationResultOut (id, status, results)
Frontend → renders cost charts + performance radar
```

### 4. Experiment
```
Browser → POST /api/v1/experiments/ (JSON: {name, scenarios[]})
Backend → validates ≥ 2 scenarios
        → generates stub comparison_results
        → persists Experiment record
       ← ExperimentOut
Frontend → side-by-side scenario comparison
```

## Database Schema

### users
| Column           | Type      | Notes              |
|------------------|-----------|--------------------|
| id               | UUID PK   | auto-generated     |
| username         | VARCHAR   | unique, indexed    |
| email            | VARCHAR   | unique, indexed    |
| hashed_password  | VARCHAR   | bcrypt             |
| role             | VARCHAR   | admin/viewer       |
| is_active        | BOOLEAN   | default true       |
| created_at       | TIMESTAMPTZ | auto             |
| updated_at       | TIMESTAMPTZ | auto             |

### metric_datasets
| Column      | Type        | Notes              |
|-------------|-------------|--------------------|
| id          | UUID PK     |                    |
| name        | VARCHAR     |                    |
| description | TEXT        | nullable           |
| file_path   | VARCHAR     | on-disk path       |
| row_count   | INTEGER     |                    |
| status      | VARCHAR     | pending/ready/error|
| uploaded_by | UUID FK     | → users.id         |
| created_at  | TIMESTAMPTZ |                    |

### simulation_runs
| Column        | Type        | Notes                      |
|---------------|-------------|----------------------------|
| id            | UUID PK     |                            |
| name          | VARCHAR     |                            |
| dataset_id    | UUID FK     | → metric_datasets.id       |
| config        | JSONB       | SimulationConfig           |
| results       | JSONB       | SimulationResults (stub)   |
| status        | VARCHAR     | queued/running/completed   |
| created_by    | UUID FK     | → users.id                 |
| created_at    | TIMESTAMPTZ |                            |
| completed_at  | TIMESTAMPTZ | nullable                   |

### experiments
| Column              | Type        | Notes                  |
|---------------------|-------------|------------------------|
| id                  | UUID PK     |                        |
| name                | VARCHAR     |                        |
| dataset_id          | UUID FK     | → metric_datasets.id   |
| scenarios           | JSONB       | ScenarioConfig[]       |
| comparison_results  | JSONB       | stub comparison        |
| status              | VARCHAR     | draft/completed/failed |
| created_by          | UUID FK     | → users.id             |
| created_at          | TIMESTAMPTZ |                        |

### reports
| Column           | Type        | Notes               |
|------------------|-------------|---------------------|
| id               | UUID PK     |                     |
| title            | VARCHAR     |                     |
| report_type      | VARCHAR     | simulation_summary… |
| simulation_id    | UUID FK     | nullable            |
| experiment_id    | UUID FK     | nullable            |
| content          | JSONB       | structured data     |
| rendered_content | TEXT        | nullable HTML/MD    |
| status           | VARCHAR     | draft/final         |
| created_by       | UUID FK     | → users.id          |
| created_at       | TIMESTAMPTZ |                     |

## Frontend Routes

| Path           | Component   | Auth Required |
|----------------|-------------|---------------|
| /login         | Login       | No            |
| /              | Dashboard   | Yes           |
| /upload        | UploadData  | Yes           |
| /simulator     | Simulator   | Yes           |
| /experiments   | Experiments | Yes           |
| /reports       | Reports     | Yes           |
| /settings      | Settings    | Yes           |

## Security

- **Passwords**: bcrypt via passlib
- **Tokens**: HS256 JWT via python-jose, 60-minute expiry
- **Transport**: CORS restricted to configured origins
- **Auth Guard**: ProtectedRoute + 401 interceptor auto-redirect to /login
- **Stateless**: No server-side session storage

## ML Integration Points (Future)

The following stubs will be replaced with scikit-learn models:

1. `backend/app/api/v1/simulator.py` → `_build_stub_results()` → Replace with trained regression model
2. `backend/app/api/v1/experiments.py` → comparison generation → Replace with statistical comparison
3. Future: `backend/app/ml/` directory with preprocessor, trainer, and predictor modules
