from typing import Optional

from omni_python_library.utils.errors.base import OmniError


class PermissionDeniedError(OmniError):
    """Raised when permission is denied"""

    def __init__(self, message: str = "Permission denied", payload: Optional[dict] = None):
        super().__init__(message, status_code=403, payload=payload)
