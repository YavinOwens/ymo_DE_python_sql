from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import logging

data_loader = DataLoader()

def layout(table_name=None):
    """Create detailed quality metrics content with consistent layout and enhanced presentation."""
    if not table_name:
        return html.Div([
            html.H2("Quality Check", className="mb-4"),
            dbc.Alert("Select a table to view quality metrics", color="info")
        ])

    try:
        table_data = data_loader.get_table_data(table_name)
        
        # Calculate quality metrics
        null_counts = table_data.isnull().sum()
        duplicate_rows = len(table_data) - len(table_data.drop_duplicates())
        total_cells = len(table_data) * len(table_data.columns)
        total_nulls = null_counts.sum()
        
        # Calculate percentages
        completeness = ((total_cells - total_nulls) / total_cells) * 100
        uniqueness = ((len(table_data) - duplicate_rows) / len(table_data)) * 100
        
        return html.Div([
            # Header
            html.H2("Quality Metrics", className="mb-4"),
            
            # Overall Quality Score
            dbc.Card([
                dbc.CardBody([
                    html.H3("Overall Quality Score", className="card-title text-center"),
                    html.H1(
                        f"{(completeness + uniqueness) / 2:.1f}%",
                        className="display-4 text-center text-primary"
                    ),
                    html.P(
                        "Based on completeness and uniqueness metrics",
                        className="text-muted text-center"
                    )
                ])
            ], className="mb-4"),
            
            # Key Metrics
            dbc.Row([
                # Completeness Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Data Completeness"),
                        dbc.CardBody([
                            html.H5(f"{completeness:.1f}%"),
                            html.P("Non-null values"),
                            html.Small(
                                f"{total_nulls:,} missing values out of {total_cells:,} total",
                                className="text-muted"
                            )
                        ])
                    ])
                ], width=6),
                
                # Uniqueness Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Data Uniqueness"),
                        dbc.CardBody([
                            html.H5(f"{uniqueness:.1f}%"),
                            html.P("Unique records"),
                            html.Small(
                                f"{duplicate_rows:,} duplicate rows found",
                                className="text-muted"
                            )
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Column Quality Details
            html.H4("Column Quality Details", className="mt-4 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    dash_table.DataTable(
                        data=pd.DataFrame({
                            'Column': table_data.columns,
                            'Missing Values': null_counts.values,
                            'Missing %': (null_counts / len(table_data) * 100).round(2).values,
                            'Unique Values': [table_data[col].nunique() for col in table_data.columns],
                            'Unique %': [(table_data[col].nunique() / len(table_data) * 100).round(2) for col in table_data.columns]
                        }).to_dict('records'),
                        columns=[
                            {'name': 'Column', 'id': 'Column'},
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
                        ]
                    )
                ])
            ])
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