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

# Set page config to wide mode
st.set_page_config(layout="wide")

# Add function to deactivate all rules
def deactivate_all_rules():
    if 'configurations' in st.session_state and st.session_state.configurations['rule_configs']:
        for config_key in st.session_state.configurations['rule_configs']:
            st.session_state.configurations['rule_configs'][config_key]['is_active'] = False
            st.session_state.configurations['rule_configs'][config_key]['deactivated_at'] = datetime.now().isoformat()
        
        # Save updated configurations
        with open('rule_configurations.json', 'w') as f:
            json.dump(st.session_state.configurations, f, indent=2)
        return True
    return False

# Initialize session state for rule filters if not exists
if 'rule_category' not in st.session_state:
    st.session_state.rule_category = 'All'
if 'rule_severity' not in st.session_state:
    st.session_state.rule_severity = 'All'
if 'filtered_rules' not in st.session_state:
    st.session_state.filtered_rules = None
if 'save_clicked' not in st.session_state:
    st.session_state.save_clicked = False
if 'selected_rules' not in st.session_state:
    st.session_state.selected_rules = []
if 'current_column' not in st.session_state:
    st.session_state.current_column = None

def update_rule_filters():
    st.session_state.rule_category = st.session_state.temp_rule_category
    st.session_state.rule_severity = st.session_state.temp_rule_severity
    # Reset selected rules when filters change
    st.session_state.selected_rules = []

def save_configuration():
    st.session_state.save_clicked = True

def deactivate_configuration(config_key):
    if config_key in st.session_state.configurations['rule_configs']:
        # Mark the configuration as inactive instead of deleting
        st.session_state.configurations['rule_configs'][config_key]['is_active'] = False
        st.session_state.configurations['rule_configs'][config_key]['deactivated_at'] = datetime.now().isoformat()
        # Save updated configurations
        with open('rule_configurations.json', 'w') as f:
            json.dump(st.session_state.configurations, f, indent=2)
        return True
    return False

def save_rule_configuration(rule_data, config_table, selected_column):
    rule_id = rule_data['id']
    config_key = f"{rule_id}_{config_table}_{selected_column}"
    
    # Create configuration dictionary
    config_data = {
        'rule_id': rule_id,
        'table_name': config_table,
        'column_name': selected_column,
        'description': rule_data['description'],
        'python_code': rule_data['validation_code'].replace('table_name', config_table).replace('column_name', selected_column),
        'sql_code': rule_data['validation_code_sql'].replace('table_name', config_table).replace('column_name', selected_column),
        'severity': rule_data['severity'],
        'category': rule_data['category'],
        'last_updated': datetime.now().isoformat(),
        'is_active': True,
        'activated_at': datetime.now().isoformat()
    }
    
    # Update session state
    st.session_state.configurations['rule_configs'][config_key] = config_data
    
    # Save updated configurations
    with open('rule_configurations.json', 'w') as f:
        json.dump(st.session_state.configurations, f, indent=2)

# read data from the database
# Create a connection to the database
conn = sqlite3.connect('assets/data/hr_database.sqlite')

# Get list of tables
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
table_names = [table[0] for table in tables]

# Add table selector dropdown
selected_table = st.sidebar.selectbox('Select a table', table_names)

# Read data from selected table
df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
conn.close()

# Add tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Data", "Rule Templates", "Rule Configuration", "Detailed Statistics", "Run Data Quality Assessment"])

with tab1:
    st.markdown("""
    ### 📊 Data Overview
    This tab shows the raw data from your selected table. You can:
    - Browse through all records in the table
    - Sort columns by clicking on headers
    - Search through data using the search box
    """)
    st.dataframe(df, use_container_width=True)

