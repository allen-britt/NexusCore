"""
Data models for the AggreGator client.

These models define the structure of data that can be retrieved from various sources
and transformed for use with the APEX system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, validator


class DataSourceType(str, Enum):
    """Types of data sources supported by AggreGator."""
    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"
    WEBHOOK = "webhook"


class FileFormat(str, Enum):
    """Supported file formats for data import/export."""
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    PARQUET = "parquet"
    EXCEL = "excel"
    TEXT = "text"


class DataSourceConfig(BaseModel):
    """Configuration for a data source in AggreGator."""
    
    name: str = Field(..., description="Unique name for the data source")
    type: DataSourceType = Field(..., description="Type of the data source")
    description: Optional[str] = Field(None, description="Description of the data source")
    
    # Connection details (varies by source type)
    connection: Dict[str, Any] = Field(
        default_factory=dict,
        description="Connection parameters specific to the data source type"
    )
    
    # Data retrieval parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for data retrieval (e.g., query, filters)"
    )
    
    # Scheduling and refresh
    refresh_interval: Optional[int] = Field(
        None,
        description="Refresh interval in seconds, None for manual refresh"
    )
    last_refreshed: Optional[datetime] = Field(
        None,
        description="Timestamp of the last successful data refresh"
    )
    
    # Data format and schema
    format: Optional[FileFormat] = Field(
        None,
        description="Format of the data (for file-based sources)"
    )
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="Schema definition for the data (optional)"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DataChunk(BaseModel):
    """A chunk of data retrieved from a data source."""
    
    source_name: str = Field(..., description="Name of the data source")
    data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="The actual data records"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about this data chunk"
    )
    
    @validator('data')
    def validate_data_not_empty(cls, v):
        """Ensure data is not empty."""
        if not v:
            raise ValueError("Data chunk cannot be empty")
        return v


class DataSourceStatus(str, Enum):
    """Status of a data source."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    REFRESHING = "refreshing"


class DataSourceHealth(BaseModel):
    """Health and status information for a data source."""
    
    status: DataSourceStatus = Field(..., description="Current status of the data source")
    last_success: Optional[datetime] = Field(
        None,
        description="Timestamp of the last successful data retrieval"
    )
    last_error: Optional[str] = Field(
        None,
        description="Last error message, if any"
    )
    error_count: int = Field(
        0,
        description="Number of consecutive errors"
    )
    record_count: Optional[int] = Field(
        None,
        description="Number of records in the last successful retrieval"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
