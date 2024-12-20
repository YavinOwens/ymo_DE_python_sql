from dash import html, dcc, dash_table, Input, Output, State, callback, callback_context
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import plotly.express as px
import pandas as pd
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
data_loader = DataLoader()

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Quality Analysis", className="mb-4"),
            
            # Rule Configuration Section
            dbc.Card([
                dbc.CardBody([
                    html.H4("Rule Configuration", className="mb-3"),
                    
                    # Rule Selector
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Rule Category"),
                            dcc.Dropdown(
                                id='rule-category-selector',
                                options=[],
                                placeholder="Select a rule category"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Select Rule"),
                            dcc.Dropdown(
                                id='rule-selector',
                                options=[],
                                placeholder="Select a rule"
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    # Table and Column Configuration
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Table"),
                            dcc.Dropdown(
                                id='table-selector',
                                options=[],
                                placeholder="Select a table"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Select Column"),
                            dcc.Dropdown(
                                id='column-selector',
                                options=[],
                                placeholder="Select a column"
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    # Save Configuration Button
                    dbc.Button(
                        "Save Configuration",
                        id="save-config-button",
                        color="primary",
                        className="mb-3"
                    ),
                    html.Div(id="save-config-status")
                ])
            ], className="mb-4"),
            
            # Assessment Controls
            dbc.Card([
                dbc.CardBody([
                    html.H4("Run Assessment", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Run All Rules",
                                id="run-all-button",
                                color="primary",
                                className="me-2"
                            ),
                            dbc.Button(
                                "Run Selected Rules",
                                id="run-selected-button",
                                color="secondary",
                                className="me-2"
                            ),
                            dbc.Button(
                                "Run By Table",
                                id="run-table-button",
                                color="info"
                            )
                        ])
                    ]),
                    dbc.Spinner(
                        html.Div(id="assessment-status", className="mt-3")
                    )
                ])
            ], className="mb-4"),
            
            # Results Summary Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Total Rules", className="card-title text-center"),
                            html.H2(id="total-rules", className="text-center")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Passed Rules", className="card-title text-center text-success"),
                            html.H2(id="passed-rules", className="text-center text-success")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Failed Rules", className="card-title text-center text-danger"),
                            html.H2(id="failed-rules", className="text-center text-danger")
                        ])
                    ])
                ], width=4),
            ], className="mb-4"),
        ])
    ])
])

# Combined callback for column selector updates
@callback(
    [Output('column-selector', 'options', allow_duplicate=True),
     Output('column-selector', 'value', allow_duplicate=True)],
    [Input('table-selector', 'value')],
    prevent_initial_call=True
)
def update_column_selector(table_name):
    """Update column selector options and value based on table selection."""
    if not table_name:
        return [], None
    try:
        columns = data_loader.get_table_columns(table_name)
        return [{'label': col, 'value': col} for col in columns], None
    except Exception as e:
        logger.error(f"Error getting columns for table {table_name}: {str(e)}")
        return [], None

# Callback to update rule selector based on category
@callback(
    Output('rule-selector', 'options'),
    [Input('rule-category-selector', 'value')]
)
def update_rule_options(category):
    if not category:
        return []
    try:
        # Add debug logging
        rules = data_loader.get_rules()
        logger.debug(f"Retrieved rules: {rules}")
        filtered_rules = [r for r in rules if r.get('category') == category]
        logger.debug(f"Filtered rules for category {category}: {filtered_rules}")
        return [{'label': f"{r['id']} - {r['name']}", 'value': r['id']} for r in filtered_rules]
    except Exception as e:
        logger.error(f"Error getting rules for category {category}: {str(e)}")
        return []

# Callback to initialize rule categories
@callback(
    Output('rule-category-selector', 'options'),
    Input('rule-category-selector', 'id')
)
def initialize_rule_categories(_):
    categories = data_loader.get_rule_categories()
    return [{'label': cat, 'value': cat} for cat in categories]

