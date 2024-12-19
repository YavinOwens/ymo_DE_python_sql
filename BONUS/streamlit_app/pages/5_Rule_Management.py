import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.utils import initialize_session_state
from utils.data_loader import DataLoader
from config import RULE_TEMPLATES_PATH

def flatten_rule_templates(templates_dict):
    """Flatten the nested rule templates structure into a single list."""
    flattened = []
    # Keep track of rule IDs to handle duplicates
    seen_ids = {}
    
    for category_key, rules in templates_dict.items():
        if isinstance(rules, list):  # Ensure we're dealing with a list of rules
            for rule in rules:
                if isinstance(rule, dict):  # Ensure each rule is a dictionary
                    # Create a copy of the rule to avoid modifying the original
                    rule_copy = rule.copy()
                    
                    # Handle duplicate IDs by adding a suffix
                    original_id = rule_copy.get('id', 'unknown')
                    if original_id in seen_ids:
                        seen_ids[original_id] += 1
                        rule_copy['id'] = f"{original_id}_{seen_ids[original_id]}"
                    else:
                        seen_ids[original_id] = 0
                        rule_copy['id'] = original_id
                    
                    # Add or update category information
                    rule_copy['category'] = rule_copy.get('category', category_key)
                    rule_copy['category_name'] = category_key.replace('_', ' ').title()
                    # Ensure all required fields exist
                    rule_copy['active'] = rule_copy.get('active', True)
                    rule_copy['severity'] = rule_copy.get('severity', 'Medium')
                    rule_copy['validation_code'] = rule_copy.get('validation_code', '')
                    rule_copy['message'] = rule_copy.get('message', 'No message provided')
                    rule_copy['type'] = rule_copy.get('type', 'Unknown')
                    flattened.append(rule_copy)
    return flattened

def initialize_rule_state(templates):
    """Initialize the rule state in session state if not already present."""
    if 'rule_states' not in st.session_state:
        st.session_state.rule_states = {
            rule['id']: rule['active'] for rule in templates
        }

def toggle_rule(rule_id):
    """Toggle the active state of a rule and record the activity."""
    new_state = not st.session_state.rule_states[rule_id]
    st.session_state.rule_states[rule_id] = new_state
    
    # Record activity
    if 'rule_activity' not in st.session_state:
        st.session_state.rule_activity = []
    
    activity = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'rule_id': rule_id,
        'action': 'Activated' if new_state else 'Deactivated'
    }
    st.session_state.rule_activity.insert(0, activity)
    
    # Keep only the last 10 activities
    st.session_state.rule_activity = st.session_state.rule_activity[:10]

def calculate_rule_statistics(df_templates):
    """Calculate statistics for rule templates."""
    stats = {
        'total_rules': len(df_templates),
        'active_rules': len(df_templates[df_templates['active'] == True]),
        'inactive_rules': len(df_templates[df_templates['active'] == False]),
        'rules_by_category': df_templates['category_name'].value_counts().to_dict(),
        'rules_by_severity': df_templates['severity'].value_counts().to_dict(),
        'activation_rate': (len(df_templates[df_templates['active'] == True]) / len(df_templates) * 100) if len(df_templates) > 0 else 0
    }
    return stats

