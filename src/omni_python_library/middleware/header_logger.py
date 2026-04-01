import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_logger")


class AuthHeaderLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Extract the headers you mapped in API Gateway
        user_id = request.headers.get("x-user-id")
        user_email = request.headers.get("x-user-email")
        user_roles = request.headers.get("x-user-roles")

        # 2. Log the findings
        # We use a structured format to make CloudWatch Logs easier to search
        logger.info(
            f"Inbound Request: path={request.url.path} | "
            f"x-user-id={user_id or 'MISSING'} | "
            f"x-user-email={user_email or 'MISSING'} | "
            f"x-user-roles={user_roles or 'MISSING'}"
        )

        # 3. Proceed with the request
        response = await call_next(request)
        return response
