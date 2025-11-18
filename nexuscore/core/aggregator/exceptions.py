"""
Exceptions for the AggreGator client.
"""

class AggregatorAPIError(Exception):
    """Base exception for AggreGator API errors."""
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"{self.status_code}: {self.message}"
        return self.message


class AggregatorConnectionError(AggregatorAPIError):
    """Raised when there is a connection error with the AggreGator service."""
    pass


class AggregatorAuthenticationError(AggregatorAPIError):
    """Raised when authentication with the AggreGator service fails."""
    pass


class AggregatorDataError(AggregatorAPIError):
    """Raised when there is an error with the data received from AggreGator."""
    pass


class AggregatorRateLimitError(AggregatorAPIError):
    """Raised when rate limits are exceeded for the AggreGator API."""
    pass
