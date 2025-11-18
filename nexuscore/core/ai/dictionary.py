"""
Data dictionary implementation for NexusCore.

Provides a user-friendly way to document and understand data fields
across different data sources.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class FieldDefinition(BaseModel):
    """Definition of a single field in a data dictionary."""
    
    name: str = Field(..., description="Name of the field")
    display_name: str = Field(..., description="User-friendly display name")
    description: str = Field("", description="Description of what the field represents")
    data_type: str = Field(..., description="Data type (string, number, date, etc.)")
    example: Optional[str] = Field(None, description="Example value")
    required: bool = Field(False, description="Whether the field is required")
    sensitive: bool = Field(False, description="Whether the field contains sensitive data")
    categories: List[str] = Field(default_factory=list, description="Categories/tags for the field")

class DataDictionary:
    """Manages data dictionaries for different data sources."""
    
    def __init__(self):
        self.dictionaries: Dict[str, Dict[str, FieldDefinition]] = {}
        
    def add_dictionary(self, source_name: str, fields: List[FieldDefinition]) -> None:
        """Add or update a data dictionary for a source."""
        self.dictionaries[source_name] = {f.name: f for f in fields}
        
    def get_field_info(self, source_name: str, field_name: str) -> Optional[FieldDefinition]:
        """Get information about a specific field."""
        return self.dictionaries.get(source_name, {}).get(field_name)
    
    def suggest_field_mappings(self, source_fields: List[str], target_fields: List[str]) -> Dict[str, str]:
        """Suggest mappings between source and target fields using semantic similarity."""
        # Implementation would use NLP to find the best matches
        # between source and target field names/descriptions
        pass
    
    def generate_documentation(self, source_name: str) -> str:
        """Generate user-friendly documentation for a data source."""
        if source_name not in self.dictionaries:
            return f"No data dictionary found for {source_name}"
            
        fields = self.dictionaries[source_name].values()
        doc = f"# {source_name} Data Dictionary\n\n"
        doc += f"Last updated: {datetime.utcnow().isoformat()}\n\n"
        
        for field in sorted(fields, key=lambda f: f.name):
            doc += f"## {field.display_name} (`{field.name}`)\n"
            doc += f"- **Type**: {field.data_type}\n"
            doc += f"- **Required**: {'Yes' if field.required else 'No'}\n"
            if field.description:
                doc += f"- **Description**: {field.description}\n"
            if field.example is not None:
                doc += f"- **Example**: `{field.example}`\n"
                
            if field.categories:
                doc += f"- **Categories**: {', '.join(field.categories)}\n"
                
            doc += "\n"
            
        return doc
