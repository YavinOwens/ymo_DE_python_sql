import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataQualityRules:
    """Collection of data quality rules similar to ydata-quality and Great Expectations"""
    
    @staticmethod
    def expect_column_values_to_not_be_null(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Expect column values to not be null"""
        null_count = df[column].isnull().sum()
        success = null_count == 0
        return {
            'success': success,
            'result': {
                'element_count': len(df),
                'null_count': null_count,
                'null_percent': (null_count / len(df)) * 100 if len(df) > 0 else 0
            }
        }
    
    @staticmethod
    def expect_column_values_to_be_unique(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Expect column values to be unique"""
        duplicate_count = len(df) - df[column].nunique()
        success = duplicate_count == 0
        return {
            'success': success,
            'result': {
                'element_count': len(df),
                'duplicate_count': duplicate_count,
                'unique_count': df[column].nunique(),
                'duplicate_percent': (duplicate_count / len(df)) * 100 if len(df) > 0 else 0
            }
        }
    
    @staticmethod
    def expect_column_values_to_be_in_range(
        df: pd.DataFrame, 
        column: str, 
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """Expect column values to be within a specified range"""
        if not pd.api.types.is_numeric_dtype(df[column]):
            return {
                'success': False,
                'result': {'error': 'Column is not numeric'}
            }
            
        series = df[column].dropna()
        if min_value is not None and max_value is not None:
            out_of_range = ~series.between(min_value, max_value)
        elif min_value is not None:
            out_of_range = series < min_value
        elif max_value is not None:
            out_of_range = series > max_value
        else:
            return {
                'success': True,
                'result': {'error': 'No range specified'}
            }
            
        violation_count = out_of_range.sum()
        return {
            'success': violation_count == 0,
            'result': {
                'element_count': len(series),
                'violation_count': violation_count,
                'violation_percent': (violation_count / len(series)) * 100 if len(series) > 0 else 0,
                'min_value': series.min(),
                'max_value': series.max()
            }
        }
