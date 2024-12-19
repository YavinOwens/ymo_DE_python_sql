from dash import html, dcc, dash_table, Input, Output, State, dash
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
import re

data_loader = DataLoader()

def load_rule_templates():
    """Load rule templates from JSON file."""
    try:
        with open('BONUS/assets/data/rule_templates.json', 'r') as f:
            templates = json.load(f)
        return templates
    except Exception as e:
        print(f"Error loading rule templates: {str(e)}")
        return {}

def run_validation_rule(df: pd.DataFrame, rule: dict, column_name: str = None) -> dict:
    """Run a single validation rule on the data."""
    try:
        # Replace column_name placeholder in validation code
        validation_code = rule['validation_code']
        if column_name:
            validation_code = validation_code.replace('column_name', f"'{column_name}'")
        
        # Execute validation code
        result = eval(validation_code, {'df': df, 'pd': pd, 'np': np, 're': re})
        
        if isinstance(result, pd.Series):
            failed_count = result.sum()
            status = 'failed' if failed_count > 0 else 'success'
            message = rule['message']
            if column_name:
                message = message.replace('Column', f"Column '{column_name}'")
            
            return {
                'rule_name': rule['name'],
                'column': column_name or 'N/A',
                'message': f"{message} ({failed_count} violations)" if failed_count > 0 else 'Pass',
                'severity': rule['severity'],
                'status': status,
                'violations': int(failed_count)
            }
        return {
            'rule_name': rule['name'],
            'column': column_name or 'N/A',
            'message': 'Unable to evaluate rule',
            'severity': rule['severity'],
            'status': 'error',
            'violations': 0
        }
    except Exception as e:
        return {
            'rule_name': rule['name'],
            'column': column_name or 'N/A',
            'message': f"Error: {str(e)}",
            'severity': rule['severity'],
            'status': 'error',
            'violations': 0
        }

def run_data_quality_checks(df: pd.DataFrame, table_name: str) -> dict:
    """Run data quality checks using rules from templates."""
    templates = load_rule_templates()
    if not templates:
        return {
            'total_rules': 0,
            'failed_rules': 0,
            'rule_results': []
        }
    
    results = {
        'total_rules': 0,
        'failed_rules': 0,
        'rule_results': []
    }
    
    # Run GDPR rules
    for rule in templates.get('gdpr_rules', []):
        if rule.get('active', False):
            for column in df.columns:
                results['total_rules'] += 1
                rule_result = run_validation_rule(df, rule, column)
                if rule_result['status'] in ['failed', 'error']:
                    results['failed_rules'] += 1
                results['rule_results'].append(rule_result)
    
    # Run data quality rules
    for rule in templates.get('data_quality_rules', []):
        if rule.get('active', False) and 'validation_code' in rule:
            results['total_rules'] += 1
            rule_result = run_validation_rule(df, rule)
            if rule_result['status'] in ['failed', 'error']:
                results['failed_rules'] += 1
            results['rule_results'].append(rule_result)
    
    # Run table-specific rules if they exist
    table_rules_key = f"{table_name.lower()}_table_rules"
    if table_rules_key in templates.get('table_specific_rules', {}):
        for rule in templates['table_specific_rules'][table_rules_key]:
            if rule.get('active', False) and 'validation_code' in rule:
                results['total_rules'] += 1
                rule_result = run_validation_rule(df, rule)
                if rule_result['status'] in ['failed', 'error']:
                    results['failed_rules'] += 1
                results['rule_results'].append(rule_result)
    
    # Run table-level rules
    for rule in templates.get('table_level_rules', []):
        if rule.get('active', False):
            results['total_rules'] += 1
            rule_result = run_validation_rule(df, rule)
            if rule_result['status'] in ['failed', 'error']:
                results['failed_rules'] += 1
            results['rule_results'].append(rule_result)
    
    return results

def create_execution_record(data_source: str, results: dict) -> dict:
    """Create an execution record from rule results."""
    now = datetime.now()
    return {
        'run_id': f"RUN_{now.strftime('%Y%m%d_%H%M%S')}",
        'start_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'failed' if results['failed_rules'] > 0 else 'success',
        'data_source': data_source,
        'rules_executed': results['total_rules'],
        'failed_rules': results['failed_rules'],
        'rule_results': results['rule_results']
    }

def save_execution_history(execution_record: dict):
    """Save execution record to history file."""
    history_path = 'BONUS/assets/data/execution_history.json'
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    
    try:
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(execution_record)
        
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error saving execution history: {str(e)}")

def create_rule_results_table(rule_results):
    """Create a DataTable for rule results."""
    if not rule_results:
        return html.Div("No rule results available", className="text-muted")
    
    return dash_table.DataTable(
        data=rule_results,
        columns=[
            {'name': 'Rule', 'id': 'rule_name'},
            {'name': 'Column', 'id': 'column'},
            {'name': 'Status', 'id': 'status'},
            {'name': 'Severity', 'id': 'severity'},
            {'name': 'Message', 'id': 'message'},
            {'name': 'Violations', 'id': 'violations'}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '12px'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'border': '1px solid rgb(200, 200, 200)'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{status} = "success"'},
                'color': 'green'
            },
            {
                'if': {'filter_query': '{status} = "failed"'},
                'color': 'red'
            },
            {
                'if': {'filter_query': '{status} = "error"'},
                'color': 'orange'
            },
            {
                'if': {'filter_query': '{severity} = "Critical"'},
                'backgroundColor': 'rgba(255, 0, 0, 0.1)'
            },
            {
                'if': {'filter_query': '{severity} = "High"'},
                'backgroundColor': 'rgba(255, 165, 0, 0.1)'
            }
        ],
        sort_action='native',
        sort_mode='multi',
        filter_action='native'
    )

