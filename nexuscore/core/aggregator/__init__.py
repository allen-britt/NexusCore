"""
AggreGator API Client for NexusCore.

This module provides a client to interact with the AggreGator API, handling data retrieval,
transformation, and integration with the APEX system.
"""

__all__ = ["AggregatorClient", "AggregatorAPIError"]

from .client import AggregatorClient
from .exceptions import AggregatorAPIError
