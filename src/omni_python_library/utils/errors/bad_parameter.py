from typing import Optional

from omni_python_library.utils.errors.base import OmniError


class BadParameterError(OmniError):
    """Raised when a parameter is invalid"""

    def __init__(self, message: str = "Bad parameter", payload: Optional[dict] = None):
        super().__init__(message, status_code=400, payload=payload)
