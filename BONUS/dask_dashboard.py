# Import required libraries
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objs as go
import uuid
import json
import os

# Constants
SEVERITY_LEVELS = ['Critical', 'High', 'Medium', 'Low']
DEFAULT_PAGE_SIZE = 10

# Load rule templates
def initialize_rule_templates():
    """Initialize rule templates file with default rules if it doesn't exist."""
    default_templates = {
        "validation_rules": [
            {
                "id": "v1",
                "name": "Email Format Check",
                "description": "Validates email format in specified columns",
                "type": "Format",
                "severity": "High",
                "validation_code": "df[column_name].str.match(r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$')",
                "active": True
            },
            {
                "id": "v2",
                "name": "Date Format Check",
                "description": "Validates date format (YYYY-MM-DD)",
                "type": "Format",
                "severity": "Medium",
                "validation_code": "pd.to_datetime(df[column_name], errors='coerce')",
                "active": True
            },
            {
                "id": "v3",
                "name": "SSN Pattern Check",
                "description": "Checks for potential SSN patterns",
                "type": "PII",
                "severity": "Critical",
                "validation_code": "df[column_name].str.match(r'\\b\\d{3}-\\d{2}-\\d{4}\\b')",
                "active": True
            }
        ],
        "data_quality_rules": [
            {
                "id": "dq1",
                "name": "Null Check",
                "description": "Checks for null values in specified columns",
                "type": "Completeness",
                "severity": "High",
                "validation_code": "df[column_name].isnull()",
                "active": True
            },
            {
                "id": "dq2",
                "name": "Duplicate Check",
                "description": "Identifies duplicate records",
                "type": "Uniqueness",
                "severity": "Medium",
                "validation_code": "df.duplicated(subset=[column_name])",
                "active": True
            }
        ]
    }
    
    template_path = os.path.join(os.path.dirname(__file__), 'rule_templates.json')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            json.dump(default_templates, f, indent=4)
        print(f"Created default rule templates at {template_path}")
    return default_templates

def load_rule_templates():
    """Load rule templates from JSON file."""
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'rule_templates.json')
        if not os.path.exists(template_path):
            return initialize_rule_templates()
        
        with open(template_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading rule templates: {str(e)}")
        return initialize_rule_templates()

# Save rule templates
def save_rule_templates(templates):
    """Save rule templates to JSON file."""
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'rule_templates.json')
        with open(template_path, 'w') as f:
            json.dump(templates, f, indent=4)
        return True, "Templates saved successfully"
    except Exception as e:
        print(f"Error saving templates: {str(e)}")
        return False, f"Error saving templates: {str(e)}"

# Update rule status in templates
def update_rule_status_in_templates(category, rule_id, new_status):
    """Update a rule's status in the templates."""
    templates = load_rule_templates()
    if category not in templates:
        return False, f"Category {category} not found"
    
    rule = next((r for r in templates[category] if r['id'] == rule_id), None)
    if not rule:
        return False, f"Rule {rule_id} not found in {category}"
    
    rule['active'] = new_status == 'active'
    success, message = save_rule_templates(templates)
    return success, message

# Initialize rule catalogue with templates
rule_templates = load_rule_templates()
rule_catalogue = {
    'gdpr': rule_templates.get('gdpr_rules', []),
    'data_quality': rule_templates.get('data_quality_rules', []),
    'business_rules': rule_templates.get('business_rules', []),
    'table_level': rule_templates.get('table_level_rules', [])
}

# Initialize recent activities list
recent_activities = [
    {'action': 'Rule Update', 'description': 'Updated data quality rules', 'timestamp': '2024-12-17 21:49'},
    {'action': 'Rule Added', 'description': 'Added new business rule', 'timestamp': '2024-12-17 21:48'}
]

# Activity log to track recent changes
activity_log = []

