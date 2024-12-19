from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import pandas as pd
import polars as pl
import logging
from datetime import datetime
import os
from config import DATA_DIR
from ydata_profiling import ProfileReport
import tempfile
import base64
import warnings
import json
from dash.exceptions import PreventUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data_loader = DataLoader()

def generate_profile_report(df, title="Data Profile Report") -> str:
    """Generate a profile report using ydata-profiling with comprehensive settings."""
    try:
        # Convert Polars DataFrame to Pandas if necessary
        if isinstance(df, pl.DataFrame):
            logger.info("Converting Polars DataFrame to Pandas")
            df = df.to_pandas()
        
        # Suppress warnings during report generation
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Configure comprehensive profile report settings
            profile = ProfileReport(
                df,
                title=title,
                explorative=True,
                html={'style': {'full_width': True}},
                correlations={
                    "pearson": {"calculate": True},
                    "spearman": {"calculate": True},
                    "kendall": {"calculate": True},
                    "phi_k": {"calculate": True},
                    "cramers": {"calculate": True},
                },
                interactions={
                    "continuous": True,
                    "targets": []
                },
                vars={
                    "num": {
                        "quantiles": [0.05, 0.25, 0.5, 0.75, 0.95],
                        "skewness_threshold": 20,
                        "low_categorical_threshold": 5
                    },
                    "cat": {
                        "length": True,
                        "characters": True,
                        "words": True,
                        "cardinality_threshold": 50,
                        "n_obs": 5
                    }
                },
                missing_diagrams={
                    "matrix": True,
                    "bar": True,
                    "dendrogram": True,
                    "heatmap": True
                },
                duplicates={
                    "head": 10,
                    "tail": 10,
                    "random": 10
                },
                plot={
                    "image_format": "svg",
                    "dpi": 300
                }
            )
            
            logger.info("Profile report generated successfully")
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp:
                logger.info(f"Saving report to temporary file: {tmp.name}")
                profile.to_file(tmp.name)
                
                # Read the saved file
                with open(tmp.name, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Encode the content
                encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                
            # Clean up the temporary file
            os.unlink(tmp.name)
            logger.info("Temporary file cleaned up")
            
            return encoded
            
    except Exception as e:
        logger.error(f"Error generating profile report: {str(e)}", exc_info=True)
        return None

def get_data_summary(data_config: dict) -> dict:
    """Get summary statistics for the loaded data."""
    try:
        if not data_config:
            return None
            
        source = data_config.get('source')
        source_type = data_config.get('source_type')
        engine = data_config.get('engine', 'polars')
        
        logger.info(f"Processing data source: {source} with engine: {engine}")
        
        if not source:
            return None
        
        # Load data based on source type and engine
        if source_type == 'sqlite':
            if engine == 'pandas':
                with data_loader.connection as conn:
                    df = pd.read_sql(f"SELECT * FROM {source}", conn)
            else:  # polars
                df = data_loader.get_table_data(source)
        else:  # files
            file_path = os.path.join(DATA_DIR, source)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Data file not found: {source}")
                
            if engine == 'pandas':
                if source.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif source.endswith('.parquet'):
                    df = pd.read_parquet(file_path)
                else:
                    raise ValueError(f"Unsupported file type for {source}")
            else:  # polars
                if source.endswith('.csv'):
                    df = pl.read_csv(file_path)
                elif source.endswith('.parquet'):
                    df = pl.read_parquet(file_path)
                else:
                    raise ValueError(f"Unsupported file type for {source}")
        
        logger.info(f"Data loaded successfully. Shape: {df.shape if isinstance(df, pd.DataFrame) else (len(df), len(df.columns))}")
        
        # Calculate summary statistics
        total_rows = len(df)
        total_cols = len(df.columns)
        
        if engine == 'pandas':
            null_counts = df.isnull().sum()
            total_nulls = null_counts.sum()
            duplicate_rows = len(df) - len(df.drop_duplicates())
        else:  # polars
            null_counts = df.null_count()
            total_nulls = sum(null_counts)
            duplicate_rows = len(df) - len(df.unique())
        
        logger.info("Generating profile report...")
        # Generate profile report
        profile_report = generate_profile_report(
            df, 
            title=f"Data Profile Report - {source}"
        )
        
        if profile_report is None:
            logger.warning("Profile report generation failed")
        else:
            logger.info("Profile report generated successfully")
        
        return {
            'source': source,
            'source_type': source_type,
            'engine': engine,
            'total_rows': total_rows,
            'total_columns': total_cols,
            'total_nulls': total_nulls,
            'duplicate_rows': duplicate_rows,
            'timestamp': datetime.now().isoformat(),
            'profile_report': profile_report
        }
    
    except Exception as e:
        logger.error(f"Error getting data summary: {str(e)}", exc_info=True)
        return {'error': str(e), 'error_type': 'general_error'}

def create_summary_cards(summary: dict) -> list:
    """Create summary metric cards."""
    if not summary:
        return []
    
    return [
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Source"),
                dbc.CardBody([
                    html.H5(summary['source']),
                    html.P(f"Type: {summary['source_type']}"),
                    html.P(f"Engine: {summary['engine']}")
                ])
            ])
        ], width=12, lg=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Size"),
                dbc.CardBody([
                    html.H5(f"{summary['total_rows']:,}"),
                    html.P("Total Rows"),
                    html.P(f"Columns: {summary['total_columns']}")
                ])
            ])
        ], width=12, lg=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Quality"),
                dbc.CardBody([
                    html.H5(f"{summary['total_nulls']:,}"),
                    html.P("Missing Values"),
                    html.P(f"Duplicate Rows: {summary['duplicate_rows']:,}")
                ])
            ])
        ], width=12, lg=4)
    ]

