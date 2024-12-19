import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import polars as pl

def show():
    st.title("Data Quality Analysis")
    
    if st.session_state.current_data is None:
        st.info("Please select a data source from the sidebar to begin analysis.")
        return
    
    df = st.session_state.current_data
    
    # Column selection
    selected_columns = st.multiselect(
        "Select columns for analysis",
        df.columns,
        default=list(df.columns)[:5]
    )
    
    if not selected_columns:
        st.warning("Please select at least one column for analysis.")
        return
    
    # Analysis tabs
    tab1, tab2, tab3 = st.tabs(["Missing Values", "Duplicates", "Data Types"])
    
    with tab1:
        st.subheader("Missing Values Analysis")
        if isinstance(df, pd.DataFrame):
            missing_data = df[selected_columns].isnull().sum()
            missing_pct = (missing_data / len(df) * 100).round(2)
        else:  # polars
            missing_data = df.select(selected_columns).null_count()
            missing_pct = (missing_data / len(df) * 100).round(2)
        
        # Create missing values bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=selected_columns,
            y=missing_pct,
            name="Missing %",
            text=missing_pct.round(1).astype(str) + '%',
            textposition='auto',
        ))
        fig.update_layout(
            title="Missing Values Percentage by Column",
            xaxis_title="Columns",
            yaxis_title="Missing %",
            showlegend=True,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Missing values table
        st.subheader("Missing Values Details")
        missing_df = pd.DataFrame({
            'Column': selected_columns,
            'Missing Count': missing_data,
            'Missing %': missing_pct
        })
        st.dataframe(missing_df.style.format({
            'Missing Count': '{:,.0f}',
            'Missing %': '{:.2f}%'
        }))
    
    with tab2:
        st.subheader("Duplicate Values Analysis")
        
        # Calculate duplicates
        if isinstance(df, pd.DataFrame):
            duplicate_counts = df[selected_columns].duplicated().sum()
            duplicate_pct = (duplicate_counts / len(df) * 100).round(2)
            
            # Duplicate combinations
            dup_combinations = df[selected_columns].value_counts().reset_index()
            dup_combinations.columns = list(selected_columns) + ['Count']
            dup_combinations = dup_combinations[dup_combinations['Count'] > 1].sort_values('Count', ascending=False)
        else:  # polars
            duplicate_counts = len(df) - len(df.unique())
            duplicate_pct = (duplicate_counts / len(df) * 100).round(2)
            
            # Duplicate combinations
            dup_combinations = (df.select(selected_columns)
                              .value_counts()
                              .filter(pl.col('count') > 1)
                              .sort('count', descending=True))
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Duplicate Rows", f"{duplicate_counts:,}")
        with col2:
            st.metric("Duplicate Percentage", f"{duplicate_pct:.2f}%")
        
        # Display duplicate combinations
        if len(dup_combinations) > 0:
            st.subheader("Most Common Duplicate Combinations")
            st.dataframe(dup_combinations.head(10))
        else:
            st.info("No duplicate combinations found in selected columns.")
    
    with tab3:
        st.subheader("Data Types Analysis")
        
        # Get data types
        if isinstance(df, pd.DataFrame):
            dtypes = pd.DataFrame({
                'Column': selected_columns,
                'Data Type': df[selected_columns].dtypes.astype(str),
                'Unique Values': df[selected_columns].nunique(),
                'Sample Values': [', '.join(map(str, df[col].dropna().unique()[:3])) for col in selected_columns]
            })
        else:  # polars
            dtypes = pd.DataFrame({
                'Column': selected_columns,
                'Data Type': [str(df.schema[col]) for col in selected_columns],
                'Unique Values': [df.select(col).n_unique() for col in selected_columns],
                'Sample Values': [', '.join(map(str, df.select(col).unique().to_series().drop_nulls().head(3))) for col in selected_columns]
            })
        
        # Display data types table
        st.dataframe(dtypes.style.format({
            'Unique Values': '{:,.0f}'
        }))
        
        # Data type distribution chart
        type_counts = dtypes['Data Type'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=.3
        )])
        fig.update_layout(
            title="Distribution of Data Types",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show() 