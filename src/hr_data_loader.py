import pandas as pd
import sqlite3

def load_hr_data():
    """Load data from SQLite database into pandas DataFrames with correct joins."""
    conn = sqlite3.connect('data/hr_database.sqlite')
    
    # Load tables
    per_df = pd.read_sql_query("SELECT * FROM per", conn)
    assignments_df = pd.read_sql_query("SELECT * FROM assignments", conn)
    addresses_df = pd.read_sql_query("SELECT * FROM addresses", conn)
    
    # Join person_assignments with person_addresses
    person_assignments_df = pd.read_sql_query("""
        SELECT * FROM person_assignments
    """, conn)
    
    person_addresses_df = pd.read_sql_query("""
        SELECT * FROM person_addresses
    """, conn)
    
    conn.close()
    
    return per_df, assignments_df, addresses_df, person_assignments_df, person_addresses_df

def get_data_summary(df):
    """Get summary of the loaded data."""
    print("\nData Summary:")
    print(f"Total number of records: {len(df)}")
    print("\nColumns available:")
    for col in df.columns:
        print(f"- {col}: {df[col].nunique()} unique values")
    print("\nSample data:")
    print(df.head())

def get_table_info():
    """Get information about table structures."""
    conn = sqlite3.connect('data/hr_database.sqlite')
    cursor = conn.cursor()
    
    tables = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for table in cursor.fetchall():
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        tables[table_name] = [col[1] for col in columns]
    
    conn.close()
    return tables
