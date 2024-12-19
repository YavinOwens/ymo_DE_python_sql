from dash import html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
from utils.data_loader import DataLoader
import logging
from functools import lru_cache
from datetime import datetime

data_loader = DataLoader()

@lru_cache(maxsize=32)
def get_table_metadata(table_name: str) -> dict:
    """Get and cache table metadata."""
    try:
        df = data_loader.get_table_data(table_name)
        
        metadata = {
            'name': table_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'size_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'columns': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for col in df.columns:
            col_data = df[col]
            col_meta = {
                'name': col,
                'type': str(col_data.dtype),
                'null_count': col_data.null_count(),
                'null_percentage': (col_data.null_count() / len(df) * 100).round(2),
                'unique_count': col_data.n_unique(),
                'unique_percentage': (col_data.n_unique() / len(df) * 100).round(2)
            }
            
            # Add sample values (first 5 non-null values)
            sample_values = col_data.dropna().head(5).tolist()
            col_meta['sample_values'] = [str(val) for val in sample_values]
            
            metadata['columns'].append(col_meta)
        
        return metadata
    except Exception as e:
        logging.error(f"Error getting table metadata: {str(e)}")
        return None

def create_table_summary_card(metadata: dict) -> dbc.Card:
    """Create a summary card for table metadata."""
    return dbc.Card([
        dbc.CardHeader(html.H4(metadata['name'], className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.P([
                        html.Strong("Rows: "),
                        f"{metadata['row_count']:,}"
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Columns: "),
                        f"{metadata['column_count']:,}"
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Size: "),
                        f"{metadata['size_mb']:.2f} MB"
                    ], className="mb-2")
                ], width=12)
            ])
        ])
    ], className="mb-4")

def create_column_table(metadata: dict) -> dash_table.DataTable:
    """Create a table showing column metadata."""
    data = [{
        'Column Name': col['name'],
        'Data Type': col['type'],
        'Missing Values': f"{col['null_count']:,} ({col['null_percentage']:.1f}%)",
        'Unique Values': f"{col['unique_count']:,} ({col['unique_percentage']:.1f}%)",
        'Sample Values': ', '.join(col['sample_values'][:3])
    } for col in metadata['columns']]
    
    return dash_table.DataTable(
        data=data,
        columns=[
            {'name': 'Column Name', 'id': 'Column Name'},
            {'name': 'Data Type', 'id': 'Data Type'},
            {'name': 'Missing Values', 'id': 'Missing Values'},
            {'name': 'Unique Values', 'id': 'Unique Values'},
            {'name': 'Sample Values', 'id': 'Sample Values'}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'minWidth': '150px',
            'maxWidth': '300px'
        },
        style_header={
            'backgroundColor': 'var(--background)',
            'fontWeight': 'bold',
            'border': '1px solid var(--border)'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Missing Values'},
                'color': 'var(--danger)'
            }
        ],
        sort_action='native',
        sort_mode='multi',
        filter_action='native'
    )

def layout(table_name=None):
    """Create data catalogue layout."""
    if not table_name:
        return html.Div([
            html.H2("Data Catalogue", className="mb-4"),
            dbc.Alert("Select a table to view metadata", color="info")
        ])
    
    try:
        # Get table metadata
        metadata = get_table_metadata(table_name)
        if not metadata:
            return html.Div([
                html.H2("Data Catalogue", className="mb-4"),
                dbc.Alert("Error loading table metadata", color="danger")
            ])
        
        return html.Div([
            # Header with timestamp
            html.Div([
                html.H2("Data Catalogue", className="mb-0"),
                html.Small(
                    f"Last updated: {datetime.fromisoformat(metadata['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
                    className="text-muted"
                )
            ], className="mb-4"),
            
            # Table summary
            create_table_summary_card(metadata),
            
            # Column details
            html.Div([
                html.H4("Column Details", className="mb-3"),
                create_column_table(metadata)
            ], className="mb-4"),
            
            # Export button
            dbc.Button(
                [html.I(className="bi bi-download me-2"), "Export Metadata"],
                id="export-metadata-btn",
                color="primary",
                className="mt-2"
            )
        ])
    except Exception as e:
        logging.error(f"Error in data catalogue layout: {str(e)}")
        return html.Div([
            html.H2("Data Catalogue", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading data catalogue: {str(e)}"
                ],
                color="danger"
            )
        ])

def register_callbacks(app):
    @app.callback(
        Output('metadata-download', 'data'),
        [Input('export-metadata-btn', 'n_clicks')],
        [State('url', 'pathname')],
        prevent_initial_call=True
    )
    def export_metadata(n_clicks, pathname):
        """Export table metadata to CSV."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Extract table name from pathname
            table_name = pathname.split('/')[-1]
            if not table_name:
                raise dash.exceptions.PreventUpdate
            
            # Get table metadata
            metadata = get_table_metadata(table_name)
            if not metadata:
                raise dash.exceptions.PreventUpdate
            
            # Convert metadata to DataFrame
            df = pd.DataFrame(metadata['columns'])
            
            # Return download component
            return dcc.send_data_frame(
                df.to_csv,
                f"table_metadata_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                index=False
            )
        except Exception as e:
            logging.error(f"Error exporting metadata: {str(e)}")
            raise dash.exceptions.PreventUpdate 