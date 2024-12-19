import streamlit as st
import pandas as pd
from utils.utils import generate_profile_report, get_data_summary
from datetime import datetime

def show():
    st.title("Data Quality Overview")
    
    if 'current_data' not in st.session_state or st.session_state.current_data is None:
        st.info("Please select a data source from the sidebar to begin analysis.")
        return
    
    # Get data summary
    df = st.session_state.current_data
    summary = get_data_summary(df)
    
    if summary is None:
        st.error("Error getting data summary.")
        return
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", f"{summary['total_rows']:,}")
    with col2:
        st.metric("Total Columns", f"{summary['total_columns']:,}")
    with col3:
        st.metric("Missing Values", f"{summary['total_nulls']:,}")
    
    # Add configuration options for the profile report
    st.subheader("Profile Report Configuration")
    minimal_mode = st.checkbox("Minimal Report Mode", value=False, 
                             help="Generate a minimal report for faster processing")
    
    # Add a button to regenerate the profile report
    if st.button("🔄 Generate/Regenerate Profile Report"):
        st.session_state.profile_report = None
    
    # Generate profile report if not already generated
    if 'profile_report' not in st.session_state:
        st.session_state.profile_report = None
        
    if st.session_state.profile_report is None:
        try:
            with st.spinner("Generating profile report... This may take a few moments."):
                profile = generate_profile_report(
                    df=df,
                    minimal=minimal_mode
                )
                if profile is not None:
                    st.session_state.profile_report = profile
                    st.success("Profile report generated successfully!")
                else:
                    st.error("Error generating profile report.")
                    return
        except Exception as e:
            st.error(f"Error generating profile report: {str(e)}")
            return
    
    # Display profile report with loading state
    if st.session_state.profile_report is not None:
        st.subheader("Data Profile Report")
        try:
            with st.spinner("Loading profile report..."):
                st_profile_report = st.session_state.profile_report.to_html()
                st.components.v1.html(
                    st_profile_report,
                    height=800,
                    scrolling=True
                )
        except Exception as e:
            st.error(f"Error displaying profile report: {str(e)}")
            st.session_state.profile_report = None  # Reset the report on error

if __name__ == "__main__":
    show() 