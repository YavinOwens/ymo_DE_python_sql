import os

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dummy_data', 'hr_database.sqlite')
DB_URI = f"sqlite:///{DB_PATH}"

# Data Quality Thresholds
COMPLETENESS_THRESHOLD = 0.9  # 90%
UNIQUENESS_THRESHOLD = 0.95   # 95%
VALIDITY_THRESHOLD = 0.88     # 88%

# Table Configurations
DEFAULT_PREVIEW_ROWS = 100
DEFAULT_SAMPLE_SIZE = 1000

# Asset Paths
ASSET_PATH = os.path.join(os.path.dirname(__file__), 'assets')
