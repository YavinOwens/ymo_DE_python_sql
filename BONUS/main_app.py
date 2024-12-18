import dash
from dash import html, dcc, Input, Output, State, ALL, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import json
import polars as pl
import numpy as np
import pandas as pd
from datetime import datetime
import re
import os
from data_loader import DataLoader
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_log.log',
    filemode='a'
)

# Initialize DataLoader
data_loader = DataLoader()

# Initialize the Dash app with a modern theme
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.FLATLY,
        dbc.icons.BOOTSTRAP
    ],
    suppress_callback_exceptions=True
)
app.title = "Data Quality Dashboard"

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .card {
                border-radius: 8px;
                transition: all 0.2s ease-in-out;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .progress {
                height: 12px;
                border-radius: 6px;
            }
            .progress-bar {
                transition: width 0.6s ease;
                font-size: 0.875rem !important;
                line-height: 12px !important;
            }
            .text-muted {
                color: #6c757d !important;
            }
            .bi {
                vertical-align: -0.125em;
                font-size: 1.1em;
            }
            .card-body {
                padding: 1.5rem;
            }
            .h4 {
                font-size: 1.5rem;
                font-weight: 600;
                line-height: 1.2;
            }
            .fs-5 {
                font-size: 1.15rem !important;
            }
            .mb-3 {
                margin-bottom: 1rem !important;
            }
            .mb-4 {
                margin-bottom: 1.5rem !important;
            }
            .me-2 {
                margin-right: 0.5rem !important;
            }
            .p-4 {
                padding: 1.5rem !important;
            }
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
        dbc.NavLink("Report", href="/report", active="exact", id="report-link"),
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
    if isinstance(preview_df, pl.DataFrame):
        preview_df = preview_df.to_pandas()
    
    sample_card = dbc.Card(
        dbc.CardBody([
            html.H4("Data Sample", className="card-title"),
            html.Hr(),
            dbc.Table.from_dataframe(
                preview_df.head(10),
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
        dbc.Row([dbc.Col(card) for card in metrics_cards]),
        dbc.Row([
            dbc.Col(gauge, width=4) for gauge in quality_gauges
        ]),
        html.H4("Data Preview", className="mt-4"),
        sample_card
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
        if isinstance(preview_df, pl.DataFrame):
            preview_df = preview_df.to_pandas()
        sample_card = dbc.Card(
            dbc.CardBody([
                html.H4("Data Sample", className="card-title"),
                html.Hr(),
                dbc.Table.from_dataframe(
                    preview_df,
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
    """Create the rule catalogue content."""
    # Load all rules using the same source as rule management
    rules = data_loader.load_all_rules()
    
    if isinstance(rules, dict) and 'error' in rules:
        return html.Div(f"Error loading rules: {rules['error']}")

    # Calculate statistics
    total_rules = len(rules)
    active_rules = len([rule for rule in rules if rule.get('active', True)])
    
    # Group rules by category
    rules_by_category = {}
    for rule in rules:
        category = rule.get('category', 'Uncategorized')
        if category not in rules_by_category:
            rules_by_category[category] = []
        rules_by_category[category].append(rule)

    # Create summary cards
    summary_cards = dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Total Rules", className="card-title text-center"),
                    html.H2(f"{total_rules}", className="text-center text-primary")
                ])
            ),
            width=3,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Active Rules", className="card-title text-center"),
                    html.H2(f"{active_rules}", className="text-center text-success")
                ])
            ),
            width=3,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Categories", className="card-title text-center"),
                    html.H2(f"{len(rules_by_category)}", className="text-center text-info mb-3"),
                    html.Div(
                        [f"{cat}: {len(rules)}" for cat, rules in rules_by_category.items()],
                        className="small text-muted px-2"
                    )
                ])
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
                ])
            ),
            width=3,
            className="mb-4"
        )
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
                            dbc.Col(html.H6(len(rules), className="text-end mb-0"), width=4)
                        ], className="mb-2")
                        for category, rules in rules_by_category.items()
                    ])
                ])
            ])
        ])
    ])

    # Create rule sections by category
    rule_sections = []
    for category, category_rules in rules_by_category.items():
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
                    html.Td(
                        html.Span(
                            rule.get('severity', 'N/A'),
                            className=f"badge {'bg-danger' if rule.get('severity') == 'Critical' else 'bg-warning'}"
                        )
                    ),
                    html.Td(
                        html.Span(
                            "Active" if rule.get('active', True) else "Inactive",
                            className=f"badge {'bg-success' if rule.get('active', True) else 'bg-secondary'}"
                        )
                    )
                ]) for rule in category_rules
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
    # Load rules using the same source as rule management
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
                    html.H2(total_rules, className="text-center text-primary")
                ])
            ),
            width=3,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Active Rules", className="card-title text-center"),
                    html.H2(active_rules, className="text-center text-success")
                ])
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
                ])
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
                ])
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
    data_loader.save_rule_status(rule_id, new_value)
    
    return rules, True, message

