from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from utils.data_loader import DataLoader
import logging
import json
import os

data_loader = DataLoader()

def layout():
    """Create a page to select a table for viewing failed data."""
    return html.Div([
        html.H2("Failed Data Analysis", className="mb-4"),
        html.P(
            "Select a table to view its failed data analysis and validation results.",
            className="lead mb-4"
        ),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Table Selection", className="card-title"),
                        dcc.Dropdown(
                            id="failed-data-table-dropdown",
                            options=[
                                {"label": table, "value": table}
                                for table in data_loader.get_table_names()
                            ],
                            placeholder="Select a table...",
                            className="mb-3"
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-search me-2"), "View Failed Data"],
                            id="view-failed-data-btn",
                            color="primary",
                            className="mt-3"
                        )
                    ])
                ])
            ], width=12, lg=6)
        ], justify="center")
    ])

def detail_layout(table_name):
    """Create a page layout to display failed data from the execution history."""
    try:
        # Load failed data for the table
        failed_data_path = f'BONUS/assets/data/failed_data/{table_name}.json'
        if os.path.exists(failed_data_path):
            with open(failed_data_path, 'r') as f:
                failed_data = json.load(f)
        else:
            failed_data = {
                'validation_results': [],
                'failed_records': [],
                'summary': {
                    'total_records': 0,
                    'failed_records': 0,
                    'failure_rate': 0,
                    'last_updated': None
                }
            }
        
        return html.Div([
            # Header with summary stats
            html.H2(f"Failed Data Analysis: {table_name}", className="mb-4"),
            
            # Summary cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(
                                f"{failed_data['summary']['failed_records']:,}",
                                className="card-title"
                            ),
                            html.P("Failed Records", className="card-text text-muted")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(
                                f"{failed_data['summary']['failure_rate']:.1f}%",
                                className="card-title"
                            ),
                            html.P("Failure Rate", className="card-text text-muted")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(
                                failed_data['summary']['last_updated'] or "Never",
                                className="card-title"
                            ),
                            html.P("Last Updated", className="card-text text-muted")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Validation Results
            html.H4("Validation Results", className="mt-4 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    dash_table.DataTable(
                        id='validation-results-table',
                        columns=[
                            {'name': 'Rule', 'id': 'rule'},
                            {'name': 'Failed Records', 'id': 'failed_records'},
                            {'name': 'Failure Rate', 'id': 'failure_rate'},
                            {'name': 'Last Failed', 'id': 'last_failed'}
                        ],
                        data=failed_data['validation_results'],
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
                        sort_action='native',
                        sort_mode='multi',
                        filter_action='native'
                    )
                ])
            ], className="mb-4"),
            
            # Failed Records
            html.H4("Failed Records", className="mt-4 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    dash_table.DataTable(
                        id='failed-records-table',
                        columns=[
                            {'name': col, 'id': col}
                            for col in (failed_data['failed_records'][0].keys() if failed_data['failed_records'] else [])
                        ],
                        data=failed_data['failed_records'],
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
                        sort_action='native',
                        sort_mode='multi',
                        filter_action='native',
                        page_action='native',
                        page_size=10
                    )
                ])
            ])
        ])
    except Exception as e:
        logging.error(f"Error in failed_data detail_layout: {str(e)}")
        return html.Div([
            html.H2("Failed Data Analysis", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading failed data: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ])

def register_callbacks(app):
    @app.callback(
        Output('url', 'pathname'),
        [Input('view-failed-data-btn', 'n_clicks')],
        [State('failed-data-table-dropdown', 'value')],
        prevent_initial_call=True
    )
    def navigate_to_failed_data_details(n_clicks, selected_table):
        """Navigate to the failed data details page for the selected table."""
        if n_clicks and selected_table:
            return f"/failed-data/{selected_table}"
        raise dash.exceptions.PreventUpdate 