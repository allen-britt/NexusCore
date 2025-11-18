"""
AI-powered data interpretation for non-technical users.
"""

from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from pydantic import BaseModel
import logging

from ..aggregator.models import DataChunk

logger = logging.getLogger(__name__)

class AIDataInterpreter:
    """Provides AI-powered data interpretation and assistance."""
    
    def __init__(self, llm_provider=None):
        """
        Initialize the AI interpreter.
        
        Args:
            llm_provider: Optional LLM provider for advanced interpretation
        """
        self.llm = llm_provider
    
    async def infer_schema(self, data: Union[DataChunk, List[Dict], pd.DataFrame]) -> Dict:
        """
        Infer the schema of the provided data.
        
        Args:
            data: Input data to analyze
            
        Returns:
            Dictionary with inferred schema information
        """
        if isinstance(data, DataChunk):
            df = pd.DataFrame(data.data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
            
        schema = {
            "fields": [],
            "stats": self._compute_basic_stats(df)
        }
        
        for col in df.columns:
            field_info = {
                "name": col,
                "type": str(df[col].dtype),
                "sample_values": df[col].dropna().head(5).tolist(),
                "null_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique())
            }
            
            # Add type-specific analysis
            if pd.api.types.is_numeric_dtype(df[col]):
                field_info.update(self._analyze_numeric(df[col]))
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                field_info.update(self._analyze_datetime(df[col]))
            elif pd.api.types.is_string_dtype(df[col]):
                field_info.update(self._analyze_string(df[col]))
                
            schema["fields"].append(field_info)
            
        return schema
    
    def suggest_transformations(self, field_info: Dict) -> List[Dict]:
        """
        Suggest possible transformations for a field.
        
        Args:
            field_info: Field information from infer_schema
            
        Returns:
            List of suggested transformations with descriptions
        """
        suggestions = []
        field_type = field_info["type"]
        
        if "int" in field_type or "float" in field_type:
            suggestions.extend([
                {"type": "normalize", "description": "Normalize to 0-1 range"},
                {"type": "bin", "description": "Group into bins/ranges"},
                {"type": "log", "description": "Apply logarithmic transformation"},
            ])
            
        if "datetime" in field_type:
            suggestions.extend([
                {"type": "extract_year", "description": "Extract year"},
                {"type": "extract_month", "description": "Extract month"},
                {"type": "extract_day", "description": "Extract day of month"},
            ])
            
        if "object" in field_type or "string" in field_type:
            suggestions.extend([
                {"type": "lowercase", "description": "Convert to lowercase"},
                {"type": "uppercase", "description": "Convert to uppercase"},
                {"type": "trim", "description": "Trim whitespace"},
            ])
            
        return suggestions
    
    async def explain_field(self, field_name: str, field_info: Dict) -> str:
        """
        Generate a natural language explanation of a field.
        
        Args:
            field_name: Name of the field
            field_info: Field information from infer_schema
            
        Returns:
            Natural language explanation of the field
        """
        if self.llm:
            # Use LLM for more sophisticated explanations if available
            prompt = self._create_explanation_prompt(field_name, field_info)
            return await self.llm.generate(prompt)
        else:
            # Fallback to simple rule-based explanation
            return self._simple_field_explanation(field_name, field_info)
    
    def _compute_basic_stats(self, df: pd.DataFrame) -> Dict:
        """Compute basic statistics for the dataset."""
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "missing_values": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        }
    
    def _analyze_numeric(self, series: pd.Series) -> Dict:
        """Analyze a numeric series."""
        stats = {
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
        }
        
        # Add distribution information
        try:
            stats["distribution"] = {
                "skew": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
            }
        except Exception as e:
            logger.debug(f"Could not compute distribution stats: {e}")
            
        return stats
    
    def _analyze_datetime(self, series: pd.Series) -> Dict:
        """Analyze a datetime series."""
        return {
            "min": str(series.min()),
            "max": str(series.max()),
            "time_span": str(series.max() - series.min()),
        }
    
    def _analyze_string(self, series: pd.Series) -> Dict:
        """Analyze a string series."""
        return {
            "avg_length": float(series.str.len().mean()),
            "unique_values": int(series.nunique()),
            "most_common": series.value_counts().head(3).to_dict(),
        }
    
    def _create_explanation_prompt(self, field_name: str, field_info: Dict) -> str:
        """Create a prompt for the LLM to explain a field."""
        return f"""
        Please explain the following data field in simple terms:
        
        Field Name: {field_name}
        Data Type: {field_info['type']}
        Sample Values: {field_info['sample_values'][:5]}
        Number of Unique Values: {field_info['unique_count']}
        Number of Missing Values: {field_info['null_count']}
        
        Based on this information, what does this field likely represent?
        What kind of analysis or transformations might be useful for this field?
        """
    
    def _simple_field_explanation(self, field_name: str, field_info: Dict) -> str:
        """Generate a simple explanation without LLM."""
        explanation = f"The field '{field_name}' contains {field_info['type']} data. "
        
        if field_info['unique_count'] == 1:
            explanation += "All values are identical. "
        elif field_info['unique_count'] < 10:
            explanation += f"It has {field_info['unique_count']} distinct values. "
        else:
            explanation += "It has many distinct values. "
            
        if field_info['null_count'] > 0:
            explanation += f"Note: {field_info['null_count']} values are missing. "
            
        if 'min' in field_info and 'max' in field_info:
            explanation += f"Values range from {field_info['min']} to {field_info['max']}. "
            
        return explanation
