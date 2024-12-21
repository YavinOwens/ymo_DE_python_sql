import streamlit as st 
import pandas as pd
import seaborn as sns
import plotly.express as px
import sqlite3
import json
from datetime import datetime
import numpy as np
import re
from datetime import timedelta
from data_quality_checks import DataQualityChecks
import streamlit.components.v1 as components

# Set page config to wide mode
st.set_page_config(layout="wide", page_title="Data Quality Dashboard")

# Load rule templates
try:
    with open('assets/data/rule_templates.json', 'r') as f:
        rule_templates_dict = json.load(f)
        
    # Flatten the nested JSON structure
    flattened_rules = []
    for category, rules in rule_templates_dict.items():
        if isinstance(rules, list):
            for rule in rules:
                rule['category'] = category
                flattened_rules.append(rule)
        else:
            for subcategory, subrules in rules.items():
                for rule in subrules:
                    rule['category'] = category
                    rule['subcategory'] = subcategory
                    flattened_rules.append(rule)
    
    rule_templates_df = pd.DataFrame(flattened_rules)
    # Define categories and severities from rule_templates_df
    categories = ['All'] + sorted(list(rule_templates_df['category'].unique()))
    severities = ['All'] + sorted(list(rule_templates_df['severity'].unique()))
except FileNotFoundError:
    st.error("Rule templates file not found!")
    rule_templates_df = pd.DataFrame()
    categories = ['All']
    severities = ['All']

