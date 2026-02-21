from typing import Optional

from omni_python_library.utils.errors.base import OmniError


class NotFoundError(OmniError):
    """Raised when a resource is not found"""

    def __init__(self, message: str = "Resource not found", payload: Optional[dict] = None):
        super().__init__(message, status_code=404, payload=payload)
