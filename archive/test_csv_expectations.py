import great_expectations as gx
import pandas as pd
from pathlib import Path

# Define paths
DATA_DIR = Path('c:/Users/ymowe/Documents/DE_PYTHON_SQL/ymo_DE_python_sql/dummy_data')
REPORT_DIR = Path('./dq_reports')
PROFILES_DIR = REPORT_DIR / 'profiles'
DATA_DOCS_DIR = REPORT_DIR / 'data_docs'
EXPECTATIONS_DIR = REPORT_DIR / 'expectations'

# Create directories if they don't exist
for dir_path in [REPORT_DIR, PROFILES_DIR, DATA_DOCS_DIR, EXPECTATIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Initialize Great Expectations context
context = gx.get_context()

# Create a datasource for CSV files
datasource_config = {
    "name": "my_csv_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_inferred_data_connector_name": {
            "class_name": "InferredAssetFilesystemDataConnector",
            "base_directory": str(DATA_DIR),
            "default_regex": {
                "pattern": "(.*)\\.csv",
                "group_names": ["data_asset_name"]
            }
        }
    }
}

try:
    # Add the datasource
    context.add_or_update_datasource(**datasource_config)
    
    # Create an expectation suite
    suite = context.create_expectation_suite(
        expectation_suite_name="hr_addresses_suite",
        overwrite_existing=True
    )
    
    # Create validator for HR_ALL_ADDRESSES
    validator = context.get_validator(
        datasource_name="my_csv_datasource",
        data_connector_name="default_inferred_data_connector_name",
        data_asset_name="HR_ALL_ADDRESSES_20241216",
        expectation_suite_name="hr_addresses_suite"
    )

    # Add basic expectations
    validator.expect_table_row_count_to_be_between(min_value=1, max_value=1000)
    validator.expect_table_columns_to_match_ordered_list(
        column_list=["street_address", "city", "country", "postcode"]
    )
    
    # Add expectations for specific columns
    validator.expect_column_values_to_not_be_null("street_address")
    validator.expect_column_values_to_not_be_null("city")
    validator.expect_column_values_to_not_be_null("country")
    validator.expect_column_values_to_not_be_null("postcode")
    
    # Add data type expectations
    validator.expect_column_values_to_be_of_type("street_address", "str")
    validator.expect_column_values_to_be_of_type("city", "str")
    validator.expect_column_values_to_be_of_type("country", "str")
    validator.expect_column_values_to_be_of_type("postcode", "str")
    
    # Save the expectation suite
    validator.save_expectation_suite(discard_failed_expectations=False)
    
    # Run validation
    checkpoint_config = {
        "name": "my_checkpoint",
        "config_version": 1.0,
        "class_name": "SimpleCheckpoint",
        "run_name_template": "%Y%m%d-%H%M%S-my-run-name-template",
    }
    
    context.add_or_update_checkpoint(**checkpoint_config)
    
    results = context.run_checkpoint(
        checkpoint_name="my_checkpoint",
        validations=[{
            "batch_request": {
                "datasource_name": "my_csv_datasource",
                "data_connector_name": "default_inferred_data_connector_name",
                "data_asset_name": "HR_ALL_ADDRESSES_20241216",
            },
            "expectation_suite_name": "hr_addresses_suite"
        }]
    )
    
    # Build data docs
    context.build_data_docs()
    
    print("Great Expectations setup successful!")
    print("Data docs have been built. You can now view them in the dq_reports/data_docs directory.")

except Exception as e:
    print(f"Error occurred: {str(e)}")
