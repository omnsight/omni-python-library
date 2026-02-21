from typing import Optional

from omni_python_library.utils.errors.base import OmniError


class InternalError(OmniError):
    """Raised when an internal error occurs"""

    def __init__(self, message: str = "Internal error", payload: Optional[dict] = None):
        super().__init__(message, status_code=500, payload=payload)
