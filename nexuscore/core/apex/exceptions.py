"""
Exceptions for the APEX client.
"""

class ApexAPIError(Exception):
    """Base exception for APEX API errors."""
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"{self.status_code}: {self.message}"
        return self.message


class ApexNotFoundError(ApexAPIError):
    """Raised when a resource is not found."""
    pass


class ApexValidationError(ApexAPIError):
    """Raised when there is a validation error."""
    pass


class ApexServerError(ApexAPIError):
    """Raised when there is a server-side error."""
    pass
