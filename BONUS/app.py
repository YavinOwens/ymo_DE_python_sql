import streamlit as st

st.set_page_config(
    page_title="Rule Engine Management",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("Rule Engine Management")
    st.write("Welcome to the Rule Engine Management System")
    
    # Add any home page content here
    st.markdown("""
    ### Available Features:
    - Rule Management
    - Rule Configuration
    - Rule Execution History
    
    Select a page from the sidebar to get started.
    """)

if __name__ == "__main__":
    main() 