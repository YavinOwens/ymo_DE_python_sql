import json

def check_rule_templates():
    try:
        with open('BONUS/assets/data/rule_templates.json', 'r') as f:
            content = f.readlines()
            
            # Check around line 2639 (20 lines before and after)
            start = max(0, 2639 - 20)
            end = min(len(content), 2639 + 20)
            
            print("\nExamining lines", start, "to", end, ":\n")
            for i in range(start, end):
                line = content[i].rstrip()
                line_num = i + 1
                prefix = ">>> " if line_num == 2639 else "    "
                print(f"{prefix}{line_num}: {line}")
                
                # Check for common JSON syntax issues
                stripped_line = line.strip()
                if stripped_line:
                    # Check for object endings without commas
                    if stripped_line == '}' and i + 1 < len(content):
                        next_line = content[i + 1].strip()
                        if next_line.startswith('{'):
                            print(f"WARNING: Possible missing comma after line {line_num}")
                    
                    # Check for array endings without commas
                    if stripped_line == ']' and i + 1 < len(content):
                        next_line = content[i + 1].strip()
                        if next_line.startswith('['):
                            print(f"WARNING: Possible missing comma after line {line_num}")
                    
                    # Check for extra commas
                    if stripped_line.endswith(','):
                        next_line = content[i + 1].strip()
                        if next_line.startswith(']') or next_line.startswith('}'):
                            print(f"WARNING: Possible extra comma on line {line_num}")

    except FileNotFoundError:
        print("Error: rule_templates.json file not found")
    except Exception as e:
        print(f"Error reading file: {str(e)}")

if __name__ == "__main__":
    print("Checking rule_templates.json around line 2639...")
    check_rule_templates() 