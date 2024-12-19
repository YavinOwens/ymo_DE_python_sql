import streamlit as st
import json
from datetime import datetime

def load_rule_templates():
    with open('assets/data/rule_templates.json', 'r') as f:
        return json.load(f)

def save_rule_templates(data):
    with open('assets/data/rule_templates.json', 'w') as f:
        json.dump(data, f, indent=4)

def app():
    st.title("Rule Configuration")
    
    # Load rule templates
    rules_data = load_rule_templates()
    
    # Category mapping
    category_mapping = {
        "GDPR Rules": "gdpr_rules",
        "Data Privacy Rules": "data_privacy_rules",
        "Specific Privacy Regulations": "specific_privacy_regulations",
        "Oracle EBS Employee Rules": "oracle_ebs_employee_rules",
        "Data Governance Rules": "data_governance_rules",
        "Enhanced Data Governance Rules": "enhanced_data_governance_rules"
    }
    
    # Category selection
    selected_category = st.selectbox("Select Rule Category", list(category_mapping.keys()))
    category_key = category_mapping[selected_category]
    
    # Get rules for selected category
    rules = rules_data.get(category_key, [])
    
    # Rule selection
    if rules:
        rule_ids = [rule['id'] for rule in rules]
        selected_rule_id = st.selectbox("Select Rule to Configure", rule_ids)
        
        # Get selected rule
        selected_rule = next((rule for rule in rules if rule['id'] == selected_rule_id), None)
        
        if selected_rule:
            with st.form("rule_configuration"):
                # Basic rule configuration
                name = st.text_input("Rule Name", selected_rule['name'])
                description = st.text_area("Description", selected_rule['description'])
                severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], 
                                     ["Low", "Medium", "High", "Critical"].index(selected_rule['severity']))
                active = st.checkbox("Active", selected_rule['active'])
                
                # Code configuration
                validation_code = st.text_area("Python Validation Code", selected_rule['validation_code'])
                validation_code_sql = st.text_area("SQL Validation Code", 
                                                 selected_rule.get('validation_code_sql', ''))
                
                if st.form_submit_button("Save Changes"):
                    # Update rule
                    selected_rule['name'] = name
                    selected_rule['description'] = description
                    selected_rule['severity'] = severity
                    
                    # Handle activation status change
                    if active != selected_rule['active']:
                        selected_rule['active'] = active
                        current_date = datetime.now().strftime('%Y-%m-%d')
                        
                        if active:
                            # Activation
                            selected_rule['activation_history'].append({
                                "activated_date": current_date,
                                "deactivated_date": None
                            })
                        else:
                            # Deactivation
                            if selected_rule['activation_history']:
                                last_activation = selected_rule['activation_history'][-1]
                                if last_activation['deactivated_date'] is None:
                                    last_activation['deactivated_date'] = current_date
                    
                    selected_rule['validation_code'] = validation_code
                    selected_rule['validation_code_sql'] = validation_code_sql
                    
                    # Save changes
                    save_rule_templates(rules_data)
                    st.success("Rule configuration updated successfully!")
    else:
        st.write(f"No rules found for category: {selected_category}")

if __name__ == "__main__":
    app() 