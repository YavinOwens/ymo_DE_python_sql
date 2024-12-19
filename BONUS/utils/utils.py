import streamlit as st
import pandas as pd
import polars as pl
from typing import Union, Dict, Any, Optional
import json
import os
from config import DATA_DIR

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_data_summary(df: Union[pd.DataFrame, pl.DataFrame]) -> Dict[str, Any]:
    """Get summary statistics for a dataframe with caching."""
    if isinstance(df, pl.DataFrame):
        df = df.to_pandas()
    
    return {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'total_nulls': df.isnull().sum().sum(),
        'duplicate_rows': df.duplicated().sum(),
        'memory_usage': df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
    }

@st.cache_data(ttl=3600)
def load_rule_templates() -> list:
    """Load rule templates from JSON file with caching."""
    try:
        template_path = os.path.join(DATA_DIR, 'rule_templates.json')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading rule templates: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_column_stats(df: Union[pd.DataFrame, pl.DataFrame], column: str) -> Dict[str, Any]:
    """Get detailed statistics for a specific column with caching."""
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
def load_database_data(table_name: str) -> Optional[pd.DataFrame]:
    """Load data from database with caching."""
    try:
        from utils.data_loader import DataLoader
        loader = DataLoader()
        return loader.get_table_data(table_name)
    except Exception as e:
        st.error(f"Error loading database data: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def load_file_data(file_path: str) -> Optional[Union[pd.DataFrame, pl.DataFrame]]:
    """Load data from file with caching."""
    try:
        if file_path.endswith('.csv'):
            return pl.read_csv(file_path)
        elif file_path.endswith('.parquet'):
            return pl.read_parquet(file_path)
        else:
            st.error(f"Unsupported file type: {file_path}")
            return None
    except Exception as e:
        st.error(f"Error loading file data: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'current_data_source' not in st.session_state:
        st.session_state.current_data_source = None
    if 'data_summary' not in st.session_state:
        st.session_state.data_summary = None 