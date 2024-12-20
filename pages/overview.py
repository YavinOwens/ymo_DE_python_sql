from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import plotly.express as px

data_loader = DataLoader()

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Overview", className="mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Data Quality Summary"),
                    dcc.Graph(
                        id='quality-summary',
                        figure=px.pie(
                            names=['Passed', 'Failed'],
                            values=[80, 20],
                            title='Validation Results'
                        )
                    )
                ])
            ])
        ])
    ])
]) 