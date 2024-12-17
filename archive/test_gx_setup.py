import great_expectations as gx
import pandas as pd
from pathlib import Path

# Set up report directories
REPORT_DIR = Path('./_dq_reports')
PROFILES_DIR = REPORT_DIR / 'profiles'
DATA_DOCS_DIR = REPORT_DIR / 'data_docs'
EXPECTATIONS_DIR = REPORT_DIR / 'expectations'

# Create directories if they don't exist
for dir_path in [REPORT_DIR, PROFILES_DIR, DATA_DOCS_DIR, EXPECTATIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Initialize Great Expectations
context = gx.get_context()

# Print available methods
print("Available methods on context:")
print([method for method in dir(context) if not method.startswith('_')])

# Try to build data docs directly
try:
    context.build_data_docs()
    print("\nSuccessfully built data docs!")
except Exception as e:
    print(f"\nError building data docs: {str(e)}")
