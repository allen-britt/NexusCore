"""
APEX API Client for NexusCore.

This module provides a client to interact with the APEX API, handling authentication,
request/response serialization, and error handling.
"""

__all__ = ["ApexClient", "ApexAPIError"]

from .client import ApexClient
from .exceptions import ApexAPIError
