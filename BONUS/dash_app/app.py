import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from components.navigation import create_sidebar
import pages.overview
import pages.quality
import pages.column_analysis
import pages.data_catalogue
import pages.rule_management
import pages.run_management
import pages.failed_data
import pages.report

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Container([
        dbc.Row([
            dbc.Col(create_sidebar(), width=2),
            dbc.Col(html.Div(id='page-content'), width=10)
        ])
    ], fluid=True)
])

@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        return pages.overview.layout
    elif pathname == '/quality':
        return pages.quality.layout
    elif pathname == '/column-analysis':
        return pages.column_analysis.layout
    elif pathname == '/data-catalogue':
        return pages.data_catalogue.layout
    elif pathname == '/rule-management':
        return pages.rule_management.layout
    elif pathname == '/run-management':
        return pages.run_management.layout
    elif pathname == '/failed-data':
        return pages.failed_data.layout
    elif pathname == '/report':
        return pages.report.layout
    else:
        return pages.overview.layout

if __name__ == '__main__':
    app.run_server(debug=True) 