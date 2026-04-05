import logging
import time

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_logger")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = request.headers.get("x-user-id", "MISSING")
        user_email = request.headers.get("x-user-email", "MISSING")
        user_roles = request.headers.get("x-user-roles", "MISSING")

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except HTTPException as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"{request.method} {request.url.path} -> {e.status_code}",
                extra={
                    "x-user-id": user_id,
                    "x-user-email": user_email,
                    "x-user-roles": user_roles,
                    "process_time": f"{process_time:.2f}ms",
                },
            )
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"{request.method} {request.url.path} -> {500}",
                extra={
                    "x-user-id": user_id,
                    "x-user-email": user_email,
                    "x-user-roles": user_roles,
                    "process_time": f"{process_time:.2f}ms",
                },
            )
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})

        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code}",
            extra={
                "x-user-id": user_id,
                "x-user-email": user_email,
                "x-user-roles": user_roles,
                "process_time": f"{process_time:.2f}ms",
            },
        )
        return response
