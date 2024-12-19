from dash import html
import dash_bootstrap_components as dbc

def create_sidebar():
    return html.Div([
        html.H2("Navigation", className="display-6 mb-4"),
        dbc.Nav([
            dbc.NavLink("Overview", href="/", active="exact"),
            dbc.NavLink("Quality", href="/quality", active="exact"),
            dbc.NavLink("Column Analysis", href="/column-analysis", active="exact"),
            dbc.NavLink("Data Catalogue", href="/data-catalogue", active="exact"),
            dbc.NavLink("Rule Management", href="/rule-management", active="exact"),
            dbc.NavLink("Run Management", href="/run-management", active="exact"),
            dbc.NavLink("Failed Data", href="/failed-data", active="exact"),
            dbc.NavLink("Report", href="/report", active="exact"),
        ],
        vertical=True,
        pills=True,
        className="mb-3"
        )
    ], className="p-3 bg-light h-100") 