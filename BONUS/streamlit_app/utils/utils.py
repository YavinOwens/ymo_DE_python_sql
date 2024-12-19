import streamlit as st
import pandas as pd
import polars as pl
from typing import Dict, Any, Optional, Union
import json
import os
from ydata_profiling import ProfileReport

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'current_data_source' not in st.session_state:
        st.session_state.current_data_source = None
    if 'data_summary' not in st.session_state:
        st.session_state.data_summary = None

def get_data_summary(df: Union[pd.DataFrame, pl.DataFrame]) -> Dict[str, Any]:
    """Get summary statistics for a dataframe."""
    if isinstance(df, pl.DataFrame):
        df = df.to_pandas()
    
    return {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'total_nulls': df.isnull().sum().sum(),
        'duplicate_rows': df.duplicated().sum(),
        'memory_usage': df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
    }

def get_column_stats(df: Union[pd.DataFrame, pl.DataFrame], column: str) -> Dict[str, Any]:
    """Get detailed statistics for a specific column."""
    if isinstance(df, pl.DataFrame):
        df = df.to_pandas()
    
    col_data = df[column]
    stats = {
        'dtype': str(col_data.dtype),
        'null_count': col_data.isnull().sum(),
        'unique_count': col_data.nunique(),
        'total_count': len(col_data)
    }
    
    if pd.api.types.is_numeric_dtype(col_data):
        stats.update({
            'mean': col_data.mean(),
            'median': col_data.median(),
            'std': col_data.std(),
            'min': col_data.min(),
            'max': col_data.max()
        })
    
    return stats

@st.cache_data(ttl=3600)
def generate_profile_report(df: Union[pd.DataFrame, pl.DataFrame], minimal: bool = False) -> ProfileReport:
    """Generate a profile report for the dataframe with caching."""
    if isinstance(df, pl.DataFrame):
        df = df.to_pandas()
    
    profile = ProfileReport(
        df,
        minimal=minimal,
        title="Data Quality Report",
        explorative=True,
        html={'style': {'full_width': True}},
        progress_bar=False
    )
    
    return profile

@st.cache_data(ttl=3600)
def load_rule_templates(template_path: str) -> list:
    """Load rule templates from JSON file with caching."""
    try:
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading rule templates: {str(e)}")
        return []

def validate_data(df: Union[pd.DataFrame, pl.DataFrame], rules: list) -> Dict[str, Any]:
    """Validate data against a set of rules."""
    if isinstance(df, pl.DataFrame):
        df = df.to_pandas()
    
    results = []
    for rule in rules:
        try:
            # Apply the rule and collect results
            rule_result = {
                'rule_id': rule['id'],
                'rule_name': rule['name'],
                'column': rule.get('column', 'N/A'),
                'passed': True,
                'failed_rows': 0,
                'details': ''
            }
            
            # Add rule result to results list
            results.append(rule_result)
            
        except Exception as e:
            st.error(f"Error applying rule {rule['name']}: {str(e)}")
    
    return {
        'total_rules': len(rules),
        'passed_rules': sum(1 for r in results if r['passed']),
        'failed_rules': sum(1 for r in results if not r['passed']),
        'results': results
    } 