# Add activity to the activity log with timestamp
def add_activity(action_type, description, activity_type='info'):
    """Add an activity to the activity log with timestamp and type."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    activity_log.append({
        'action': action_type,
        'description': description,
        'timestamp': timestamp,
        'type': activity_type
    })
    # Keep only the last 100 activities
    if len(activity_log) > 100:
        activity_log.pop()

def get_activity_icon_class(activity_type):
    """Get the appropriate icon class and color based on activity type."""
    icon_map = {
        'success': {'icon': 'bi-check-circle-fill', 'color': 'success'},
        'warning': {'icon': 'bi-exclamation-triangle-fill', 'color': 'warning'},
        'info': {'icon': 'bi-info-circle-fill', 'color': 'info'},
        'primary': {'icon': 'bi-plus-circle-fill', 'color': 'primary'}
    }
    return icon_map.get(activity_type, icon_map['info'])

def create_activity_list(num_activities=5):
    """Create a list of recent activities with styled icons."""
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.H5("Recent Activity", className="card-title"),
                html.Div([
                    dbc.ListGroup([
                        dbc.ListGroupItem(
                            [
                                html.I(
                                    className=f"bi {get_activity_icon_class(activity.get('type', 'info'))['icon']} me-2",
                                    style={'color': f"var(--bs-{get_activity_icon_class(activity.get('type', 'info'))['color']})"}
                                ),
                                html.Span(activity['description'])
                            ],
                            className="d-flex align-items-center border-0"
                        )
                        for activity in activity_log[-num_activities:][::-1]  # Show most recent first
                    ], flush=True)
                ], className="activity-list")
            ]),
            className="shadow-sm"
        )
    ])

# Initialize activity log with some sample activities
activity_log.extend([
    {
        'action': 'Data Quality Check',
        'description': 'Data quality check completed',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'type': 'success'
    },
    {
        'action': 'Validation Rules',
        'description': '3 new validation rules added',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'type': 'warning'
    },
    {
        'action': 'Analysis Update',
        'description': 'Updated salary analysis',
        'timestamp': datetime.now().strftime("%Y-%m-d %H:%M:%S"),
        'type': 'info'
    },
    {
        'action': 'Score Update',
        'description': 'Data quality score improved',
        'timestamp': datetime.now().strftime("%Y-%m-d %H:%M:%S"),
        'type': 'primary'
    }
])

# Initialize the app with Bootstrap and suppress callback exceptions
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css'
    ],
    prevent_initial_callbacks=True,
    suppress_callback_exceptions=True
)

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
''' + """
    .app-container {
        display: flex;
        min-height: 100vh;
        color: #000000;
    }
    
    .sidebar {
        width: 280px;
        background: #f8f9fa;
        border-right: 1px solid #dee2e6;
        position: fixed;
        height: 100vh;
        overflow-y: auto;
    }
    
    .content-wrapper {
        flex: 1;
        margin-left: 280px;
        padding: 2rem;
    }
    
    .sidebar-divider {
        margin: 1rem 0;
        border-color: #dee2e6;
    }
    
    .sidebar-section {
        padding: 1rem;
    }
    
    .sidebar-section-title {
        color: #000000;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .activity-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .activity-item {
        font-size: 0.875rem;
        color: #000000;
        display: flex;
        align-items: center;
        padding: 0.5rem;
        border-radius: 4px;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .activity-item i {
        font-size: 1rem;
    }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        padding: 1.5rem;
        height: 100%;
        color: #000000;
    }
    
    .progress-circle-container {
        position: relative;
        width: 120px;
        height: 120px;
        margin: 1.5rem auto;
        background: #f5f5f5;
        border-radius: 50%;
        overflow: hidden;
    }
    
    .progress-semicircle-left,
    .progress-semicircle-right {
        position: absolute;
        top: 0;
        width: 50%;
        height: 100%;
        transform-origin: right center;
    }
    
    .progress-semicircle-left {
        left: 0;
        border-radius: 120px 0 0 120px;
        transform-origin: right center;
        z-index: 2;
    }
    
    .progress-semicircle-right {
        right: 0;
        border-radius: 0 120px 120px 0;
        transform-origin: left center;
        z-index: 1;
    }
    
    .progress-inner-circle {
        position: absolute;
        top: 10%;
        left: 10%;
        width: 80%;
        height: 80%;
        background: white;
        border-radius: 50%;
        z-index: 3;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 600;
        color: #000000;
        margin: 0.5rem 0;
    }
    
    .nav-link {
        color: #000000;
        padding: 0.75rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .nav-link:hover {
        color: #0d6efd;
        background: rgba(13, 110, 253, 0.1);
        border-radius: 4px;
    }
    
    .nav-link.active {
        color: #0d6efd;
        background: rgba(13, 110, 253, 0.1);
        border-radius: 4px;
    }
""" + '''
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Sample DataFrames for demonstration
dfs = {
    'employees': pd.DataFrame({
        'employee_id': range(1, 6),
        'email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com', 'charlie@example.com'],
        'salary': [50000, 60000, 75000, 85000, 90000],
        'hire_date': ['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01'],
        'phone': ['+1234567890', '+1234567891', '+1234567892', '+1234567893', '+1234567894'],
        'department_id': [1, 1, 2, 2, 3],
        'age': [25, 30, 35, 40, 45],
        'job_title': ['Developer', 'Manager', 'Developer', 'Designer', 'Developer'],
        'manager_id': [None, None, 2, 2, 2]
    }),
    'departments': pd.DataFrame({
        'department_id': [1, 2, 3],
        'department_name': ['Engineering', 'Design', 'Marketing'],
        'location': ['New York', 'San Francisco', 'Chicago'],
        'budget': [1000000, 500000, 750000],
        'manager_id': [2, 4, None],
        'creation_date': ['2020-01-01', '2020-01-01', '2020-01-01'],
        'department_code': ['EN001', 'DE001', 'MA001'],
        'status': ['Active', 'Active', 'Inactive']
    }),
    'salaries': pd.DataFrame({
        'salary_id': [1, 2, 3, 4, 5],
        'employee_id': [1, 2, 3, 4, 5],
        'salary': [50000, 60000, 75000, 85000, 90000],
        'effective_date': ['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01'],
        'end_date': ['2020-12-31', '2020-12-31', '2020-12-31', '2020-12-31', '2020-12-31']
    }),
    'job_history': pd.DataFrame({
        'job_history_id': [1, 2, 3, 4, 5],
        'employee_id': [1, 2, 3, 4, 5],
        'department_id': [1, 1, 2, 2, 3],
        'start_date': ['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01'],
        'end_date': ['2020-12-31', '2020-12-31', '2020-12-31', '2020-12-31', '2020-12-31']
    }),
    'locations': pd.DataFrame({
        'location_id': [1, 2, 3],
        'city': ['New York', 'San Francisco', 'Chicago'],
        'country_code': ['US', 'US', 'US'],
        'postal_code': ['10001', '94101', '60601']
    }),
    'dependents': pd.DataFrame({
        'dependent_id': [1, 2, 3, 4, 5],
        'employee_id': [1, 2, 3, 4, 5],
        'first_name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
        'last_name': ['Doe', 'Doe', 'Smith', 'Johnson', 'Brown'],
        'relationship': ['Spouse', 'Child', 'Spouse', 'Child', 'Spouse']
    })
}

# Data Quality Rules
def get_table_rules():
    """Get validation rules for each table."""
    return {
        'employees': [
            {
                'rule': 'employee_id_not_null',
                'description': 'Employee ID must not be null',
                'severity': 'Critical'
            },
            {
                'rule': 'valid_email_format',
                'description': 'Email must be in valid format',
                'severity': 'High'
            },
            {
                'rule': 'salary_range',
                'description': 'Salary must be between 20000 and 200000',
                'severity': 'High'
            }
        ],
        'departments': [
            {
                'rule': 'unique_department_id',
                'description': 'Department ID must be unique',
                'severity': 'Critical'
            },
            {
                'rule': 'department_name_not_empty',
                'description': 'Department name must not be empty',
                'severity': 'High'
            }
        ],
        'salaries': [
            {
                'rule': 'unique_salary_id',
                'description': 'Salary ID must be unique',
                'severity': 'Critical'
            },
            {
                'rule': 'valid_employee_id',
                'description': 'Employee ID must exist',
                'severity': 'High'
            }
        ],
        'locations': [
            {
                'rule': 'unique_location_id',
                'description': 'Location ID must be unique',
                'severity': 'Critical'
            },
            {
                'rule': 'city_not_empty',
                'description': 'City must not be empty',
                'severity': 'High'
            },
            {
                'rule': 'valid_country_code',
                'description': 'Country code must be valid',
                'severity': 'Medium'
            }
        ],
        'job_history': [
            {
                'rule': 'unique_job_history_id',
                'description': 'Job history ID must be unique',
                'severity': 'Critical'
            },
            {
                'rule': 'valid_employee_id',
                'description': 'Employee ID must exist',
                'severity': 'High'
            },
            {
                'rule': 'valid_date_range',
                'description': 'End date must be after start date',
                'severity': 'High'
            }
        ],
        'dependents': [
            {
                'rule': 'unique_dependent_id',
                'description': 'Dependent ID must be unique',
                'severity': 'Critical'
            },
            {
                'rule': 'valid_employee_id',
                'description': 'Employee ID must exist',
                'severity': 'High'
            },
            {
                'rule': 'valid_relationship',
                'description': 'Relationship must be valid',
                'severity': 'Medium'
            }
        ]
    }

def validate_table_rules(table_name, df):
    """Validate rules for a specific table."""
    validation_results = {}
    
    if table_name == 'employees':
        validation_results['employee_id_not_null'] = not df['employee_id'].isnull().any()
        validation_results['valid_email_format'] = df['email'].str.contains('@').all()
        validation_results['salary_range'] = df['salary'].between(20000, 200000).all()
    
    elif table_name == 'departments':
        validation_results['unique_department_id'] = not df['department_id'].duplicated().any()
        validation_results['department_name_not_empty'] = not df['department_name'].isnull().any()
    
    elif table_name == 'salaries':
        validation_results['unique_salary_id'] = not df['salary_id'].duplicated().any()
        validation_results['valid_employee_id'] = df['employee_id'].isin(dfs['employees']['employee_id']).all()
    
    elif table_name == 'locations':
        validation_results['unique_location_id'] = not df['location_id'].duplicated().any()
        validation_results['city_not_empty'] = not df['city'].isnull().any()
        validation_results['valid_country_code'] = df['country_code'].isin(['US', 'CA', 'MX']).all()
    
    elif table_name == 'job_history':
        validation_results['unique_job_history_id'] = not df['job_history_id'].duplicated().any()
        validation_results['valid_employee_id'] = df['employee_id'].isin(dfs['employees']['employee_id']).all()
        validation_results['valid_date_range'] = (
            pd.to_datetime(df['end_date']) > pd.to_datetime(df['start_date'])
        ).all()
    
    elif table_name == 'dependents':
        validation_results['unique_dependent_id'] = not df['dependent_id'].duplicated().any()
        validation_results['valid_employee_id'] = df['employee_id'].isin(dfs['employees']['employee_id']).all()
        validation_results['valid_relationship'] = df['relationship'].isin(['Spouse', 'Child']).all()
    
    return validation_results

def create_rules_content(table_name):
    """Create the rules content for a specific table."""
    rules = get_table_rules()[table_name]
    validation_results = validate_table_rules(table_name, dfs[table_name])
    
    # Calculate summary statistics
    total_rules = len(rules)
    passed_rules = sum(1 for rule in rules if validation_results.get(rule['rule'], False))
    failed_rules = total_rules - passed_rules
    
    return html.Div([
        # Rules overview
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Rules Summary"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                create_circular_indicator(
                                    "Passed Rules",
                                    f"{(passed_rules/total_rules*100):.0f}%",
                                    "Success Rate",
                                    "increase",
                                    str(passed_rules),
                                    "success"
                                )
                            ], width=4),
                            dbc.Col([
                                create_circular_indicator(
                                    "Failed Rules",
                                    f"{(failed_rules/total_rules*100):.0f}%",
                                    "Failure Rate",
                                    "decrease",
                                    str(failed_rules),
                                    "danger"
                                )
                            ], width=4),
                            dbc.Col([
                                create_circular_indicator(
                                    "Total Rules",
                                    str(total_rules),
                                    "Active Rules",
                                    None,
                                    "100",
                                    "primary"
                                )
                            ], width=4),
                        ])
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Active rules
        dbc.Row([
            dbc.Col([
                html.H4("Active Rules", className="mb-3"),
                html.Div([
                    create_rule_card({
                        'rule': rule['rule'],
                        'description': rule['description'],
                        'severity': rule['severity'],
                        'status': 'Passed' if validation_results.get(rule['rule'], False) else 'Failed'
                    }) for rule in rules
                ])
            ])
        ])
    ])

def create_rules_page_layout():
    """Create the combined rules page layout."""
    return html.Div([
        html.H2("Data Validation Rules", className="mb-4"),
        
        # Table selector
        dbc.Row([
            dbc.Col([
                html.Label("Select Table", className="mb-2"),
                dcc.Dropdown(
                    id='table-selector',
                    options=[
                        {'label': table.capitalize(), 'value': table}
                        for table in dfs.keys()
                    ],
                    value=list(dfs.keys())[0],  # Set default value
                    className="mb-4"
                )
            ], width=6)
        ]),
        
        # Rules content container
        html.Div(id='rules-content', className="mb-4"),
    ])

def create_overview_layout():
    """Create the overview dashboard layout."""
    return html.Div([
        html.H2("Overview Dashboard", className="mb-4"),
        dbc.Row([
            dbc.Col(
                create_circular_indicator(
                    "Orders",
                    "932.00",
                    "Completed",
                    None,
                    "5443",
                    "primary"
                ),
                width=3
            ),
            dbc.Col(
                create_circular_indicator(
                    "Unique Visitors",
                    "756.00",
                    "Increased since yesterday",
                    "increase",
                    "50",
                    "success"
                ),
                width=3
            ),
            dbc.Col(
                create_circular_indicator(
                    "Impressions",
                    "100.38",
                    "Increased since yesterday",
                    "increase",
                    "35",
                    "warning"
                ),
                width=3
            ),
            dbc.Col(
                create_circular_indicator(
                    "Followers",
                    "4250k",
                    "Decreased since yesterday",
                    "decrease",
                    "25",
                    "danger"
                ),
                width=3
            ),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Employee Distribution"),
                    dbc.CardBody(
                        dcc.Graph(
                            id='employees-dept-chart',
                            figure=create_employees_per_dept_chart(),
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Salary Distribution"),
                    dbc.CardBody(
                        dcc.Graph(
                            id='salary-dist-chart',
                            figure=create_salary_distribution_chart(),
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], width=6)
        ]),
    ])

def create_data_quality_layout():
    """Create the combined data quality and details dashboard layout."""
    metrics = calculate_data_quality_metrics()
    
    return html.Div([
        html.H2("Data Quality Overview", className="mb-4"),
        
        # Overall metrics cards
        dbc.Row([
            dbc.Col([
                create_circular_indicator(
                    "Overall Quality",
                    f"{sum(m['overall'] for m in metrics.values()) / len(metrics):.1f}%",
                    "Average across all tables",
                    "increase",
                    "85",
                    "primary"
                )
            ], width=3),
            dbc.Col([
                create_circular_indicator(
                    "Data Completeness",
                    f"{sum(m['completeness'] for m in metrics.values()) / len(metrics):.1f}%",
                    "No missing values",
                    "increase",
                    "90",
                    "success"
                )
            ], width=3),
            dbc.Col([
                create_circular_indicator(
                    "Data Uniqueness",
                    f"{sum(m['uniqueness'] for m in metrics.values()) / len(metrics):.1f}%",
                    "Unique key fields",
                    "increase",
                    "95",
                    "warning"
                )
            ], width=3),
            dbc.Col([
                create_circular_indicator(
                    "Data Validity",
                    f"{sum(m['validity'] for m in metrics.values()) / len(metrics):.1f}%",
                    "Valid data formats",
                    "increase",
                    "88",
                    "danger"
                )
            ], width=3)
        ], className="mb-4"),
        
        # Table selector and metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Table Details"),
                    dbc.CardBody([
                        html.Label("Select Table", className="mb-2"),
                        dcc.Dropdown(
                            id='detail-table-selector',
                            options=[{'label': name.capitalize(), 'value': name} for name in dfs.keys()],
                            value=list(dfs.keys())[0],
                            className="mb-4"
                        ),
                        html.Div(id='detail-table-content')
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Quality metrics by table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Quality Metrics by Table"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Table"),
                                    html.Th("Completeness"),
                                    html.Th("Uniqueness"),
                                    html.Th("Validity"),
                                    html.Th("Overall Score")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(table_name.capitalize()),
                                    html.Td(f"{metrics[table_name]['completeness']:.1f}%"),
                                    html.Td(f"{metrics[table_name]['uniqueness']:.1f}%"),
                                    html.Td(f"{metrics[table_name]['validity']:.1f}%"),
                                    html.Td(f"{metrics[table_name]['overall']:.1f}%")
                                ]) for table_name in metrics.keys()
                            ])
                        ], className="table table-hover")
                    ])
                ])
            ], width=12)
        ]),
        
        # Quality trends chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Quality Metrics Overview"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_overall_quality_chart(metrics),
                            config={'displayModeBar': False}
                        )
                    ])
                ])
            ], width=12, className="mb-4")
        ])
    ])

def calculate_data_quality_metrics():
    """Calculate data quality metrics for all tables."""
    metrics = {}
    
    for table_name, df in dfs.items():
        # Calculate completeness
        completeness = (1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
        
        # Calculate uniqueness for key columns
        key_columns = {
            'employees': 'employee_id',
            'departments': 'department_id',
            'salaries': 'salary_id',
            'job_history': 'job_history_id',
            'locations': 'location_id',
            'dependents': 'dependent_id'
        }
        
        if table_name in key_columns:
            uniqueness = (1 - (df[key_columns[table_name]].duplicated().sum() / len(df))) * 100
        else:
            uniqueness = 100
        
        # Calculate validity based on data types
        validity = 100  # Default to 100%
        try:
            # Check numeric columns
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    validity -= 5
            
            # Check date columns
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            for col in date_cols:
                try:
                    pd.to_datetime(df[col])
                except:
                    validity -= 5
        except:
            validity = 90  # Default if checks fail
        
        # Store metrics
        metrics[table_name] = {
            'completeness': round(completeness, 2),
            'uniqueness': round(uniqueness, 2),
            'validity': round(validity, 2),
            'overall': round((completeness + uniqueness + validity) / 3, 2)
        }
    
    return metrics

def create_detail_page_layout():
    return html.Div([
        html.H2('Details', className='welcome-text'),
        html.P('Detailed data analysis and insights', className='subtitle-text'),
        
        # Table Selection
        html.Div([
            dcc.Dropdown(
                id='detail-table-selector',
                options=[{'label': name.title(), 'value': name} for name in dfs.keys()],
                value=list(dfs.keys())[0],
                className='table-dropdown'
            )
        ], className='dropdown-container'),
        
        # Table Display
        html.Div(id='detail-table-content', className='table-container')
    ])

def create_employees_per_dept_chart():
    dept_counts = dfs['employees']['department_id'].value_counts().reset_index()
    dept_counts.columns = ['department_id', 'count']
    dept_info = dfs['departments'][['department_id', 'department_name']]
    dept_counts = dept_counts.merge(dept_info, on='department_id')
    
    fig = px.bar(
        dept_counts,
        x='department_name',
        y='count',
        text='count',
        title='Employees per Department'
    )
    
    fig.update_traces(
        marker_color='#4361ee',
        textposition='auto'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(
            title='Department',
            showgrid=False,
            showline=True,
            linecolor='rgba(0,0,0,0.2)'
        ),
        yaxis=dict(
            title='Number of Employees',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        height=350,
        showlegend=False,
        font=dict(color='#2d3436')
    )
    
    return fig

def create_salary_distribution_chart():
    fig = px.histogram(
        dfs['employees'],
        x='salary',
        nbins=10,
        title='Salary Distribution'
    )
    
    fig.update_traces(
        marker_color='#4361ee'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(
            title='Salary Range',
            showgrid=False,
            showline=True,
            linecolor='rgba(0,0,0,0.2)',
            tickformat='$,.0f'
        ),
        yaxis=dict(
            title='Number of Employees',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        height=350,
        showlegend=False,
        font=dict(color='#2d3436')
    )
    
    return fig

def create_completeness_chart():
    completeness_data = []
    
    for table, df in dfs.items():
        for column in df.columns:
            completeness = (1 - df[column].isnull().sum() / len(df)) * 100
            completeness_data.append({
                'table': table,
                'column': column,
                'completeness': completeness
            })
    
    completeness_df = pd.DataFrame(completeness_data)
    
    fig = go.Figure(data=[
        go.Bar(
            x=[f"{row['table']}.{row['column']}" for _, row in completeness_df.iterrows()],
            y=completeness_df['completeness'],
            marker_color='#4361ee',
            text=[f"{x:.1f}%" for x in completeness_df['completeness']],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=80),
        xaxis=dict(
            title='Column',
            showgrid=False,
            showline=True,
            linecolor='rgba(0,0,0,0.2)',
            tickangle=-45
        ),
        yaxis=dict(
            title='Completeness (%)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)',
            range=[0, 100]
        ),
        height=350,
        showlegend=False,
        font=dict(color='#2d3436')
    )
    
    return fig

def create_overall_quality_chart(metrics):
    categories = ['Completeness', 'Uniqueness', 'Validity']
    tables = list(metrics.keys())
    
    fig = go.Figure()
    
    for category in categories:
        values = [metrics[table][category.lower()] for table in tables]
        fig.add_trace(go.Bar(
            name=category,
            x=tables,
            y=values,
            text=[f"{v:.1f}%" for v in values],
            textposition='auto'
        ))
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(
            title='Tables',
            showgrid=False,
            showline=True,
            linecolor='rgba(0,0,0,0.2)'
        ),
        yaxis=dict(
            title='Percentage',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)',
            range=[0, 100]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        font=dict(color='#2d3436')
    )
    return fig

def create_metric_item(label, value, icon, is_warning=False):
    return html.Div([
        html.Div([
            html.I(className=f"bi {icon} me-2"),
            html.Span(label, className="metric-label")
        ], className="d-flex align-items-center mb-1"),
        html.H5(value, className=f"{'text-warning' if is_warning else 'text-primary'} mb-0")
    ])

def create_recent_activity():
    """Create the recent activity component."""
    return html.Div([
        html.H6("Recent Activity", className="sidebar-section-title"),
        html.Div([
            html.Div([
                html.I(className="bi bi-check-circle-fill text-success me-2"),
                "Data quality check completed"
            ], className="activity-item"),
            html.Div([
                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                "3 new validation rules added"
            ], className="activity-item"),
            html.Div([
                html.I(className="bi bi-info-circle-fill text-info me-2"),
                "Updated salary analysis"
            ], className="activity-item"),
            html.Div([
                html.I(className="bi bi-arrow-up-circle-fill text-primary me-2"),
                "Data quality score improved"
            ], className="activity-item"),
        ], className="activity-list")
    ], className="sidebar-section")

def create_circular_indicator(title, value, subtitle, trend=None, trend_value=None, color='primary'):
    """Create a circular progress indicator similar to the overview dashboard."""
    if isinstance(value, (int, float)):
        formatted_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
    else:
        formatted_value = value

    # Define icons for each metric type
    icons = {
        'Orders': 'fas fa-lightbulb',
        'Unique Visitors': 'fas fa-user',
        'Impressions': 'fas fa-eye',
        'Followers': 'fas fa-eye'
    }

    # Map colors to actual CSS colors
    color_map = {
        'primary': '#1a73e8',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545'
    }

    # Calculate rotation for left and right circles
    progress = float(trend_value) if trend_value else 75
    rotation_right = min(progress, 50) * 3.6  # 3.6 degrees per percentage point
    rotation_left = max(0, progress - 50) * 3.6

    return dbc.Card([
        dbc.CardBody([
            # Title
            html.Div(title, className='text-muted mb-2', style={'font-size': '0.875rem'}),
            
            # Value
            html.Div(
                formatted_value,
                className='metric-value mb-4',
                style={'font-size': '1.75rem', 'font-weight': 'bold'}
            ),
            
            # Progress Circle Container
            html.Div([
                # Left Half Container
                html.Div(
                    className='progress-semicircle-left',
                    style={
                        'transform': f'rotate({rotation_left}deg)',
                        'background': color_map[color] if progress > 50 else 'transparent'
                    }
                ),
                
                # Right Half Container
                html.Div(
                    className='progress-semicircle-right',
                    style={
                        'transform': f'rotate({rotation_right}deg)',
                        'background': color_map[color]
                    }
                ),
                
                # Inner Circle
                html.Div(className='progress-inner-circle'),
                
                # Icon
                html.I(
                    className=icons.get(title, 'fas fa-chart-line'),
                    style={
                        'position': 'absolute',
                        'top': '50%',
                        'left': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'font-size': '1.2rem',
                        'color': '#2d3436',
                        'zIndex': 10
                    }
                )
            ], className='progress-circle-container'),
            
            # Subtitle and Percentage
            html.Div([
                html.Div(subtitle, className='text-muted small mb-1'),
                html.Div(
                    f"{trend_value}%" if trend_value else "",
                    className='fw-bold'
                )
            ], className='text-center mt-3')
        ], className='text-center')
    ], className='metric-card h-100 border-0')

def create_rule_card(rule):
    status_colors = {
        'Passed': '#4361ee',
        'Failed': '#ef233c',
        'Error': '#ff9f1c'
    }
    
    severity_icons = {
        'Critical': 'bi-exclamation-triangle-fill',
        'High': 'bi-exclamation-triangle',
        'Medium': 'bi-exclamation'
    }
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"bi {severity_icons.get(rule['severity'], 'bi-info-circle')} severity-icon"),
                html.Span(rule['severity'], className="ms-2 text-muted"),
            ], className="d-flex align-items-center"),
            html.Div([
                html.I(className=f"bi {'bi-check-circle' if rule['status'] == 'Passed' else 'bi-x-circle'}"),
                html.Span(rule['status'])
            ], className=f"rule-status {rule['status'].lower()}")
        ], className='rule-header'),
        html.H4(rule['description'], className='rule-title'),
        html.Code(rule['rule'], className='rule-code')
    ], className=f"rule-card {rule['status'].lower()}")

# Add rule states dictionary
rule_states = {
    table_name: {rule['rule']: True for rule in rules}
    for table_name, rules in get_table_rules().items()
}

def create_unified_rule_page():
    """Create a unified page combining rule catalogue and configuration."""
    templates = load_rule_templates()
    
    # Create a flat list of all rules with their categories
    all_rules = []
    for category, rules in templates.items():
        for rule in rules:
            all_rules.append({
                'name': rule['name'],
                'category': category.replace('_rules', '').title(),
                'description': rule['description'],
                'type': rule['type'],
                'severity': rule['severity'],
                'active': 'Active' if rule.get('active', True) else 'Inactive'
            })
    
    return dbc.Container([
        html.H2("Rule Management", className="mb-4"),
        
        # Main content row
        dbc.Row([
            # Left column - Rules Catalogue
            dbc.Col([
                html.H4("Rules Catalogue", className="mb-3"),
                dash_table.DataTable(
                    id='rules-catalogue-table',
                    columns=[
                        {'name': 'Name', 'id': 'name'},
                        {'name': 'Category', 'id': 'category'},
                        {'name': 'Description', 'id': 'description'},
                        {'name': 'Type', 'id': 'type'},
                        {'name': 'Severity', 'id': 'severity'},
                        {'name': 'Status', 'id': 'active'}
                    ],
                    data=all_rules,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{active} = "Active"'},
                            'backgroundColor': '#e6ffe6',
                            'color': '#006600'
                        },
                        {
                            'if': {'filter_query': '{active} = "Inactive"'},
                            'backgroundColor': '#ffe6e6',
                            'color': '#cc0000'
                        },
                        {
                            'if': {'filter_query': '{severity} = "Critical"'},
                            'color': '#dc3545'
                        },
                        {
                            'if': {'filter_query': '{severity} = "High"'},
                            'color': '#fd7e14'
                        }
                    ],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_size=DEFAULT_PAGE_SIZE
                )
            ], md=8),
            
            # Right column - Rule Configuration
            dbc.Col([
                html.H4("Rule Configuration", className="mb-3"),
                dbc.Card(dbc.CardBody([
                    # Rule Selection
                    dbc.Label("Select Rule", html_for="rule-dropdown", className="mb-2"),
                    dcc.Dropdown(
                        id='rule-dropdown',
                        options=[
                            {
                                'label': f"{rule['name']} ({category})",
                                'value': f"{category}:{rule['id']}"
                            }
                            for category, rules in templates.items()
                            for rule in rules
                        ],
                        placeholder="Select a rule to manage",
                        className="mb-3"
                    ),
                    
                    # Rule Status
                    dbc.Label("Rule Status", html_for="rule-status-dropdown", className="mb-2"),
                    dcc.Dropdown(
                        id='rule-status-dropdown',
                        options=[
                            {'label': 'Active', 'value': 'active'},
                            {'label': 'Inactive', 'value': 'inactive'}
                        ],
                        placeholder="Select rule status",
                        className="mb-3"
                    ),
                    
                    # Submit Button
                    dbc.Button(
                        "Save Changes",
                        id="save-rule-button",
                        color="primary",
                        className="mt-3"
                    ),
                    
                    # Status Message
                    html.Div(id='rule-update-status', className="mt-3")
                ]))
            ], md=4)
        ])
    ], fluid=True)

@app.callback(
    [Output('rule-update-status', 'children'),
     Output('rules-catalogue-table', 'data'),
     Output('sidebar-activity-list', 'children')],
    [Input('save-rule-button', 'n_clicks')],
    [State('rule-dropdown', 'value'),
     State('rule-status-dropdown', 'value')]
)
def save_rule_status(n_clicks, selected_rule, status):
    """Save the rule status changes to the JSON file and update activities."""
    if n_clicks is None or not selected_rule or not status:
        raise dash.exceptions.PreventUpdate()
    
    try:
        category, rule_id = selected_rule.split(':')
        success, message = update_rule_status_in_templates(category, rule_id, status)
        
        if success:
            templates = load_rule_templates()
            rule = next((r for r in templates[category] if r['id'] == rule_id), None)
            
            if rule:
                action = 'activated' if status == 'active' else 'deactivated'
                
                # Count total rule changes
                active_count = sum(1 for cat in templates.values() 
                                 for r in cat if r.get('active', True))
                inactive_count = sum(1 for cat in templates.values() 
                                  for r in cat if not r.get('active', True))
                
                # Add activity with counts
                add_activity(
                    'Rule Status Update',
                    f"{active_count} rules active, {inactive_count} rules inactive",
                    'success' if status == 'active' else 'warning'
                )
                
                # Update the rules catalogue data
                all_rules = []
                for cat, rules in templates.items():
                    for r in rules:
                        all_rules.append({
                            'name': r['name'],
                            'category': cat.replace('_rules', '').title(),
                            'description': r['description'],
                            'type': r['type'],
                            'severity': r['severity'],
                            'active': 'Active' if r.get('active', True) else 'Inactive'
                        })
                
                return (
                    html.Div(f"Rule successfully {action}!", className='text-success'),
                    all_rules,
                    create_activity_list()
                )
        
        return html.Div(message, className='text-danger'), dash.no_update, dash.no_update
        
    except Exception as e:
        add_activity('Error', f"Failed to update rule: {str(e)}", 'warning')
        return html.Div(f"Error updating rule: {str(e)}", className='text-danger'), dash.no_update, create_activity_list()

def create_sidebar():
    """Create the sidebar navigation."""
    return dbc.Nav([
        dbc.NavLink([
            html.I(className="bi bi-house-door me-2"),
            "Overview"
        ], href="/", active="exact"),
        
        dbc.NavLink([
            html.I(className="bi bi-check-circle me-2"),
            "Data Quality"
        ], href="/data-quality", active="exact"),
        
        dbc.NavLink([
            html.I(className="bi bi-gear me-2"),
            "Rules Management"
        ], href="/rules", active="exact"),
        
        dbc.NavLink([
            html.I(className="bi bi-info-circle me-2"),
            "Details"
        ], href="/details", active="exact")
    ], vertical=True, pills=True, className="bg-light")

# Initialize the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # Sidebar
    html.Div([
        html.H2("Data Quality", className="p-3"),
        create_sidebar(),
        
        # Recent Activity Section
        html.Hr(className="sidebar-divider"),
        html.Div(id='sidebar-activity-list', children=create_activity_list())
    ], className="sidebar"),
    
    # Main content
    html.Div(id='page-content', className="content")
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    """Route to the appropriate page based on URL pathname."""
    page_routes = {
        '/': create_overview_layout,
        '/data-quality': create_data_quality_layout,
        '/rules': create_unified_rule_page,
        '/details': create_detail_page_layout
    }
    
    return page_routes.get(pathname, create_overview_layout)()

@app.callback(
    Output('rules-content', 'children'),
    [Input('table-selector', 'value')]
)
def update_rules_content(selected_table):
    if selected_table is None:
        return html.Div("Please select a table", className="text-muted")
    return create_rules_content(selected_table)

@app.callback(
    Output('detail-table-content', 'children'),
    Input('detail-table-selector', 'value')
)
def update_detail_content(selected_table):
    if selected_table is None:
        return html.Div("Please select a table", className='no-data-message')
    
    df = dfs[selected_table]
    
    return html.Div([
        # Table Stats
        html.Div([
            html.H3('Table Statistics', className='section-title'),
            html.Div([
                html.Div([
                    html.Strong('Total Records: '),
                    str(len(df))
                ], className='stat-item'),
                html.Div([
                    html.Strong('Columns: '),
                    str(len(df.columns))
                ], className='stat-item'),
                html.Div([
                    html.Strong('Missing Values: '),
                    str(df.isnull().sum().sum())
                ], className='stat-item')
            ], className='stats-container')
        ], className='stats-section'),
        
        # Data Preview
        html.Div([
            html.H3('Data Preview', className='section-title'),
            dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #dee2e6'
                },
                style_data={
                    'border': '1px solid #dee2e6'
                }
            )
        ], className='table-section')
    ])

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
