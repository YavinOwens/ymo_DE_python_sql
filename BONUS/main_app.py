import dash
from dash import html, dcc, Input, Output, State, ALL, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from data_loader import DataLoader
from config import DEFAULT_PREVIEW_ROWS
import pandas as pd
import json
from datetime import datetime

# Initialize the Dash app with a modern theme
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True
)
app.title = "Data Quality Dashboard"

# Initialize data loader
data_loader = DataLoader()

# Sidebar layout
sidebar = dbc.Nav(
    [
        dbc.NavLink("Overview", href="/overview", active="exact", id="overview-link"),
        dbc.NavLink("Data Quality", href="/quality", active="exact", id="quality-link"),
        dbc.NavLink("Column Analysis", href="/columns", active="exact", id="columns-link"),
        dbc.NavLink("Data Catalogue", href="/catalogue", active="exact", id="catalogue-link"),
        dbc.NavLink("Rule Catalogue", href="/rules", active="exact", id="rules-link"),
        dbc.NavLink("Rule Management", href="/manage-rules", active="exact", id="manage-rules-link"),
        dbc.NavLink("Run Management", href="/run-management", active="exact", id="run-management-link"),
    ],
    vertical=True,
    pills=True,
    className="bg-light",
)

# Layout components
def create_overview_content(table_name=None):
    if not table_name:
        return html.Div("Please select a table to view data quality metrics.")
    
    table_data = data_loader.load_table_data(table_name)
    if 'error' in table_data:
        return html.Div(f"Error loading table: {table_data['error']}")
    
    stats = table_data['stats']
    quality_metrics = table_data['quality_metrics']['overall']
    
    # Create metrics cards
    metrics_cards = [
        dbc.Card(
            dbc.CardBody([
                html.H4("Total Rows", className="card-title"),
                html.H2(f"{stats['row_count']:,}", className="text-primary")
            ]),
            className="mb-4"
        ),
        dbc.Card(
            dbc.CardBody([
                html.H4("Total Columns", className="card-title"),
                html.H2(f"{stats['column_count']}", className="text-primary")
            ]),
            className="mb-4"
        ),
        dbc.Card(
            dbc.CardBody([
                html.H4("Data Quality Score", className="card-title"),
                html.H2(f"{quality_metrics['total_score']:.2%}", className="text-primary")
            ]),
            className="mb-4"
        )
    ]
    
    # Create quality metrics gauge charts
    quality_gauges = [
        dcc.Graph(
            figure=create_gauge_chart(
                quality_metrics['completeness'],
                "Completeness",
                "Measures the presence of required data"
            )
        ),
        dcc.Graph(
            figure=create_gauge_chart(
                quality_metrics['uniqueness'],
                "Uniqueness",
                "Measures distinct values in data"
            )
        ),
        dcc.Graph(
            figure=create_gauge_chart(
                quality_metrics['validity'],
                "Validity",
                "Measures data type conformance"
            )
        )
    ]
    
    # Data preview
    preview_df = data_loader.get_table_preview(table_name)
    preview_table = dbc.Table.from_dataframe(
        preview_df.head(10).to_pandas(),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mt-4"
    )
    
    return html.Div([
        dbc.Row([dbc.Col(card) for card in metrics_cards]),
        dbc.Row([
            dbc.Col(gauge, width=4) for gauge in quality_gauges
        ]),
        html.H4("Data Preview", className="mt-4"),
        preview_table
    ])

def create_quality_content(table_name=None):
    if not table_name:
        return html.Div("Please select a table to view detailed quality metrics.")
    
    table_data = data_loader.load_table_data(table_name)
    if 'error' in table_data:
        return html.Div(f"Error loading table: {table_data['error']}")
    
    quality_metrics = table_data['quality_metrics']
    df = table_data['data']
    
    # Create column quality metrics table
    columns_quality = []
    for col in df.columns:
        columns_quality.append({
            'Column': col,
            'Completeness': f"{quality_metrics['completeness'][col]:.2%}",
            'Uniqueness': f"{quality_metrics['uniqueness'][col]:.2%}",
            'Validity': f"{quality_metrics['validity'][col]:.2%}"
        })
    
    quality_table = dbc.Table.from_dataframe(
        pd.DataFrame(columns_quality),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True
    )
    
    return html.Div([
        html.H4("Column Quality Metrics"),
        quality_table
    ])