# Custom CSS with improved spacing
st.markdown("""
<style>
    /* Global Spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card Styling */
    .card {
        border-radius: 10px;
        padding: 1.5rem;
        background-color: white;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
    }
    
    /* Header Styling */
    h1, h2, h3, h4, h5 {
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    
    /* Metric Cards */
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.4rem;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        font-weight: 500;
    }
    
    /* Tab Styling */
    .stTabs {
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        padding: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        background-color: white;
        border-radius: 8px;
        color: #666;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        margin-right: 0.5rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    
    /* DataFrame Styling */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
    }
    
    /* Select Box Styling */
    .stSelectbox {
        margin: 0.8rem 0;
    }
    .stSelectbox > div {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Container Spacing */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Column Spacing */
    .row-widget.stHorizontal {
        gap: 1rem;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 0.5rem;
    }
    
    /* Success/Error Message Styling */
    .stSuccess, .stError {
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_card(title, description=None):
    """Create a styled card with title and optional description."""
    card_html = f"""
        <div style="background-color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); margin-bottom: 1.5rem;">
            <h3 style="color: #1f77b4; margin-bottom: 0.8rem; font-weight: 600;">{title}</h3>
            {f'<p style="color: #666; margin-bottom: 1rem;">{description}</p>' if description else ''}
        </div>
    """
    return st.markdown(card_html, unsafe_allow_html=True)

# Initialize session states and load configurations
if 'configurations' not in st.session_state:
    try:
        with open('rule_configurations.json', 'r') as f:
            st.session_state.configurations = json.load(f)
    except FileNotFoundError:
        st.session_state.configurations = {'rule_configs': {}}

# Additional session states
session_state_vars = {
    'rule_category': 'All',
    'rule_severity': 'All',
    'filtered_rules': None,
    'save_clicked': False,
    'selected_rules': [],
    'current_column': None,
    'current_table': None,
    'active_tab': 0,
    'assessment_results': pd.DataFrame().to_dict(),
    'last_assessment': None,
    'report_view': "All",
    'selected_check': "All"
}

for var, default in session_state_vars.items():
    if var not in st.session_state:
        st.session_state[var] = default

def update_rule_filters():
    st.session_state.rule_category = st.session_state.temp_rule_category
    st.session_state.rule_severity = st.session_state.temp_rule_severity
    st.session_state.selected_rules = []

def save_configuration():
    st.session_state.save_clicked = True

def deactivate_configuration(config_key):
    if config_key in st.session_state.configurations['rule_configs']:
        st.session_state.configurations['rule_configs'][config_key]['is_active'] = False
        st.session_state.configurations['rule_configs'][config_key]['deactivated_at'] = datetime.now().isoformat()
        with open('rule_configurations.json', 'w') as f:
            json.dump(st.session_state.configurations, f, indent=2)
        return True
    return False

def deactivate_all_rules():
    if 'configurations' in st.session_state and st.session_state.configurations['rule_configs']:
        for config_key in st.session_state.configurations['rule_configs']:
            st.session_state.configurations['rule_configs'][config_key]['is_active'] = False
            st.session_state.configurations['rule_configs'][config_key]['deactivated_at'] = datetime.now().isoformat()
        with open('rule_configurations.json', 'w') as f:
            json.dump(st.session_state.configurations, f, indent=2)
        return True
    return False

def create_data_table(df, key=None, height=400):
    return st.dataframe(
        df,
        use_container_width=True,
        height=height,
        hide_index=True,
        column_config={
            "severity": st.column_config.TextColumn(
                "Severity",
                help="Rule severity level",
                width="medium",
            ),
            "category": st.column_config.TextColumn(
                "Category",
                help="Rule category",
                width="medium",
            ),
        }
    )

def display_metrics(metrics_data):
    cols = st.columns(len(metrics_data))
    for col, (label, value) in zip(cols, metrics_data):
        col.markdown(f"""
            <div style="background-color: white; border-radius: 10px; padding: 1.2rem; text-align: center; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); margin: 0.5rem 0;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #1f77b4; margin-bottom: 0.4rem;">{value}</div>
                <div style="font-size: 0.9rem; color: #666; font-weight: 500;">{label}</div>
            </div>
        """, unsafe_allow_html=True)

def save_rule_configuration(rule_data, table_name, column_name):
    config_key = f"{rule_data['id']}_{table_name}_{column_name}"
    
    st.session_state.configurations['rule_configs'][config_key] = {
        'rule_id': rule_data['id'],
        'name': rule_data['name'],
        'description': rule_data['description'],
        'category': rule_data['category'],
        'severity': rule_data['severity'],
        'table_name': table_name,
        'column_name': column_name,
        'is_active': True,
        'activated_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    with open('rule_configurations.json', 'w') as f:
        json.dump(st.session_state.configurations, f, indent=2)

# Database connection helper
def get_db_connection():
    return sqlite3.connect('assets/data/hr_database.sqlite')

# Get list of tables (do this once at startup)
conn = get_db_connection()
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
table_names = [table[0] for table in tables]
conn.close()

# Sidebar with custom styling
with st.sidebar:
    st.markdown("""
        <div class="card">
            <h3>Data Source Selection</h3>
        </div>
    """, unsafe_allow_html=True)
    selected_table = st.selectbox('Select a table', table_names)

# Read data from selected table
conn = get_db_connection()
df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
conn.close()

# Create tabs with custom styling
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Data", "📚 Rules", "⚙️ Config", "📈 Stats", "🔍 Assessment"])

# Tab 1: Data Overview
with tab1:
    create_card(
        "📊 Data Overview",
        "This tab shows the raw data from your selected table."
    )
    st.dataframe(df, use_container_width=True)

# Tab 2: Rule Templates
with tab2:
    create_card(
        "📚 Rule Templates",
        "Browse through our collection of pre-built data quality rules."
    )
    
    # Add filter controls with better spacing
    with st.container():
        create_card("Filter Options")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="margin: 0.5rem 0;">', unsafe_allow_html=True)
            selected_category = st.selectbox('Filter by Category', categories)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div style="margin: 0.5rem 0;">', unsafe_allow_html=True)
            selected_severity = st.selectbox('Filter by Severity', severities)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters and display table
    filtered_df = rule_templates_df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_severity != 'All':
        filtered_df = filtered_df[filtered_df['severity'] == selected_severity]
    
    create_data_table(filtered_df)

# Tab 3: Rule Configuration
with tab3:
    create_card(
        "⚙️ Rule Configuration",
        "Configure and manage your data quality rules."
    )
    
    left_col, right_col = st.columns([2, 3])
    
    with left_col:
        create_card("Select Data Source")
        st.markdown('<div style="margin: 0.8rem 0;">', unsafe_allow_html=True)
        config_table = st.selectbox('Table', table_names, key='config_table_select')
        conn = get_db_connection()
        config_df = pd.read_sql_query(f"SELECT * FROM {config_table}", conn)
        conn.close()
        selected_column = st.selectbox('Column', config_df.columns, key='config_column_select')
        st.markdown('</div>', unsafe_allow_html=True)
        
        create_card("Filter Rules")
        st.markdown('<div style="margin: 0.8rem 0;">', unsafe_allow_html=True)
        rule_category = st.selectbox('Category', categories, key='temp_rule_category')
        rule_severity = st.selectbox('Severity', severities, key='temp_rule_severity')
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        create_card("Available Rules")
        filtered_rules = rule_templates_df.copy()
        if rule_category != 'All':
            filtered_rules = filtered_rules[filtered_rules['category'] == rule_category]
        if rule_severity != 'All':
            filtered_rules = filtered_rules[filtered_rules['severity'] == rule_severity]
        
        create_data_table(filtered_rules[['id', 'name', 'description', 'category', 'severity']])
        
        create_card("Rule Selection")
        st.markdown('<div style="margin: 0.8rem 0;">', unsafe_allow_html=True)
        selected_rules = st.multiselect(
            'Select Rules to Configure',
            filtered_rules['id'].unique(),
            format_func=lambda x: f"{x} - {filtered_rules[filtered_rules['id'] == x].iloc[0]['name']}"
        )
        
        st.markdown('<div style="margin: 1rem 0;">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button('Save Selected', use_container_width=True):
            for rule_id in selected_rules:
                rule_data = filtered_rules[filtered_rules['id'] == rule_id].iloc[0]
                save_rule_configuration(rule_data, config_table, selected_column)
            st.success(f'Successfully saved {len(selected_rules)} rule configurations!')
        
        if col2.button('Save All Filtered', use_container_width=True):
            for _, rule_data in filtered_rules.iterrows():
                save_rule_configuration(rule_data, config_table, selected_column)
            st.success(f'Successfully saved {len(filtered_rules)} rule configurations!')
        st.markdown('</div>', unsafe_allow_html=True)

# Tab 4: Detailed Statistics
with tab4:
    create_card(
        "📈 Statistics & Analytics",
        "Get insights into your data quality rules."
    )
    
    if 'configurations' in st.session_state and st.session_state.configurations['rule_configs']:
        configs_df = pd.DataFrame(st.session_state.configurations['rule_configs']).T
        
        create_card("Summary Metrics")
        total_rules = len(rule_templates_df)
        active_rules = len(configs_df[configs_df.get('is_active', True) == True])
        
        metrics_data = [
            ("Total Available Rules", total_rules),
            ("Configured Rules", len(configs_df)),
            ("Active Rules", active_rules),
            ("Adoption Rate", f"{(active_rules/total_rules)*100:.1f}%")
        ]
        
        display_metrics(metrics_data)
        
        st.markdown('<div style="margin: 2rem 0;">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            create_card("Rules by Severity")
            fig = px.pie(configs_df, names='severity')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            create_card("Rules by Category")
            fig = px.pie(configs_df, names='category')
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No configurations available yet. Start by adding some rules!")

# Tab 5: Run Assessment
with tab5:
    create_card(
        "🔍 Data Quality Assessment",
        "Run quality checks on your data and get a comprehensive quality report."
    )
    
    if 'configurations' in st.session_state and st.session_state.configurations['rule_configs']:
        configs_df = pd.DataFrame(st.session_state.configurations['rule_configs']).T
        active_configs = configs_df[configs_df.get('is_active', True) == True]
        
        create_card("Assessment Configuration")
        st.markdown('<div style="margin: 0.8rem 0;">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        tables = list(active_configs['table_name'].unique())
        selected_table = col1.selectbox('Select Table to Assess', tables, key='assess_table')
        
        columns = ['All'] + list(active_configs[active_configs['table_name'] == selected_table]['column_name'].unique())
        selected_column = col2.selectbox('Select Column (Optional)', columns, key='assess_column')
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 1.5rem 0;">', unsafe_allow_html=True)
        if st.button('Run Assessment', use_container_width=True):
            conn = get_db_connection()
            df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
            conn.close()
            
            with st.spinner('Running quality assessment...'):
                quality_checks = DataQualityChecks(df)
                
                create_card("Data Summary")
                summary = quality_checks.get_basic_stats()
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Records", summary['row_count'])
                col2.metric("Total Columns", summary['column_count'])
                col3.metric("Memory Usage (MB)", f"{summary['memory_usage'] / 1024 / 1024:.2f}")
                
                results_tab1, results_tab2 = st.tabs(["Quality Checks", "Pass/Fail Report"])
                
                with results_tab1:
                    if selected_column != 'All':
                        create_card("Column Quality Checks")
                        checks_config = quality_checks._get_default_checks_config(selected_column)
                        results = quality_checks.run_column_checks(selected_column, checks_config)
                        
                        for check in results['checks']:
                            with st.expander(f"Check: {check['check_name']}", expanded=True):
                                if check['success']:
                                    st.success("✅ Check passed")
                                else:
                                    st.error("❌ Check failed")
                                st.json(check['result'])
                
                with results_tab2:
                    create_card("Pass/Fail Report")
                    
                    col1, col2, col3 = st.columns(3)
                    report_view = col1.radio(
                        "Show Records",
                        ["Failed", "Passed", "All"],
                        horizontal=True,
                        key='report_radio',
                        on_change=update_report_view
                    )
                    
                    if selected_column != 'All':
                        checks_config = quality_checks._get_default_checks_config(selected_column)
                        results = quality_checks.run_column_checks(selected_column, checks_config)
                        
                        create_card("Results")
                        
                        # Collect all results in one DataFrame
                        all_results = []
                        for check in results['checks']:
                            try:
                                if 'validation_result' in check['result']:
                                    mask = check['result']['validation_result']
                                    result_df = df.copy()
                                    result_df['check_name'] = check['check_name']
                                    result_df['status'] = np.where(mask, 'Passed', 'Failed')
                                    result_df['column_checked'] = selected_column
                                    all_results.append(result_df)
                            except Exception as e:
                                st.error(f"Error processing check {check['check_name']}: {str(e)}")
                        
                        if all_results:
                            combined_results = pd.concat(all_results, ignore_index=True)
                            
                            # Display summary metrics with consistent styling
                            st.markdown('<div style="margin: 1.5rem 0;">', unsafe_allow_html=True)
                            total = len(combined_results)
                            passed = len(combined_results[combined_results['status'] == 'Passed'])
                            failed = len(combined_results[combined_results['status'] == 'Failed'])
                            
                            metrics_data = [
                                ("Total Records", total),
                                ("Passed", passed),
                                ("Failed", failed)
                            ]
                            display_metrics(metrics_data)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Add additional filters with consistent styling
                            create_card("Filter Results")
                            st.markdown('<div style="margin: 0.8rem 0;">', unsafe_allow_html=True)
                            check_names = ['All'] + list(combined_results['check_name'].unique())
                            selected_check = st.selectbox(
                                'Filter by Check',
                                check_names,
                                key='check_filter',
                                on_change=update_selected_check
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Apply filters using session state values
                            filtered_results = combined_results.copy()
                            if st.session_state.report_view != "All":
                                filtered_results = filtered_results[filtered_results['status'] == st.session_state.report_view]
                            if st.session_state.selected_check != "All":
                                filtered_results = filtered_results[filtered_results['check_name'] == st.session_state.selected_check]
                            
                            # Display filtered results with consistent styling
                            create_card(f"{st.session_state.report_view} Records")
                            display_cols = [col for col in filtered_results.columns if col not in ['check_name', 'status', 'column_checked']]
                            st.dataframe(filtered_results[display_cols], use_container_width=True)
                        else:
                            st.info("No results available for the selected column.")
                    else:
                        st.info("Please select a specific column to view the pass/fail report.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No active configurations available. Please configure some rules first!")

def save_assessment_results(results_df):
    """Save assessment results to both session state and JSON"""
    st.session_state.assessment_results = results_df.to_dict()
    st.session_state.last_assessment = {
        'timestamp': datetime.now().isoformat(),
        'table': st.session_state.get('assess_table'),
        'column': st.session_state.get('assess_column')
    }
    # Save to JSON as backup
    with open('assessment_results.json', 'w') as f:
        json.dump({
            'results': st.session_state.assessment_results,
            'metadata': st.session_state.last_assessment
        }, f)

def load_assessment_results():
    """Load assessment results from session state or JSON"""
    if 'assessment_results' in st.session_state and st.session_state.assessment_results:
        return pd.DataFrame.from_dict(st.session_state.assessment_results)
    try:
        with open('assessment_results.json', 'r') as f:
            data = json.load(f)
            st.session_state.assessment_results = data['results']
            st.session_state.last_assessment = data['metadata']
            return pd.DataFrame.from_dict(data['results'])
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame()

def update_report_view():
    """Update the report view in session state"""
    if 'report_radio' not in st.session_state:
        st.session_state.report_view = "All"
    else:
        st.session_state.report_view = st.session_state.report_radio

def update_selected_check():
    """Update the selected check in session state"""
    if 'check_filter' not in st.session_state:
        st.session_state.selected_check = "All"
    else:
        st.session_state.selected_check = st.session_state.check_filter