from dash import html, dcc, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

logger = logging.getLogger(__name__)
data_loader = DataLoader()

def create_empty_plot(message="No data available"):
    """Create an empty plot with a message"""
    return go.Figure().add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False
    )

# Initialize table options
available_tables = data_loader.get_available_tables()

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Column Analysis", className="mb-4"),
            
            # Table selector
            dbc.Card([
                dbc.CardBody([
                    html.H5("Select Table", className="mb-3"),
                    dcc.Dropdown(
                        id='table-selector',
                        options=[{'label': table, 'value': table} for table in available_tables],
                        placeholder="Select a table to analyze",
                        className="mb-3"
                    ),
                    
                    # Column selector
                    html.H5("Select Columns", className="mb-3"),
                    dcc.Dropdown(
                        id='column-selector',
                        options=[],  # Will be populated based on table selection
                        placeholder="Select columns to analyze",
                        multi=True,  # Allow multiple column selection
                        className="mb-3"
                    ),
                ])
            ], className="mb-4"),
            
            # Analysis output
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="analysis-output")
                ])
            ])
        ])
    ])
])

# Update column selector based on table selection
# @callback(
#     [Output('column-selector', 'options', allow_duplicate=True),
#      Output('column-selector', 'value', allow_duplicate=True)],
#     [Input('table-selector', 'value')],
#     prevent_initial_call=True
# )
# def update_column_options(table_name):
#     """Update column options based on selected table."""
#     if not table_name:
#         return [], None
#     try:
#         columns = data_loader.get_table_columns(table_name)
#         return [{'label': col, 'value': col} for col in columns], None
#     except Exception as e:
#         logger.error(f"Error getting columns for table {table_name}: {str(e)}")
#         return [], None

# Callback to update analysis output
@callback(
    Output('analysis-output', 'children'),
    [Input('table-selector', 'value'),
     Input('column-selector', 'value')]
)
def update_analysis(selected_table, selected_columns):
    if not selected_table or not selected_columns:
        return html.Div([
            html.H4("No Data Selected", className="text-center text-muted my-4"),
            html.P("Please select a table and at least one column to analyze.", 
                  className="text-center text-muted")
        ])
    
    try:
        # Load data for selected table and columns
        df = data_loader.get_table_data(selected_table, selected_columns)
        
        if df.empty:
            return html.Div([
                html.H4("Empty Table", className="text-center text-muted my-4"),
                html.P(f"The selected table '{selected_table}' is empty.", 
                      className="text-center text-muted")
            ])
        
        # Create analysis components for each selected column
        analysis_components = []
        for column in selected_columns:
            column_stats = get_column_statistics(df, column)
            column_plot = create_column_plot(df, column)
            
            analysis_components.extend([
                html.H4(f"Analysis for {column}", className="mt-4"),
                
                # Statistics card
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.P(f"Data Type: {str(df[column].dtype)}"),
                                html.P(f"Unique Values: {column_stats['unique_count']}"),
                                html.P(f"Missing Values: {column_stats['missing_count']} ({column_stats['missing_percentage']}%)"),
                            ], width=6),
                            dbc.Col([
                                html.P(f"Min: {column_stats['min']}"),
                                html.P(f"Max: {column_stats['max']}"),
                                html.P(f"Mean: {column_stats['mean']}" if column_stats['mean'] is not None else ""),
                            ], width=6),
                        ])
                    ])
                ], className="mb-3"),
                
                # Distribution plot
                dcc.Graph(figure=column_plot)
            ])
        
        return html.Div(analysis_components)
        
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        return html.Div([
            html.H4("Error", className="text-center text-danger my-4"),
            html.P(f"An error occurred while analyzing the data: {str(e)}", 
                  className="text-center text-muted")
        ])

def get_column_statistics(df, column):
    """Calculate statistics for a column"""
    try:
        stats = {
            'unique_count': df[column].nunique(),
            'missing_count': df[column].isna().sum(),
            'missing_percentage': round(df[column].isna().mean() * 100, 2),
            'min': str(df[column].min()) if pd.api.types.is_numeric_dtype(df[column]) else None,
            'max': str(df[column].max()) if pd.api.types.is_numeric_dtype(df[column]) else None,
            'mean': round(df[column].mean(), 2) if pd.api.types.is_numeric_dtype(df[column]) else None
        }
        return stats
    except Exception as e:
        logger.error(f"Error calculating statistics for column {column}: {str(e)}")
        return {
            'unique_count': 0,
            'missing_count': 0,
            'missing_percentage': 0,
            'min': None,
            'max': None,
            'mean': None
        }

def create_column_plot(df, column):
    """Create appropriate plot for column based on its data type"""
    try:
        if pd.api.types.is_numeric_dtype(df[column]):
            # Histogram for numeric data
            fig = px.histogram(
                df, x=column,
                title=f"Distribution of {column}",
                template="plotly_white"
            )
        else:
            # Bar chart for categorical data
            value_counts = df[column].value_counts()
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Distribution of {column}",
                template="plotly_white"
            )
            fig.update_layout(xaxis_title=column, yaxis_title="Count")
        
        return fig
    except Exception as e:
        logger.error(f"Error creating plot for column {column}: {str(e)}")
        return create_empty_plot(f"Error creating plot for {column}") 