def create_rule_management_content():
    """Creates the main content for the Rule Management page."""
    return create_rule_management_layout()

def create_run_management_content(table_name=None):
    """Creates the layout for the Run Management page with execution history and insights."""
    try:
        # Create execute button
        execute_button = dbc.Button(
            [html.I(className="bi bi-play-circle me-2"), "Execute Rules"],
            id="execute-rules-button",
            color="primary",
            className="mb-4"
        )
        
        # Get execution history
        history = data_loader.get_execution_history()
        table_history = [run for run in history if run['table_name'] == table_name] if table_name else []
        
        # Get latest run for accurate rule count
        latest_run = table_history[-1] if table_history else None
        total_rules = latest_run['rules_executed'] if latest_run else 0
        
        # Calculate summary statistics
        total_executions = len(table_history)
        if total_executions > 0:
            total_passed = sum(run['passed_rules'] for run in table_history)
            total_rules_executed = sum(run['rules_executed'] for run in table_history)
            avg_pass_rate = (total_passed / total_rules_executed * 100) if total_rules_executed > 0 else 0
            total_failed = sum(run['failed_rules'] for run in table_history)
        else:
            avg_pass_rate = 0
            total_failed = 0
        
        # Create summary cards
        summary_cards = dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-play-circle fs-1 text-primary"),
                        html.H4("Total Rules", className="mt-3"),
                        html.H2(f"{total_rules}", className="text-primary")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-check-circle fs-1 text-success"),
                        html.H4("Total Executions", className="mt-3"),
                        html.H2(f"{total_executions}", className="text-success")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-percent fs-1 text-info"),
                        html.H4("Average Pass Rate", className="mt-3"),
                        html.H2(f"{avg_pass_rate:.1f}%", className="text-info")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-x-circle fs-1 text-danger"),
                        html.H4("Failed Rules", className="mt-3"),
                        html.H2(
                            str(total_failed) if table_history else "0",
                            className="text-danger"
                        )
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            )
        ])
        
        # Create execution history table
        if table_history:
            history_table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Timestamp"),
                        html.Th("Rules Executed"),
                        html.Th("Pass Rate"),
                        html.Th("Status"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(run['timestamp']),
                        html.Td(run['rules_executed']),
                        html.Td(f"{(run['passed_rules'] / run['rules_executed'] * 100):.1f}%"),
                        html.Td(
                            html.Span(
                                "All Passed" if run['failed_rules'] == 0 else f"{run['failed_rules']} Failed",
                                className=f"badge {'bg-success' if run['failed_rules'] == 0 else 'bg-danger'}"
                            )
                        ),
                        html.Td([
                            dbc.Button(
                                [html.I(className="bi bi-info-circle me-2"), "View Details"],
                                id={'type': 'view-details-btn', 'index': i},
                                color="info",
                                size="sm",
                                className="me-2"
                            ),
                            dbc.Button(
                                [html.I(className="bi bi-exclamation-circle me-2"), "View Failed Data"],
                                id={'type': 'view-failed-data-btn', 'index': i},
                                color="danger",
                                size="sm",
                                disabled=run['failed_rules'] == 0
                            )
                        ])
                    ]) for i, run in enumerate(reversed(table_history))
                ])
            ], bordered=True, hover=True, className="mb-4")
        else:
            history_table = html.Div("No execution history available.", className="text-muted")
        
        # Create failed rules section
        failed_rules_section = html.Div(id="failed-rules-section")
        
        # Create details modal
        details_modal = dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Run Details")),
            dbc.ModalBody(id="run-details-modal-body"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-run-details-modal", className="ms-auto")
            )
        ], id="run-details-modal", size="xl")

        # Create failed data modal
        failed_data_modal = create_failed_data_modal(table_name)

        return html.Div([
            html.Div(id="run-management-content", children=[
                html.H2("Run Management", className="mb-4"),
                execute_button,
                html.Div(id='execution-status', className="mb-4"),
                summary_cards,
                html.H4("Execution History", className="mb-3"),
                history_table,
                failed_rules_section,
                details_modal,
                failed_data_modal
            ])
        ])
        
    except Exception as e:
        return html.Div(f"Error creating run management page: {str(e)}")

