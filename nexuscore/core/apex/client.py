"""
APEX API Client for NexusCore.

This module provides a client to interact with the APEX API, handling authentication,
request/response serialization, and error handling.
"""

import json
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, HttpUrl, validator

from .exceptions import (
    ApexAPIError,
    ApexNotFoundError,
    ApexValidationError,
    ApexServerError,
)


class ApexClientConfig(BaseModel):
    """Configuration for the APEX client."""

    base_url: HttpUrl = "http://localhost:8000"
    api_key: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True


class ApexClient:
    """Client for interacting with the APEX API."""

    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the APEX client.
        
        Args:
            config: Optional configuration dictionary. If not provided, defaults are used.
        """
        self.config = ApexClientConfig(**(config or {}))
        self._client = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            self._headers["Authorization"] = f"Bearer {self.config.api_key}"
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=str(self.config.base_url),
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers=self._headers,
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """Make an HTTP request to the APEX API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., "/missions")
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            JSON response as a dictionary
            
        Raises:
            ApexAPIError: If the request fails
        """
        if self._client is None:
            await self.connect()
        
        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
            )
            
            # Handle error responses
            if response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = {"detail": response.text or "Unknown error"}
                
                if response.status_code == 404:
                    raise ApexNotFoundError(
                        message=error_data.get("detail", "Resource not found"),
                        status_code=404,
                        details=error_data,
                    )
                elif response.status_code == 422:
                    raise ApexValidationError(
                        message="Validation error",
                        status_code=422,
                        details=error_data,
                    )
                elif 500 <= response.status_code < 600:
                    raise ApexServerError(
                        message=error_data.get("detail", "Server error"),
                        status_code=response.status_code,
                        details=error_data,
                    )
                else:
                    raise ApexAPIError(
                        message=error_data.get("detail", "API request failed"),
                        status_code=response.status_code,
                        details=error_data,
                    )
            
            return response.json() if response.content else {}
            
        except httpx.RequestError as e:
            raise ApexAPIError(f"Request failed: {str(e)}") from e
    
    # Mission Operations
    
    async def create_mission(self, name: str, description: str = None) -> dict:
        """Create a new mission.
        
        Args:
            name: Mission name
            description: Optional mission description
            
        Returns:
            Created mission data
        """
        return await self._request(
            "POST",
            "/missions",
            json_data={"name": name, "description": description},
        )
    
    async def get_mission(self, mission_id: int) -> dict:
        """Get a mission by ID.
        
        Args:
            mission_id: Mission ID
            
        Returns:
            Mission data
        """
        return await self._request("GET", f"/missions/{mission_id}")
    
    async def list_missions(self) -> List[dict]:
        """List all missions.
        
        Returns:
            List of missions
        """
        return await self._request("GET", "/missions")
    
    async def delete_mission(self, mission_id: int) -> None:
        """Delete a mission.
        
        Args:
            mission_id: Mission ID to delete
        """
        await self._request("DELETE", f"/missions/{mission_id}")
    
    # Document Operations
    
    async def add_document(
        self,
        mission_id: int,
        content: str,
        title: str = None,
        include_in_analysis: bool = True,
    ) -> dict:
        """Add a document to a mission.
        
        Args:
            mission_id: Mission ID
            content: Document content
            title: Optional document title
            include_in_analysis: Whether to include in analysis
            
        Returns:
            Created document data
        """
        return await self._request(
            "POST",
            f"/missions/{mission_id}/documents",
            json_data={
                "title": title,
                "content": content,
                "include_in_analysis": include_in_analysis,
            },
        )
    
    async def list_documents(self, mission_id: int) -> List[dict]:
        """List all documents in a mission.
        
        Args:
            mission_id: Mission ID
            
        Returns:
            List of documents
        """
        return await self._request("GET", f"/missions/{mission_id}/documents")
    
    # Analysis Operations
    
    async def analyze_mission(
        self,
        mission_id: int,
        profile: str = "humint",
    ) -> dict:
        """Start analysis for a mission.
        
        Args:
            mission_id: Mission ID to analyze
            profile: Analysis profile (humint, sigint, osint)
            
        Returns:
            Analysis run data
        """
        return await self._request(
            "POST",
            f"/missions/{mission_id}/analyze",
            params={"profile": profile},
        )
    
    async def get_analysis_runs(self, mission_id: int) -> List[dict]:
        """Get analysis runs for a mission.
        
        Args:
            mission_id: Mission ID
            
        Returns:
            List of analysis runs
        """
        return await self._request("GET", f"/missions/{mission_id}/agent_runs")
    
    async def get_analysis_run(self, run_id: int) -> dict:
        """Get an analysis run by ID.
        
        Args:
            run_id: Analysis run ID
            
        Returns:
            Analysis run data
        """
        # Note: This endpoint might need to be implemented in the APEX API
        return await self._request("GET", f"/agent_runs/{run_id}")

    async def create_mission_dataset(
        self,
        mission_id: int,
        name: str,
        sources: List[Dict[str, Any]],
        profile: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Create a mission dataset within APEX."""

        payload: Dict[str, Any] = {
            "name": name,
            "sources": sources,
        }
        if profile is not None:
            payload["profile"] = profile

        return await self._request(
            "POST",
            f"/missions/{mission_id}/datasets",
            json_data=payload,
        )
