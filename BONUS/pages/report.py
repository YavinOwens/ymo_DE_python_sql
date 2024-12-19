from dash import html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import DataLoader
import logging
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

data_loader = DataLoader()

def create_quality_trend_chart(validation_history: list) -> go.Figure:
    """Create a line chart showing quality trends over time."""
    try:
        if not validation_history:
            return None
        
        # Convert validation history to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': datetime.fromisoformat(record['timestamp']),
                'pass_rate': (record['total_rules'] - record['failed_rules']) / record['total_rules'] * 100
                if record['total_rules'] > 0 else 0,
                'completeness': record.get('quality_metrics', {}).get('completeness', 0) * 100,
                'uniqueness': record.get('quality_metrics', {}).get('uniqueness', 0) * 100
            }
            for record in validation_history
        ])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Create figure
        fig = go.Figure()
        
        # Add traces for each metric
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['pass_rate'],
            name='Pass Rate',
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['completeness'],
            name='Completeness',
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['uniqueness'],
            name='Uniqueness',
            mode='lines+markers'
        ))
        
        # Update layout
        fig.update_layout(
            title="Quality Metrics Over Time",
            xaxis_title="Date",
            yaxis_title="Score (%)",
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error creating quality trend chart: {str(e)}")
        return None

def create_issue_distribution_chart(validation_results: dict) -> go.Figure:
    """Create a pie chart showing distribution of quality issues."""
    try:
        if not validation_results or 'rule_results' not in validation_results:
            return None
        
        # Group issues by category
        issues = pd.DataFrame(validation_results['rule_results'])
        if issues.empty:
            return None
        
        issues = issues[~issues['passed']].groupby('category').size().reset_index()
        issues.columns = ['Category', 'Count']
        
        # Create pie chart
        fig = px.pie(
            issues,
            values='Count',
            names='Category',
            title="Distribution of Quality Issues by Category"
        )
        
        # Update layout
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=True
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error creating issue distribution chart: {str(e)}")
        return None

def create_severity_breakdown(validation_results: dict) -> dash_table.DataTable:
    """Create a table showing breakdown of issues by severity."""
    try:
        if not validation_results or 'rule_results' not in validation_results:
            return None
        
        # Group issues by severity
        issues = pd.DataFrame(validation_results['rule_results'])
        if issues.empty:
            return None
        
        severity_counts = issues[~issues['passed']].groupby('severity').size().reset_index()
        severity_counts.columns = ['Severity', 'Count']
        
        return dash_table.DataTable(
            data=severity_counts.to_dict('records'),
            columns=[
                {'name': 'Severity', 'id': 'Severity'},
                {'name': 'Count', 'id': 'Count'}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '12px'
            },
            style_header={
                'backgroundColor': 'var(--background)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Severity} = "Critical"'},
                    'backgroundColor': 'rgba(255, 0, 0, 0.1)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Severity} = "High"'},
                    'backgroundColor': 'rgba(255, 165, 0, 0.1)',
                    'color': 'orange'
                }
            ]
        )
    except Exception as e:
        logging.error(f"Error creating severity breakdown: {str(e)}")
        return None

def layout(table_name=None):
    """Creates a report page with comprehensive data quality analysis."""
    if not table_name:
        return html.Div([
            html.H2("Data Quality Report", className="mb-4"),
            dbc.Alert("Select a table to view quality reports", color="info")
        ])
    
    try:
        # Get validation history and latest results
        validation_history = data_loader.get_validation_history(table_name)
        latest_validation = validation_history[0] if validation_history else None
        
        if not latest_validation:
            return html.Div([
                html.H2("Data Quality Report", className="mb-4"),
                dbc.Alert("No validation history available for this table", color="warning")
            ])
        
        # Calculate overall quality score
        total_rules = latest_validation.get('total_rules', 0)
        failed_rules = latest_validation.get('failed_rules', 0)
        quality_score = ((total_rules - failed_rules) / total_rules * 100) if total_rules > 0 else 0
        
        return html.Div([
            # Header
            html.H2(f"Data Quality Report: {table_name}", className="mb-4"),
            
            # Summary cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{quality_score:.1f}%", className="card-title"),
                            html.P("Overall Quality Score", className="card-text text-muted")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(str(total_rules), className="card-title"),
                            html.P("Total Rules", className="card-text text-muted")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(str(failed_rules), className="card-title"),
                            html.P("Failed Rules", className="card-text text-muted")
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
                                figure=create_quality_trend_chart(validation_history),
                                config={'displayModeBar': False}
                            ) if validation_history else html.P(
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
                                figure=create_issue_distribution_chart(latest_validation),
                                config={'displayModeBar': False}
                            ) if latest_validation else html.P(
                                "No issue data available",
                                className="text-muted text-center"
                            )
                        ])
                    ])
                ], width=12, lg=4)
            ], className="mb-4"),
            
            # Severity Breakdown
            html.H4("Issue Severity Breakdown", className="mt-4 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    create_severity_breakdown(latest_validation) if latest_validation else html.P(
                        "No severity data available",
                        className="text-muted text-center"
                    )
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

def register_callbacks(app):
    @app.callback(
        Output('report-download', 'data'),
        [Input('export-report-btn', 'n_clicks')],
        [State('url', 'pathname')],
        prevent_initial_call=True
    )
    def export_report(n_clicks, pathname):
        """Export the data quality report."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Extract table name from pathname
            table_name = pathname.split('/')[-1]
            if not table_name:
                raise dash.exceptions.PreventUpdate
            
            # Get validation history
            validation_history = data_loader.get_validation_history(table_name)
            if not validation_history:
                raise dash.exceptions.PreventUpdate
            
            # Create report DataFrame
            report_data = []
            for record in validation_history:
                report_data.append({
                    'Timestamp': record['timestamp'],
                    'Total Rules': record['total_rules'],
                    'Failed Rules': record['failed_rules'],
                    'Pass Rate': f"{((record['total_rules'] - record['failed_rules']) / record['total_rules'] * 100):.1f}%"
                    if record['total_rules'] > 0 else "0%"
                })
            
            df = pd.DataFrame(report_data)
            
            # Return download component
            return dcc.send_data_frame(
                df.to_csv,
                f"quality_report_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                index=False
            )
        except Exception as e:
            logging.error(f"Error exporting report: {str(e)}")
            raise dash.exceptions.PreventUpdate 