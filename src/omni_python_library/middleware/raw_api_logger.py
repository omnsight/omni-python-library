import logging
import time

from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("fastapi_json")


def safe_decode(headers : dict, key: str, default=b"MISSING"):
    # Headers in ASGI are lowercase bytes
    val = headers.get(key.lower().encode(), default)
    return val.decode("utf-8", errors="replace") if isinstance(val, bytes) else str(val)

def safe_scope_decode(scope: Scope, key: str):
    val = scope.get(key, b"")
    return val.decode("utf-8", errors="replace") if isinstance(val, bytes) else str(val)


class RawASGILoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.perf_counter()

        try:
            headers = dict(scope.get("headers", []))
            extra_fields = {
                "x-user-id": safe_decode(headers, "x-user-id"),
                "x-user-email": safe_decode(headers, "x-user-email"),
                "x-user-roles": safe_decode(headers, "x-user-roles"),
                "method": scope.get("method", "UNKNOWN"),
                "path": scope.get("path", "UNKNOWN"),
                "query_string": safe_scope_decode(scope, "query_string"),
            }
            await self.app(scope, receive, send)
        except HTTPException as e:
            process_time = (time.perf_counter() - start_time) * 1000
            extra_fields["process_time"] = f"{process_time:.2f}ms"
            logger.exception(f"{scope['method']} {scope['path']} -> {e.status_code}", extra=extra_fields)
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            extra_fields["process_time"] = f"{process_time:.2f}ms"
            logger.exception(f"{scope['method']} {scope['path']} -> 500", extra=extra_fields)
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        else:
            if scope["path"] != "/health":
                process_time = (time.perf_counter() - start_time) * 1000
                extra_fields["process_time"] = f"{process_time:.2f}ms"
                logger.info(f"{scope['method']} {scope['path']} -> 200", extra=extra_fields)
