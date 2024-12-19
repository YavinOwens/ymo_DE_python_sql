import os

# Database Configuration
DB_PATH = r"C:\Users\ymowe\Documents\DE_PYTHON_SQL\ymo_DE_python_sql\dummy_data\hr_database.sqlite"

# Ensure the database path exists
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database file not found at: {DB_PATH}")

# Rule Templates Configuration
RULE_TEMPLATES_PATH = os.path.join('BONUS', 'assets', 'data', 'rule_templates.json')

# Default rule patterns
DEFAULT_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone': r'^\+?1?\d{9,15}$',
    'date': r'^\d{4}-\d{2}-\d{2}$',
    'numeric': r'^\d+(\.\d+)?$',
    'text': r'^[a-zA-Z\s]+$'
}

# Data quality thresholds
QUALITY_THRESHOLDS = {
    'completeness': 0.95,  # 95% non-null values
    'uniqueness': 0.98,    # 98% unique values
    'validity': 0.99       # 99% valid values
}

# Logging Configuration
LOG_PATH = os.path.join('BONUS', 'assets', 'logs', 'app.log')
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