def create_column_analysis_content(table_name=None, selected_columns=None):
    if not table_name:
        return html.Div("Please select a table to view column analysis.")

    # Get column options for the dropdown
    table_schema = data_loader.get_table_schema(table_name)
    column_options = [{'label': col['name'], 'value': col['name']} for col in table_schema]
    
    # Create column selection dropdown
    column_selector = dbc.Row([
        dbc.Col(
            [
                html.H4("Select Columns"),
                dcc.Dropdown(
                    id='column-multi-dropdown',
                    options=column_options,
                    value=selected_columns if selected_columns else [],
                    multi=True,
                    className="mb-4"
                )
            ],
            width=12
        )
    ])
    
    if not selected_columns:
        return html.Div([
            html.H2("Column Analysis", className="mb-4"),
            column_selector,
            html.Div("Please select one or more columns to analyze.", className="mt-4")
        ])
    
    analysis_sections = []
    
    # Create correlation matrix if multiple columns are selected
    if len(selected_columns) > 1:
        try:
            correlation_data = data_loader.get_correlation_matrix(table_name, selected_columns)
            if 'error' not in correlation_data:
                correlation_fig = px.imshow(
                    correlation_data,
                    labels=dict(x="Column", y="Column", color="Correlation"),
                    color_continuous_scale="RdBu",
                    aspect="auto"
                )
                correlation_fig.update_layout(
                    title="Correlation Matrix",
                    height=400
                )
                analysis_sections.append(
                    dbc.Card(
                        dbc.CardBody([
                            html.H4("Correlation Analysis", className="card-title"),
                            dcc.Graph(figure=correlation_fig)
                        ]),
                        className="mb-4"
                    )
                )
        except Exception as e:
            analysis_sections.append(
                html.Div(f"Error generating correlation matrix: {str(e)}")
            )
    
    # Individual column profiles
    for column_name in selected_columns:
        profile = data_loader.get_column_profile(table_name, column_name)
        if 'error' in profile:
            analysis_sections.append(
                html.Div(f"Error loading profile for {column_name}: {profile['error']}")
            )
            continue
        
        # Column header with stats
        column_header = dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Data Type", className="card-title"),
                        html.H3(profile['dtype'], className="text-primary")
                    ]),
                    className="mb-4"
                )
            ], width=4),
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Non-null Count", className="card-title"),
                        html.H3(f"{profile['non_null_count']:,}", className="text-primary")
                    ]),
                    className="mb-4"
                )
            ], width=4),
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Unique Values", className="card-title"),
                        html.H3(f"{profile['unique_count']:,}", className="text-primary")
                    ]),
                    className="mb-4"
                )
            ], width=4)
        ])
        
        # Distribution visualization
        distribution_section = None
        if profile['dtype'] in ['int64', 'float64']:
            # Numerical distribution
            try:
                hist_data = data_loader.get_numerical_distribution(table_name, column_name)
                if 'error' not in hist_data:
                    hist_fig = px.histogram(
                        hist_data,
                        x=column_name,
                        title=f"Distribution of {column_name}",
                        marginal="box"
                    )
                    distribution_section = dcc.Graph(figure=hist_fig)
            except Exception as e:
                distribution_section = html.Div(f"Error generating histogram: {str(e)}")
        else:
            # Categorical distribution
            if profile['frequent_values'] and isinstance(profile['frequent_values'], list):
                # Convert the frequent values list to a DataFrame with correct column names
                freq_df = pd.DataFrame(profile['frequent_values'])
                if not freq_df.empty and all(col in freq_df.columns for col in ['value', 'count']):
                    fig = px.bar(
                        freq_df,
                        x='value',
                        y='count',
                        title=f"Top Values in {column_name}"
                    )
                    fig.update_layout(
                        xaxis_title="Value",
                        yaxis_title="Frequency",
                        bargap=0.2
                    )
                    distribution_section = dcc.Graph(figure=fig)
                else:
                    distribution_section = html.Div("No valid frequency distribution data available")
            else:
                distribution_section = html.Div("No frequency distribution data available")
        
        # Summary statistics
        stats_section = None
        if profile['dtype'] in ['int64', 'float64']:
            try:
                stats = data_loader.get_numerical_stats(table_name, column_name)
                if 'error' not in stats:
                    stats_section = dbc.Table([
                        html.Thead([
                            html.Tr([html.Th("Statistic"), html.Th("Value")])
                        ]),
                        html.Tbody([
                            html.Tr([html.Td(k), html.Td(f"{v:,.2f}")]) 
                            for k, v in stats.items()
                        ])
                    ], bordered=True, hover=True, striped=True, className="mb-4")
            except Exception as e:
                stats_section = html.Div(f"Error generating statistics: {str(e)}")
        
        # Add all sections for this column
        analysis_sections.append(
            dbc.Card([
                dbc.CardHeader(html.H3(column_name)),
                dbc.CardBody([
                    column_header,
                    distribution_section,
                    stats_section
                ])
            ], className="mb-4")
        )
    
    return html.Div([
        html.H2("Column Analysis", className="mb-4"),
        column_selector,
        *analysis_sections
    ])