def create_welcome_message():
    """Create a welcome message with instructions."""
    return html.Div([
        html.H2("Welcome to Data Quality Dashboard", className="mb-4"),
        html.P("This dashboard helps you analyze and monitor data quality across your datasets.", className="lead"),
        dbc.Card([
            dbc.CardHeader(html.H4("Getting Started", className="mb-0")),
            dbc.CardBody([
                html.P("Follow these steps to begin your analysis:"),
                html.Ol([
                    html.Li([
                        html.Strong("Select Data Source: "),
                        "Choose between SQLite database or data files from the sidebar."
                    ]),
                    html.Li([
                        html.Strong("Choose Processing Engine: "),
                        "Select either Pandas or Polars as your data processing engine."
                    ]),
                    html.Li([
                        html.Strong("Load Data: "),
                        "Select your table or file and click 'Load Data' to begin analysis."
                    ])
                ]),
                html.P([
                    html.I(className="bi bi-info-circle me-2"),
                    "The dashboard will automatically update with quality metrics and generate a detailed profile report once data is loaded."
                ], className="mt-3 text-muted")
            ])
        ])
    ])

def create_loading_spinner():
    """Create a loading spinner component."""
    return html.Div([
        html.Div([
            html.Div(className="loading-spinner"),
            html.P("Processing data and generating profile report...", 
                  className="mt-3 text-center text-muted")
        ], className="loading-container")
    ], id="loading-spinner", style={'display': 'none'})

def layout():
    """Create overview page layout."""
    return html.Div([
        dcc.Store(id='overview-store'),
        html.Div(id="overview-content"),
        create_loading_spinner(),
        html.Div(id="profile-report-container", className="profile-report-container")
    ])

def register_callbacks(app):
    @app.callback(
        [Output('overview-content', 'children'),
         Output('profile-report-container', 'children'),
         Output('loading-spinner', 'style')],
        [Input('data-loader-store', 'data')],
        [State('loading-spinner', 'style')]
    )
    def update_overview(data_config, loading_style):
        """Update the overview content based on selected data source."""
        if not data_config:
            return create_welcome_message(), None, {'display': 'none'}
        
        # Show loading spinner
        loading_style = {'display': 'block'}
        
        try:
            # Get data summary
            summary = get_data_summary(data_config)
            if not summary:
                return dbc.Alert(
                    "Please select a valid data source to begin analysis.",
                    color="info"
                ), None, {'display': 'none'}
            
            # Check for specific errors
            if 'error' in summary:
                error_msg = summary['error']
                if summary['error_type'] == 'file_not_found':
                    return dbc.Alert(
                        [
                            html.I(className="bi bi-exclamation-triangle-fill me-2"),
                            f"File not found: {error_msg}"
                        ],
                        color="danger"
                    ), None, {'display': 'none'}
                elif summary['error_type'] == 'value_error':
                    return dbc.Alert(
                        [
                            html.I(className="bi bi-exclamation-triangle-fill me-2"),
                            f"Invalid data format: {error_msg}"
                        ],
                        color="danger"
                    ), None, {'display': 'none'}
                else:
                    return dbc.Alert(
                        [
                            html.I(className="bi bi-exclamation-triangle-fill me-2"),
                            f"Error loading data: {error_msg}"
                        ],
                        color="danger"
                    ), None, {'display': 'none'}
            
            # Create main content
            main_content = html.Div([
                # Header
                html.H2("Data Quality Overview", className="mb-4"),
                
                # Summary Cards
                dbc.Row(
                    create_summary_cards(summary),
                    className="mb-4"
                ),
                
                # Last Update Info
                html.Small(
                    f"Last updated: {datetime.fromisoformat(summary['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
                    className="text-muted"
                )
            ])
            
            # Create profile report content if available
            profile_content = None
            if summary.get('profile_report'):
                try:
                    decoded_report = base64.b64decode(summary['profile_report']).decode('utf-8')
                    logger.info("Profile report decoded successfully")
                    
                    profile_content = html.Div([
                        html.Hr(),
                        html.H3("Detailed Data Profile Report", className="mb-4"),
                        html.Iframe(
                            srcDoc=decoded_report,
                            style={
                                'width': '100%',
                                'height': '800px',
                                'border': 'none',
                                'background': 'white',
                                'overflow': 'auto'
                            }
                        )
                    ])
                except Exception as e:
                    logger.error(f"Error displaying profile report: {str(e)}", exc_info=True)
                    profile_content = dbc.Alert(
                        [
                            html.I(className="bi bi-exclamation-triangle-fill me-2"),
                            "Error displaying profile report. Please try refreshing the page."
                        ],
                        color="warning"
                    )
            
            # Hide loading spinner
            loading_style = {'display': 'none'}
            
            return main_content, profile_content, loading_style
            
        except Exception as e:
            logger.error(f"Error updating overview: {str(e)}", exc_info=True)
            return dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error: {str(e)}"
                ],
                color="danger"
            ), None, {'display': 'none'}