import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'assets', 'data')
CSS_DIR = os.path.join(BASE_DIR, 'assets', 'css')

# Database configuration
DATABASE_PATH = os.path.join(DATA_DIR, 'data_quality.db')

# Rule templates configuration
RULE_TEMPLATES_PATH = os.path.join(DATA_DIR, 'rule_templates.json')

# Application configuration
APP_TITLE = "Data Quality Dashboard"
APP_DESCRIPTION = "Monitor and analyze data quality across your datasets"

# Page titles
PAGE_TITLES = {
    'overview': 'Overview',
    'quality': 'Quality Analysis',
    'column_analysis': 'Column Analysis',
    'data_catalogue': 'Data Catalogue',
    'rule_management': 'Rule Management',
    'run_management': 'Run Management',
    'failed_data': 'Failed Data',
    'report': 'Report'
}

# Default settings
DEFAULT_PROFILE_MINIMAL = False
DEFAULT_CACHE_TTL = 3600  # 1 hour

# Chart configuration
CHART_CONFIG = {
    'displayModeBar': True,
    'responsive': True
}

# Color schemes
COLORS = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8'
} 