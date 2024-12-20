from dash import html
import dash_bootstrap_components as dbc

def create_navigation():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Overview", href="/")),
            dbc.NavItem(dbc.NavLink("Quality Analysis", href="/quality")),
            dbc.NavItem(dbc.NavLink("Column Analysis", href="/column-analysis")),
            dbc.NavItem(dbc.NavLink("Rule Management", href="/rule-management")),
        ],
        brand="Data Quality Dashboard",
        brand_href="/",
        color="primary",
        dark=True,
    ) 