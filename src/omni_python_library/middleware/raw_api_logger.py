import json
import logging
import time

from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("fastapi_json")


class RawASGILoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.perf_counter()

        headers = dict(scope.get("headers", []))
        extra_fields = {
            "x-user-id": headers.get(b"x-user-id", b"MISSING").decode(),
            "x-user-email": headers.get(b"x-user-email", b"MISSING").decode(),
            "x-user-roles": headers.get(b"x-user-roles", b"MISSING").decode(),
            "method": scope["method"],
            "path": scope["path"],
            "query_string": scope["query_string"].decode(),
        }

        try:
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
