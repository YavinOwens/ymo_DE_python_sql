import streamlit as st 
import pandas as pd
import seaborn as sns
import plotly.express as px
import sqlite3



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

# with st.expander("Data Preview for " + selected_table):
#     st.dataframe(df)

# Add tabs for different views
tab1, tab2, tab3 = st.tabs(["Data", "Rule Templates", "Rule Configuration"])

with tab1:
    # Move the existing dataframe display here
    st.dataframe(df)

with tab2:
    # Load and display rule templates
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
        st.dataframe(filtered_df)
        
    except Exception as e:
        st.error(f"Error loading rule templates: {str(e)}")

with tab3:
    try:
        config = None
        # Create a form
        with st.form("rule_config_form"):
            # Column selector
            selected_column = st.selectbox('Select Column', df.columns)
            
            # Rule selector  
            rule_id = st.selectbox('Select Rule', rule_templates_df['id'].unique())
            
            # Form submit button
            submitted = st.form_submit_button('Save Configuration')
            
            if submitted:
                # Create configuration dictionary with index
                config_data = {
                    'rule_id': [rule_id],
                    'table_name': [selected_table],
                    'column_name': [selected_column],
                    'last_updated': [pd.Timestamp.now().isoformat()]
                }
                config = pd.DataFrame(config_data)
            
            # Load existing configurations or create new
            try:
                with open('rule_configurations.json', 'r') as f:
                    configurations = json.load(f)
            except FileNotFoundError:
                configurations = {'rule_configs': {}}
            
            # Update configuration
            configurations['rule_configs'][rule_id] = config
            
            # Save updated configurations
            with open('rule_configurations.json', 'w') as f:
                json.dump(configurations, f, indent=2)
            
            st.success('Configuration saved successfully!')
            
            # Display current configurations
            configs_df = pd.DataFrame(configurations['rule_configs']).T
            st.subheader('Current Configurations')
            st.dataframe(configs_df)
            
    except Exception as e:
        st.error(f"Error in rule configuration: {str(e)}")