@app.callback(
    [Output("execution-status", "children"),
     Output("run-management-content", "children"),
     Output("page-content", "children", allow_duplicate=True)],
    [Input("execute-rules-button", "n_clicks")],
    [State("table-dropdown", "value"),
     State("url", "pathname")],
    prevent_initial_call=True
)
def execute_rules(n_clicks, table_name, pathname):
    """Execute active rules and update run history."""
    # Enhanced input validation
    if n_clicks is None:
        logging.info("Rule execution prevented: No button click")
        raise dash.exceptions.PreventUpdate
    
    if not table_name:
        logging.warning("Rule execution prevented: No table selected")
        return html.Div([
            html.Div([
                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                "No Table Selected"
            ], className="alert alert-warning"),
            html.P("Please select a table before executing rules.", className="text-muted")
        ]), dash.no_update, dash.no_update
    
    try:
        # Extensive logging
        logging.info(f"Starting rule execution for table: {table_name}")
        
        # Robust rule loading
        try:
            rules = data_loader.load_all_rules()
            if isinstance(rules, dict) and 'error' in rules:
                logging.error(f"Rule loading error: {rules['error']}")
                return html.Div([
                    html.Div([
                        html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"),
                        "Rule Loading Error"
                    ], className="alert alert-danger"),
                    html.P(rules['error'], className="text-muted")
                ]), dash.no_update, dash.no_update
        except Exception as rule_load_error:
            logging.error(f"Unexpected error loading rules: {rule_load_error}")
            return html.Div([
                html.Div([
                    html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"),
                    "Rule Loading Failure"
                ], className="alert alert-danger"),
                html.P(f"Unable to load rules: {rule_load_error}", className="text-muted")
            ]), dash.no_update, dash.no_update
        
        # Filter active rules with detailed logging
        active_rules = [rule for rule in rules if rule.get('active', False)]
        if not active_rules:
            logging.warning("No active rules found to execute")
            return html.Div([
                html.Div([
                    html.I(className="bi bi-info-circle-fill text-info me-2"),
                    "No Active Rules"
                ], className="alert alert-info"),
                html.P("Please activate at least one rule before execution.", className="text-muted")
            ]), dash.no_update, dash.no_update
        
        # Robust data loading with enhanced error handling
        try:
            table_data_result = data_loader.load_table_data(table_name)
        except Exception as load_error:
            logging.error(f"Error loading table data: {load_error}")
            return html.Div([
                html.Div([
                    html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"),
                    "Data Loading Error"
                ], className="alert alert-danger"),
                html.P(f"Failed to load table data: {load_error}", className="text-muted")
            ]), dash.no_update, dash.no_update
        
        # Ensure we have a pandas DataFrame with comprehensive type checking
        if isinstance(table_data_result, dict) and 'data' in table_data_result:
            if isinstance(table_data_result['data'], pl.DataFrame):
                table_data = table_data_result['data'].to_pandas()
            elif isinstance(table_data_result['data'], pd.DataFrame):
                table_data = table_data_result['data']
            else:
                logging.error("Unable to convert table data to DataFrame")
                return html.Div([
                    html.Div([
                        html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"),
                        "Data Conversion Error"
                    ], className="alert alert-danger"),
                    html.P("Unsupported data format detected.", className="text-muted")
                ]), dash.no_update, dash.no_update
        elif isinstance(table_data_result, pl.DataFrame):
            table_data = table_data_result.to_pandas()
        elif isinstance(table_data_result, pd.DataFrame):
            table_data = table_data_result
        else:
            logging.error("Unable to convert table data to DataFrame")
            return html.Div([
                html.Div([
                    html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"),
                    "Data Conversion Error"
                ], className="alert alert-danger"),
                html.P("Unsupported data format detected.", className="text-muted")
            ]), dash.no_update, dash.no_update
        
        # Execute rules
        results = []
        passed_rules = 0
        failed_rules = 0
        total_failed_rows = 0
        
        for rule in active_rules:
            rule_result = execute_rule(rule, table_data)
            results.append(rule_result)
            
            # Update pass/fail counters
            if rule_result['passed']:
                passed_rules += 1
            else:
                failed_rules += 1
                total_failed_rows += rule_result['failed_rows_count']
        
        # Calculate pass rate
        total_rules = len(active_rules)
        pass_rate = passed_rules / total_rules if total_rules > 0 else 0
        
        # Save execution results
        execution_results = {
            "timestamp": datetime.now().isoformat(),
            "rules_executed": total_rules,
            "passed_rules": passed_rules,
            "failed_rules": failed_rules,
            "pass_rate": pass_rate,
            "total_failed_rows": total_failed_rows,
            "results": results
        }
        data_loader.save_execution_results(table_name, execution_results)
        
        # Prepare success message
        success_message = html.Div([
            html.I(className="bi bi-check-circle-fill text-success me-2"),
            f"Executed {total_rules} rules: ",
            html.Span(f"{passed_rules} passed", className="text-success"),
            " / ",
            html.Span(f"{failed_rules} failed", className="text-danger"),
            html.Div(f"Pass Rate: {pass_rate:.2%}", className="text-muted mt-2"),
            html.Div(f"Total Failed Rows: {total_failed_rows}", className="text-muted")
        ])
        
        # Update page content based on current page
        page_content = create_report_content(table_name) if pathname == '/report' else dash.no_update
        
        # Return updated content
        return success_message, create_run_management_content(table_name), page_content
    
    except Exception as e:
        logging.error(f"Unexpected error in rule execution: {str(e)}")
        logging.error(traceback.format_exc())
        return html.Div([
            html.Div([
                html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"),
                "Unexpected Rule Execution Error"
            ], className="alert alert-danger"),
            html.P(str(e), className="text-muted mt-2")
        ]), dash.no_update, dash.no_update

