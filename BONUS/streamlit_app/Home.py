import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Data Quality Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'current_table' not in st.session_state:
        st.session_state.current_table = None
    if 'data_summary' not in st.session_state:
        st.session_state.data_summary = None
    if 'profile_report' not in st.session_state:
        st.session_state.profile_report = None

def get_table_names(conn):
    """Get list of tables from SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [row[0] for row in cursor.fetchall()]

def get_database_path():
    """Get the path to the SQLite database."""
    # List of possible database paths
    possible_paths = [
        Path("BONUS/assets/data/hr_database.sqlite"),
        Path("assets/data/hr_database.sqlite"),
        Path("../assets/data/hr_database.sqlite"),
        Path("../../assets/data/hr_database.sqlite"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def load_rule_templates():
    with open('assets/data/rule_templates.json', 'r') as file:
        return json.load(file)

def calculate_active_duration(activation_history):
    total_duration = datetime.timedelta()
    
    for period in activation_history:
        start_date = datetime.strptime(period['activated_date'], '%Y-%m-%d')
        if period['deactivated_date']:
            end_date = datetime.strptime(period['deactivated_date'], '%Y-%m-%d')
        else:
            end_date = datetime.now()
        
        duration = end_date - start_date
        total_duration += duration
    
    return total_duration

def display_rule_details(rule):
    st.write(f"**Rule ID:** {rule['id']}")
    st.write(f"**Name:** {rule['name']}")
    st.write(f"**Description:** {rule['description']}")
    st.write(f"**Category:** {rule['category']}")
    st.write(f"**Type:** {rule['type']}")
    st.write(f"**Severity:** {rule['severity']}")
    st.write(f"**Status:** {'Active' if rule['active'] else 'Inactive'}")
    
    # Display date information
    created_date = datetime.strptime(rule['created_date'], '%Y-%m-%d')
    st.write(f"**Created:** {created_date.strftime('%d %B %Y')}")
    
    # Calculate and display active duration
    duration = calculate_active_duration(rule['activation_history'])
    days = duration.days
    
    if days < 30:
        duration_str = f"{days} days"
    elif days < 365:
        months = days // 30
        duration_str = f"{months} months"
    else:
        years = days // 365
        remaining_months = (days % 365) // 30
        duration_str = f"{years} years" + (f", {remaining_months} months" if remaining_months > 0 else "")
    
    st.write(f"**Total Active Duration:** {duration_str}")
    
    # Display validation code
    st.write("**Python Validation Code:**")
    st.code(rule['validation_code'], language='python')
    
    if 'validation_code_sql' in rule:
        st.write("**SQL Validation Code:**")
        st.code(rule['validation_code_sql'], language='sql')
    
    # Display activation history
    st.write("**Activation History:**")
    for period in rule['activation_history']:
        activated = datetime.strptime(period['activated_date'], '%Y-%m-%d')
        if period['deactivated_date']:
            deactivated = datetime.strptime(period['deactivated_date'], '%Y-%m-%d')
            st.write(f"- Activated: {activated.strftime('%d %B %Y')} → Deactivated: {deactivated.strftime('%d %B %Y')}")
        else:
            st.write(f"- Activated: {activated.strftime('%d %B %Y')} → Current")

def main():
    st.title("Data Quality Dashboard 📊")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for data source selection
    with st.sidebar:
        st.title("Data Source")
        st.markdown("---")
        
        # Database connection
        db_path = get_database_path()
        
        if db_path is None:
            st.error("Database file not found!")
            st.info("Please ensure the SQLite database file exists in the assets/data directory.")
            return
        
        try:
            conn = sqlite3.connect(db_path)
            tables = get_table_names(conn)
            
            if not tables:
                st.info("No tables found in the database.")
                st.info("Please ensure the database contains tables.")
                return
            
            # Table selection
            selected_table = st.selectbox(
                "Select a table",
                tables,
                key="table_selector",
                help="Choose a table to analyze"
            )
            
            # Add a refresh button
            if st.button("🔄 Refresh Data"):
                st.session_state.current_data = None
                st.rerun()
            
        except sqlite3.Error as e:
            st.error(f"Database error: {str(e)}")
            return
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return
    
    # Main content area
    if 'conn' in locals() and selected_table:
        try:
            with st.spinner("Loading data..."):
                # Load data using pandas
                query = f"SELECT * FROM {selected_table}"
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    st.session_state.current_data = df
                    st.session_state.current_table = selected_table
                    
                    # Display data summary in a nice grid
                    st.markdown("### Data Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Total Rows",
                            f"{len(df):,}",
                            help="Total number of records in the table"
                        )
                    with col2:
                        st.metric(
                            "Total Columns",
                            len(df.columns),
                            help="Number of columns in the table"
                        )
                    with col3:
                        missing = df.isnull().sum().sum()
                        st.metric(
                            "Missing Values",
                            f"{missing:,}",
                            help="Total number of null values across all columns"
                        )
                    with col4:
                        duplicates = df.duplicated().sum()
                        st.metric(
                            "Duplicate Rows",
                            f"{duplicates:,}",
                            help="Number of duplicate records"
                        )
                    
                    # Display welcome message and instructions
                    st.markdown("""
                    ## Welcome to the Data Quality Dashboard!
                    
                    This dashboard provides comprehensive data quality analysis and monitoring tools.
                    Use the sidebar to navigate between different pages:
                    
                    - **Overview**: Get a high-level summary of your data quality
                    - **Quality Analysis**: Detailed quality metrics and analysis
                    - **Column Analysis**: In-depth analysis of individual columns
                    - **Data Catalogue**: Metadata and schema information
                    - **Rule Management**: Configure and manage data quality rules
                    
                    Select a table from the sidebar to begin your analysis.
                    """)
                    
                    # Preview the data with expander
                    with st.expander("Data Preview", expanded=True):
                        st.dataframe(
                            df.head(),
                            use_container_width=True,
                            column_config={
                                col: st.column_config.Column(
                                    help=f"Type: {df[col].dtype}"
                                ) for col in df.columns
                            }
                        )
                        
                        # Add download button for the data
                        st.download_button(
                            "Download Data as CSV",
                            df.to_csv(index=False).encode('utf-8'),
                            f"{selected_table}.csv",
                            "text/csv",
                            key='download-csv'
                        )
                    
                else:
                    st.warning(f"No data found in table: {selected_table}")
                    
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
        finally:
            conn.close()

if __name__ == "__main__":
    main() 