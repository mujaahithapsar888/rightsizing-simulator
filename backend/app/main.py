from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, event_recovery, experiments, feedback, metrics, predictor as model_predictor, reports, simulator, telemetry
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
app.include_router(telemetry.router, prefix=f"{PREFIX}/telemetry", tags=["Telemetry Stream"])


# ─── Global Error Boundaries & Exception Handlers ───────────────────────────
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("rightsizing.api")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path,
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "message": "Input validation error in request body or query parameters",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "An unexpected internal server error occurred. The incident has been logged.",
            "path": request.url.path,
        },
    )

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