def create_catalogue_content(table_name=None):
    """Create the data catalogue content showing metadata about tables and columns."""
    if not table_name:
        return html.Div("Please select a table to view its catalogue information.")
    
    try:
        # Get table metadata
        schema = data_loader.get_table_schema(table_name)
        table_data = data_loader.load_table_data(table_name)
        
        if 'error' in table_data:
            return html.Div(f"Error loading table: {table_data['error']}")
        
        # Create table info card
        table_info_card = dbc.Card(
            dbc.CardBody([
                html.H4("Table Information", className="card-title"),
                html.Hr(),
                html.Div([
                    html.P([
                        html.Strong("Table Name: "), 
                        table_name
                    ]),
                    html.P([
                        html.Strong("Number of Columns: "), 
                        str(len(schema))
                    ]),
                    html.P([
                        html.Strong("Number of Rows: "), 
                        f"{table_data['stats']['row_count']:,}"
                    ]),
                    html.P([
                        html.Strong("Storage Size: "), 
                        f"{table_data['stats']['memory_usage'] / 1024 / 1024:.2f} MB"
                    ])
                ])
            ]),
            className="mb-4"
        )
        
        # Create column details table
        columns = []
        for col in schema:
            col_profile = data_loader.get_column_profile(table_name, col['name'])
            
            # Skip if there was an error getting the profile
            if 'error' in col_profile:
                continue
                
            column_info = {
                'Column Name': col['name'],
                'Data Type': col['type'],
                'Primary Key': 'Yes' if col['pk'] else 'No',
                'Nullable': 'No' if col['notnull'] else 'Yes',
                'Default': col['default'] if col['default'] else '-',
                'Unique Values': f"{col_profile['unique_count']:,}",
                'Non-null Values': f"{col_profile['non_null_count']:,}"
            }
            columns.append(column_info)
        
        column_table = dbc.Table.from_dataframe(
            pd.DataFrame(columns),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mt-4"
        )
        
        # Create data sample card
        preview_df = data_loader.get_table_preview(table_name, limit=5)
        sample_card = dbc.Card(
            dbc.CardBody([
                html.H4("Data Sample", className="card-title"),
                html.Hr(),
                dbc.Table.from_dataframe(
                    preview_df.to_pandas(),
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    className="mt-2"
                )
            ]),
            className="mb-4"
        )
        
        return html.Div([
            html.H2("Data Catalogue", className="mb-4"),
            table_info_card,
            html.H4("Column Details", className="mb-3"),
            column_table,
            sample_card
        ])
        
    except Exception as e:
        return html.Div(f"Error creating catalogue: {str(e)}")

