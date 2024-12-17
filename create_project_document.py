import pandas as pd
from datetime import datetime, timedelta

# File paths
template_path = 'project plan template.xlsx'
learning_plan_path = 'Python_learning_Plan.xlsx'
output_csv = 'project_de_plan.csv'

# Read the Excel files
template_df = pd.read_excel(template_path, sheet_name='Plan')
learning_plan_df = pd.read_excel(learning_plan_path, sheet_name='30_Day_Plan')

# Create a new DataFrame for the project plan
project_plan = []

# Get today's date as the starting point
start_date = datetime.now()

# Process each learning plan item
for index, row in learning_plan_df.iterrows():
    if pd.notna(row['Topic']):  # Only process rows with actual content
        task_date = start_date + timedelta(weeks=int(row['Week'].split()[1])-1)
        
        project_plan.append({
            'Task': row['Topic'],
            'Priority': 'P1',  # Default priority
            'Owner': 'ymo',  # Default owner
            'Status': 'Not started',
            'Start date': task_date.strftime('%Y-%m-%d'),
            'End date': (task_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            'Milestone': '',
            'Deliverable': '',
            'Notes': f"Effort: {row.get('Effort', '')}, Estimated Days: {row.get('Estimated Days', '')}"
        })

# Convert to DataFrame
final_df = pd.DataFrame(project_plan)

# Save to CSV
final_df.to_csv(output_csv, index=False)
print(f"Project plan has been created and saved to {output_csv}")