def show():
    st.title("Rule Management")
    
    # Initialize session state
    initialize_session_state()
    
    # Check if rule templates file exists
    if not os.path.exists(RULE_TEMPLATES_PATH):
        st.error(f"Rule templates file not found at: {RULE_TEMPLATES_PATH}")
        return
    
    # Load rule templates with error handling
    try:
        with open(RULE_TEMPLATES_PATH, 'r') as f:
            templates_dict = json.load(f)
        if not templates_dict:
            st.warning("Rule templates file is empty.")
            return
            
        # Flatten the templates structure
        templates = flatten_rule_templates(templates_dict)
        
        if not templates:
            st.warning("No valid rule templates found.")
            return
            
        # Initialize rule states
        initialize_rule_state(templates)
        
        # Convert templates to DataFrame for better display
        df_templates = pd.DataFrame(templates)
        
        # Calculate statistics
        stats = calculate_rule_statistics(df_templates)
            
    except json.JSONDecodeError as e:
        st.error(f"Error parsing rule templates file: {str(e)}")
        return
    except Exception as e:
        st.error(f"Error loading rule templates: {str(e)}")
        return
    
    # Create tabs for different rule management sections
    tab1, tab2, tab3 = st.tabs(["Rule Statistics", "Rule Templates", "Rule Configuration"])
    
    with tab1:
        st.subheader("Rule Statistics Dashboard")
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rules", stats['total_rules'])
        with col2:
            st.metric("Active Rules", stats['active_rules'])
        with col3:
            st.metric("Inactive Rules", stats['inactive_rules'])
        with col4:
            st.metric("Activation Rate", f"{stats['activation_rate']:.1f}%")
        
        # Create visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Rules by Category
            fig_category = px.pie(
                values=list(stats['rules_by_category'].values()),
                names=list(stats['rules_by_category'].keys()),
                title="Rules by Category"
            )
            st.plotly_chart(fig_category, use_container_width=True)
        
        with col2:
            # Rules by Severity
            fig_severity = px.bar(
                x=list(stats['rules_by_severity'].keys()),
                y=list(stats['rules_by_severity'].values()),
                title="Rules by Severity",
                labels={'x': 'Severity', 'y': 'Count'}
            )
            st.plotly_chart(fig_severity, use_container_width=True)
        
        # Recent Activity
        st.subheader("Recent Activity")
        if 'rule_activity' not in st.session_state:
            st.session_state.rule_activity = []
        
        activity_df = pd.DataFrame(st.session_state.rule_activity)
        if not activity_df.empty:
            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No recent activity recorded")
    
    with tab2:
        st.subheader("Available Rule Templates")
        
        # Convert templates to DataFrame for better display
        df_templates = pd.DataFrame(templates)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.multiselect(
                "Filter by Category",
                options=sorted(df_templates['category_name'].unique()),
                default=[]
            )
        with col2:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=sorted(df_templates['severity'].unique()),
                default=[]
            )
        with col3:
            active_filter = st.multiselect(
                "Filter by Status",
                options=["Active", "Inactive"],
                default=[]
            )
        
        # Apply filters
        filtered_df = df_templates.copy()
        if category_filter:
            filtered_df = filtered_df[filtered_df['category_name'].isin(category_filter)]
        if severity_filter:
            filtered_df = filtered_df[filtered_df['severity'].isin(severity_filter)]
        if active_filter:
            is_active = [x == "Active" for x in active_filter]
            filtered_df = filtered_df[filtered_df['active'].isin(is_active)]
        
        # Display rules grouped by category
        st.write("### Rule Templates")
        
        # Create tabs for each category
        categories = sorted(filtered_df['category_name'].unique())
        if categories:
            category_tabs = st.tabs(categories)
            
            for cat_tab, category in zip(category_tabs, categories):
                with cat_tab:
                    category_rules = filtered_df[filtered_df['category_name'] == category]
                    
                    for idx, rule in category_rules.iterrows():
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**{rule['name']}**")
                            st.write(f"_{rule['description']}_")
                        
                        with col2:
                            st.write(f"**Severity:** {rule['severity']}")
                            st.write(f"**Type:** {rule.get('type', 'N/A')}")
                        
                        with col3:
                            st.write(f"**ID:** {rule['id']}")
                            if rule.get('validation_code'):
                                st.code(rule['validation_code'], language='python')
                        
                        with col4:
                            # Toggle button for rule activation with unique key
                            is_active = st.toggle(
                                "Active",
                                value=st.session_state.rule_states[rule['id']],
                                key=f"toggle_{category}_{idx}_{rule['id']}",
                                on_change=toggle_rule,
                                args=(rule['id'],)
                            )
        
        # Add a button to save rule states
        st.markdown("---")
        if st.button("💾 Save Rule Configuration"):
            st.session_state.rule_configs = [
                {
                    'id': rule_id,
                    'active': active
                }
                for rule_id, active in st.session_state.rule_states.items()
            ]
            st.success("Rule configuration saved successfully!")
            st.json(st.session_state.rule_configs)
    
    with tab3:
        st.subheader("Rule Execution Configuration")
        
        # Load available tables
        try:
            data_loader = DataLoader()
            tables = data_loader.get_table_names()
            
            if not tables:
                st.info("No tables available for rule configuration.")
                return
            
            # Table selection
            selected_table = st.selectbox(
                "Select a table",
                tables,
                key="rule_config_table"
            )
            
            if selected_table:
                # Load table schema
                schema = data_loader.get_table_schema(selected_table)
                
                if schema:
                    # Get active rules
                    active_rules = [
                        rule for rule in templates
                        if st.session_state.rule_states[rule['id']]
                    ]
                    
                    if not active_rules:
                        st.warning("No active rules available. Please enable rules in the Rule Templates tab.")
                        return
                    
                    st.write(f"### Active Rules for {selected_table}")
                    
                    # Create tabs for active rules
                    rule_tabs = st.tabs([f"{rule['name']}" for rule in active_rules])
                    
                    for rule_tab, rule in zip(rule_tabs, active_rules):
                        with rule_tab:
                            st.write(f"**Description:** {rule['description']}")
                            st.write(f"**Severity:** {rule['severity']}")
                            
                            # Column selection if needed
                            if 'column_name' in rule.get('validation_code', ''):
                                selected_column = st.selectbox(
                                    "Select Column",
                                    [c['name'] for c in schema['columns']],
                                    key=f"col_{rule['id']}"
                                )
                            
                            st.code(rule['validation_code'], language='python')
                    
                    # Add execution button
                    st.markdown("---")
                    if st.button("▶️ Execute Rules"):
                        st.info("Rule execution started...")
                        # Here you would implement the rule execution logic
                        st.success("Rules executed successfully!")
                        
                else:
                    st.error(f"Error loading schema for table: {selected_table}")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    show() 