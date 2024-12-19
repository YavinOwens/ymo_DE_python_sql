import json
import sys

def validate_json_file(file_path):
    """
    Validates a JSON file and provides detailed error information
    Returns (is_valid, error_message)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            try:
                json.loads(content)
                return True, "JSON is valid"
            except json.JSONDecodeError as e:
                # Get the problematic line
                lines = content.split('\n')
                line_no = e.lineno
                
                # Get more context around line 2639 (20 lines before and after)
                error_context = []
                
                # First show the immediate error context
                start = max(0, line_no - 6)
                end = min(len(lines), line_no + 5)
                for i in range(start, end):
                    prefix = "-> " if i == line_no - 1 else "   "
                    error_context.append(f"{prefix}{i+1}: {lines[i]}")

                # If error is near line 2639, show that context too
                if abs(line_no - 2639) < 50:  # If error is within 50 lines of 2639
                    error_context.append("\nContext around line 2639:")
                    start_2639 = max(0, 2639 - 10)
                    end_2639 = min(len(lines), 2639 + 10)
                    for i in range(start_2639, end_2639):
                        prefix = ">> " if i == 2638 else "   "  # 2639 - 1 because lines are 0-based
                        error_context.append(f"{prefix}{i+1}: {lines[i]}")
                
                error_context = "\n".join(error_context)
                
                # Add suggestions based on the error
                suggestions = []
                if "Expecting ',' delimiter" in str(e):
                    suggestions.append("- Check for missing comma between objects")
                    suggestions.append("- Make sure there's no comma after the last item in an array")
                    suggestions.append("- Verify that all objects are properly separated")
                elif "Expecting property name" in str(e):
                    suggestions.append("- Check for missing quotes around property names")
                    suggestions.append("- Verify that all properties have values")
                
                error_message = f"""
JSON Error at line {e.lineno}, column {e.colno}
Error: {str(e)}

Context:
{error_context}

Possible fixes:
{chr(10).join(suggestions)}
                """
                return False, error_message
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

if __name__ == "__main__":
    file_path = 'BONUS/assets/data/rule_templates.json'
    is_valid, message = validate_json_file(file_path)
    
    if is_valid:
        print("✅ JSON file is valid")
    else:
        print("❌ JSON validation failed:")
        print(message) 