def execute_rule(rule, table_data):
    """
    Execute a single rule with comprehensive error handling and detailed reporting
    
    Args:
        rule (dict): Rule configuration
        table_data (pd.DataFrame): DataFrame to apply rule against
    
    Returns:
        dict: Detailed rule execution result
    """
    rule_result = {
        "rule_name": rule["name"],
        "rule_type": rule["type"],
        "description": rule.get("description", "No description provided"),
        "passed": True,
        "failed_indices": [],
        "error": None,
        "failed_rows_count": 0
    }
    
    try:
        # Rule type-specific execution
        if rule["type"] == "null_check":
            column = rule["parameters"]["column"]
            
            # Validate column existence
            if column not in table_data.columns:
                rule_result.update({
                    "passed": False,
                    "error": f"Column '{column}' not found in table"
                })
                return rule_result
            
            # Find null values
            failed_rows = table_data[table_data[column].isna()]
            if not failed_rows.empty:
                rule_result.update({
                    "passed": False,
                    "failed_indices": failed_rows.index.tolist(),
                    "failed_rows_count": len(failed_rows)
                })
        
        elif rule["type"] == "unique_check":
            column = rule["parameters"]["column"]
            
            # Validate column existence
            if column not in table_data.columns:
                rule_result.update({
                    "passed": False,
                    "error": f"Column '{column}' not found in table"
                })
                return rule_result
            
            # Find duplicate values
            duplicates = table_data[table_data.duplicated(subset=[column], keep=False)]
            if not duplicates.empty:
                rule_result.update({
                    "passed": False,
                    "failed_indices": duplicates.index.tolist(),
                    "failed_rows_count": len(duplicates)
                })
        
        elif rule["type"] == "type":
            column = rule["parameters"]["column"]
            expected_type = rule["parameters"]["expected_type"].lower()
            
            # Validate column existence
            if column not in table_data.columns:
                rule_result.update({
                    "passed": False,
                    "error": f"Column '{column}' not found in table"
                })
                return rule_result
            
            # Type-specific validation
            try:
                if expected_type == "integer":
                    converted = pd.to_numeric(table_data[column], errors='coerce')
                    failed_rows = table_data[converted.isna() & table_data[column].notna()]
                
                elif expected_type == "float":
                    converted = pd.to_numeric(table_data[column], errors='coerce')
                    failed_rows = table_data[converted.isna() & table_data[column].notna()]
                
                elif expected_type == "string":
                    failed_rows = table_data[~table_data[column].apply(lambda x: isinstance(x, str))]
                
                elif expected_type == "boolean":
                    failed_rows = table_data[~table_data[column].apply(lambda x: isinstance(x, bool))]
                
                elif expected_type == "datetime":
                    converted = pd.to_datetime(table_data[column], errors='coerce')
                    failed_rows = table_data[converted.isna() & table_data[column].notna()]
                
                else:
                    rule_result.update({
                        "passed": False,
                        "error": f"Unsupported type: {expected_type}"
                    })
                    return rule_result
                
                # Update result if failed rows exist
                if not failed_rows.empty:
                    rule_result.update({
                        "passed": False,
                        "failed_indices": failed_rows.index.tolist(),
                        "failed_rows_count": len(failed_rows)
                    })
            
            except Exception as type_err:
                rule_result.update({
                    "passed": False,
                    "error": f"Type validation error: {str(type_err)}"
                })
        
        elif rule["type"] == "value_range":
            column = rule["parameters"]["column"]
            min_val = rule["parameters"].get("min")
            max_val = rule["parameters"].get("max")
            
            # Validate column existence
            if column not in table_data.columns:
                rule_result.update({
                    "passed": False,
                    "error": f"Column '{column}' not found in table"
                })
                return rule_result
            
            # Convert to numeric and check range
            try:
                numeric_data = pd.to_numeric(table_data[column], errors='coerce')
                
                # Create mask for out-of-range values
                mask = pd.Series(False, index=table_data.index)
                if min_val is not None:
                    mask |= numeric_data < min_val
                if max_val is not None:
                    mask |= numeric_data > max_val
                
                # Find failed rows
                failed_rows = table_data[mask]
                if not failed_rows.empty:
                    rule_result.update({
                        "passed": False,
                        "failed_indices": failed_rows.index.tolist(),
                        "failed_rows_count": len(failed_rows)
                    })
            
            except Exception as range_err:
                rule_result.update({
                    "passed": False,
                    "error": f"Range validation error: {str(range_err)}"
                })
        
        else:
            rule_result.update({
                "passed": False,
                "error": f"Unsupported rule type: {rule['type']}"
            })
        
        return rule_result
    
    except Exception as e:
        logging.error(f"Unexpected error executing rule {rule['name']}: {e}")
        return {
            "rule_name": rule["name"],
            "rule_type": rule["type"],
            "description": rule.get("description", "No description provided"),
            "passed": False,
            "failed_indices": [],
            "error": f"Unexpected error: {str(e)}",
            "failed_rows_count": 0
        }

