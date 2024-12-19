import json
import re

def fix_json_file():
    try:
        with open('BONUS/assets/data/rule_templates.json', 'r') as f:
            content = f.read()
            
        # Fix common JSON issues
        
        # 1. Fix missing commas between objects
        content = re.sub(r'}\s*{', '},{', content)
        content = re.sub(r']\s*\[', '],[', content)
        
        # 2. Remove extra commas before closing brackets
        content = re.sub(r',(\s*})', r'\1', content)
        content = re.sub(r',(\s*])', r'\1', content)
        
        # Try to parse the fixed content
        try:
            json_data = json.loads(content)
            
            # Write the fixed content back
            with open('BONUS/assets/data/rule_templates_fixed.json', 'w') as f:
                json.dump(json_data, f, indent=4)
            
            print("✅ Fixed JSON written to rule_templates_fixed.json")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Still invalid JSON after fixes: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Attempting to fix rule_templates.json...")
    fix_json_file() 