from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.api.v1.routes.health import database_health_check, health_check
from backend.api.v1.router import api_v1_router
from backend.core.config import settings
from backend.core.exceptions import StudioException
from backend.core.logging import get_logger

logger = get_logger("studio.api")
allowed_origins = [str(settings.frontend_url)] if settings.frontend_url else []


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Studio API started")
    yield
    logger.info("Studio API stopped")


app = FastAPI(title="Studio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info(
        "request completed | method=%s path=%s status_code=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(StudioException)
async def handle_studio_exception(_: Request, exc: StudioException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed", "detail": exc.errors()},
    )


@app.get("/health")
async def root_health_check() -> dict[str, str]:
    return await health_check()


@app.get("/health/db")
async def root_database_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await database_health_check(db)
