from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import logging

data_loader = DataLoader()

def layout(table_name=None):
    """Create the data catalogue content showing metadata about tables and columns."""
    try:
        tables = data_loader.get_available_tables()
        
        if not table_name:
            # Show overview of all tables
            table_cards = []
            for table_info in tables:
                card = dbc.Card([
                    dbc.CardHeader(html.H5(table_info['name'], className="mb-0")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Strong("Rows: "),
                                    f"{table_info['row_count']:,}"
                                ], className="mb-2"),
                                html.Div([
                                    html.Strong("Columns: "),
                                    str(table_info['column_count'])
                                ])
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="bi bi-table me-2"), "View Details"],
                                    href=f"/catalogue?table={table_info['name']}",
                                    color="primary",
                                    size="sm",
                                    className="float-end"
                                )
                            ], width=6)
                        ])
                    ])
                ], className="mb-3")
                table_cards.append(card)

            return html.Div([
                html.H2("Data Catalogue", className="mb-4"),
                html.P(
                    "Select a table to view detailed schema information and metadata.",
                    className="lead mb-4"
                ),
                dbc.Row([
                    dbc.Col(card, width=12, lg=6) for card in table_cards
                ])
            ])
        else:
            # Show detailed view of selected table
            metadata = data_loader.get_table_metadata(table_name)
            if not metadata:
                return html.Div([
                    html.H2("Data Catalogue", className="mb-4"),
                    dbc.Alert(f"Table {table_name} not found", color="danger")
                ])
            
            return html.Div([
                # Header with table name and basic info
                html.H2(f"Table: {table_name}", className="mb-4"),
                
                # Overview cards
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{metadata['row_count']:,}", className="card-title"),
                                html.P("Total Rows", className="card-text text-muted")
                            ])
                        ])
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(str(metadata['column_count']), className="card-title"),
                                html.P("Total Columns", className="card-text text-muted")
                            ])
                        ])
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{metadata['memory_usage']/1024/1024:.1f} MB", className="card-title"),
                                html.P("Memory Usage", className="card-text text-muted")
                            ])
                        ])
                    ], width=4)
                ], className="mb-4"),
                
                # Column details table
                html.H4("Column Details", className="mt-4 mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=[
                                {
                                    'Column': col['name'],
                                    'Type': col['type'],
                                    'Missing Values': col['null_count'],
                                    'Missing %': f"{(col['null_count']/metadata['row_count']*100):.1f}%"
                                }
                                for col in metadata['columns']
                            ],
                            columns=[
                                {'name': 'Column', 'id': 'Column'},
                                {'name': 'Type', 'id': 'Type'},
                                {'name': 'Missing Values', 'id': 'Missing Values'},
                                {'name': 'Missing %', 'id': 'Missing %'}
                            ],
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
                            }
                        )
                    ])
                ])
            ])
    except Exception as e:
        logging.error(f"Error in catalogue layout: {str(e)}")
        return html.Div([
            html.H2("Data Catalogue", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading catalogue: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ]) 