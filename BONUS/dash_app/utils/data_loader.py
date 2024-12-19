import pandas as pd
import polars as pl
from sqlalchemy import create_engine, text
import os
from typing import Dict, Optional, Union

class DataLoader:
    def __init__(self, database_path: str = "data/data_quality.db"):
        """Initialize the DataLoader with the database path."""
        self.database_path = database_path
        self.engine = create_engine(f'sqlite:///{database_path}')
        
    def get_table_names(self) -> list:
        """Get list of available tables in the database."""
        with self.engine.connect() as conn:
            query = text("SELECT name FROM sqlite_master WHERE type='table'")
            result = conn.execute(query)
            return [row[0] for row in result]
    
    def get_table_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """Load data from a specific table."""
        try:
            query = f"SELECT * FROM {table_name}"
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"Error loading table {table_name}: {str(e)}")
            return None
    
    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """Get schema information for a specific table."""
        try:
            with self.engine.connect() as conn:
                query = text(f"PRAGMA table_info({table_name})")
                result = conn.execute(query)
                columns = []
                for row in result:
                    columns.append({
                        'name': row[1],
                        'type': row[2],
                        'notnull': bool(row[3]),
                        'pk': bool(row[5])
                    })
                return {'table_name': table_name, 'columns': columns}
        except Exception as e:
            print(f"Error getting schema for table {table_name}: {str(e)}")
            return None
    
    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """Execute a custom SQL query."""
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return None 