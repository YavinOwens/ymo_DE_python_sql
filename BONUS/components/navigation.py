from dash import html, dcc, dash_table, ALL, MATCH, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from utils.data_loader import DataLoader
import logging

data_loader = DataLoader()

def create_sidebar():
    """Create the navigation sidebar with table selector."""
    return html.Div([
        html.H4("Data Quality Dashboard", className="mb-4"),
        
        # Table Selector
        html.Div([
            html.H6("Select Table", className="mb-2"),
            dcc.Dropdown(
                id="table-selector",
                options=[
                    {"label": table, "value": table}
                    for table in data_loader.get_table_names()
                ],
                placeholder="Select a table...",
                className="mb-3"
            ),
            
            # Table Info
            html.Div(
                id="table-info",
                className="mb-3 text-muted small"
            )
        ], className="mb-4"),
        
        # Navigation Links
        html.H6("Navigation", className="mb-3"),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="bi bi-house me-2"), "Overview"],
                    href="/",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-shield-check me-2"), "Quality Metrics"],
                    href="/quality",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-bar-chart me-2"), "Column Analysis"],
                    href="/column-analysis",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-table me-2"), "Data Catalogue"],
                    href="/catalogue",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-gear me-2"), "Rule Management"],
                    href="/rule-management",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-play-circle me-2"), "Run Management"],
                    href="/run-management",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-exclamation-triangle me-2"), "Failed Data"],
                    href="/failed-data",
                    active="exact"
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-file-text me-2"), "Reports"],
                    href="/report",
                    active="exact"
                )
            ],
            vertical=True,
            pills=True,
            className="nav-pills-custom"
        ),
        
        # Database Info
        html.Div([
            html.Hr(),
            html.H6("Database Info", className="mb-2"),
            html.P(
                f"Connected to: {data_loader.db_path}",
                className="text-muted small mb-1",
                style={"wordBreak": "break-all"}
            )
        ], className="mt-4")
    ], className="sidebar bg-light p-4 h-100")

def init_callbacks(app):
    """Initialize callbacks for navigation components."""
    
    @app.callback(
        Output("table-info", "children"),
        [Input("table-selector", "value")]
    )
    def update_table_info(selected_table):
        """Update the table information display."""
        if not selected_table:
            return "No table selected"
        
        try:
            metadata = data_loader.get_table_metadata(selected_table)
            if not metadata:
                return "Error loading table metadata"
            
            return html.Div([
                html.P(f"Rows: {metadata['row_count']:,}", className="mb-1"),
                html.P(f"Columns: {metadata['column_count']}", className="mb-1"),
                html.P(
                    f"Last Validated: {metadata['last_validated'] or 'Never'}",
                    className="mb-1"
                )
            ])
        
        except Exception as e:
            logging.error(f"Error updating table info: {str(e)}")
            return f"Error: {str(e)}"
    
    @app.callback(
        Output("data-loader-store", "data"),
        [Input("table-selector", "value")]
    )
    def update_data_source(selected_table):
        """Update the data source in the store."""
        if not selected_table:
            return {}
        
        try:
            metadata = data_loader.get_table_metadata(selected_table)
            if not metadata:
                return {"error": "Failed to load table metadata"}
            
            return {
                "table": selected_table,
                "metadata": metadata
            }
        
        except Exception as e:
            logging.error(f"Error updating data source: {str(e)}")
            return {"error": str(e)}