def create_report_content(table_name=None):
    """Creates a report page with high-level cards for each column."""
    if not table_name:
        return html.Div("Please select a table to view the report.")

    try:
        # Get table data and schema
        table_data = data_loader.load_table_data(table_name)
        schema = data_loader.get_table_schema(table_name)
        
        if 'error' in table_data:
            return html.Div(f"Error loading table: {table_data['error']}")

        # Create overview cards
        overview_cards = dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-table fs-1 text-primary"),
                        html.H4("Total Columns", className="mt-3"),
                        html.H2(f"{len(schema)}", className="text-primary")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-list-columns fs-1 text-success"),
                        html.H4("Total Rows", className="mt-3"),
                        html.H2(f"{table_data['stats']['row_count']:,}", className="text-success")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-shield-lock fs-1 text-warning"),
                        html.H4("GDPR Risk Level", className="mt-3"),
                        html.H2("Medium", className="text-warning")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.I(className="bi bi-hdd-stack fs-1 text-info"),
                        html.H4("Storage Size", className="mt-3"),
                        html.H2(f"{table_data['stats']['memory_usage'] / 1024 / 1024:.1f} MB", className="text-info")
                    ], className="text-center"),
                ),
                width=3,
                className="mb-4"
            )
        ])

        # Create column cards
        column_cards = []
        for col in schema:
            try:
                col_profile = data_loader.get_column_profile(table_name, col['name'])
                quality_metrics = table_data['quality_metrics']
                
                if 'error' in col_profile:
                    continue

                # Determine appropriate icon based on data type
                icon_class = {
                    'int64': 'bi-123',
                    'float64': 'bi-percent',
                    'datetime64': 'bi-calendar',
                    'bool': 'bi-toggle-on',
                    'category': 'bi-tag',
                }.get(str(col_profile['dtype']), 'bi-fonts')

                # Check for GDPR risks
                gdpr_risks = []
                col_name_lower = col['name'].lower()
                
                # PII data patterns
                pii_patterns = ['name', 'email', 'phone', 'address', 'ssn', 'dob', 'passport', 'postcode', 'zip']
                sensitive_patterns = ['password', 'secret', 'token', 'key', 'credit', 'card', 'auth', 'medical']
                
                # Check for PII data
                if any(pattern in col_name_lower for pattern in pii_patterns):
                    gdpr_risks.append({
                        'type': 'PII Data',
                        'severity': 'Critical',
                        'icon': 'bi-exclamation-triangle-fill'
                    })
                
                # Check for sensitive data
                if any(pattern in col_name_lower for pattern in sensitive_patterns):
                    gdpr_risks.append({
                        'type': 'Sensitive Data',
                        'severity': 'High',
                        'icon': 'bi-shield-exclamation'
                    })

                # Create quality score based on execution results and metrics
                execution_history = data_loader.get_execution_history()
                table_history = [run for run in execution_history if run['table_name'] == table_name]
                
                # Calculate quality score from execution results
                rule_quality_score = 1.0
                if table_history:
                    latest_run = table_history[-1]
                    if latest_run['rules_executed'] > 0:
                        rule_quality_score = latest_run['passed_rules'] / latest_run['rules_executed']
                
                # Calculate metrics-based score
                metrics_score = (
                    quality_metrics['completeness'].get(col['name'], 0) +
                    quality_metrics['uniqueness'].get(col['name'], 0) +
                    quality_metrics['validity'].get(col['name'], 0)
                ) / 3
                
                # Combine both scores (50% weight each)
                quality_score = (rule_quality_score + metrics_score) / 2
                
                # Create the column card with GDPR indicators
                column_cards.append(
                    dbc.Col(
                        dbc.Card([
                            dbc.CardBody([
                                # Title row with column name and icons
                                dbc.Row([
                                    dbc.Col([
                                        html.I(className=f"bi {icon_class} me-2"),
                                        html.Span(col['name'], className="h4 mb-0"),
                                        *[
                                            html.I(
                                                className=f"bi {risk['icon']} ms-2",
                                                style={'color': 'red' if risk['severity'] == 'Critical' else 'orange'},
                                                title=f"{risk['type']} - {risk['severity']}"
                                            ) for risk in gdpr_risks
                                        ]
                                    ], className="d-flex align-items-center")
                                ], className="mb-4"),
                                
                                # Stats with icons in larger text
                                html.Div([
                                    html.Div([
                                        html.I(className="bi bi-info-circle me-2 text-muted"),
                                        html.Span("Type: ", className="text-muted fs-5"),
                                        html.Span(str(col_profile['dtype']), className="fw-bold fs-5")
                                    ], className="mb-3"),
                                    html.Div([
                                        html.I(className="bi bi-hash me-2 text-muted"),
                                        html.Span("Unique: ", className="text-muted fs-5"),
                                        html.Span(f"{col_profile['unique_count']:,}", className="fw-bold fs-5")
                                    ], className="mb-3"),
                                    html.Div([
                                        html.I(className="bi bi-exclamation-triangle me-2 text-muted"),
                                        html.Span("Null: ", className="text-muted fs-5"),
                                        html.Span(
                                            f"{table_data['stats']['row_count'] - col_profile['non_null_count']:,}",
                                            className="fw-bold fs-5 text-danger"
                                        )
                                    ], className="mb-3"),
                                ], className="mb-4"),
                                
                                # GDPR risks section with larger text
                                html.Div([
                                    html.Div([
                                        html.I(className=f"bi {risk['icon']} me-2", 
                                              style={'color': 'red' if risk['severity'] == 'Critical' else 'orange'}),
                                        html.Span(f"{risk['type']}: ", className="fs-5"),
                                        html.Span(
                                            risk['severity'],
                                            className="fw-bold fs-5",
                                            style={'color': 'red' if risk['severity'] == 'Critical' else 'orange'}
                                        )
                                    ], className="mb-3") for risk in gdpr_risks
                                ], className="mb-4"),
                                
                                # Quality score section with larger text
                                html.Div([
                                    html.H5("Quality Score", className="mb-3"),
                                    dbc.Progress([
                                        dbc.Progress(
                                            value=quality_score * 100,
                                            color="success" if quality_score >= 0.8 else "warning" if quality_score >= 0.6 else "danger",
                                            bar=True,
                                            label=f"{quality_score:.0%}",
                                            className="fs-6 fw-bold"
                                        )
                                    ], className="mb-2", style={"height": "12px"}),
                                    html.Div([
                                        html.Span("0", className="text-muted fs-6"),
                                        html.Span("50", className="position-absolute start-50 translate-middle-x text-muted fs-6"),
                                        html.Span("100", className="float-end text-muted fs-6")
                                    ], className="position-relative")
                                ])
                            ], className="p-4")
                        ], className="h-100 shadow-sm"),
                        width=6,
                        className="mb-4"
                    )
                )
            except Exception as e:
                logging.error(f"Error processing column {col['name']}: {str(e)}")
                continue

        # Create rows of column cards (2 cards per row)
        column_rows = [
            dbc.Row(column_cards[i:i+2])
            for i in range(0, len(column_cards), 2)
        ]

        return html.Div([
            html.Link(
                rel='stylesheet',
                href='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css'
            ),
            html.H2("Data Quality Report", className="mb-4"),
            html.P(f"Detailed quality report for table: {table_name}", className="text-muted mb-4"),
            overview_cards,
            html.H4("Column Details", className="mb-4"),
            *column_rows
        ])

    except Exception as e:
        logging.error(f"Error creating report: {str(e)}")
        return html.Div(f"Error creating report: {str(e)}")

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
        return create_run_management_content(table_name)
    elif pathname == "/report":
        return create_report_content(table_name)
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
     Output("run-management-link", "active"),
     Output("report-link", "active")],
    [Input("url", "pathname")]
)
def toggle_active_links(pathname):
    if pathname == "/overview" or pathname == "/":
        return True, False, False, False, False, False, False, False
    elif pathname == "/quality":
        return False, True, False, False, False, False, False, False
    elif pathname == "/columns":
        return False, False, True, False, False, False, False, False
    elif pathname == "/catalogue":
        return False, False, False, True, False, False, False, False
    elif pathname == "/rules":
        return False, False, False, False, True, False, False, False
    elif pathname == "/manage-rules":
        return False, False, False, False, False, True, False, False
    elif pathname == "/run-management":
        return False, False, False, False, False, False, True, False
    elif pathname == "/report":
        return False, False, False, False, False, False, False, True
    return True, False, False, False, False, False, False, False

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