def create_rule_catalogue_content():
    with open('rule_templates.json', 'r') as f:
        rules = json.loads(f.read())
    
    # Calculate statistics
    total_rules = 0
    active_rules = 0
    category_counts = {}
    
    for category, rule_list in rules.items():
        if isinstance(rule_list, list):  # Skip table_specific_rules which is a dict
            category_name = category.replace('_', ' ').title()
            category_counts[category_name] = len(rule_list)
            total_rules += len(rule_list)
            active_rules += sum(1 for rule in rule_list if rule.get('active', True))
    
    # Create summary cards
    summary_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Rules", className="card-title text-center"),
                    html.H2(f"{total_rules}", className="text-primary text-center mb-0")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Active Rules", className="card-title text-center"),
                    html.H2(f"{active_rules}", className="text-success text-center mb-0")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Inactive Rules", className="card-title text-center"),
                    html.H2(f"{total_rules - active_rules}", className="text-danger text-center mb-0")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Categories", className="card-title text-center"),
                    html.H2(f"{len(category_counts)}", className="text-info text-center mb-0")
                ])
            ], className="mb-4")
        ], width=3)
    ])
    
    # Create category breakdown
    category_breakdown = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Rules by Category"),
                dbc.CardBody([
                    html.Div([
                        dbc.Row([
                            dbc.Col(html.H6(category, className="mb-0"), width=8),
                            dbc.Col(html.H6(count, className="text-end mb-0"), width=4)
                        ], className="mb-2")
                        for category, count in category_counts.items()
                    ])
                ])
            ])
        ])
    ])
    
    rule_sections = []
    
    for category, rule_list in rules.items():
        if isinstance(rule_list, list):  # Skip table_specific_rules which is a dict
            category_name = category.replace('_', ' ').title()
            rules_table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("ID"),
                        html.Th("Name"),
                        html.Th("Description"),
                        html.Th("Type"),
                        html.Th("Severity"),
                        html.Th("Status")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(rule['id']),
                        html.Td(rule['name']),
                        html.Td(rule['description']),
                        html.Td(rule.get('type', 'N/A')),
                        html.Td(rule.get('severity', 'N/A')),
                        html.Td(
                            html.Span(
                                "Active" if rule.get('active', True) else "Inactive",
                                className=f"badge {'bg-success' if rule.get('active', True) else 'bg-secondary'}"
                            )
                        )
                    ]) for rule in rule_list
                ])
            ], striped=True, bordered=True, hover=True, className="mb-4")

            rule_sections.append(
                dbc.Card([
                    dbc.CardHeader(category_name),
                    dbc.CardBody(rules_table)
                ], className="mb-4")
            )
    
    return html.Div([
        html.H2("Rule Catalogue", className="mb-4"),
        html.P("Browse and manage data quality rules by category.", className="mb-4"),
        summary_cards,
        category_breakdown,
        html.Hr(),
        *rule_sections
    ])

def create_rules_table(rules, category_filter=None, severity_filter=None, status_filter=None):
    """Create the filtered rules table."""
    filtered_rules = rules.copy()
    
    # Apply filters
    if category_filter:
        filtered_rules = [r for r in filtered_rules if r.get('category', '') in category_filter]
    if severity_filter:
        filtered_rules = [r for r in filtered_rules if r.get('severity', '') in severity_filter]
    if status_filter:
        filtered_rules = [r for r in filtered_rules 
                         if ('active' in status_filter and r.get('active', False)) or 
                            ('inactive' in status_filter and not r.get('active', False))]
    
    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("ID"),
                html.Th("Name"),
                html.Th("Category"),
                html.Th("Description"),
                html.Th("Type"),
                html.Th("Severity"),
                html.Th("Status"),
                html.Th("Action")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(rule.get('id', '')),
                html.Td(rule.get('name', '')),
                html.Td(rule.get('category', '')),
                html.Td(rule.get('description', '')),
                html.Td(rule.get('type', '')),
                html.Td(
                    dbc.Badge(
                        rule.get('severity', 'N/A'),
                        color={
                            'Critical': 'danger',
                            'High': 'warning',
                            'Medium': 'info',
                            'Low': 'secondary'
                        }.get(rule.get('severity', ''), 'primary'),
                        className="me-1"
                    )
                ),
                html.Td(
                    dbc.Badge(
                        "Active" if rule.get('active', False) else "Inactive",
                        color="success" if rule.get('active', False) else "secondary",
                        className="me-1"
                    )
                ),
                html.Td(
                    dbc.Switch(
                        id={'type': 'rule-toggle', 'index': rule.get('id', '')},
                        value=rule.get('active', False),
                        className="d-inline-block"
                    )
                )
            ]) for rule in filtered_rules
        ])
    ], bordered=True, hover=True, striped=True, className="mb-4")

