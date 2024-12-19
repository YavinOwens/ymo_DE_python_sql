from dash import html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import dash
from utils.data_loader import DataLoader
import logging
from datetime import datetime
import pandas as pd

data_loader = DataLoader()

def create_failed_data_summary(table_name: str, validation_results: dict) -> list:
    """Create summary cards for failed data analysis."""
    total_rules = validation_results.get('total_rules', 0)
    failed_rules = validation_results.get('failed_rules', 0)
    pass_rate = ((total_rules - failed_rules) / total_rules * 100) if total_rules > 0 else 0
    
    return [
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{failed_rules:,}", className="card-title"),
                    html.P("Failed Rules", className="card-text text-muted")
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{pass_rate:.1f}%", className="card-title"),
                    html.P("Pass Rate", className="card-text text-muted")
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(
                        datetime.fromisoformat(validation_results.get('timestamp', '')).strftime('%Y-%m-%d %H:%M')
                        if validation_results.get('timestamp') else "Never",
                        className="card-title"
                    ),
                    html.P("Last Validation", className="card-text text-muted")
                ])
            ])
        ], width=4)
    ]

def create_failed_rules_table(validation_results: dict) -> dash_table.DataTable:
    """Create a table showing failed validation rules."""
    failed_rules = [
        rule for rule in validation_results.get('rule_results', [])
        if not rule.get('passed', True)
    ]
    
    return dash_table.DataTable(
        id='failed-rules-table',
        columns=[
            {'name': 'Rule Name', 'id': 'rule_name'},
            {'name': 'Category', 'id': 'category'},
            {'name': 'Severity', 'id': 'severity'},
            {'name': 'Failed Count', 'id': 'failed_count'},
            {'name': 'Message', 'id': 'message'}
        ],
        data=failed_rules,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': 'var(--background)',
            'fontWeight': 'bold',
            'border': '1px solid var(--border)'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'severity', 'filter_query': '{severity} = "Critical"'},
                'backgroundColor': 'rgba(255, 0, 0, 0.1)',
                'color': 'red'
            },
            {
                'if': {'column_id': 'severity', 'filter_query': '{severity} = "High"'},
                'backgroundColor': 'rgba(255, 165, 0, 0.1)',
                'color': 'orange'
            }
        ],
        sort_action='native',
        sort_mode='multi',
        filter_action='native'
    )

def layout():
    """Create the failed data analysis page layout."""
    # Get available tables from DataLoader
    tables = data_loader.get_table_names()
    
    return html.Div([
        dcc.Store(id='failed-data-store', storage_type='memory'),
        
        # Header
        html.H2("Failed Data Analysis", className="mb-4"),
        html.P(
            "Select a table to view its failed data analysis and validation results.",
            className="lead mb-4"
        ),
        
        # Table selection
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Table Selection", className="card-title"),
                        dcc.Dropdown(
                            id="failed-data-table-dropdown",
                            options=[
                                {"label": table, "value": table}
                                for table in tables
                            ],
                            placeholder="Select a table...",
                            className="mb-3"
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-search me-2"), "Analyze Failed Data"],
                            id="analyze-failed-data-btn",
                            color="primary",
                            className="mt-3"
                        )
                    ])
                ])
            ], width=12, lg=6)
        ], justify="center", className="mb-4"),
        
        # Results section (initially hidden)
        html.Div(id="failed-data-results")
    ])

def register_callbacks(app):
    @app.callback(
        [Output('failed-data-store', 'data'),
         Output('failed-data-results', 'children')],
        [Input('analyze-failed-data-btn', 'n_clicks')],
        [State('failed-data-table-dropdown', 'value')],
        prevent_initial_call=True
    )
    def analyze_failed_data(n_clicks, table_name):
        """Analyze failed data for the selected table."""
        if not n_clicks or not table_name:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Get validation results
            validation_results = data_loader.run_validation_rules(table_name)
            
            if 'error' in validation_results:
                return None, dbc.Alert(
                    f"Error analyzing data: {validation_results['error']}",
                    color="danger",
                    className="mt-4"
                )
            
            # Create results layout
            results_layout = html.Div([
                # Summary cards
                dbc.Row(
                    create_failed_data_summary(table_name, validation_results),
                    className="mb-4"
                ),
                
                # Failed rules table
                html.H4("Failed Rules", className="mt-4 mb-3"),
                create_failed_rules_table(validation_results),
                
                # Export button
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Export Results"],
                    id="export-failed-data-btn",
                    color="secondary",
                    className="mt-4"
                )
            ])
            
            return validation_results, results_layout
            
        except Exception as e:
            logging.error(f"Error in analyze_failed_data: {str(e)}")
            return None, dbc.Alert(
                f"An error occurred: {str(e)}",
                color="danger",
                className="mt-4"
            )
    
    @app.callback(
        Output('failed-data-download', 'data'),
        Input('export-failed-data-btn', 'n_clicks'),
        State('failed-data-store', 'data'),
        prevent_initial_call=True
    )
    def export_failed_data(n_clicks, stored_data):
        """Export failed data analysis results."""
        if not n_clicks or not stored_data:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Convert stored data to DataFrame
            df = pd.DataFrame(stored_data.get('rule_results', []))
            
            # Return download component
            return dcc.send_data_frame(
                df.to_csv,
                f"failed_data_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                index=False
            )
        except Exception as e:
            logging.error(f"Error exporting failed data: {str(e)}")
            raise dash.exceptions.PreventUpdate