# Callback to handle run details modal
@app.callback(
    [Output("run-details-modal", "is_open"),
     Output("run-details-modal-body", "children")],
    [Input({"type": "view-details-btn", "index": ALL}, "n_clicks"),
     Input("close-run-details-modal", "n_clicks")],
    [State("run-details-modal", "is_open"),
     State("table-dropdown", "value")],
    prevent_initial_call=True
)
def toggle_run_details_modal(view_clicks, close_clicks, is_open, table_name):
    """Handle opening/closing the run details modal and populating its content."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, None
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if triggered_id == "close-run-details-modal":
        return False, None
        
    if not any(view_clicks):
        return False, None
        
    # Find which button was clicked
    try:
        button_index = next(i for i, clicks in enumerate(view_clicks) if clicks)
    except StopIteration:
        return False, None
        
    # Get execution history
    history = data_loader.get_execution_history()
    table_history = [run for run in history if run['table_name'] == table_name] if table_name else []
    
    # Get the run details (reverse order to match display)
    runs = list(reversed(table_history))
    if not table_history:
        return False, dbc.Alert("No execution history found for this table.", color="warning")
        
    run = runs[button_index]
        
    # Create detailed content
    failed_rules = [
        result for result in run.get('results', [])
        if result.get('status', '') in ['Failed', 'Error']  # Include both Failed and Error states
    ]
        
    content = []
        
    # Add run summary
    content.extend([
        html.H5("Run Summary", className="mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H6("Timestamp", className="mb-2"),
                        html.P(run['timestamp'], className="mb-0")
                    ]),
                    className="mb-3"
                )
            ], width=4),
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H6("Pass Rate", className="mb-2"),
                        html.P(
                            f"{(run['passed_rules'] / run['rules_executed'] * 100):.1f}%",
                            className=f"mb-0 {'text-success' if run['passed_rules'] == run['rules_executed'] else 'text-warning'}"
                        )
                    ]),
                    className="mb-3"
                )
            ], width=4),
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H6("Failed Rules", className="mb-2"),
                        html.P(
                            [
                                html.I(className="bi bi-exclamation-circle-fill me-2"),
                                f"{run['failed_rules']}"
                            ],
                            className="mb-0 text-danger"
                        ) if run['failed_rules'] > 0 else html.P(
                            [
                                html.I(className="bi bi-check-circle-fill me-2"),
                                "0"
                            ],
                            className="mb-0 text-success"
                        )
                    ]),
                    className="mb-3"
                )
            ], width=4)
        ])
    ])
        
    # Add failed rules details
    if run['failed_rules'] > 0:
        if failed_rules:  # We have detailed failure information
            content.extend([
                html.H5("Failed Rules", className="mb-3 mt-4"),
                html.Div([
                    dbc.Alert(
                        [
                            html.I(className="bi bi-exclamation-circle-fill me-2"),
                            f"The following {run['failed_rules']} rules failed during execution:"
                        ],
                        color="danger",
                        className="mb-3"
                    ),
                    html.Div([
                        dbc.Card(
                            dbc.CardBody([
                                html.H6(
                                    [
                                        html.I(className="bi bi-exclamation-circle-fill me-2 text-danger"),
                                        rule['rule_name']
                                    ],
                                    className="card-title"
                                ),
                                html.P([
                                    html.Strong("Severity: "),
                                    html.Span(
                                        rule['severity'],
                                        className=f"badge {'bg-danger' if rule['severity'] == 'Critical' else 'bg-warning'} me-2"
                                    ),
                                    html.Strong("Category: "),
                                    html.Span(
                                        rule['category'].replace('_', ' ').title(),
                                        className="badge bg-info me-2"
                                    ),
                                    html.Strong("Status: "),
                                    html.Span(
                                        rule['status'],
                                        className=f"badge {'bg-danger' if rule['status'] == 'Failed' else 'bg-warning'} me-2"
                                    )
                                ], className="mb-2"),
                                html.P("Failure Details:", className="mb-2 fw-bold"),
                                html.Ul([
                                    html.Li(
                                        detail,
                                        className="text-danger"
                                    ) for detail in rule.get('details', ["No detailed failure information available."])
                                ], className="mb-0")
                            ]),
                            className="mb-3 border-danger"
                        ) for rule in failed_rules
                    ])
                ])
            ])
        else:  # No detailed failure information available
            content.append(
                dbc.Alert(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        f"This run has {run['failed_rules']} failed rules, but detailed failure information is not available."
                    ],
                    color="warning",
                    className="mb-0 mt-4"
                )
            )
    else:
        content.append(
            dbc.Alert(
                [html.I(className="bi bi-check-circle-fill me-2"), "All rules passed successfully!"],
                color="success",
                className="mb-0 mt-4"
            )
        )
    
    return True, html.Div(content)

@app.callback(
    [
        Output("failed-data-modal", "is_open"),
        Output("failed-data-modal-body", "children")
    ],
    [
        Input({"type": "view-failed-data-btn", "index": ALL}, "n_clicks"),
        Input("close-failed-data-modal", "n_clicks")
    ],
    [State("table-dropdown", "value")],
    prevent_initial_call=True
)
def toggle_failed_data_modal(view_clicks, close_clicks, table_name):
    """
    Handle showing failed data in modal.
    Reads from execution history JSON to retrieve detailed failed data.
    
    Args:
        view_clicks (int): Number of times view failed data button was clicked
        close_clicks (int): Number of times close button was clicked
        table_name (str): Name of the table
    
    Returns:
        tuple: Modal open state and modal content
    """
    # Prevent update if no clicks or no table selected
    if not table_name or view_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    # Determine if modal should be open
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Read execution history
    try:
        with open('execution_history.json', 'r') as f:
            execution_history = json.load(f)
    except Exception as e:
        logging.error(f"Error reading execution history: {e}")
        return False, html.Div("Error loading execution history")
    
    # Find the most recent execution for the table
    table_executions = [
        exec_data for exec_data in execution_history 
        if exec_data.get('table_name') == table_name
    ]
    
    if not table_executions:
        return False, html.Div("No execution history found for this table")
    
    # Sort to get the most recent execution
    latest_execution = max(table_executions, key=lambda x: x.get('timestamp', ''))
    
    # Prepare failed data display
    failed_data_content = []
    for rule_result in latest_execution.get('results', []):
        if not rule_result['passed']:
            # Create a card for each failed rule
            failed_data_card = dbc.Card(
                dbc.CardBody([
                    html.H5(rule_result['rule_name'], className="card-title"),
                    html.P(rule_result['description'], className="card-text text-muted"),
                    html.Div([
                        html.Strong("Failed Rows Indices: "),
                        ", ".join(map(str, rule_result['failed_indices']))
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Failed Rows Count: "),
                        str(rule_result['failed_rows_count'])
                    ], className="mb-2"),
                    dbc.Button(
                        "Fix Error", 
                        color="primary", 
                        className="mt-2",
                        id={'type': 'fix-error-btn', 'rule': rule_result['rule_name']}
                    )
                ])
            )
            failed_data_content.append(failed_data_card)
    
    # If no failed rules, show a message
    if not failed_data_content:
        failed_data_content = [
            html.Div("No failed rules found in the latest execution.", className="alert alert-success")
        ]
    
    # Create modal content
    modal_content = dbc.ModalBody([
        html.H3(f"Failed Rules for {table_name}", className="mb-4"),
        dbc.Container(failed_data_content, fluid=True)
    ])
    
    # Determine modal state
    is_open = trigger_id == 'view-failed-data-btn' and view_clicks is not None
    
    return is_open, modal_content

def create_failed_data_modal(table_name):
    """
    Create a modal to display failed data from rule execution
    
    Args:
        table_name (str): Name of the table for which failed data is being displayed
    
    Returns:
        dbc.Modal: A modal component with failed data table
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(f"Failed Data for {table_name}"),
            dbc.ModalBody(
                html.Div(id="failed-data-modal-body", children=[
                    html.P("No failed data to display.")
                ])
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-failed-data-modal", className="ms-auto")
            )
        ],
        id="failed-data-modal",
        size="xl",
        scrollable=True,
        is_open=False
    )

def safe_execute(func):
    """
    Decorator to provide safe execution with logging and error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            logging.error(traceback.format_exc())
            return html.Div([
                html.H3("An error occurred", className="text-danger"),
                html.P(str(e), className="text-muted")
            ])
    return wrapper

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
