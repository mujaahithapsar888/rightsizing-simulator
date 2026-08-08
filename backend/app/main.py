from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, event_recovery, experiments, feedback, metrics, predictor as model_predictor, reports, simulator
from app.core.config import settings
from app.core.database import engine, Base
from app.core.security import create_admin_user


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Startup / shutdown lifecycle."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await create_admin_user()

    yield

    await engine.dispose()


app = FastAPI(
    title="Performance-Safe Rightsizing Simulator",
    description=(
        "API for simulating cloud resource rightsizing decisions "
        "for media streaming platforms while preserving SLA performance."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{PREFIX}/auth", tags=["Authentication"])
app.include_router(metrics.router, prefix=f"{PREFIX}/metrics", tags=["Metrics"])
app.include_router(simulator.router, prefix=f"{PREFIX}/simulator", tags=["Simulator"])
app.include_router(model_predictor.router, prefix=f"{PREFIX}/models", tags=["Predictive Models"])
app.include_router(event_recovery.router, prefix=f"{PREFIX}/event-recovery", tags=["Event Recovery"])
app.include_router(experiments.router, prefix=f"{PREFIX}/experiments", tags=["Experiments"])
app.include_router(reports.router, prefix=f"{PREFIX}/reports", tags=["Reports"])
app.include_router(feedback.router, prefix=f"{PREFIX}/feedback", tags=["Stakeholder Feedback"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
