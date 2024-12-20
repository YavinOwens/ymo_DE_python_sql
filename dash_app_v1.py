import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import logging
from components.navigation import create_navigation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the DataLoader with cache clearing
data_loader = DataLoader()

# Initialize the Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

# Import your pages after app initialization to avoid circular imports
from pages import quality, rule_management, column_analysis, overview

# Create the layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    
    # Navigation
    create_navigation(),
    
    # Content
    html.Div(id='page-content', className="mt-4")
], fluid=True)

# Callback for page routing
@app.callback(
    dash.Output('page-content', 'children'),
    [dash.Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/quality':
        return quality.layout
    elif pathname == '/column-analysis':
        return column_analysis.layout
    elif pathname == '/rule-management':
        return rule_management.layout
    else:
        return overview.layout

if __name__ == '__main__':
    app.run_server(debug=True) 