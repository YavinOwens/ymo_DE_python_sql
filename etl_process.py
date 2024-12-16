#!/usr/bin/env python3
"""
ETL Process for HR Data
This script implements an ETL (Extract, Transform, Load) process for HR data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
from datetime import datetime
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataLoader:
    """Class to handle data loading and validation operations."""
    
    def __init__(self, data_dir: Path):
        """Initialize DataLoader with data directory path."""
        self.data_dir = data_dir
        self.dfs: Dict[str, pd.DataFrame] = {}
    
    def load_csv(self, filename: str) -> Optional[pd.DataFrame]:
        """Load CSV file into pandas DataFrame."""
        try:
            file_path = self.data_dir / filename
            df = pd.read_csv(file_path)
            logging.info(f"Successfully loaded {filename}")
            return df
        except FileNotFoundError:
            logging.error(f"File not found: {filename}")
            return None
    
    def load_all_data(self) -> None:
        """Load all CSV files from the data directory."""
        csv_files = list(self.data_dir.glob("*.csv"))
        for file_path in csv_files:
            # Extract the main part of the filename (e.g., 'HR' from 'HR_ALL_ADDRESSES_20241216.csv')
            table_name = file_path.stem.split('_')[0]
            df = self.load_csv(file_path.name)
            if df is not None:
                self.dfs[table_name] = df
                logging.info(f"Added DataFrame for {table_name}")

class DataTransformer:
    """Class to handle data transformation and cleaning operations."""
    
    def __init__(self, dfs: Dict[str, pd.DataFrame]):
        """Initialize DataTransformer with dictionary of DataFrames."""
        self.dfs = dfs
        self.processed_dfs: Dict[str, pd.DataFrame] = {}
    
    def add_index_columns(self) -> None:
        """Add index columns to each DataFrame."""
        for table_name, df in self.dfs.items():
            id_column = f'{table_name.lower()}_id'
            df[id_column] = range(1, len(df) + 1)
            # Don't set index yet as we need to keep it as a regular column for the database
            self.dfs[table_name] = df
            logging.info(f"Added index to {table_name}")
    
    def clean_column_names(self) -> None:
        """Clean and standardize column names."""
        for table_name, df in self.dfs.items():
            df.columns = [
                col.lower().replace(' ', '_')
                for col in df.columns
            ]
            self.dfs[table_name] = df
            logging.info(f"Cleaned column names for {table_name}")
    
    def process_people_data(self) -> None:
        """Process PER_ALL_PEOPLE_F data."""
        if 'PER' in self.dfs:
            df = self.dfs['PER'].copy()
            
            # Convert date_of_birth to datetime safely
            try:
                df['date_of_birth'] = pd.to_datetime(df['date_of_birth'])
                # Calculate age
                df['age'] = (pd.Timestamp.now() - df['date_of_birth']).dt.days // 365
            except Exception as e:
                logging.warning(f"Error processing date_of_birth: {e}")
            
            # Clean string columns
            string_columns = ['name', 'nino', 'job', 'company']
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            self.processed_dfs['per'] = df
            logging.info("Processed people data")
    
    def process_assignments_data(self) -> None:
        """Process PER_ALL_ASSIGNMENTS_F data."""
        if 'PER' in self.dfs:  # Note: The file starts with PER but we want it in 'assignments' table
            df = self.dfs['PER'].copy()
            
            # Clean string columns
            string_columns = ['job', 'company']
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # Convert date columns safely
            if 'date_joined' in df.columns:
                try:
                    df['date_joined'] = pd.to_datetime(df['date_joined'])
                except Exception as e:
                    logging.warning(f"Error processing date_joined: {e}")
            
            self.processed_dfs['assignments'] = df
            logging.info("Processed assignments data")
    
    def process_addresses_data(self) -> None:
        """Process HR_ALL_ADDRESSES data."""
        if 'HR' in self.dfs:
            df = self.dfs['HR'].copy()
            
            # Clean and standardize address fields
            address_columns = ['street_address', 'city', 'country', 'postcode']
            for col in address_columns:
                if col in df.columns:
                    # Convert to string first to handle any non-string values
                    df[col] = df[col].astype(str).str.strip()
                    # Only apply title case to appropriate fields
                    if col in ['street_address', 'city', 'country']:
                        df[col] = df[col].str.title()
            
            self.processed_dfs['addresses'] = df
            logging.info("Processed addresses data")
    
    def process_all_data(self) -> None:
        """Process all datasets."""
        self.add_index_columns()
        self.clean_column_names()
        self.process_people_data()
        self.process_assignments_data()
        self.process_addresses_data()

class DatabaseLoader:
    """Class to handle database operations and data loading."""
    
    def __init__(self, db_path: str):
        """Initialize DatabaseLoader with database path."""
        self.db_path = db_path
        self.conn = None
    
    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Enable foreign key support
            self.conn.execute("PRAGMA foreign_keys = ON")
            logging.info("Connected to database")
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
    
    def create_tables(self, dfs: Dict[str, pd.DataFrame]) -> None:
        """Create database tables for each DataFrame."""
        if self.conn is None:
            self.connect()
        
        try:
            # Create tables with proper schema
            for table_name, df in dfs.items():
                # Create table with appropriate data types
                create_table_sql = self._generate_create_table_sql(table_name, df)
                self.conn.execute(create_table_sql)
                
                # Insert data
                df.to_sql(table_name, self.conn, if_exists='replace', index=False)
                logging.info(f"Created table: {table_name}")
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
    
    def _generate_create_table_sql(self, table_name: str, df: pd.DataFrame) -> str:
        """Generate CREATE TABLE SQL statement with appropriate data types."""
        columns = []
        primary_key = f"{table_name.lower()}_id"
        
        for column in df.columns:
            if column == primary_key:
                columns.append(f"{column} INTEGER PRIMARY KEY")
            else:
                dtype = df[column].dtype
                sql_type = (
                    "INTEGER" if np.issubdtype(dtype, np.integer)
                    else "REAL" if np.issubdtype(dtype, np.floating)
                    else "DATETIME" if dtype == 'datetime64[ns]'
                    else "TEXT"
                )
                columns.append(f"{column} {sql_type}")
        
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(columns) + "\n)"
    
    def create_relationships(self) -> None:
        """Create foreign key relationships between tables."""
        if self.conn is None:
            return
        
        try:
            # Create relationships
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS person_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    per_id INTEGER,
                    assignment_id INTEGER,
                    FOREIGN KEY (per_id) REFERENCES per(per_id),
                    FOREIGN KEY (assignment_id) REFERENCES assignments(assignments_id)
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS person_addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    per_id INTEGER,
                    address_id INTEGER,
                    FOREIGN KEY (per_id) REFERENCES per(per_id),
                    FOREIGN KEY (address_id) REFERENCES addresses(addresses_id)
                )
            """)
            
            self.conn.commit()
            logging.info("Created table relationships")
        except sqlite3.Error as e:
            logging.error(f"Error creating relationships: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn is not None:
            self.conn.close()
            logging.info("Closed database connection")

def main():
    """Main ETL process function."""
    # Set up paths
    data_dir = Path('setup_outputs/dummy_data')
    db_path = 'hr_database.sqlite'
    
    # Initialize components
    loader = DataLoader(data_dir)
    loader.load_all_data()
    
    transformer = DataTransformer(loader.dfs)
    transformer.process_all_data()
    
    db_loader = DatabaseLoader(db_path)
    db_loader.connect()
    db_loader.create_tables(transformer.processed_dfs)
    db_loader.create_relationships()
    db_loader.close()
    
    logging.info("ETL process completed successfully")

if __name__ == "__main__":
    main()
