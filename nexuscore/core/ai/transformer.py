# nexuscore/core/ai/transformer.py

from datetime import datetime
import re
import logging
from typing import Any, Dict, List, Optional, Union, Callable
import pandas as pd
import numpy as np
from pydantic import BaseModel, validator

# Set up logging
logger = logging.getLogger(__name__)

class TransformationError(Exception):
    """Custom exception for transformation errors."""
    pass

class TransformationResult(BaseModel):
    """Result of a data transformation."""
    success: bool
    transformed_data: Any
    message: str = ""
    metadata: Dict[str, Any] = {}

class SmartTransformer:
    """Provides intelligent data transformation capabilities."""
    
    def __init__(self, data_dictionary=None):
        """
        Initialize the smart transformer.
        
        Args:
            data_dictionary: Optional DataDictionary instance for field information
        """
        self.data_dictionary = data_dictionary
        self._custom_transforms: Dict[str, Callable] = {}
        
    def register_transform(self, name: str, transform_func: Callable) -> None:
        """
        Register a custom transformation function.
        
        Args:
            name: Name to identify the transformation
            transform_func: Function that takes a Series and returns a transformed Series
        """
        self._custom_transforms[name] = transform_func
    
    async def transform(
        self,
        data: Union[pd.DataFrame, List[Dict]],
        transformation_spec: Dict[str, Any]
    ) -> TransformationResult:
        """
        Apply transformations to data based on a specification.
        
        Args:
            data: Input data to transform
            transformation_spec: Dictionary specifying transformations
            
        Returns:
            TransformationResult with the transformed data
        """
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
            
        try:
            # Apply each transformation step
            for step in transformation_spec.get('steps', []):
                df = await self._apply_transformation_step(df, step)
                
            return TransformationResult(
                success=True,
                transformed_data=df.to_dict('records'),
                message="Transformation completed successfully",
                metadata={
                    "transformed_columns": list(df.columns),
                    "row_count": len(df)
                }
            )
        except Exception as e:
            logger.error(f"Transformation failed: {str(e)}", exc_info=True)
            return TransformationResult(
                success=False,
                transformed_data=data,
                message=f"Transformation failed: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def _apply_transformation_step(
        self,
        df: pd.DataFrame,
        step: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply a single transformation step to the dataframe."""
        step_type = step.get('type')
        column = step.get('column')
        
        # Validate required parameters
        if not step_type:
            raise TransformationError("Transformation type is required")
        if not column and step_type not in ['add_column', 'drop_duplicates']:
            raise TransformationError(f"Column is required for {step_type} transformation")
            
        try:
            # Handle built-in transformations
            if step_type == 'rename':
                return self._rename_column(df, column, step['new_name'])
                
            elif step_type == 'drop':
                return self._drop_column(df, column)
                
            elif step_type == 'fillna':
                return self._fill_na(df, column, step.get('value', 0))
                
            elif step_type == 'normalize':
                return self._normalize_column(df, column)
                
            elif step_type == 'log':
                return self._log_transform(df, column)
                
            elif step_type == 'lowercase':
                return self._to_lowercase(df, column)
                
            elif step_type == 'uppercase':
                return self._to_uppercase(df, column)
                
            elif step_type == 'trim':
                return self._trim_whitespace(df, column)
                
            elif step_type == 'extract_date_part':
                return self._extract_date_part(
                    df, column, 
                    part=step.get('part', 'year'),
                    output_column=step.get('output_column')
                )
                
            elif step_type == 'one_hot_encode':
                return self._one_hot_encode(
                    df, column,
                    prefix=step.get('prefix'),
                    drop_original=step.get('drop_original', True)
                )
                
            elif step_type == 'clean_text':
                return self._clean_text(
                    df, column,
                    remove_numbers=step.get('remove_numbers', False),
                    remove_special_chars=step.get('remove_special_chars', True)
                )
                
            elif step_type == 'custom' and 'transform_name' in step:
                return self._apply_custom_transform(
                    df, column, 
                    step['transform_name'],
                    **step.get('params', {})
                )
                
            elif step_type in self._custom_transforms:
                return self._apply_custom_transform(df, column, step_type, **step.get('params', {}))
                
            else:
                raise TransformationError(f"Unknown transformation type: {step_type}")
                
        except Exception as e:
            logger.error(f"Error applying {step_type} to {column}: {str(e)}")
            raise TransformationError(f"Failed to apply {step_type} to {column}: {str(e)}")
    
    # Individual transformation methods
    def _rename_column(self, df: pd.DataFrame, column: str, new_name: str) -> pd.DataFrame:
        """Rename a column in the dataframe."""
        return df.rename(columns={column: new_name})
        
    def _drop_column(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Drop a column from the dataframe."""
        return df.drop(columns=[column])
        
    def _fill_na(self, df: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
        """Fill NA values in a column."""
        df[column] = df[column].fillna(value)
        return df
        
    def _normalize_column(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Normalize numeric column to 0-1 range."""
        min_val = df[column].min()
        max_val = df[column].max()
        df[column] = (df[column] - min_val) / (max_val - min_val)
        return df
        
    def _log_transform(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Apply log transformation to a numeric column."""
        df[column] = np.log1p(df[column])
        return df
        
    def _to_lowercase(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert string column to lowercase."""
        df[column] = df[column].astype(str).str.lower()
        return df
        
    def _to_uppercase(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert string column to uppercase."""
        df[column] = df[column].astype(str).str.upper()
        return df
        
    def _trim_whitespace(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Trim whitespace from string column."""
        df[column] = df[column].astype(str).str.strip()
        return df
        
    def _extract_date_part(
        self, 
        df: pd.DataFrame, 
        column: str, 
        part: str = 'year',
        output_column: Optional[str] = None
    ) -> pd.DataFrame:
        """Extract part of a datetime column."""
        output_col = output_column or f"{column}_{part}"
        
        if part == 'year':
            df[output_col] = pd.to_datetime(df[column]).dt.year
        elif part == 'month':
            df[output_col] = pd.to_datetime(df[column]).dt.month
        elif part == 'day':
            df[output_col] = pd.to_datetime(df[column]).dt.day
        elif part == 'hour':
            df[output_col] = pd.to_datetime(df[column]).dt.hour
        elif part == 'minute':
            df[output_col] = pd.to_datetime(df[column]).dt.minute
        elif part == 'second':
            df[output_col] = pd.to_datetime(df[column]).dt.second
        elif part == 'dayofweek':
            df[output_col] = pd.to_datetime(df[column]).dt.dayofweek
        elif part == 'dayofyear':
            df[output_col] = pd.to_datetime(df[column]).dt.dayofyear
        elif part == 'weekofyear':
            df[output_col] = pd.to_datetime(df[column]).dt.isocalendar().week
        elif part == 'quarter':
            df[output_col] = pd.to_datetime(df[column]).dt.quarter
        else:
            raise TransformationError(f"Unsupported date part: {part}")
            
        return df
        
    def _one_hot_encode(
        self,
        df: pd.DataFrame,
        column: str,
        prefix: Optional[str] = None,
        drop_original: bool = True
    ) -> pd.DataFrame:
        """One-hot encode a categorical column."""
        prefix = prefix or f"{column}_"
        dummies = pd.get_dummies(df[column], prefix=prefix)
        df = pd.concat([df, dummies], axis=1)
        
        if drop_original:
            df = df.drop(columns=[column])
            
        return df
        
    def _clean_text(
        self,
        df: pd.DataFrame,
        column: str,
        remove_numbers: bool = False,
        remove_special_chars: bool = True
    ) -> pd.DataFrame:
        """Clean text in a column."""
        text_series = df[column].astype(str)
        
        # Convert to lowercase
        text_series = text_series.str.lower()
        
        # Remove numbers if requested
        if remove_numbers:
            text_series = text_series.str.replace(r'\d+', '', regex=True)
            
        # Remove special characters if requested
        if remove_special_chars:
            text_series = text_series.str.replace(r'[^\w\s]', '', regex=True)
            
        # Replace multiple whitespace with single space
        text_series = text_series.str.replace(r'\s+', ' ', regex=True).str.strip()
        
        df[column] = text_series
        return df
        
    def _apply_custom_transform(
        self,
        df: pd.DataFrame,
        column: str,
        transform_name: str,
        **params
    ) -> pd.DataFrame:
        """Apply a custom transformation function."""
        if transform_name not in self._custom_transforms:
            raise TransformationError(f"Custom transform not found: {transform_name}")
            
        transform_func = self._custom_transforms[transform_name]
        df[column] = transform_func(df[column], **params)
        return df