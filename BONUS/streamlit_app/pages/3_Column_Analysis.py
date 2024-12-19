import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.utils import get_column_stats, initialize_session_state
from utils.data_loader import DataLoader

def show():
    st.title("Column Analysis")
    
    # Initialize session state
    initialize_session_state()
    
    data_loader = DataLoader()
    tables = data_loader.get_table_names()
    
    if not tables:
        st.info("No tables available in the database.")
        return
    
    # Table selection
    selected_table = st.selectbox(
        "Select a table",
        tables,
        key="column_analysis_table"
    )
    
    if selected_table:
        with st.spinner("Loading table data..."):
            df = data_loader.get_table_data(selected_table)
            
            if df is not None:
                # Column selection
                selected_column = st.selectbox(
                    "Select a column to analyze",
                    df.columns,
                    key="column_analysis_column"
                )
                
                if selected_column:
                    # Get column statistics
                    stats = get_column_stats(df, selected_column)
                    
                    # Display statistics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Data Type", stats['dtype'])
                    with col2:
                        st.metric("Total Values", f"{stats['total_count']:,}")
                    with col3:
                        st.metric("Null Values", f"{stats['null_count']:,}")
                    with col4:
                        st.metric("Unique Values", f"{stats['unique_count']:,}")
                    
                    # Create visualizations based on data type
                    st.subheader("Column Distribution")
                    
                    if df[selected_column].dtype.kind in 'biufc':  # numeric data
                        # Histogram
                        fig = px.histogram(
                            df,
                            x=selected_column,
                            title=f"Distribution of {selected_column}",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Box plot
                        fig = px.box(
                            df,
                            y=selected_column,
                            title=f"Box Plot of {selected_column}",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Additional numeric statistics
                        st.subheader("Numeric Statistics")
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric("Mean", f"{stats.get('mean', 0):.2f}")
                        with col2:
                            st.metric("Median", f"{stats.get('median', 0):.2f}")
                        with col3:
                            st.metric("Std Dev", f"{stats.get('std', 0):.2f}")
                        with col4:
                            st.metric("Min", f"{stats.get('min', 0):.2f}")
                        with col5:
                            st.metric("Max", f"{stats.get('max', 0):.2f}")
                    else:  # categorical data
                        # Value counts
                        value_counts = df[selected_column].value_counts()
                        
                        # Create DataFrame for plotting
                        plot_df = pd.DataFrame({
                            'Value': value_counts.index,
                            'Count': value_counts.values
                        })
                        
                        # Bar chart
                        fig = px.bar(
                            plot_df,
                            x='Value',
                            y='Count',
                            title=f"Value Distribution of {selected_column}",
                            template="plotly_white"
                        )
                        fig.update_layout(
                            xaxis_title=selected_column,
                            yaxis_title="Count",
                            xaxis_tickangle=-45
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Pie chart
                        fig = px.pie(
                            plot_df,
                            values='Count',
                            names='Value',
                            title=f"Value Distribution (%) of {selected_column}",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Data preview with value counts
                    st.subheader("Data Analysis")
                    
                    # Show value counts
                    st.write("**Value Counts**")
                    value_counts_df = df[selected_column].value_counts().reset_index()
                    value_counts_df.columns = ['Value', 'Count']
                    value_counts_df['Percentage'] = (value_counts_df['Count'] / len(df) * 100).round(2)
                    
                    st.dataframe(
                        value_counts_df,
                        column_config={
                            "Value": st.column_config.Column(
                                "Value",
                                help="Unique values in the column"
                            ),
                            "Count": st.column_config.NumberColumn(
                                "Count",
                                help="Number of occurrences"
                            ),
                            "Percentage": st.column_config.NumberColumn(
                                "Percentage (%)",
                                help="Percentage of total",
                                format="%.2f%%"
                            )
                        },
                        use_container_width=True
                    )
                    
                    # Show sample data
                    st.write("**Sample Data**")
                    st.dataframe(
                        df[[selected_column]].head(10),
                        column_config={
                            selected_column: st.column_config.Column(
                                selected_column,
                                help=f"Type: {df[selected_column].dtype}"
                            )
                        },
                        use_container_width=True
                    )
            else:
                st.error(f"Error loading table: {selected_table}")

if __name__ == "__main__":
    show() 