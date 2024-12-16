import pandas as pd
import sqlite3

def load_hr_data():
    """Load data from SQLite database into pandas DataFrames with direct relationships."""
    conn = sqlite3.connect('hr_database.sqlite')
    
    # Load base tables
    per_df = pd.read_sql_query("SELECT * FROM per", conn)
    assignments_df = pd.read_sql_query("SELECT * FROM assignments", conn)
    addresses_df = pd.read_sql_query("SELECT * FROM addresses", conn)
    
    # Join tables directly using per_id
    merged_df = pd.read_sql_query("""
        SELECT p.*, a.*, addr.*
        FROM per p
        LEFT JOIN assignments a ON p.per_id = a.per_id
        LEFT JOIN addresses addr ON p.per_id = addr.hr_id
    """, conn)
    
    conn.close()
    
    return merged_df

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
    conn = sqlite3.connect('hr_database.sqlite')
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
