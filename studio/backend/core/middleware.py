import asyncio

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if "/stream/" in request.url.path:
            return await call_next(request)

        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=settings.request_timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning("Request timed out: %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=504,
                content={"error": "Request timed out", "code": 504},
            )
