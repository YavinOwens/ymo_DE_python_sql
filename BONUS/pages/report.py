from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import DataLoader
import logging
import pandas as pd

data_loader = DataLoader()

def create_quality_trend_chart(table_name):
    """Create a line chart showing quality trends over time."""
    try:
        # In a real application, this would load historical quality data
        # For now, we'll create some dummy data
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        quality_scores = {
            'Completeness': [90 + i for i in range(len(dates))],
            'Uniqueness': [85 + i * 0.5 for i in range(len(dates))],
            'Consistency': [88 + i * 0.3 for i in range(len(dates))]
        }
        
        fig = go.Figure()
        for metric, scores in quality_scores.items():
            fig.add_trace(go.Scatter(
                x=dates,
                y=scores,
                name=metric,
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title=f"Quality Trends for {table_name}",
            xaxis_title="Date",
            yaxis_title="Quality Score (%)",
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error creating quality trend chart: {str(e)}")
        return None

def create_issue_distribution_chart(table_name):
    """Create a pie chart showing distribution of quality issues."""
    try:
        # In a real application, this would load actual issue data
        # For now, we'll create some dummy data
        issues = {
            'Missing Values': 45,
            'Invalid Format': 25,
            'Duplicates': 15,
            'Out of Range': 10,
            'Other': 5
        }
        
        fig = px.pie(
            values=list(issues.values()),
            names=list(issues.keys()),
            title=f"Quality Issues Distribution for {table_name}"
        )
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error creating issue distribution chart: {str(e)}")
        return None

def layout(table_name=None):
    """Creates a report page with high-level cards for each column."""
    if not table_name:
        return html.Div([
            html.H2("Data Quality Report", className="mb-4"),
            dbc.Alert("Select a table to view quality reports", color="info")
        ])
    
    try:
        # Get table metadata
        metadata = data_loader.get_table_metadata(table_name)
        if not metadata:
            return html.Div([
                html.H2("Data Quality Report", className="mb-4"),
                dbc.Alert(f"Table {table_name} not found", color="danger")
            ])
        
        # Create quality trend chart
        trend_chart = create_quality_trend_chart(table_name)
        
        # Create issue distribution chart
        issue_chart = create_issue_distribution_chart(table_name)
        
        return html.Div([
            # Header
            html.H2(f"Data Quality Report: {table_name}", className="mb-4"),
            
            # Summary cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("92%", className="card-title"),
                            html.P("Overall Quality Score", className="card-text text-muted")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("24", className="card-title"),
                            html.P("Active Rules", className="card-text text-muted")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("3", className="card-title"),
                            html.P("Critical Issues", className="card-text text-muted")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Charts
            dbc.Row([
                # Quality Trends
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                figure=trend_chart if trend_chart else {},
                                config={'displayModeBar': False}
                            ) if trend_chart else html.P(
                                "No trend data available",
                                className="text-muted text-center"
                            )
                        ])
                    ])
                ], width=12, lg=8),
                
                # Issue Distribution
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                figure=issue_chart if issue_chart else {},
                                config={'displayModeBar': False}
                            ) if issue_chart else html.P(
                                "No issue data available",
                                className="text-muted text-center"
                            )
                        ])
                    ])
                ], width=12, lg=4)
            ], className="mb-4"),
            
            # Recommendations
            html.H4("Recommendations", className="mt-4 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.Ul([
                        html.Li([
                            html.Strong("Address Missing Values: "),
                            "Consider implementing data validation at source"
                        ], className="mb-2"),
                        html.Li([
                            html.Strong("Improve Data Format: "),
                            "Standardize date formats across the table"
                        ], className="mb-2"),
                        html.Li([
                            html.Strong("Monitor Trends: "),
                            "Set up alerts for sudden quality drops"
                        ])
                    ], className="mb-0")
                ])
            ], className="mb-4"),
            
            # Export options
            dbc.Button(
                [html.I(className="bi bi-download me-2"), "Export Report"],
                id="export-report-btn",
                color="primary"
            )
        ])
    except Exception as e:
        logging.error(f"Error in report layout: {str(e)}")
        return html.Div([
            html.H2("Data Quality Report", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error generating report: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ]) 