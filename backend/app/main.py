import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import engine
from app.domain.state_machine import InvalidTransitionError
from app.logging_config import configure_logging
from app.middleware.metrics import PrometheusMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.repositories.complaints import ComplaintNotFoundError
from app.routes import complaints, health, meta, observability, readiness, stats

configure_logging(os.environ.get("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Uvicorn stops accepting new connections and drains in-flight requests
    # on SIGTERM before triggering this lifespan shutdown, so it's safe to
    # close the pool here. Kubernetes sends SIGTERM to every pod on a
    # rolling update; without this, in-flight requests get cut off and
    # Postgres connections leak on every single deploy.
    engine.dispose()


app = FastAPI(title="CivicPulse", lifespan=lifespan)

_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(part) for part in err["loc"] if part != "body"),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=400, content={"error": "validation_error", "fields": fields}
    )


@app.exception_handler(ComplaintNotFoundError)
async def handle_complaint_not_found(
    request: Request, exc: ComplaintNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404, content={"error": "not_found", "message": str(exc)}
    )


@app.exception_handler(InvalidTransitionError)
async def handle_invalid_transition(
    request: Request, exc: InvalidTransitionError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "invalid_transition",
            "from": exc.current.value,
            "to": exc.target.value,
            "message": f"Cannot transition from {exc.current.value} to {exc.target.value}",
        },
    )


app.include_router(health.router)
app.include_router(readiness.router)
app.include_router(complaints.router)
app.include_router(stats.router)
app.include_router(meta.router)
app.include_router(observability.router)
