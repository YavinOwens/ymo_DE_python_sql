from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import logging

data_loader = DataLoader()

def layout(table_name=None):
    """Creates an overview content with consistent layout and enhanced data presentation."""
    if not table_name:
        return html.Div([
            html.H2("Overview", className="mb-4"),
            html.P("Welcome to the Data Quality Dashboard. Please select a table to begin analysis.", className="lead"),
            html.Hr(),
            dbc.Alert("No table selected. Choose a table from the sidebar to view detailed metrics.", color="info")
        ])
    
    try:
        # Get table stats using DataLoader
        table_data = data_loader.get_table_data(table_name)
        row_count = len(table_data)
        col_count = len(table_data.columns)
        
        return html.Div([
            # Header with table name
            html.H2(f"Overview: {table_name}", className="mb-4"),
            
            # Key metrics cards
            dbc.Row([
                # Total Rows Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{row_count:,}", className="card-title"),
                            html.P("Total Rows", className="card-text text-muted")
                        ])
                    ], className="mb-3")
                ], width=4),
                
                # Total Columns Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(str(col_count), className="card-title"),
                            html.P("Total Columns", className="card-text text-muted")
                        ])
                    ], className="mb-3")
                ], width=4),
                
                # Memory Usage Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{table_data.memory_usage().sum()/1024/1024:.1f} MB", className="card-title"),
                            html.P("Memory Usage", className="card-text text-muted")
                        ])
                    ], className="mb-3")
                ], width=4)
            ]),
            
            # Data Quality Summary
            html.H3("Data Quality Summary", className="mt-4 mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Completeness"),
                        dbc.CardBody([
                            html.H5(f"{(1 - table_data.isnull().sum().sum()/(row_count*col_count))*100:.1f}%"),
                            html.P("Overall data completeness")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Uniqueness"),
                        dbc.CardBody([
                            html.H5(f"{(1 - len(table_data.duplicated())/(row_count))*100:.1f}%"),
                            html.P("Unique records")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Recent Activity
            html.H3("Recent Activity", className="mt-4 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.P("No recent activity to display", className="text-muted")
                    # Add actual activity data here when available
                ])
            ])
        ])
    except Exception as e:
        logging.error(f"Error in overview layout: {str(e)}")
        return html.Div([
            html.H2("Overview", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading overview data: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ]) 