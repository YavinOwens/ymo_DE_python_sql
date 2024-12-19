import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import logging

# Import pages
from pages import overview, quality, column_analysis, catalogue, rule_management, run_management, failed_data, report

# Import components
from components.navigation import create_sidebar, init_callbacks

# Initialize the app with custom styles
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Custom styles for the app
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Data Quality Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .app-container {
                min-height: 100vh;
                padding: 1rem;
            }
            .sidebar-col {
                background-color: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                padding: 1.5rem;
                min-height: calc(100vh - 2rem);
                border-radius: 8px;
            }
            .content-col {
                padding: 1.5rem;
                background-color: white;
                min-height: calc(100vh - 2rem);
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .nav-link {
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                border-radius: 4px;
                transition: all 0.2s ease;
            }
            .nav-link:hover {
                background-color: #f8f9fa;
            }
            .nav-link.active {
                background-color: #e9ecef;
                font-weight: bold;
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

# Create the app layout
app.layout = html.Div([
    dcc.Store(id='data-loader-store'),
    dbc.Container([
        dbc.Row([
            # Sidebar
            dbc.Col(
                create_sidebar(),
                width=3,
                className="sidebar-col me-3"
            ),
            # Main content
            dbc.Col([
                dcc.Location(id='url', refresh=False),
                html.Div(
                    id='page-content',
                    className="h-100 overflow-auto"
                )
            ],
            width=8,
            className="content-col"
            )
        ],
        className="g-3 h-100"
        )
    ],
    fluid=True,
    className="app-container"
    )
],
className="h-100"
)

# Initialize navigation callbacks
init_callbacks(app)

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'),
     Input('data-loader-store', 'data')]
)
def display_page(pathname, data_source):
    """Route to the appropriate page based on URL pathname."""
    try:
        pages = {
            '/': overview.layout,
            '/quality': quality.layout,
            '/column-analysis': column_analysis.layout,
            '/catalogue': catalogue.layout,
            '/rule-management': rule_management.layout,
            '/run-management': run_management.layout,
            '/failed-data': failed_data.layout,
            '/report': report.layout
        }
        
        return pages.get(pathname, overview.layout)()
    
    except Exception as e:
        logging.error(f"Error displaying page {pathname}: {str(e)}")
        return dbc.Container([
            html.H2("Error", className="text-danger mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading page: {str(e)}"
                ],
                color="danger",
                className="error-state mb-4"
            ),
            dbc.Button(
                [html.I(className="bi bi-arrow-left me-2"), "Return to Overview"],
                href="/",
                color="primary"
            )
        ],
        className="py-4"
        )

if __name__ == '__main__':
    app.run_server(debug=True, port=8050) 