def create_rule_management_layout():
    """Creates the layout for the Rule Management page with statistics and filters."""
    # Create an instance of DataLoader
    data_loader = DataLoader()
    
    # Load rules using the instance
    rules = data_loader.load_all_rules()
    
    if isinstance(rules, dict) and 'error' in rules:
        return html.Div(f"Error loading rules: {rules['error']}")

    # Calculate statistics
    total_rules = len(rules)
    active_rules = len([rule for rule in rules if rule.get('active', False)])
    rules_by_category = {}
    rules_by_severity = {}
    
    for rule in rules:
        category = rule.get('category', 'Uncategorized')
        severity = rule.get('severity', 'Undefined')
        rules_by_category[category] = rules_by_category.get(category, 0) + 1
        rules_by_severity[severity] = rules_by_severity.get(severity, 0) + 1

    # Create statistics cards with consistent spacing and styling
    stats_cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Total Rules", className="card-title text-center"),
                    html.H2(total_rules, className="text-center text-primary mb-0")
                ]),
                className="h-100 shadow-sm"
            ),
            width=3,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Active Rules", className="card-title text-center"),
                    html.H2(active_rules, className="text-center text-success mb-0")
                ]),
                className="h-100 shadow-sm"
            ),
            width=3,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Categories", className="card-title text-center"),
                    html.H2(len(rules_by_category), className="text-center text-info mb-3"),
                    html.Div(
                        [f"{cat}: {count}" for cat, count in rules_by_category.items()],
                        className="small text-muted px-2"
                    )
                ]),
                className="h-100 shadow-sm"
            ),
            width=3,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("By Severity", className="card-title text-center"),
                    html.Div([
                        html.Div(
                            [
                                html.Span(f"{sev}: ", className="fw-bold"),
                                html.Span(f"{count}")
                            ],
                            className="mb-2"
                        ) for sev, count in rules_by_severity.items()
                    ], className="px-2")
                ]),
                className="h-100 shadow-sm"
            ),
            width=3,
            className="mb-4"
        )
    ]

    # Create filter dropdowns with consistent spacing
    filter_row = dbc.Row([
        dbc.Col([
            html.Label("Category:", className="fw-bold mb-2"),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': cat, 'value': cat} for cat in rules_by_category.keys()],
                multi=True,
                placeholder="Select Category",
                className="mb-3"
            )
        ], width=4),
        dbc.Col([
            html.Label("Severity:", className="fw-bold mb-2"),
            dcc.Dropdown(
                id='severity-filter',
                options=[{'label': sev, 'value': sev} for sev in rules_by_severity.keys()],
                multi=True,
                placeholder="Select Severity",
                className="mb-3"
            )
        ], width=4),
        dbc.Col([
            html.Label("Status:", className="fw-bold mb-2"),
            dcc.Dropdown(
                id='status-filter',
                options=[
                    {'label': 'Active', 'value': 'active'},
                    {'label': 'Inactive', 'value': 'inactive'}
                ],
                multi=True,
                placeholder="Select Status",
                className="mb-3"
            )
        ], width=4)
    ], className="mb-4")

    # Create initial rules table
    rules_table = html.Div(id="filtered-rules-table")

    # Return the complete layout with consistent spacing
    return html.Div([
        html.H2("Rule Management", className="mb-4"),
        html.P("Manage and configure data quality rules.", className="mb-4 text-muted"),
        dbc.Row(stats_cards, className="mb-4"),
        filter_row,
        rules_table,
        dcc.Store(id='rules-data', data=rules),
        dbc.Toast(
            id="rule-update-toast",
            header="Rule Status Update",
            is_open=False,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350},
        )
    ], className="p-4")

@app.callback(
    Output("filtered-rules-table", "children"),
    [
        Input("category-filter", "value"),
        Input("severity-filter", "value"),
        Input("status-filter", "value"),
        Input("rules-data", "data")
    ]
)
def update_filtered_table(category_filter, severity_filter, status_filter, rules):
    """Update the rules table based on selected filters."""
    return create_rules_table(rules, category_filter, severity_filter, status_filter)

@app.callback(
    [Output("rules-data", "data"),
     Output("rule-update-toast", "is_open"),
     Output("rule-update-toast", "children")],
    [Input({'type': 'rule-toggle', 'index': ALL}, 'value')],
    [State({'type': 'rule-toggle', 'index': ALL}, 'id'),
     State("rules-data", "data")]
)
def update_rule_status(values, ids, rules):
    """Update rule status when toggle switches are changed."""
    if not values or not ids:
        raise dash.exceptions.PreventUpdate
        
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
        
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if input_id == '':
        raise dash.exceptions.PreventUpdate
        
    rule_id = eval(input_id)['index']
    new_value = ctx.triggered[0]['value']
    
    # Update the rule status in the rules list
    for rule in rules:
        if rule['id'] == rule_id:
            rule['active'] = new_value
            message = f"Rule '{rule['name']}' has been {'activated' if new_value else 'deactivated'}."
            break
    
    # Save updated rules to file
    data_loader = DataLoader()
    data_loader.save_rule_status(rule_id, new_value)
    
    return rules, True, message

