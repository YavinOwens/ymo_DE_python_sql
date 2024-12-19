from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import os
from config import DB_PATH, DATA_DIR

data_loader = DataLoader()

def create_sidebar():
    """Create the navigation sidebar with data source selection."""
    return html.Div([
        html.H4("Data Quality Dashboard", className="mb-4"),
        
        # Data Source Selection Accordion
        dbc.Accordion([
            dbc.AccordionItem([
                # Database Selection
                dbc.RadioItems(
                    id='data-source-type',
                    options=[
                        {'label': 'SQLite Database', 'value': 'sqlite'},
                        {'label': 'Data Files', 'value': 'files'}
                    ],
                    value='sqlite',
                    className="mb-3"
                ),
                
                # Engine Selection
                dbc.Label("Data Processing Engine:", className="mt-3"),
                dbc.RadioItems(
                    id='data-engine',
                    options=[
                        {'label': 'Pandas', 'value': 'pandas'},
                        {'label': 'Polars', 'value': 'polars'}
                    ],
                    value='polars',
                    className="mb-3"
                ),
                
                # File Selection (shown only when files are selected)
                html.Div(
                    id='file-selection-div',
                    children=[
                        dbc.Label("Select Data File:"),
                        dcc.Dropdown(
                            id='file-selector',
                            options=[],
                            placeholder="Select a data file",
                            className="mb-3"
                        )
                    ],
                    style={'display': 'none'}
                ),
                
                # Table Selection (shown only when database is selected)
                html.Div(
                    id='table-selection-div',
                    children=[
                        dbc.Label("Select Database Table:"),
                        dcc.Dropdown(
                            id='table-selector',
                            options=[],
                            placeholder="Select a table",
                            className="mb-3"
                        )
                    ]
                ),
                
                # Load Data Button
                dbc.Button(
                    "Load Data",
                    id="load-data-btn",
                    color="primary",
                    className="w-100 mt-2"
                ),
                
                # Status Message
                html.Div(
                    id="data-load-status",
                    className="mt-2"
                )
            ], title="Data Source Selection", item_id="data-source")
        ], start_collapsed=False, id="sidebar-accordion"),
        
        # Navigation Links
        html.Hr(),
        dbc.Nav([
            dbc.NavLink("Overview", href="/", active="exact"),
            dbc.NavLink("Quality Check", href="/quality", active="exact"),
            dbc.NavLink("Column Analysis", href="/column-analysis", active="exact"),
            dbc.NavLink("Data Catalogue", href="/catalogue", active="exact"),
            dbc.NavLink("Rule Management", href="/rule-management", active="exact"),
            dbc.NavLink("Run Management", href="/run-management", active="exact"),
            dbc.NavLink("Failed Data", href="/failed-data", active="exact"),
            dbc.NavLink("Report", href="/report", active="exact")
        ], vertical=True, pills=True)
    ])

def init_callbacks(app):
    """Initialize navigation callbacks."""
    
    @app.callback(
        [Output('file-selection-div', 'style'),
         Output('table-selection-div', 'style'),
         Output('file-selector', 'options'),
         Output('table-selector', 'options')],
        [Input('data-source-type', 'value')]
    )
    def update_source_selection(source_type):
        """Update the visibility and options of source selection components."""
        try:
            if source_type == 'files':
                # Get available data files from DATA_DIR
                files = [f for f in os.listdir(DATA_DIR) 
                        if f.endswith(('.csv', '.json', '.parquet'))]
                file_options = [{'label': f, 'value': f} for f in files]
                return (
                    {'display': 'block'},
                    {'display': 'none'},
                    file_options,
                    []
                )
            else:
                # Get available tables from database
                tables = data_loader.get_table_names()
                table_options = [{'label': t, 'value': t} for t in tables]
                return (
                    {'display': 'none'},
                    {'display': 'block'},
                    [],
                    table_options
                )
        except Exception as e:
            return (
                {'display': 'none'},
                {'display': 'block'},
                [],
                []
            )
    
    @app.callback(
        [Output('data-load-status', 'children'),
         Output('data-loader-store', 'data')],
        [Input('load-data-btn', 'n_clicks')],
        [State('data-source-type', 'value'),
         State('data-engine', 'value'),
         State('file-selector', 'value'),
         State('table-selector', 'value')]
    )
    def load_data_source(n_clicks, source_type, engine, file_name, table_name):
        """Load the selected data source with the chosen engine."""
        if not n_clicks:
            return "", {}
        
        try:
            # Create data source configuration
            data_config = {
                'source_type': source_type,
                'engine': engine,
                'source': file_name if source_type == 'files' else table_name
            }
            
            # Validate selection
            if source_type == 'files' and not file_name:
                return dbc.Alert("Please select a data file", color="warning"), {}
            elif source_type == 'sqlite' and not table_name:
                return dbc.Alert("Please select a database table", color="warning"), {}
            
            # Store the configuration
            return (
                dbc.Alert(
                    f"Successfully loaded data from {data_config['source']} using {engine}",
                    color="success"
                ),
                data_config
            )
            
        except Exception as e:
            return dbc.Alert(f"Error loading data: {str(e)}", color="danger"), {}