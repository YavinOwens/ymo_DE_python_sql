import pandas as pd
import polars as pl
from sqlalchemy import create_engine, text
import os
from typing import Dict, Optional, Union
from config import DATABASE_PATH

class DataLoader:
    def __init__(self):
        """Initialize the DataLoader with the database path from config."""
        if not os.path.exists(DATABASE_PATH):
            raise FileNotFoundError(f"Database file not found at: {DATABASE_PATH}")
        
        # Create the SQLite connection URL
        db_url = f'sqlite:///{DATABASE_PATH}'
        
        try:
            self.engine = create_engine(db_url)
            # Test the connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
        
    def get_table_names(self) -> list:
        """Get list of available tables in the database."""
        try:
            with self.engine.connect() as conn:
                query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                result = conn.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            st.error(f"Error getting table names: {str(e)}")
            return []
    
    def get_table_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """Load data from a specific table."""
        try:
            query = f"SELECT * FROM {table_name}"
            return pd.read_sql(query, self.engine)
        except Exception as e:
            st.error(f"Error loading table {table_name}: {str(e)}")
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
            st.error(f"Error getting schema for table {table_name}: {str(e)}")
            return None
    
    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """Execute a custom SQL query."""
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")
            return None
    
    @staticmethod
    def convert_to_polars(df: pd.DataFrame) -> pl.DataFrame:
        """Convert pandas DataFrame to polars DataFrame."""
        return pl.from_pandas(df)
    
    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            st.error(f"Database connection test failed: {str(e)}")
            return False