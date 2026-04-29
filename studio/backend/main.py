import asyncio
import uuid
from contextlib import asynccontextmanager, suppress
from time import perf_counter

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.api.deps import get_db
from backend.api.v1.routes.health import database_health_check, health_check
from backend.api.v1.router import api_v1_router
from backend.core.config import settings
from backend.core.exceptions import StudioException
from backend.core.logging import get_logger, request_id_context
from backend.core.middleware import TimeoutMiddleware
from backend.core.monitoring import register_metrics_route
from backend.core.redis_client import close_pools
from backend.db.session import AsyncSessionLocal
from backend.tools.warmup import warm_vector_stores

logger = get_logger("studio.api")
allowed_origins = [str(settings.frontend_url)] if settings.frontend_url else []


async def _warm_vector_stores_background() -> None:
    try:
        async with AsyncSessionLocal() as session:
            await warm_vector_stores(session)
    except Exception as exc:
        logger.warning("Vector store warmup failed: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Studio API started")
    warmup_task = asyncio.create_task(_warm_vector_stores_background())
    yield
    if not warmup_task.done():
        warmup_task.cancel()
        with suppress(asyncio.CancelledError):
            await warmup_task
    logger.info("Studio API stopped")
    await close_pools()


is_production = settings.environment.lower() == "production"

app = FastAPI(
    title="Studio API",
    version="1.0.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(TimeoutMiddleware)

app.include_router(api_v1_router)
register_metrics_route(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    token = request_id_context.set(request_id)
    started_at = perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.info(
            (
                "request completed | method=%s path=%s "
                "status_code=%s duration_ms=%s"
            ),
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    finally:
        request_id_context.reset(token)


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
