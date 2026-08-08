# 🎯 Performance-Safe Rightsizing Simulator

A full-stack web application for cloud media streaming platforms to safely rightsize VM/container resources — without sacrificing performance.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python FastAPI (async) |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy (async) + Alembic |
| Auth | JWT (python-jose) |
| Charts | Chart.js + react-chartjs-2 |
| Containerization | Docker + Docker Compose |
| State Management | Zustand + React Query |

---

## 🚀 Quick Start (Docker)

```bash
# 1. Clone the repo
git clone <repo-url>
cd rightsizing-simulator

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker-compose up --build

# 4. Open the app
open http://localhost:5173
```

**Default Admin Credentials:** `admin` / `admin123`

---

## 🖥️ Local Development

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Start PostgreSQL separately, then:
alembic upgrade head          # Run migrations
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # Starts on http://localhost:5173
```

---

## 📁 Project Structure

```
rightsizing-simulator/
├── frontend/          # React + TypeScript (Vite)
│   └── src/
│       ├── api/       # API client functions
│       ├── components/# Reusable UI + chart components
│       ├── context/   # Auth context
│       ├── pages/     # Route-level page components
│       ├── store/     # Zustand state stores
│       ├── types/     # TypeScript interfaces
│       └── utils/     # Formatters, helpers
├── backend/           # FastAPI
│   └── app/
│       ├── api/v1/    # REST endpoints
│       ├── core/      # Config, security, DB
│       ├── models/    # SQLAlchemy ORM models
│       ├── schemas/   # Pydantic request/response schemas
│       └── services/  # Business logic layer
├── docs/              # Architecture docs
├── docker-compose.yml
└── .env.example
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user info |
| POST | `/api/v1/metrics/upload` | Upload CSV metrics file |
| GET | `/api/v1/metrics/` | List all metric datasets |
| POST | `/api/v1/simulator/run` | Run a rightsizing simulation |
| GET | `/api/v1/simulator/runs` | List all simulation runs |
| POST | `/api/v1/experiments/` | Create an A/B experiment |
| GET | `/api/v1/experiments/` | List all experiments |
| POST | `/api/v1/reports/generate` | Generate a report |
| GET | `/api/v1/reports/` | List all reports |

Full interactive docs: `http://localhost:8000/docs`

---

## 🧭 Navigation

| Page | Path | Description |
|------|------|-------------|
| Dashboard | `/` | KPI overview, recent activity, summary charts |
| Upload Data | `/upload` | CSV file upload + preview + history |
| Simulator | `/simulator` | Configure and run rightsizing simulations |
| Experiments | `/experiments` | Create and compare A/B scenarios |
| Reports | `/reports` | Generate and download analysis reports |
| Settings | `/settings` | User profile and app preferences |

---

## 📝 License

MIT
