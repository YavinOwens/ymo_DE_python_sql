import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
DATA_DIR = os.path.join(ASSETS_DIR, 'data')
DUMMY_DATA_DIR = os.path.join(ASSETS_DIR, 'dummy_data')

# Database path
DB_PATH = os.path.join(DATA_DIR, 'data_quality.db')

# JSON file paths
RULE_TEMPLATES_PATH = os.path.join(DATA_DIR, 'rule_templates.json')
MASTER_CONFIG_PATH = os.path.join(DATA_DIR, 'master_config.json')
DATA_CONFIG_PATH = os.path.join(DATA_DIR, 'data_config.json')
EXECUTION_HISTORY_PATH = os.path.join(DATA_DIR, 'execution_history.json')
RULE_EXECUTION_HISTORY_PATH = os.path.join(DATA_DIR, 'rule_execution_history.json')

# Cache file paths
COLUMN_STATS_CACHE_PATH = os.path.join(DATA_DIR, 'column_statistics_cache.json')
RULE_MANAGEMENT_CACHE_PATH = os.path.join(DATA_DIR, 'rule_management_content_cache.json')
RULE_EXECUTION_CACHE_PATH = os.path.join(DATA_DIR, 'rule_execution_cache.json')
RULES_PROCESSING_CACHE_PATH = os.path.join(DATA_DIR, 'rules_processing_cache.json')

# Default patterns for data validation
DEFAULT_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone': r'^\+?1?\d{9,15}$',
    'date': r'^\d{4}-\d{2}-\d{2}$',
    'url': r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    'completeness': 0.95,
    'uniqueness': 0.98,
    'consistency': 0.95,
    'validity': 0.98
}

# Logging Configuration
LOG_PATH = os.path.join('BONUS', 'assets', 'logs', 'app.log')

# Only create directories if they don't exist
required_dirs = [
    os.path.join(ASSETS_DIR, 'data'),
    os.path.join(ASSETS_DIR, 'dummy_data')
]

for directory in required_dirs:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
