import streamlit as st
import json
import pandas as pd
from datetime import datetime
import traceback
from utils.json_validator import validate_json_file

def load_rule_templates():
    """Load and validate rule templates with error handling"""
    try:
        # Validate JSON first
        is_valid, error_message = validate_json_file('assets/data/rule_templates.json')
        if not is_valid:
            st.error("Invalid JSON in rule templates file:")
            st.code(error_message)
            
            # Show specific fix suggestion
            if "Expecting ',' delimiter" in error_message:
                st.warning("""
                Common fixes:
                1. Check for missing commas between objects
                2. Remove empty objects from arrays
                3. Remove trailing commas
                4. Ensure all arrays and objects are properly closed
                """)
            return {}
            
        with open('assets/data/rule_templates.json', 'r') as f:
            data = json.load(f)
            
            # Clean up empty objects from arrays
            for category in data:
                if isinstance(data[category], list):
                    data[category] = [rule for rule in data[category] if rule]  # Remove empty objects
            
            return data
            
    except FileNotFoundError:
        st.error("Rule templates file not found")
        return {}
    except Exception as e:
        st.error(f"Error loading rule templates: {str(e)}")
        st.code(traceback.format_exc())
        return {}

def display_rule_details(rule):
    """Display detailed information about a rule"""
    try:
        st.write(f"**Rule ID:** {rule['id']}")
        st.write(f"**Name:** {rule['name']}")
        st.write(f"**Description:** {rule['description']}")
        st.write(f"**Category:** {rule.get('category', 'N/A')}")
        st.write(f"**Type:** {rule.get('type', 'N/A')}")
        st.write(f"**Severity:** {rule['severity']}")
        st.write(f"**Status:** {'Active' if rule['active'] else 'Inactive'}")
        
        # Display validation code
        with st.expander("View Python Validation Code"):
            st.code(rule['validation_code'], language='python')
        
        if 'validation_code_sql' in rule:
            with st.expander("View SQL Validation Code"):
                st.code(rule['validation_code_sql'], language='sql')
        
        # Calculate and display total active duration
        if 'activation_history' in rule:
            total_duration = 0
            for period in rule['activation_history']:
                start = datetime.strptime(period['activated_date'], '%Y-%m-%d')
                if period['deactivated_date']:
                    end = datetime.strptime(period['deactivated_date'], '%Y-%m-%d')
                else:
                    end = datetime.now()
                duration = (end - start).days
                total_duration += duration
            
            st.write(f"**Total Active Duration:** {total_duration} days")
            
            # Display activation history
            with st.expander("View Activation History"):
                for period in rule['activation_history']:
                    activated = datetime.strptime(period['activated_date'], '%Y-%m-%d')
                    if period['deactivated_date']:
                        deactivated = datetime.strptime(period['deactivated_date'], '%Y-%m-%d')
                        st.write(f"- Activated: {activated.strftime('%d %B %Y')} → Deactivated: {deactivated.strftime('%d %B %Y')}")
                    else:
                        st.write(f"- Activated: {activated.strftime('%d %B %Y')} → Current")
    except Exception as e:
        st.error(f"Error displaying rule details: {str(e)}")
        st.code(traceback.format_exc())

def get_rules_from_category(rules_data, category_key):
    """Extract rules from the flattened structure"""
    return rules_data.get(category_key, [])

def app():
    st.title("Rule Management")
    
    try:
        # Load rule templates
        rules_data = load_rule_templates()
        
        if not rules_data:
            st.warning("No rules found. Please check the rule templates file.")
            return

        # Create a list of all rule categories
        rule_categories = [
            "GDPR Rules",
            "Employee Table Rules",
            "Payroll Table Rules",
            "Leave Table Rules",
            "Performance Table Rules",
            "Training Table Rules",
            "Certification Table Rules",
            "Cross Table Rules",
            "Complex Business Rules"
        ]
        
        # Category mapping (simplified for flat structure)
        category_mapping = {
            "GDPR Rules": "gdpr_rules",
            "Employee Table Rules": "employee_table_rules",
            "Payroll Table Rules": "payroll_table_rules",
            "Leave Table Rules": "leave_table_rules",
            "Performance Table Rules": "performance_table_rules",
            "Training Table Rules": "training_table_rules",
            "Certification Table Rules": "certification_table_rules",
            "Cross Table Rules": "cross_table_rules",
            "Complex Business Rules": "complex_business_rules"
        }
        
        # Add filters in sidebar
        with st.sidebar:
            st.header("Filters")
            selected_category = st.selectbox("Select Rule Category", rule_categories)
            show_active_only = st.checkbox("Show Active Rules Only")
            search_term = st.text_input("Search Rules", "")
        
        # Get rules for selected category
        category_key = category_mapping[selected_category]
        rules = get_rules_from_category(rules_data, category_key)
        
        # Apply filters
        if show_active_only:
            rules = [rule for rule in rules if rule['active']]
        
        if search_term:
            rules = [rule for rule in rules if 
                    search_term.lower() in rule['name'].lower() or 
                    search_term.lower() in rule['description'].lower()]
        
        # Display rules summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rules", len(rules))
        with col2:
            st.metric("Active Rules", len([r for r in rules if r['active']]))
        with col3:
            st.metric("Critical Rules", len([r for r in rules if r['severity'] == "Critical"]))
        
        # Display rules table
        if rules:
            rules_df = pd.DataFrame([{
                'ID': rule['id'],
                'Name': rule['name'],
                'Severity': rule['severity'],
                'Status': 'Active' if rule['active'] else 'Inactive'
            } for rule in rules])
            
            st.dataframe(rules_df, use_container_width=True)
            
            # Rule details section
            st.subheader("Rule Details")
            selected_rule_id = st.selectbox("Select a rule to view details", rules_df['ID'])
            
            selected_rule = next((rule for rule in rules if rule['id'] == selected_rule_id), None)
            if selected_rule:
                display_rule_details(selected_rule)
        else:
            st.info(f"No rules found for category: {selected_category}")
            
    except Exception as e:
        st.error(f"Error in rule management: {str(e)}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    app()