def create_rule_management_content():
    """Creates the main content for the Rule Management page."""
    return create_rule_management_layout()

def create_run_management_content(table_name=None):
    """Creates the layout for the Run Management page with execution history and insights."""
    
    # Load active rules
    data_loader = DataLoader()
    rules = data_loader.load_all_rules()
    active_rules = [rule for rule in rules if rule.get('active', False)]
    
    # Create run history data (mock data for now - this would come from a database in production)
    run_history = pd.DataFrame({
        'run_id': range(1, 6),
        'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=5, freq='D'),
        'rules_executed': [len(active_rules)] * 5,
        'pass_rate': [0.85, 0.88, 0.82, 0.90, 0.87],
        'fail_rate': [0.15, 0.12, 0.18, 0.10, 0.13],
        'duration_seconds': [120, 115, 125, 118, 122]
    })
    
    # Create summary cards
    summary_cards = dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Active Rules", className="card-title text-center"),
                    html.H2(f"{len(active_rules)}", className="text-center text-primary")
                ])
            ),
            width=3
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Latest Pass Rate", className="card-title text-center"),
                    html.H2(f"{run_history['pass_rate'].iloc[-1]:.1%}", className="text-center text-success")
                ])
            ),
            width=3
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Latest Run Duration", className="card-title text-center"),
                    html.H2(f"{run_history['duration_seconds'].iloc[-1]}s", className="text-center text-info")
                ])
            ),
            width=3
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Total Runs", className="card-title text-center"),
                    html.H2(f"{len(run_history)}", className="text-center text-secondary")
                ])
            ),
            width=3
        )
    ], className="mb-4")
    
    # Create trend charts
    trend_charts = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Pass/Fail Rate Trend"),
                dbc.CardBody(
                    dcc.Graph(
                        figure=px.line(
                            run_history,
                            x='timestamp',
                            y=['pass_rate', 'fail_rate'],
                            title="Pass/Fail Rate Over Time",
                            labels={'value': 'Rate', 'timestamp': 'Date', 'variable': 'Metric'},
                            color_discrete_map={'pass_rate': 'green', 'fail_rate': 'red'}
                        )
                    )
                )
            ]),
            width=6
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Run Duration Trend"),
                dbc.CardBody(
                    dcc.Graph(
                        figure=px.line(
                            run_history,
                            x='timestamp',
                            y='duration_seconds',
                            title="Run Duration Over Time",
                            labels={'duration_seconds': 'Duration (seconds)', 'timestamp': 'Date'}
                        )
                    )
                )
            ]),
            width=6
        )
    ], className="mb-4")
    
    # Create run history table
    history_table = dbc.Card([
        dbc.CardHeader("Run History"),
        dbc.CardBody(
            dash_table.DataTable(
                data=run_history.to_dict('records'),
                columns=[
                    {'name': 'Run ID', 'id': 'run_id'},
                    {'name': 'Timestamp', 'id': 'timestamp'},
                    {'name': 'Rules Executed', 'id': 'rules_executed'},
                    {'name': 'Pass Rate', 'id': 'pass_rate', 'format': {'specifier': '.1%'}},
                    {'name': 'Fail Rate', 'id': 'fail_rate', 'format': {'specifier': '.1%'}},
                    {'name': 'Duration (s)', 'id': 'duration_seconds'}
                ],
                style_table={'overflowX': 'auto'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'pass_rate', 'filter_query': '{pass_rate} >= 0.85'},
                        'backgroundColor': '#e6ffe6',
                        'color': 'green'
                    },
                    {
                        'if': {'column_id': 'fail_rate', 'filter_query': '{fail_rate} >= 0.15'},
                        'backgroundColor': '#ffe6e6',
                        'color': 'red'
                    }
                ],
                sort_action='native',
                page_size=10
            )
        )
    ])
    
    # Create execute rules button
    execute_button = dbc.Row(
        dbc.Col(
            dbc.Button(
                "Execute Active Rules",
                id="execute-rules-button",
                color="primary",
                className="mb-4"
            ),
            width={"size": 3, "offset": 9}
        )
    )
    
    # Return complete layout
    return html.Div([
        html.H2("Run Management", className="mb-4"),
        html.P(
            "Monitor rule execution history, track performance trends, and execute active rules.",
            className="mb-4 text-muted"
        ),
        execute_button,
        summary_cards,
        trend_charts,
        history_table,
        dbc.Toast(
            id="execution-toast",
            header="Rule Execution",
            is_open=False,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350},
        )
    ])

