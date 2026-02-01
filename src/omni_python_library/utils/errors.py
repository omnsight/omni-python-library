from typing import Optional


class OmniError(Exception):
    """Base class for all Omni exceptions"""

    def __init__(self, message: str, status_code: int = 500, payload: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


class NotFoundError(OmniError):
    """Raised when a resource is not found"""

    def __init__(self, message: str = "Resource not found", payload: Optional[dict] = None):
        super().__init__(message, status_code=404, payload=payload)


class BadParameterError(OmniError):
    """Raised when a parameter is invalid"""

    def __init__(self, message: str = "Bad parameter", payload: Optional[dict] = None):
        super().__init__(message, status_code=400, payload=payload)


class InternalError(OmniError):
    """Raised when an internal error occurs"""

    def __init__(self, message: str = "Internal error", payload: Optional[dict] = None):
        super().__init__(message, status_code=500, payload=payload)


class PermissionDeniedError(OmniError):
    """Raised when permission is denied"""

    def __init__(self, message: str = "Permission denied", payload: Optional[dict] = None):
        super().__init__(message, status_code=403, payload=payload)
