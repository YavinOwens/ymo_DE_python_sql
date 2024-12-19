from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
from utils.data_loader import DataLoader
import logging
from functools import lru_cache
from datetime import datetime

data_loader = DataLoader()

@lru_cache(maxsize=32)
def get_column_stats(table_name: str, column_name: str) -> dict:
    """Calculate and cache column statistics."""
    try:
        df = data_loader.get_table_data(table_name)
        column_data = df[column_name]
        
        stats = {
            'name': column_name,
            'dtype': str(column_data.dtype),
            'count': len(column_data),
            'null_count': column_data.null_count(),
            'unique_count': column_data.n_unique(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add numeric statistics if applicable
        if pd.api.types.is_numeric_dtype(column_data.dtype):
            stats.update({
                'min': float(column_data.min()),
                'max': float(column_data.max()),
                'mean': float(column_data.mean()),
                'std': float(column_data.std()),
                'quartiles': [
                    float(column_data.quantile(0.25)),
                    float(column_data.quantile(0.5)),
                    float(column_data.quantile(0.75))
                ]
            })
            
            # Create histogram data
            hist_data = column_data.dropna()
            if len(hist_data) > 0:
                hist, bins = np.histogram(hist_data, bins='auto')
                stats['histogram'] = {
                    'counts': hist.tolist(),
                    'bins': bins.tolist()
                }
        
        # Add categorical statistics if applicable
        if pd.api.types.is_string_dtype(column_data.dtype) or pd.api.types.is_categorical_dtype(column_data.dtype):
            value_counts = column_data.value_counts()
            stats['value_counts'] = {
                'values': value_counts.index.tolist()[:20],  # Top 20 values
                'counts': value_counts.values.tolist()[:20]
            }
        
        return stats
    except Exception as e:
        logging.error(f"Error calculating column stats: {str(e)}")
        return None

def create_distribution_plot(stats: dict) -> dcc.Graph:
    """Create distribution plot based on column type."""
    try:
        if 'histogram' in stats:
            # Numeric data
            fig = px.histogram(
                x=stats['histogram']['bins'][:-1],
                y=stats['histogram']['counts'],
                labels={'x': stats['name'], 'y': 'Count'},
                title=f'Distribution of {stats["name"]}'
            )
        elif 'value_counts' in stats:
            # Categorical data
            fig = px.bar(
                x=stats['value_counts']['values'],
                y=stats['value_counts']['counts'],
                labels={'x': stats['name'], 'y': 'Count'},
                title=f'Value Distribution of {stats["name"]}'
            )
        else:
            return html.Div("No distribution plot available for this column type")
        
        fig.update_layout(
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return dcc.Graph(figure=fig)
    except Exception as e:
        logging.error(f"Error creating distribution plot: {str(e)}")
        return html.Div("Error creating distribution plot")

def create_stats_cards(stats: dict) -> list:
    """Create statistics cards."""
    cards = [
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Basic Information"),
                dbc.CardBody([
                    html.P([html.Strong("Data Type: "), stats['dtype']]),
                    html.P([html.Strong("Total Count: "), f"{stats['count']:,}"]),
                    html.P([html.Strong("Null Count: "), f"{stats['null_count']:,}"]),
                    html.P([html.Strong("Unique Count: "), f"{stats['unique_count']:,}"])
                ])
            ])
        ], width=6)
    ]
    
    if 'mean' in stats:
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Numeric Statistics"),
                    dbc.CardBody([
                        html.P([html.Strong("Mean: "), f"{stats['mean']:.2f}"]),
                        html.P([html.Strong("Std Dev: "), f"{stats['std']:.2f}"]),
                        html.P([html.Strong("Min: "), f"{stats['min']:.2f}"]),
                        html.P([html.Strong("Max: "), f"{stats['max']:.2f}"]),
                        html.P([
                            html.Strong("Quartiles: "),
                            f"Q1={stats['quartiles'][0]:.2f}, ",
                            f"Q2={stats['quartiles'][1]:.2f}, ",
                            f"Q3={stats['quartiles'][2]:.2f}"
                        ])
                    ])
                ])
            ], width=6)
        )
    
    return cards

def layout(table_name=None, column_name=None):
    """Create column analysis layout."""
    if not table_name or not column_name:
        return html.Div([
            html.H2("Column Analysis", className="mb-4"),
            dbc.Alert("Select a table and column to analyze", color="info")
        ])
    
    try:
        # Get column statistics
        stats = get_column_stats(table_name, column_name)
        if not stats:
            return html.Div([
                html.H2("Column Analysis", className="mb-4"),
                dbc.Alert("Error calculating column statistics", color="danger")
            ])
        
        return html.Div([
            # Header with timestamp
            html.Div([
                html.H2(f"Analysis of {column_name}", className="mb-0"),
                html.Small(
                    f"Last updated: {datetime.fromisoformat(stats['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
                    className="text-muted"
                )
            ], className="mb-4"),
            
            # Statistics cards
            dbc.Row(create_stats_cards(stats), className="mb-4"),
            
            # Distribution plot
            html.Div([
                html.H4("Distribution Analysis", className="mb-3"),
                create_distribution_plot(stats)
            ], className="mb-4"),
            
            # Export button
            dbc.Button(
                [html.I(className="bi bi-download me-2"), "Export Analysis"],
                id="export-analysis-btn",
                color="primary",
                className="mt-2"
            )
        ])
    except Exception as e:
        logging.error(f"Error in column analysis layout: {str(e)}")
        return html.Div([
            html.H2("Column Analysis", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading column analysis: {str(e)}"
                ],
                color="danger"
            )
        ])

def register_callbacks(app):
    @app.callback(
        Output('analysis-download', 'data'),
        [Input('export-analysis-btn', 'n_clicks')],
        [State('url', 'pathname')],
        prevent_initial_call=True
    )
    def export_analysis(n_clicks, pathname):
        """Export column analysis to CSV."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Extract table and column names from pathname
            parts = pathname.split('/')
            if len(parts) < 3:
                raise dash.exceptions.PreventUpdate
            
            table_name = parts[-2]
            column_name = parts[-1]
            
            # Get column statistics
            stats = get_column_stats(table_name, column_name)
            if not stats:
                raise dash.exceptions.PreventUpdate
            
            # Convert stats to DataFrame
            df = pd.DataFrame([stats])
            
            # Return download component
            return dcc.send_data_frame(
                df.to_csv,
                f"column_analysis_{table_name}_{column_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                index=False
            )
        except Exception as e:
            logging.error(f"Error exporting column analysis: {str(e)}")
            raise dash.exceptions.PreventUpdate 