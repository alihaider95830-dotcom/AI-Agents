from fastapi import APIRouter, Depends

from backend.api.deps import rate_limit_global
from backend.api.routes.auth import router as auth_router
from backend.api.v1.routes.admin import router as admin_router
from backend.api.v1.routes.billing import router as billing_router
from backend.api.v1.routes.billing_stripe import router as billing_stripe_router
from backend.api.v1.routes.export import router as export_router
from backend.api.v1.routes.health import router as health_router
from backend.api.v1.routes.jobs import router as jobs_router
from backend.api.v1.routes.knowledge import router as knowledge_router
from backend.api.v1.routes.reports import router as reports_router
from backend.api.v1.routes.stream import router as stream_router

api_v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(rate_limit_global)],
)
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, tags=["auth"])
api_v1_router.include_router(export_router, tags=["reports"])
api_v1_router.include_router(reports_router, tags=["reports"])
api_v1_router.include_router(jobs_router, tags=["jobs"])
api_v1_router.include_router(billing_router, tags=["billing"])
api_v1_router.include_router(billing_stripe_router, tags=["billing"])
api_v1_router.include_router(admin_router, tags=["admin"])
api_v1_router.include_router(knowledge_router, tags=["knowledge"])
api_v1_router.include_router(stream_router, tags=["stream"])
