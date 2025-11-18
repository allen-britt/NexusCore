"""AggreGator API Client for NexusCore.

This module provides a client to interact with the AggreGator service,
handling data retrieval, transformation, and integration with the APEX system.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiofiles
import aiohttp
import pandas as pd
from pydantic import BaseModel, HttpUrl, ValidationError, validator

from .exceptions import (
    AggregatorAPIError,
    AggregatorAuthenticationError,
    AggregatorConnectionError,
    AggregatorDataError,
    AggregatorRateLimitError,
)
from .models import (
    DataChunk,
    DataSourceConfig,
    DataSourceHealth,
    DataSourceStatus,
    DataSourceType,
    FileFormat,
)

# Configure logging
logger = logging.getLogger(__name__)


class AggregatorClient:
    """Client for interacting with the AggreGator service."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """Initialize the AggreGator client.

        Args:
            base_url: Base URL of the AggreGator API
            api_key: API key for authentication (if required)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            session: Optional aiohttp ClientSession to use
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session = session
        self._session_owner = session is None
        self._data_sources: Dict[str, DataSourceConfig] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self):
        """Initialize the HTTP client session if not already initialized."""
        if self._session is None or self._session.closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                raise_for_status=True,
            )
            self._session_owner = True

    async def close(self):
        """Close the HTTP client session if we own it."""
        if self._session_owner and self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_on: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AggreGator API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., "/api/v1/sources")
            params: Query parameters
            json_data: JSON-serializable request body
            data: Raw request body
            headers: Additional headers
            retry_on: List of status codes to retry on

        Returns:
            JSON response as a dictionary

        Raises:
            AggregatorAPIError: If the request fails after all retries
        """
        if retry_on is None:
            retry_on = [429, 500, 502, 503, 504]

        attempt = 0
        last_exception = None

        while attempt <= self.max_retries:
            try:
                async with self._session.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=headers,
                ) as response:
                    if response.status < 400:
                        if response.status == 204:  # No Content
                            return {}
                        return await response.json()

                    # Handle specific error statuses
                    if response.status == 401:
                        raise AggregatorAuthenticationError(
                            "Authentication failed. Check your API key.",
                            status_code=401,
                        )
                    elif response.status == 403:
                        raise AggregatorAuthenticationError(
                            "Permission denied. Check your API key and permissions.",
                            status_code=403,
                        )
                    elif response.status == 404:
                        raise AggregatorAPIError(
                            f"Resource not found: {endpoint}",
                            status_code=404,
                        )
                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                        raise AggregatorRateLimitError(
                            "Rate limit exceeded",
                            status_code=429,
                            details={"retry_after": retry_after},
                        )
                    elif response.status >= 500:
                        error_data = await self._parse_error_response(response)
                        raise AggregatorAPIError(
                            f"Server error: {error_data.get('detail', 'Unknown error')}",
                            status_code=response.status,
                            details=error_data,
                        )
                    else:
                        error_data = await self._parse_error_response(response)
                        raise AggregatorAPIError(
                            f"API request failed: {error_data.get('detail', 'Unknown error')}",
                            status_code=response.status,
                            details=error_data,
                        )

            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                
                # Don't retry on client errors (4xx) unless explicitly specified
                if hasattr(e, 'status') and 400 <= getattr(e, 'status') < 500 and \
                   getattr(e, 'status') not in retry_on:
                    raise AggregatorAPIError(
                        f"Client error: {str(e)}",
                        status_code=getattr(e, 'status', 400),
                    ) from e
                
                # Check if we should retry
                if attempt >= self.max_retries:
                    if isinstance(e, aiohttp.ClientConnectionError):
                        raise AggregatorConnectionError(
                            f"Failed to connect to {self.base_url}",
                            status_code=None,
                        ) from e
                    raise AggregatorAPIError(
                        f"Request failed after {self.max_retries} attempts: {str(e)}",
                        status_code=getattr(e, 'status', 500),
                    ) from e
                
                # Exponential backoff with jitter
                delay = min(self.retry_delay * (2 ** attempt), 30)  # Cap at 30 seconds
                await asyncio.sleep(delay)
                attempt += 1

        # This should never be reached due to the raise above, but just in case
        raise AggregatorAPIError(
            f"Request failed after {self.max_retries + 1} attempts",
            status_code=getattr(last_exception, 'status', 500) if last_exception else 500,
        )

    async def _parse_error_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Parse error response from the API.
        
        Args:
            response: The aiohttp response object
            
        Returns:
            Parsed error data as a dictionary
        """
        try:
            return await response.json()
        except (ValueError, aiohttp.ContentTypeError):
            return {"detail": await response.text() or "Unknown error"}

    # Data Source Management

    async def list_data_sources(self) -> List[DataSourceConfig]:
        """List all configured data sources.
        
        Returns:
            List of data source configurations
        """
        response = await self._request("GET", "/api/v1/sources")
        return [DataSourceConfig(**source) for source in response.get("sources", [])]

    async def get_data_source(self, name: str) -> DataSourceConfig:
        """Get configuration for a specific data source.
        
        Args:
            name: Name of the data source
            
        Returns:
            Data source configuration
            
        Raises:
            AggregatorAPIError: If the data source is not found
        """
        response = await self._request("GET", f"/api/v1/sources/{name}")
        return DataSourceConfig(**response)

    async def create_data_source(self, config: DataSourceConfig) -> DataSourceConfig:
        """Create a new data source.
        
        Args:
            config: Data source configuration
            
        Returns:
            Created data source configuration
        """
        response = await self._request(
            "POST",
            "/api/v1/sources",
            json_data=config.dict(exclude_unset=True),
        )
        return DataSourceConfig(**response)

    async def update_data_source(self, name: str, config: DataSourceConfig) -> DataSourceConfig:
        """Update an existing data source.
        
        Args:
            name: Name of the data source to update
            config: Updated data source configuration
            
        Returns:
            Updated data source configuration
        """
        response = await self._request(
            "PUT",
            f"/api/v1/sources/{name}",
            json_data=config.dict(exclude_unset=True),
        )
        return DataSourceConfig(**response)

    async def delete_data_source(self, name: str) -> None:
        """Delete a data source.
        
        Args:
            name: Name of the data source to delete
        """
        await self._request("DELETE", f"/api/v1/sources/{name}")

    async def get_data_source_health(self, name: str) -> DataSourceHealth:
        """Get health status for a data source.
        
        Args:
            name: Name of the data source
            
        Returns:
            Data source health information
        """
        response = await self._request("GET", f"/api/v1/sources/{name}/health")
        return DataSourceHealth(**response)

    # Data Retrieval

    async def fetch_data(
        self,
        source_name: str,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        format: FileFormat = FileFormat.JSON,
    ) -> DataChunk:
        """Fetch data from a data source.
        
        Args:
            source_name: Name of the data source
            limit: Maximum number of records to return
            offset: Number of records to skip
            filters: Filter criteria
            sort: Sort criteria
            format: Output format
            
        Returns:
            DataChunk containing the retrieved data
        """
        params: Dict[str, Any] = {"offset": offset, "format": format.value}
        if limit is not None:
            params["limit"] = limit
        if filters:
            params["filter"] = json.dumps(filters)
        if sort:
            params["sort"] = json.dumps(sort)
            
        response = await self._request(
            "GET",
            f"/api/v1/sources/{source_name}/data",
            params=params,
        )
        
        return DataChunk(
            source_name=source_name,
            data=response.get("data", []),
            metadata=response.get("metadata", {}),
        )

    async def stream_data(
        self,
        source_name: str,
        chunk_size: int = 1000,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[DataChunk]:
        """Stream data from a data source in chunks.
        
        Args:
            source_name: Name of the data source
            chunk_size: Number of records per chunk
            filters: Filter criteria
            sort: Sort criteria
            
        Yields:
            DataChunk objects containing chunks of data
        """
        offset = 0
        total = None
        
        while True:
            chunk = await self.fetch_data(
                source_name=source_name,
                limit=chunk_size,
                offset=offset,
                filters=filters,
                sort=sort,
            )
            
            if not chunk.data:
                break
                
            yield chunk
            
            if len(chunk.data) < chunk_size:
                break
                
            offset += len(chunk.data)
            
            # Update total from metadata if available
            if "total" in chunk.metadata:
                total = int(chunk.metadata["total"])
                if offset >= total:
                    break

    async def profile_source(self, source_key: str) -> Dict[str, Any]:
        """Request AggreGator to ingest/profile a registered source and return its profile."""

        await self.connect()
        return await self._request(
            "POST",
            f"/api/v1/sources/{source_key}/profile",
        )

    async def upload_file(
        self,
        file_path: Union[str, Path],
        source_name: str,
        format: Optional[FileFormat] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Upload a file to be processed as a data source.
        
        Args:
            file_path: Path to the file to upload
            source_name: Name for the data source
            format: File format (auto-detected if not specified)
            **kwargs: Additional parameters for the data source
            
        Returns:
            Upload result
        """

        await self.connect()

        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if format is None:
            ext = file_path.suffix.lower().lstrip(".")
            try:
                format = FileFormat(ext)
            except ValueError as exc:
                raise ValueError(
                    "Could not determine file format from extension. "
                    "Please specify format explicitly. Available formats: "
                    + ", ".join(f.value for f in FileFormat)
                ) from exc

        data = aiohttp.FormData()
        file_bytes = file_path.read_bytes()
        data.add_field(
            "file",
            file_bytes,
            filename=file_path.name,
            content_type=self._get_content_type(format),
        )
        data.add_field("name", source_name)
        data.add_field("format", format.value)
        for key, value in kwargs.items():
            if value is not None:
                data.add_field(key, str(value))

        response = await self._request(
            "POST",
            "/api/v1/upload",
            data=data,
            headers={"Content-Type": None},
        )

        return response
    
    def _get_content_type(self, format: FileFormat) -> str:
        """Get content type for a file format."""
        content_types = {
            FileFormat.CSV: "text/csv",
            FileFormat.JSON: "application/json",
            FileFormat.XML: "application/xml",
            FileFormat.PARQUET: "application/octet-stream",
            FileFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FileFormat.TEXT: "text/plain",
        }
        return content_types.get(format, "application/octet-stream")

    # Data Transformation
    
    async def transform_data(
        self,
        source_name: str,
        transform_spec: Dict[str, Any],
        output_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply a transformation to data from a source.
        
        Args:
            source_name: Name of the source data
            transform_spec: Transformation specification
            output_name: Optional name for the transformed output
            
        Returns:
            Transformation result
        """
        payload = {
            "source": source_name,
            "transform": transform_spec,
        }
        if output_name:
            payload["output_name"] = output_name
            
        return await self._request(
            "POST",
            "/api/v1/transform",
            json_data=payload,
        )

    # Utility Methods
    
    async def test_connection(self) -> bool:
        """Test the connection to the AggreGator API.
        
        Returns:
            True if the connection is successful
            
        Raises:
            AggregatorConnectionError: If the connection fails
        """
        try:
            await self._request("GET", "/api/v1/health")
            return True
        except AggregatorAPIError as e:
            if e.status_code == 404:
                # If we get a 404, the API is responding but the endpoint doesn't exist
                # This might be fine if we're talking to a different version of the API
                return True
            raise
        except Exception as e:
            raise AggregatorConnectionError(
                f"Failed to connect to AggreGator API: {str(e)}"
            ) from e

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information about the AggreGator service.
        
        Returns:
            System information
        """
        return await self._request("GET", "/api/v1/system/info")
