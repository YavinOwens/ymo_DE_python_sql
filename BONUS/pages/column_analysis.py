from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

data_loader = DataLoader()

def create_column_visualization(table_data, column_name):
    """Create appropriate visualization based on column type."""
    try:
        if pd.api.types.is_numeric_dtype(table_data[column_name]):
            # Histogram for numeric data
            fig = px.histogram(
                table_data,
                x=column_name,
                title=f"Distribution of {column_name}",
                template="plotly_white"
            )
        else:
            # Bar chart for categorical data
            value_counts = table_data[column_name].value_counts().head(20)
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Top 20 Values in {column_name}",
                template="plotly_white"
            )
            fig.update_layout(
                xaxis_title=column_name,
                yaxis_title="Count"
            )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=300
        )
        return fig
    except Exception as e:
        logging.error(f"Error creating visualization for {column_name}: {str(e)}")
        return None

def layout(table_name=None, selected_columns=None):
    """Create column analysis content with detailed statistics and visualizations."""
    if not table_name:
        return html.Div([
            html.H2("Column Analysis", className="mb-4"),
            dbc.Alert("Select a table and columns to analyze", color="info")
        ])

    try:
        table_data = data_loader.get_table_data(table_name)
        if not selected_columns:
            selected_columns = table_data.columns.tolist()

        analysis_cards = []
        for col in selected_columns:
            # Get column statistics
            stats = data_loader.get_column_stats(table_name, col)
            if not stats:
                continue
            
            # Create visualization
            fig = create_column_visualization(table_data, col)
            
            # Create card with statistics and visualization
            card = dbc.Card([
                dbc.CardHeader(html.H5(col, className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        # Statistics
                        dbc.Col([
                            html.Div([
                                html.Strong("Type: "), 
                                str(stats['type'])
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("Unique Values: "), 
                                str(stats['unique_count'])
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("Missing Values: "), 
                                str(stats['null_count'])
                            ], className="mb-2"),
                            # Add numeric statistics if available
                            *([
                                html.Div([
                                    html.Strong(f"{key.title()}: "),
                                    f"{value:.2f}" if isinstance(value, float) else str(value)
                                ], className="mb-2")
                                for key, value in stats.items()
                                if key in ['min', 'max', 'mean', 'std']
                            ] if 'min' in stats else [])
                        ], width=12, lg=4),
                        
                        # Visualization
                        dbc.Col([
                            dcc.Graph(
                                figure=fig if fig else {},
                                config={'displayModeBar': False}
                            ) if fig else html.P("No visualization available", className="text-muted")
                        ], width=12, lg=8)
                    ])
                ])
            ], className="mb-4")
            analysis_cards.append(card)

        # Create the layout with all components
        layout_content = [
            # Header
            html.H2("Column Analysis", className="mb-4"),
            
            # Column selector
            dbc.Card([
                dbc.CardBody([
                    html.H5("Select Columns", className="card-title"),
                    dcc.Dropdown(
                        id="column-selector",
                        options=[{"label": col, "value": col} for col in table_data.columns],
                        value=selected_columns,
                        multi=True,
                        className="mb-3"
                    )
                ])
            ], className="mb-4")
        ]
        
        # Add analysis cards or warning message
        if analysis_cards:
            layout_content.extend(analysis_cards)
        else:
            layout_content.append(
                dbc.Alert(
                    "No columns selected for analysis",
                    color="warning",
                    className="mb-4"
                )
            )
        
        return html.Div(layout_content)
    except Exception as e:
        logging.error(f"Error in column_analysis layout: {str(e)}")
        return html.Div([
            html.H2("Column Analysis", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error analyzing columns: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ]) 