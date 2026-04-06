import logging
import time

from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("fastapi_json")


def safe_decode(headers: dict, key: str, default=b"MISSING"):
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
        extra_fields = {}

        try:
            headers = dict(scope.get("headers", []))
            extra_fields["x-user-id"] = safe_decode(headers, "x-user-id")
            extra_fields["x-user-email"] = safe_decode(headers, "x-user-email")
            extra_fields["x-user-roles"] = safe_decode(headers, "x-user-roles")
            extra_fields["method"] = scope.get("method", "UNKNOWN")
            extra_fields["path"] = scope.get("path", "UNKNOWN")
            extra_fields["host"] = safe_scope_decode(scope, "host")
            await self.app(scope, receive, send)
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            extra_fields["process_time"] = f"{process_time:.2f}ms"
            logger.exception(
                f"{scope.get('method', 'UNKNOWN')} {scope.get('path', 'UNKNOWN')} -> 500", extra=extra_fields
            )
            raise e
        else:
            if scope["path"] != "/health":
                process_time = (time.perf_counter() - start_time) * 1000
                extra_fields["process_time"] = f"{process_time:.2f}ms"
                logger.info(
                    f"{scope.get('method', 'UNKNOWN')} {scope.get('path', 'UNKNOWN')} -> 200", extra=extra_fields
                )
