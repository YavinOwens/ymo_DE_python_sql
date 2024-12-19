import os
from pathlib import Path

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BONUS_DIR = os.path.dirname(BASE_DIR)  # Parent directory of streamlit_app
ASSETS_DATA_DIR = os.path.join(BONUS_DIR, 'assets', 'data')

# Database configuration
DATABASE_PATH = os.path.join(ASSETS_DATA_DIR, 'hr_database.sqlite')

# Rule templates configuration
RULE_TEMPLATES_PATH = os.path.join(ASSETS_DATA_DIR, 'rule_templates.json')

# Application configuration
APP_TITLE = "Data Quality Dashboard"
APP_DESCRIPTION = "Monitor and analyze data quality across your datasets"

# Page configuration
PAGE_CONFIG = {
    "page_title": APP_TITLE,
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
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

# Cache settings
CACHE_SETTINGS = {
    'ttl': DEFAULT_CACHE_TTL,
    'max_entries': 100
} 