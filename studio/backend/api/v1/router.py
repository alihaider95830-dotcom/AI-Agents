from fastapi import APIRouter

from backend.api.routes.auth import router as auth_router
from backend.api.v1.routes.health import router as health_router
from backend.api.v1.routes.jobs import router as jobs_router
from backend.api.v1.routes.reports import router as reports_router
from backend.api.v1.routes.stream import router as stream_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, tags=["auth"])
api_v1_router.include_router(reports_router, tags=["reports"])
api_v1_router.include_router(jobs_router, tags=["jobs"])
api_v1_router.include_router(stream_router, tags=["stream"])
