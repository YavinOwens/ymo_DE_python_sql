import json

def clean_rule_templates():
    """Clean up the rule templates JSON file by removing empty objects and fixing common issues"""
    try:
        with open('assets/data/rule_templates.json', 'r') as f:
            data = json.load(f)
        
        # Clean up empty objects from arrays
        for category in data:
            if isinstance(data[category], list):
                data[category] = [rule for rule in data[category] if rule]
        
        # Write back the cleaned data
        with open('assets/data/rule_templates.json', 'w') as f:
            json.dump(data, f, indent=4)
            
        print("✅ Successfully cleaned rule templates file")
        return True
    except Exception as e:
        print(f"❌ Error cleaning rule templates: {str(e)}")
        return False

if __name__ == "__main__":
    clean_rule_templates() 