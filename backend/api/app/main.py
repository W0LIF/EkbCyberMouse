import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.app.routers import demo, reference, plan, events, mobile
from api.app.repositories.db import AsyncSessionLocal
from api.app.models import Health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS order_facts (
                order_id VARCHAR(20) PRIMARY KEY,
                work_type_code VARCHAR(50) NOT NULL,
                technology VARCHAR(20) NOT NULL,
                actual_duration_min INT NOT NULL CHECK (actual_duration_min > 0),
                occurred_at TIMESTAMPTZ NOT NULL
            )
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_order_facts_type_technology
            ON order_facts(work_type_code, technology)
        """))
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS mobile_visit_actions (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                staff_id VARCHAR(10) NOT NULL,
                order_id VARCHAR(20) NOT NULL,
                action VARCHAR(20) NOT NULL
                    CHECK (action IN ('CALL_CUSTOMER', 'ARRIVED', 'COMPLETED')),
                occurred_at TIMESTAMPTZ NOT NULL,
                UNIQUE (date, staff_id, order_id, action)
            )
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_mobile_visit_actions_route
            ON mobile_visit_actions(date, staff_id)
        """))
        await session.commit()
    if os.getenv("SEED_DEMO_DATA", "").lower() == "true":
        from api.app.services.demo_seed import seed_demo_data_if_empty

        await seed_demo_data_if_empty()
    yield


app = FastAPI(title="RTK Dispatch API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reference.router, prefix="/api/v1")
app.include_router(plan.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(mobile.router, prefix="/api/v1")


def _error(code: str, message: str, details: list[dict] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error("UNPROCESSABLE", "Некорректные данные запроса", details),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        content = detail
    else:
        code = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE",
        }.get(exc.status_code, "HTTP_ERROR")
        content = _error(code, str(detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception):
    logger.exception("Unhandled API error for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error("INTERNAL", "Внутренняя ошибка сервера"),
    )


@app.get("/api/v1/health", response_model=Health)
async def health_check():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok", "team": "EkbCyberMouse", "version": "1.0.0"}