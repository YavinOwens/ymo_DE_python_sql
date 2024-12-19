import json

def flatten_rule_templates():
    try:
        with open('assets/data/rule_templates.json', 'r') as f:
            data = json.load(f)
        
        # Create flattened structure
        flattened_structure = {
            "gdpr_rules": data.get("gdpr_rules", []),
            "employee_table_rules": data.get("table_specific_rules", {}).get("employee_table_rules", []),
            "payroll_table_rules": data.get("table_specific_rules", {}).get("payroll_table_rules", []),
            "leave_table_rules": data.get("table_specific_rules", {}).get("leave_table_rules", []),
            "performance_table_rules": data.get("table_specific_rules", {}).get("performance_table_rules", []),
            "training_table_rules": data.get("table_specific_rules", {}).get("training_table_rules", []),
            "certification_table_rules": data.get("table_specific_rules", {}).get("certification_table_rules", []),
            "cross_table_rules": data.get("cross_table_rules", []),
            "complex_business_rules": data.get("complex_business_rules", [])
        }
        
        # Write the flattened structure back
        with open('assets/data/rule_templates.json', 'w') as f:
            json.dump(flattened_structure, f, indent=4)
            
        print("✅ Successfully flattened rule templates structure")
        return True
        
    except Exception as e:
        print(f"❌ Error flattening rule templates structure: {str(e)}")
        return False

if __name__ == "__main__":
    flatten_rule_templates() 