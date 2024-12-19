from dash import html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from functools import lru_cache

data_loader = DataLoader()

@lru_cache(maxsize=32)
def calculate_quality_metrics(table_name: str) -> dict:
    """Calculate quality metrics with caching for better performance."""
    try:
        df = data_loader.get_table_data(table_name)
        total_cells = len(df) * len(df.columns)
        
        # Calculate completeness
        null_counts = df.null_count()
        total_nulls = null_counts.sum()
        completeness = ((total_cells - total_nulls) / total_cells) * 100
        
        # Calculate uniqueness
        duplicate_rows = len(df) - len(df.drop_duplicates())
        uniqueness = ((len(df) - duplicate_rows) / len(df)) * 100
        
        # Calculate column-level statistics
        column_stats = []
        for col in df.columns:
            col_data = df[col]
            unique_count = col_data.n_unique()
            null_count = col_data.null_count()
            
            stats = {
                'Column': col,
                'Missing Values': null_count,
                'Missing %': (null_count / len(df) * 100).round(2),
                'Unique Values': unique_count,
                'Unique %': (unique_count / len(df) * 100).round(2),
                'Data Type': str(col_data.dtype)
            }
            
            # Add numeric statistics if applicable
            if pd.api.types.is_numeric_dtype(col_data.dtype):
                stats.update({
                    'Min': float(col_data.min()),
                    'Max': float(col_data.max()),
                    'Mean': float(col_data.mean()),
                    'Std': float(col_data.std())
                })
            
            column_stats.append(stats)
        
        return {
            'completeness': completeness,
            'uniqueness': uniqueness,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'total_nulls': total_nulls,
            'duplicate_rows': duplicate_rows,
            'column_stats': column_stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error calculating quality metrics: {str(e)}")
        return None

def create_quality_cards(metrics: dict) -> list:
    """Create quality metric cards."""
    return [
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Completeness"),
                dbc.CardBody([
                    html.H5(f"{metrics['completeness']:.1f}%"),
                    html.P("Non-null values"),
                    html.Small(
                        f"{metrics['total_nulls']:,} missing values out of {metrics['total_rows'] * metrics['total_columns']:,} total",
                        className="text-muted"
                    )
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Uniqueness"),
                dbc.CardBody([
                    html.H5(f"{metrics['uniqueness']:.1f}%"),
                    html.P("Unique records"),
                    html.Small(
                        f"{metrics['duplicate_rows']:,} duplicate rows found",
                        className="text-muted"
                    )
                ])
            ])
        ], width=6)
    ]

def create_column_quality_table(column_stats: list) -> dash_table.DataTable:
    """Create a table showing column quality details."""
    return dash_table.DataTable(
        data=column_stats,
        columns=[
            {'name': 'Column', 'id': 'Column'},
            {'name': 'Data Type', 'id': 'Data Type'},
            {'name': 'Missing Values', 'id': 'Missing Values'},
            {'name': 'Missing %', 'id': 'Missing %'},
            {'name': 'Unique Values', 'id': 'Unique Values'},
            {'name': 'Unique %', 'id': 'Unique %'}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': 'var(--background)',
            'fontWeight': 'bold',
            'border': '1px solid var(--border)'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Missing %', 'filter_query': '{Missing %} > 20'},
                'color': 'var(--danger)'
            },
            {
                'if': {'column_id': 'Missing %', 'filter_query': '{Missing %} <= 5'},
                'color': 'var(--success)'
            }
        ],
        sort_action='native',
        sort_mode='multi',
        filter_action='native'
    )

def layout(table_name=None):
    """Create detailed quality metrics content with consistent layout and enhanced presentation."""
    if not table_name:
        return html.Div([
            html.H2("Quality Check", className="mb-4"),
            dbc.Alert("Select a table to view quality metrics", color="info")
        ])

    try:
        # Calculate quality metrics
        metrics = calculate_quality_metrics(table_name)
        if not metrics:
            return html.Div([
                html.H2("Quality Check", className="mb-4"),
                dbc.Alert("Error calculating quality metrics", color="danger")
            ])
        
        return html.Div([
            # Header with timestamp
            html.Div([
                html.H2("Quality Metrics", className="mb-0"),
                html.Small(
                    f"Last updated: {datetime.fromisoformat(metrics['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
                    className="text-muted"
                )
            ], className="mb-4"),
            
            # Quality metric cards
            dbc.Row(create_quality_cards(metrics), className="mb-4"),
            
            # Column quality details
            html.Div([
                html.H4("Column Quality Details", className="mb-3"),
                html.Div([
                    create_column_quality_table(metrics['column_stats'])
                ], className="table-responsive")
            ]),
            
            # Export button
            dbc.Button(
                [html.I(className="bi bi-download me-2"), "Export Metrics"],
                id="export-quality-btn",
                color="primary",
                className="mt-4"
            )
        ])
    except Exception as e:
        logging.error(f"Error in quality layout: {str(e)}")
        return html.Div([
            html.H2("Quality Check", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading quality metrics: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ])

def register_callbacks(app):
    @app.callback(
        Output('quality-download', 'data'),
        [Input('export-quality-btn', 'n_clicks')],
        [State('url', 'pathname')],
        prevent_initial_call=True
    )
    def export_quality_metrics(n_clicks, pathname):
        """Export quality metrics to CSV."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Extract table name from pathname
            table_name = pathname.split('/')[-1]
            if not table_name:
                raise dash.exceptions.PreventUpdate
            
            # Get quality metrics
            metrics = calculate_quality_metrics(table_name)
            if not metrics:
                raise dash.exceptions.PreventUpdate
            
            # Create DataFrame from column stats
            df = pd.DataFrame(metrics['column_stats'])
            
            # Return download component
            return dcc.send_data_frame(
                df.to_csv,
                f"quality_metrics_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                index=False
            )
        except Exception as e:
            logging.error(f"Error exporting quality metrics: {str(e)}")
            raise dash.exceptions.PreventUpdate 