@app.callback(
    [Output("execution-toast", "is_open"),
     Output("execution-toast", "children")],
    [Input("execute-rules-button", "n_clicks"),
     Input("table-dropdown", "value")],
    prevent_initial_call=True
)
def execute_rules(n_clicks, table_name):
    if not n_clicks or not table_name:
        raise dash.exceptions.PreventUpdate
    
    try:
        data_loader = DataLoader()
        result = data_loader.execute_rules(table_name)
        
        # Create a summary message
        message = f"""
        Rules executed successfully!
        - Rules Executed: {result['rules_executed']}
        - Pass Rate: {result['pass_rate']:.1%}
        - Duration: {result['duration_seconds']:.1f}s
        """
        
        return True, message
    except Exception as e:
        return True, f"Error executing rules: {str(e)}"

# App layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='selected-columns-store', data=[]),
    dbc.Row([
        dbc.Col(html.H1("Data Quality Dashboard", className="text-primary mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("Select Table"),
            dcc.Dropdown(
                id='table-dropdown',
                options=[{'label': table, 'value': table} for table in data_loader.get_table_names()],
                value=None,
                clearable=False,
                className="mb-4"
            )
        ])
    ]),
    dbc.Row([
        dbc.Col(sidebar, width=2, className="bg-light"),
        dbc.Col(html.Div(id="page-content"), width=10)
    ])
], fluid=True)

# Callback for page content
@app.callback(
    Output("page-content", "children"),
    [Input("table-dropdown", "value"),
     Input("url", "pathname"),
     Input("selected-columns-store", "data")]
)
def render_page_content(table_name, pathname, selected_columns):
    if pathname == "/quality":
        return create_quality_content(table_name)
    elif pathname == "/columns":
        return create_column_analysis_content(table_name, selected_columns)
    elif pathname == "/catalogue":
        return create_catalogue_content(table_name)
    elif pathname == "/rules":
        return create_rule_catalogue_content()
    elif pathname == "/manage-rules":
        return create_rule_management_content()
    elif pathname == "/overview" or pathname == "/":
        return create_overview_content(table_name)
    elif pathname == "/run-management":
        return create_run_management_content()
    else:
        return html.Div("404 - Page not found")

# Callback to update selected columns when dropdown changes
@app.callback(
    Output("selected-columns-store", "data"),
    [Input("column-multi-dropdown", "value")],
    [State("selected-columns-store", "data")],
    prevent_initial_call=True
)
def update_selected_columns(new_value, current_value):
    if new_value is None:
        return current_value
    return new_value

# Reset selected columns when table changes
@app.callback(
    Output("selected-columns-store", "data", allow_duplicate=True),
    [Input("table-dropdown", "value")],
    prevent_initial_call=True
)
def reset_selected_columns(table_name):
    return []

# Callback to update navigation active states
@app.callback(
    [Output("overview-link", "active"),
     Output("quality-link", "active"),
     Output("columns-link", "active"),
     Output("catalogue-link", "active"),
     Output("rules-link", "active"),
     Output("manage-rules-link", "active"),
     Output("run-management-link", "active")],
    [Input("url", "pathname")]
)
def toggle_active_links(pathname):
    if pathname == "/overview" or pathname == "/":
        return True, False, False, False, False, False, False
    elif pathname == "/quality":
        return False, True, False, False, False, False, False
    elif pathname == "/columns":
        return False, False, True, False, False, False, False
    elif pathname == "/catalogue":
        return False, False, False, True, False, False, False
    elif pathname == "/rules":
        return False, False, False, False, True, False, False
    elif pathname == "/manage-rules":
        return False, False, False, False, False, True, False
    elif pathname == "/run-management":
        return False, False, False, False, False, False, True
    return True, False, False, False, False, False, False

def create_gauge_chart(value, title, description):
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 60], 'color': "red"},
                    {'range': [60, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': value * 100
                }
            }
        )
    )

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