# Callback to initialize table selector
@callback(
    Output('table-selector', 'options'),
    Input('table-selector', 'id')
)
def initialize_table_selector(_):
    tables = data_loader.get_available_tables()
    return [{'label': table, 'value': table} for table in tables]

# Callback to save rule configuration
@callback(
    Output('save-config-status', 'children'),
    [Input('save-config-button', 'n_clicks')],
    [State('rule-selector', 'value'),
     State('table-selector', 'value'),
     State('column-selector', 'value')]
)
def save_rule_configuration(n_clicks, rule_id, table_name, column_name):
    if not n_clicks or not all([rule_id, table_name, column_name]):
        return ""
    
    try:
        data_loader.save_rule_configuration(rule_id, table_name, column_name)
        return html.Div("Configuration saved successfully!", className="text-success")
    except Exception as e:
        return html.Div(f"Error saving configuration: {str(e)}", className="text-danger")

# Combined assessment callback
@callback(
    [Output('assessment-status', 'children', allow_duplicate=True),
     Output('total-rules', 'children', allow_duplicate=True),
     Output('passed-rules', 'children', allow_duplicate=True),
     Output('failed-rules', 'children', allow_duplicate=True)],
    [Input('run-all-button', 'n_clicks'),
     Input('run-selected-button', 'n_clicks'),
     Input('run-table-button', 'n_clicks')],
    [State('rule-selector', 'value'),
     State('table-selector', 'value')],
    prevent_initial_call=True
)
def run_assessment(n_all, n_selected, n_table, selected_rule, selected_table):
    """Combined callback for all assessment operations."""
    ctx = callback_context
    if not ctx.triggered:
        return "", "0", "0", "0"
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        results = []
        passed_count = 0
        failed_count = 0
        
        if trigger_id == 'run-all-button':
            # Run all rules logic
            rules = data_loader.get_rules()
            for rule in rules:
                rule_config = data_loader.get_rule_configuration(rule['id'])
                if rule_config:
                    df = data_loader.get_table_data(rule_config['table_name'])
                    validation_result = data_loader.execute_rule(rule, df)
                    if validation_result is not None:
                        results.extend(data_loader.process_validation_result(
                            rule, df, validation_result, rule_config['table_name']
                        ))
                        if any(r['status'] == 'failed' for r in results):
                            failed_count += 1
                        else:
                            passed_count += 1
                            
        elif trigger_id == 'run-selected-button' and selected_rule:
            # Run selected rule logic
            rule_config = data_loader.get_rule_configuration(selected_rule)
            if not rule_config:
                return "No configuration found for selected rule", "0", "0", "0"
            
            df = data_loader.get_table_data(rule_config['table_name'])
            rule = next((r for r in data_loader.get_rules() if r['id'] == selected_rule), None)
            if rule:
                validation_result = data_loader.execute_rule(rule, df)
                if validation_result is not None:
                    results.extend(data_loader.process_validation_result(
                        rule, df, validation_result, rule_config['table_name']
                    ))
                    if any(r['status'] == 'failed' for r in results):
                        failed_count += 1
                    else:
                        passed_count += 1
                        
        elif trigger_id == 'run-table-button' and selected_table:
            # Run table rules logic
            table_rules = data_loader.get_table_rules(selected_table)
            if not table_rules:
                return f"No rules configured for table {selected_table}", "0", "0", "0"
            
            df = data_loader.get_table_data(selected_table)
            for rule in table_rules:
                validation_result = data_loader.execute_rule(rule, df)
                if validation_result is not None:
                    results.extend(data_loader.process_validation_result(
                        rule, df, validation_result, selected_table
                    ))
                    if any(r['status'] == 'failed' for r in results):
                        failed_count += 1
                    else:
                        passed_count += 1
        
        # Save results
        if results:
            data_loader.save_validation_results(results)
        
        total_rules = passed_count + failed_count
        success_message = f"Assessment completed. Processed {total_rules} rules."
        
        return success_message, str(total_rules), str(passed_count), str(failed_count)
        
    except Exception as e:
        error_message = f"Error in assessment: {str(e)}"
        logger.error(error_message)
        return error_message, "0", "0", "0"