def layout():
    """Create the run management page layout."""
    try:
        # Load execution history
        history_path = 'BONUS/assets/data/execution_history.json'
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                execution_history = json.load(f)
                # Create a simplified version for the history table
                history_table_data = [
                    {
                        'run_id': record['run_id'],
                        'data_source': record['data_source'],
                        'start_time': record['start_time'],
                        'end_time': record['end_time'],
                        'status': record['status'],
                        'rules_executed': record['rules_executed'],
                        'failed_rules': record['failed_rules']
                    }
                    for record in execution_history
                ]
        else:
            execution_history = []
            history_table_data = []
        
        # Calculate statistics
        total_runs = len(execution_history)
        successful_runs = sum(1 for run in execution_history if run.get('status') == 'success')
        failed_runs = total_runs - successful_runs
        
        return html.Div([
            # Header with stats
            html.Div([
                html.H2("Run Management", className="mb-0"),
                html.Div([
                    html.Span(f"{total_runs} Total Runs", className="text-muted me-3"),
                    html.Span(f"{successful_runs} Successful", className="text-success me-3"),
                    html.Span(f"{failed_runs} Failed", className="text-danger")
                ], className="rule-stats-inline")
            ], className="page-header"),
            
            # Run controls
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="bi bi-play-fill me-2"), "Start New Run"],
                        id="start-run-btn",
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                        id="refresh-run-btn",
                        color="secondary"
                    )
                ], className="mb-4")
            ]),
            
            # Latest Run Summary
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Latest Run Summary"),
                        dbc.CardBody(
                            create_rule_results_table(execution_history[-1]['rule_results']) if execution_history else "No runs yet"
                        )
                    ], className="mb-4")
                ])
            ]) if execution_history else None,
            
            # Execution history table
            dbc.Row([
                dbc.Col([
                    dash_table.DataTable(
                        id='execution-history-table',
                        columns=[
                            {'name': 'Run ID', 'id': 'run_id'},
                            {'name': 'Data Source', 'id': 'data_source'},
                            {'name': 'Start Time', 'id': 'start_time'},
                            {'name': 'End Time', 'id': 'end_time'},
                            {'name': 'Status', 'id': 'status'},
                            {'name': 'Rules Executed', 'id': 'rules_executed'},
                            {'name': 'Failed Rules', 'id': 'failed_rules'}
                        ],
                        data=history_table_data,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '12px'},
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold',
                            'border': '1px solid rgb(200, 200, 200)'
                        },
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{status} = "success"'},
                                'color': 'green'
                            },
                            {
                                'if': {'filter_query': '{status} = "failed"'},
                                'color': 'red'
                            }
                        ],
                        sort_action='native',
                        sort_mode='multi',
                        sort_by=[{'column_id': 'start_time', 'direction': 'desc'}]
                    )
                ])
            ])
        ])
    except Exception as e:
        return html.Div([
            html.H2("Run Management", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading run management: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ])

def init_callbacks(app):
    """Initialize callbacks for run management page."""
    
    @app.callback(
        [Output('execution-history-table', 'data'),
         Output('execution-history-table', 'style_data_conditional')],
        [Input('start-run-btn', 'n_clicks'),
         Input('refresh-run-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_run_buttons(start_clicks, refresh_clicks):
        """Handle run and refresh button clicks."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if button_id == 'start-run-btn':
                # Get current data source info
                source_type = data_loader.current_source
                table_name = data_loader.current_table
                
                if not source_type or (source_type == "Sample Database" and not table_name):
                    raise ValueError("Please select a data source and table first")
                
                # Get data and run checks
                df = data_loader.get_table_data()
                if df.empty:
                    raise ValueError("No data available to validate")
                
                results = run_data_quality_checks(df, table_name)
                record = create_execution_record(
                    f"{source_type} - {table_name}" if table_name else source_type,
                    results
                )
                save_execution_history(record)
            
            # Load and return updated history
            with open('BONUS/assets/data/execution_history.json', 'r') as f:
                history = json.load(f)
            
            # Create simplified history data for table
            history_data = [
                {
                    'run_id': record['run_id'],
                    'data_source': record['data_source'],
                    'start_time': record['start_time'],
                    'end_time': record['end_time'],
                    'status': record['status'],
                    'rules_executed': record['rules_executed'],
                    'failed_rules': record['failed_rules']
                }
                for record in history
            ]
            
            # Style conditional for status column
            style_data_conditional = [
                {
                    'if': {'filter_query': '{status} = "success"'},
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{status} = "failed"'},
                    'color': 'red'
                }
            ]
            
            return history_data, style_data_conditional
        
        except Exception as e:
            # Return empty data with error styling
            return [], [
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]