with tab2:
    st.markdown("""
    ### 📚 Rule Templates
    Browse through our collection of pre-built data quality rules. Here you can:
    - Filter rules by category and severity
    - View rule descriptions and validation logic
    - Switch between Python and SQL implementations
    - Find the right rules for your data quality needs
    """)
    try:
        import json
        with open('assets/data/rule_templates.json') as f:
            rule_templates_dict = json.load(f)
            
        # Flatten the nested JSON structure
        flattened_rules = []
        
        # Process each rule category
        for category, rules in rule_templates_dict.items():
            if isinstance(rules, list):  # Handle direct list of rules
                for rule in rules:
                    rule['category'] = category  # Add category field
                    flattened_rules.append(rule)
            else:  # Handle nested structure
                for subcategory, subrules in rules.items():
                    for rule in subrules:
                        rule['category'] = category
                        rule['subcategory'] = subcategory
                        flattened_rules.append(rule)
        
        # Convert to DataFrame
        rule_templates_df = pd.DataFrame(flattened_rules)
        
        # Add filter controls
        col1, col2, col3 = st.columns(3)
        
        # Category filter
        categories = ['All'] + list(rule_templates_df['category'].unique())
        selected_category = col1.selectbox('Filter by Category', categories)
        
        # Severity filter 
        severities = ['All'] + list(rule_templates_df['severity'].unique())
        selected_severity = col2.selectbox('Filter by Severity', severities)
        
        # Code view radio buttons
        code_view = col3.radio('Code View', ['Python', 'SQL'], horizontal=True)
        
        # Apply filters
        filtered_df = rule_templates_df.copy()
        
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
            
        if selected_severity != 'All':
            filtered_df = filtered_df[filtered_df['severity'] == selected_severity]
            
        # Show/hide validation code columns based on selection
        if code_view == 'Python':
            # Drop SQL validation column
            cols = [col for col in filtered_df.columns if col != 'validation_code_sql']
        else:
            # Drop Python validation column
            cols = [col for col in filtered_df.columns if col != 'validation_code']
            
        filtered_df = filtered_df[cols]
        st.dataframe(filtered_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading rule templates: {str(e)}")

with tab3:
    st.markdown("""
    ### ⚙️ Rule Configuration
    Configure and manage your data quality rules. This page allows you to:
    - Select tables and columns to apply rules to
    - Filter and choose from available rules
    - Save multiple rules at once
    - View and manage your active configurations
    - Monitor rule statistics and coverage
    """)
    try:
        # Initialize session state for configurations if not exists
        if 'configurations' not in st.session_state:
            try:
                with open('rule_configurations.json', 'r') as f:
                    st.session_state.configurations = json.load(f)
            except FileNotFoundError:
                st.session_state.configurations = {'rule_configs': {}}

        # Create two columns for the main layout
        left_col, right_col = st.columns([2, 3])

        with left_col:
            st.markdown("### 📝 Configure New Rule")
            
            # Table and Column Selection in a container
            with st.container():
                st.markdown("#### Select Data Source")
                config_table = st.selectbox('Table', table_names, key='config_table_select')
                
                # Get columns for selected table
                conn = sqlite3.connect('assets/data/hr_database.sqlite')
                config_df = pd.read_sql_query(f"SELECT * FROM {config_table}", conn)
                conn.close()
                
                selected_column = st.selectbox('Column', config_df.columns, key='config_column_select')
            
            # Rule filtering in a container
            with st.container():
                st.markdown("#### Filter Rules")
                categories = ['All'] + list(rule_templates_df['category'].unique())
                rule_category = st.selectbox(
                    'Category',
                    categories,
                    key='temp_rule_category',
                    on_change=update_rule_filters
                )
                
                severities = ['All'] + list(rule_templates_df['severity'].unique())
                rule_severity = st.selectbox(
                    'Severity',
                    severities,
                    key='temp_rule_severity',
                    on_change=update_rule_filters
                )

        with right_col:
            st.markdown("### 📋 Available Rules")
            
            # Filter and display rules
            filtered_rules = rule_templates_df.copy()
            if st.session_state.rule_category != 'All':
                filtered_rules = filtered_rules[filtered_rules['category'] == st.session_state.rule_category]
            if st.session_state.rule_severity != 'All':
                filtered_rules = filtered_rules[filtered_rules['severity'] == st.session_state.rule_severity]
            
            st.session_state.filtered_rules = filtered_rules
            
            # Display filtered rules in a scrollable container
            st.dataframe(
                filtered_rules[['id', 'name', 'description', 'category', 'severity']], 
                use_container_width=True,
                height=300
            )
            
            # Rule selection and actions
            available_rule_ids = filtered_rules['id'].unique()
            if len(available_rule_ids) > 0:
                selected_rules = st.multiselect(
                    'Select Rules to Configure',
                    available_rule_ids,
                    format_func=lambda x: f"{x} - {filtered_rules[filtered_rules['id'] == x].iloc[0]['name']}"
                )
                
                col1, col2 = st.columns(2)
                if col1.button('💾 Save Selected', use_container_width=True):
                    for rule_id in selected_rules:
                        rule_data = filtered_rules[filtered_rules['id'] == rule_id].iloc[0]
                        save_rule_configuration(rule_data, config_table, selected_column)
                    st.success(f'Successfully saved {len(selected_rules)} rule configurations!')
                
                if col2.button('💾 Save All Filtered', use_container_width=True):
                    for _, rule_data in filtered_rules.iterrows():
                        save_rule_configuration(rule_data, config_table, selected_column)
                    st.success(f'Successfully saved {len(filtered_rules)} rule configurations!')

        # Display current configurations section
        st.markdown("---")
        if st.session_state.configurations['rule_configs']:
            # Configuration management header with metrics
            st.markdown("### 🔧 Active Configurations")
            configs_df = pd.DataFrame(st.session_state.configurations['rule_configs']).T
            
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Rules", len(configs_df))
            col2.metric("Critical Rules", len(configs_df[configs_df['severity'] == 'Critical']))
            col3.metric("Tables Covered", configs_df['table_name'].nunique())
            col4.metric("Active Rules", len(configs_df[configs_df.get('is_active', True) == True]))
            
            # Configuration filters
            with st.expander("🔍 Filter Configurations", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                tables = ['All'] + list(configs_df['table_name'].unique())
                selected_table_filter = col1.selectbox('Table', tables, key='config_table_filter')
                
                columns = ['All'] + list(configs_df['column_name'].unique())
                selected_col = col2.selectbox('Column', columns, key='config_col')
                
                categories = ['All'] + list(configs_df['category'].unique())
                selected_cat = col3.selectbox('Category', categories, key='config_cat')
                
                severities = ['All'] + list(configs_df['severity'].unique())
                selected_sev = col4.selectbox('Severity', severities, key='config_sev')
            
            # Apply filters and display active configurations
            filtered_configs = configs_df[configs_df.get('is_active', True) == True].copy()
            if selected_table_filter != 'All':
                filtered_configs = filtered_configs[filtered_configs['table_name'] == selected_table_filter]
            if selected_col != 'All':
                filtered_configs = filtered_configs[filtered_configs['column_name'] == selected_col]
            if selected_cat != 'All':
                filtered_configs = filtered_configs[filtered_configs['category'] == selected_cat]
            if selected_sev != 'All':
                filtered_configs = filtered_configs[filtered_configs['severity'] == selected_sev]
            
            # Display active configurations with actions
            if not filtered_configs.empty:
                for idx, row in filtered_configs.iterrows():
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(
                                f"**{row['rule_id']} - {row['table_name']}.{row['column_name']}**  \n"
                                f"🏷️ {row['category']} | ⚠️ {row['severity']}"
                            )
                        with col2:
                            if st.button('❌ Deactivate', key=f"deact_{idx}", use_container_width=True):
                                if deactivate_configuration(idx):
                                    st.success(f"Deactivated: {idx}")
                                    st.rerun()
                        st.markdown("---")
                
                # Deactivate all button
                if st.button('❌ Deactivate All Rules', type='secondary', use_container_width=True):
                    with st.expander("⚠️ Confirm Deactivation", expanded=True):
                        st.warning("Are you sure you want to deactivate all rules?")
                        col1, col2 = st.columns(2)
                        if col1.button("Yes, Deactivate All", use_container_width=True):
                            if deactivate_all_rules():
                                st.success("Successfully deactivated all rules!")
                                st.rerun()
                        if col2.button("Cancel", use_container_width=True):
                            st.rerun()
            else:
                st.info("No active configurations match the current filters.")
        else:
            st.info("No configurations available. Add some rules to get started!")
            
    except Exception as e:
        st.error(f"Error in rule configuration: {str(e)}")

with tab4:
    st.markdown("""
    ### 📈 Statistics & Analytics
    Get insights into your data quality rules. This dashboard shows:
    - Overall rule adoption and coverage
    - Distribution of rules by severity and category
    - Rule usage across different tables
    - Timeline of rule activations and changes
    - Recent updates and modifications
    """)
    try:
        if 'configurations' in st.session_state and st.session_state.configurations['rule_configs']:
            configs_df = pd.DataFrame(st.session_state.configurations['rule_configs']).T
            
            # Summary metrics at the top
            st.markdown("### 📊 Data Quality Rules Overview")
            col1, col2, col3, col4 = st.columns(4)
            total_rules = len(rule_templates_df)
            active_rules = len(configs_df[configs_df.get('is_active', True) == True])
            
            col1.metric("Total Available Rules", total_rules)
            col2.metric("Configured Rules", len(configs_df))
            col3.metric("Active Rules", active_rules)
            col4.metric("Adoption Rate", f"{(active_rules/total_rules)*100:.1f}%")
            
            # Create two main columns for the layout
            left_col, right_col = st.columns([1, 1])
            
            with left_col:
                # Rules by Severity
                with st.container():
                    st.markdown("#### 🎯 Rules by Severity")
                    severity_counts = configs_df['severity'].value_counts()
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.dataframe(severity_counts, use_container_width=True)
                    with col2:
                        fig = px.pie(configs_df, names='severity', title='')
                        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
                
                # Rules by Category
                with st.container():
                    st.markdown("#### 📑 Rules by Category")
                    category_counts = configs_df['category'].value_counts()
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.dataframe(category_counts, use_container_width=True)
                    with col2:
                        fig = px.pie(configs_df, names='category', title='')
                        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
            
            with right_col:
                # Rules by Table
                with st.container():
                    st.markdown("#### 📋 Rules by Table")
                    table_counts = configs_df['table_name'].value_counts()
                    table_data = table_counts.reset_index()
                    table_data.columns = ['table', 'count']
                    
                    fig = px.bar(table_data, 
                               x='count', 
                               y='table',
                               orientation='h',
                               title='')
                    fig.update_layout(
                        margin=dict(t=0, b=0, l=0, r=0),
                        xaxis_title="Number of Rules",
                        yaxis_title="Table Name",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Timeline section
            st.markdown("### 📈 Timeline Analysis")
            
            # Rule activity timeline
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown("#### Rule Activity Over Time")
                # Prepare timeline data
                timeline_df = configs_df.copy()
                timeline_df['activated_at'] = pd.to_datetime(timeline_df['activated_at'])
                timeline_df['deactivated_at'] = pd.to_datetime(timeline_df['deactivated_at'])
                
                # Create activation events
                activations = pd.DataFrame({
                    'date': timeline_df['activated_at'].dt.date,
                    'type': 'Activation',
                    'count': 1
                }).dropna()
                
                # Create deactivation events
                deactivations = pd.DataFrame({
                    'date': timeline_df['deactivated_at'].dt.date,
                    'type': 'Deactivation',
                    'count': 1
                }).dropna()
                
                # Combine events and aggregate
                timeline_data = pd.concat([activations, deactivations])
                if not timeline_data.empty:
                    activity_data = timeline_data.groupby(['date', 'type'])['count'].sum().reset_index()
                    
                    fig = px.line(activity_data, 
                                x='date', 
                                y='count',
                                color='type',
                                title='')
                    fig.update_layout(
                        margin=dict(t=0, b=0, l=0, r=0),
                        xaxis_title="Date",
                        yaxis_title="Number of Rules",
                        legend_title="Action Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No activity data available yet")
            
            with col2:
                st.markdown("#### Recent Updates")
                recent_updates = configs_df.sort_values('last_updated', ascending=False)[
                    ['rule_id', 'table_name', 'column_name', 'last_updated']
                ].head(5)
                st.dataframe(
                    recent_updates,
                    use_container_width=True,
                    hide_index=True
                )
        
        else:
            st.info("👋 No configurations available yet. Start by adding some rules in the Configuration tab!")
            
    except Exception as e:
        st.error(f"Error in detailed statistics: {str(e)}")

with tab5:
    st.markdown("""
    ### 🔍 Data Quality Assessment
    Run quality checks on your data. This tool helps you:
    - Select specific tables and columns to assess
    - Run all active rules against your data
    - View detailed results and violations
    - Get a comprehensive quality report
    - Identify areas needing attention
    """)
    try:
        if 'configurations' in st.session_state and st.session_state.configurations['rule_configs']:
            configs_df = pd.DataFrame(st.session_state.configurations['rule_configs']).T
            active_configs = configs_df[configs_df.get('is_active', True) == True]
            
            # Filter options
            col1, col2 = st.columns(2)
            
            # Table filter
            tables = list(active_configs['table_name'].unique())
            selected_table = col1.selectbox('Select Table to Assess', tables, key='assess_table')
            
            # Column selection (optional)
            columns = ['All'] + list(active_configs[active_configs['table_name'] == selected_table]['column_name'].unique())
            selected_column = col2.selectbox('Select Column (Optional)', columns, key='assess_column')
            
            if st.button('Run Assessment'):
                # Load the data
                conn = sqlite3.connect('assets/data/hr_database.sqlite')
                df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
                conn.close()
                
                with st.spinner('Running quality assessment...'):
                    # Initialize quality checks
                    quality_checks = DataQualityChecks(df)
                    
                    # Get data summary
                    summary = quality_checks.get_basic_stats()
                    st.markdown("### Data Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Records", summary['row_count'])
                    col2.metric("Total Columns", summary['column_count'])
                    col3.metric("Memory Usage (MB)", f"{summary['memory_usage'] / 1024 / 1024:.2f}")
                    
                    # Run assessment based on selection
                    if selected_column != 'All':
                        # Define checks configuration
                        checks_config = quality_checks._get_default_checks_config(selected_column)
                        
                        # Run column checks
                        results = quality_checks.run_column_checks(selected_column, checks_config)
                        
                        st.markdown("#### Column Quality Checks")
                        for check in results['checks']:
                            with st.expander(f"Check: {check['check_name']}", expanded=True):
                                # Show check results
                                if check['success']:
                                    st.success("✅ Check passed")
                                else:
                                    st.error("❌ Check failed")
                                st.json(check['result'])
                    else:
                        # Run table-level assessment
                        basic_stats = quality_checks.get_basic_stats()
                        st.markdown("#### Table Profile")
                        st.json(basic_stats)
                        
                        # Run relationship checks for numeric columns
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 1:
                            st.markdown("#### Correlation Analysis")
                            correlations = []
                            for col1 in numeric_cols:
                                for col2 in numeric_cols:
                                    if col1 < col2:  # Avoid duplicate combinations
                                        result = quality_checks.check_relationship(col1, col2)
                                        correlations.append(result)
                            
                            # Create correlation matrix
                            corr_matrix = df[numeric_cols].corr()
                            fig = px.imshow(corr_matrix,
                                          title='Correlation Heatmap',
                                          labels=dict(color="Correlation"))
                            st.plotly_chart(fig)

                    
                    # Run custom rules
                    st.markdown("### Custom Rule Results")
                    table_rules = active_configs[active_configs['table_name'] == selected_table]
                    if selected_column != 'All':
                        table_rules = table_rules[table_rules['column_name'] == selected_column]
                    
                    for _, rule in table_rules.iterrows():
                        result = quality_checks.run_rule_validation(rule)
                        with st.expander(f"Rule: {result['rule_id']} ({result['severity']})", expanded=True):
                            if 'error' in result:
                                st.error(f"Error executing rule: {result['error']}")
                            else:
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Total Records", result['total_records'])
                                col2.metric("Violations", result['violations'])
                                col3.metric("Compliance Rate", f"{result['compliance_rate']:.1f}%")
                                
                                if result['violations'] > 0:
                                    st.markdown("**Sample Violations:**")
                                    try:
                                        violations_mask = eval(result['validation_code'], 
                                                            {'__builtins__': {}}, 
                                                            {'df': df, 'pd': pd, 'np': np})
                                        if isinstance(violations_mask, pd.Series):
                                            violations_df = df[violations_mask].head()
                                            st.dataframe(violations_df, use_container_width=True)
                                    except Exception as e:
                                        st.error(f"Error showing sample violations: {str(e)}")

        
        else:
            st.warning("No active rule configurations available. Please configure some rules first.")
            
    except Exception as e:
        st.error(f"Error in assessment execution: {str(e)}")
