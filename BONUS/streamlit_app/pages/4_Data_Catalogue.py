import streamlit as st
import pandas as pd
import polars as pl
from utils.utils import get_data_summary, initialize_session_state
from utils.data_loader import DataLoader
from config import DATABASE_PATH

def show():
    st.title("Data Catalogue")
    
    # Initialize session state
    initialize_session_state()
    
    try:
        data_loader = DataLoader()
        
        # Test database connection
        if not data_loader.test_connection():
            st.error(f"Could not connect to database at: {DATABASE_PATH}")
            st.info("Please ensure the database file exists and is accessible.")
            return
        
        # Get table names
        tables = data_loader.get_table_names()
        
        if not tables:
            st.info("No tables found in the database.")
            return
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Table Overview", "Column Details"])
        
        with tab1:
            st.subheader("Database Tables")
            
            # Display table summaries
            for table in tables:
                with st.expander(f"Table: {table}"):
                    with st.spinner(f"Loading metadata for {table}..."):
                        df = data_loader.get_table_data(table)
                        
                        if df is not None:
                            # Get table summary
                            summary = get_data_summary(df)
                            
                            # Display summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Total Rows", f"{summary['total_rows']:,}")
                            with col2:
                                st.metric("Total Columns", f"{summary['total_columns']:,}")
                            with col3:
                                st.metric("Missing Values", f"{summary['total_nulls']:,}")
                            with col4:
                                st.metric("Memory Usage", f"{summary['memory_usage']:.2f} MB")
                            
                            # Display schema information
                            schema = data_loader.get_table_schema(table)
                            if schema:
                                st.write("**Schema Information**")
                                schema_df = pd.DataFrame(schema['columns'])
                                st.dataframe(
                                    schema_df,
                                    column_config={
                                        "name": "Column Name",
                                        "type": "Data Type",
                                        "notnull": st.column_config.CheckboxColumn("Not Null"),
                                        "pk": st.column_config.CheckboxColumn("Primary Key")
                                    },
                                    use_container_width=True
                                )
                            
                            # Display sample data
                            st.write("**Sample Data**")
                            st.dataframe(
                                df.head(),
                                use_container_width=True,
                                column_config={
                                    col: st.column_config.Column(
                                        help=f"Type: {df[col].dtype}"
                                    ) for col in df.columns
                                }
                            )
                        else:
                            st.error(f"Error loading table: {table}")
        
        with tab2:
            st.subheader("Column Analysis")
            
            # Table selection for column analysis
            selected_table = st.selectbox(
                "Select a table",
                tables,
                key="catalogue_table"
            )
            
            if selected_table:
                with st.spinner("Loading table data..."):
                    df = data_loader.get_table_data(selected_table)
                    
                    if df is not None:
                        # Get column information
                        column_info = []
                        for col in df.columns:
                            info = {
                                'Column': col,
                                'Type': str(df[col].dtype),
                                'Non-Null Count': df[col].count(),
                                'Null Count': df[col].isnull().sum(),
                                'Unique Values': df[col].nunique()
                            }
                            
                            # Add sample values
                            sample_values = df[col].dropna().unique()[:3]
                            info['Sample Values'] = ', '.join(map(str, sample_values))
                            
                            column_info.append(info)
                        
                        # Create and display column information dataframe
                        column_df = pd.DataFrame(column_info)
                        st.dataframe(
                            column_df,
                            column_config={
                                "Column": "Column Name",
                                "Type": "Data Type",
                                "Non-Null Count": st.column_config.NumberColumn(
                                    "Non-Null Count",
                                    help="Number of non-null values"
                                ),
                                "Null Count": st.column_config.NumberColumn(
                                    "Null Count",
                                    help="Number of null values"
                                ),
                                "Unique Values": st.column_config.NumberColumn(
                                    "Unique Values",
                                    help="Number of unique values"
                                ),
                                "Sample Values": st.column_config.TextColumn(
                                    "Sample Values",
                                    help="Up to 3 sample values from the column",
                                    width="large"
                                )
                            },
                            use_container_width=True
                        )
                        
                        # Column details in expandable sections
                        st.subheader("Detailed Column Information")
                        for col in df.columns:
                            with st.expander(f"Column: {col}"):
                                # Basic statistics
                                stats = df[col].describe()
                                st.write("**Basic Statistics**")
                                st.dataframe(stats)
                                
                                # Unique values distribution
                                if df[col].nunique() <= 10:
                                    st.write("**Value Distribution**")
                                    value_counts = df[col].value_counts()
                                    st.bar_chart(value_counts)
                    else:
                        st.error(f"Error loading table: {selected_table}")
                        
    except Exception as e:
        st.error(f"Error initializing Data Catalogue: {str(e)}")
        st.info("Please check your database configuration and try again.")

if __name__ == "__main__":
    show() 