import json
import pandas as pd
import logging
from pathlib import Path
from functools import lru_cache
import os
import sqlite3  # or your preferred database connector
from datetime import datetime
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.rules_path = 'assets/data/rule_templates.json'
        self.config_path = 'assets/data/rule_configurations.json'
        self.db_path = 'assets/data/hr_database.sqlite'
        self._rules_cache = None
        self._config_cache = None
        self._data_cache = {}
        self._local = threading.local()
        self._init_control_tables()

    @contextmanager
    def _get_connection(self):
        """Get SQLite connection in a thread-safe way."""
        try:
            if not hasattr(self._local, 'connection') or self._local.connection is None:
                self._local.connection = sqlite3.connect(self.db_path)
            yield self._local.connection
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            yield None
        finally:
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                self._local.connection.close()
                self._local.connection = None

    def get_rules(self):
        """Load rules from rule_templates.json with caching."""
        if self._rules_cache is None:
            try:
                with open(self.rules_path, 'r') as f:
                    self._rules_cache = json.load(f)
                logger.debug(f"Loaded {len(self._rules_cache)} rule categories")
            except Exception as e:
                logger.error(f"Error loading rules: {str(e)}")
                self._rules_cache = {}
        return self._rules_cache

    def get_rule_configuration(self, rule_id):
        """Get configuration for a specific rule."""
        if self._config_cache is None:
            try:
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        config_data = json.load(f)
                        self._config_cache = config_data.get('rule_configs', {})
                else:
                    # Initialize with empty structure
                    self._config_cache = {}
                    with open(self.config_path, 'w') as f:
                        json.dump({'rule_configs': {}}, f, indent=2)
            except Exception as e:
                logger.error(f"Error loading rule configurations: {str(e)}")
                self._config_cache = {}
        
        return self._config_cache.get(rule_id)

    def save_rule_configuration(self, rule_id, config):
        """Save configuration for a specific rule."""
        try:
            # Load existing configurations
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = {'rule_configs': {}}
            
            # Update configuration
            if 'rule_configs' not in config_data:
                config_data['rule_configs'] = {}
            
            config_data['rule_configs'][rule_id] = config
            
            # Save back to file
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Update cache
            if self._config_cache is None:
                self._config_cache = {}
            self._config_cache[rule_id] = config
            
            logger.debug(f"Saved configuration for rule {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving rule configuration: {str(e)}")
            return False

    def get_table_data(self, table_name):
        """Get data for a specific table with caching."""
        if table_name not in self._data_cache:
            try:
                with self._get_connection() as conn:
                    if conn is not None:
                        query = f"SELECT * FROM {table_name}"
                        df = pd.read_sql_query(query, conn)
                        self._data_cache[table_name] = df
                        logger.info(f"Retrieved {len(df)} rows from {table_name}")
                        return df
                return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error loading table {table_name}: {str(e)}")
                return pd.DataFrame()
        return self._data_cache[table_name]

    def execute_rule(self, rule, df, column_name=None):
        """Execute a validation rule on the dataframe."""
        try:
            rule_id = rule.get('id', '')
            
            # Get rule configuration
            if not column_name:
                rule_config = self.get_rule_configuration(rule_id)
                if rule_config:
                    column_name = rule_config.get('column_name')
                    table_name = rule_config.get('table_name')
                else:
                    # Try to determine table from rule category
                    table_name = None
                    for category, rules in self.get_rules().items():
                        if category.endswith('_table_rules'):
                            table_name = category.replace('_rules', '')
                            if isinstance(rules, list) and any(r['id'] == rule_id for r in rules):
                                break

            # Handle special rules that don't require column_name
            if 'validation_code' in rule:
                validation_code = rule['validation_code']
                
                # Special handling for isin() operations
                if 'isin' in validation_code:
                    # If checking against the same dataframe
                    if "df['" in validation_code and ".isin(df['" in validation_code:
                        # No modification needed as it's comparing within same dataframe
                        pass
                    # If checking against reference data
                    elif any(ref in validation_code for ref in ['valid_departments', 'approved_authorities']):
                        local_vars = {'df': df}
                        local_vars.update(self._get_reference_data_for_rule(rule))
                    else:
                        # Convert the validation code to use values instead of column names
                        validation_code = validation_code.replace('.isin(', '.isin(df[')
                
                # Regular column name replacement
                if 'column_name' in validation_code:
                    if not column_name:
                        raise ValueError(f"Column name required for rule {rule_id}")
                    if column_name not in df.columns:
                        logger.error(f"Column {column_name} not found in dataframe. Available columns: {df.columns.tolist()}")
                        raise ValueError(f"Column {column_name} not found in dataframe")
                    validation_code = validation_code.replace('column_name', f"df['{column_name}']")

                # Execute the validation code
                local_vars = {'df': df}
                result = eval(validation_code, {}, local_vars)
                return result
                
            return None
        except Exception as e:
            logger.error(f"Error executing rule {rule.get('id', '')}: {str(e)}")
            return None

    def _get_reference_data_for_rule(self, rule):
        """Get all necessary reference data for a rule."""
        reference_data = {}
        validation_code = rule.get('validation_code', '')
        
        if 'valid_departments' in validation_code:
            reference_data['valid_departments'] = self.get_reference_data('valid_departments')
        if 'approved_authorities' in validation_code:
            reference_data['approved_authorities'] = self.get_reference_data('approved_authorities')
        if 'salary_ranges' in validation_code:
            reference_data['salary_ranges'] = self.get_reference_data('salary_ranges')
        if 'postal_code_patterns' in validation_code:
            reference_data['postal_code_patterns'] = self.get_reference_data('postal_code_patterns')
            
        return reference_data

    def get_reference_data(self, data_type):
        """Get reference data for validation rules."""
        try:
            with self._get_connection() as conn:
                if conn is not None:
                    if data_type == 'valid_departments':
                        df = pd.read_sql_query("SELECT id FROM departments", conn)
                        return df['id'].tolist()
                    elif data_type == 'salary_ranges':
                        df = pd.read_sql_query("SELECT * FROM salary_ranges", conn)
                        return {row['grade']: {'min': row['min_salary'], 'max': row['max_salary']} 
                                for _, row in df.iterrows()}
                    elif data_type == 'postal_code_patterns':
                        return {
                            'US': r'^\d{5}(-\d{4})?$',
                            'UK': r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$',
                            'DE': r'^\d{5}$'
                        }
            return None
        except Exception as e:
            logger.error(f"Error getting reference data: {str(e)}")
            return None

    def process_validation_result(self, rule, df, validation_result, table_name):
        """Process the validation result and return formatted output."""
        try:
            if isinstance(validation_result, pd.Series):
                failed_rows = df[validation_result]
                status = 'failed' if not failed_rows.empty else 'passed'
                return [{
                    'rule_id': rule['id'],
                    'table_name': table_name,
                    'status': status,
                    'failed_count': len(failed_rows),
                    'message': rule['message'],
                    'timestamp': datetime.now().isoformat()
                }]
            return []
        except Exception as e:
            logger.error(f"Error processing validation result: {str(e)}")
            return []

    def get_rule_categories(self):
        """Get list of available rule categories."""
        try:
            rules_data = self.get_rules()
            # Extract top-level categories from rule_templates.json
            categories = [
                'gdpr_rules',
                'data_quality_rules',
                'validation_rules',
                'business_rules',
                'cross_table_rules',
                'complex_business_rules'
            ]
            # Add table-specific rules if they exist
            if 'table_specific_rules' in rules_data:
                for table_category in rules_data['table_specific_rules'].keys():
                    categories.append(table_category)
            
            logger.debug(f"Found {len(categories)} rule categories")
            return categories
        except Exception as e:
            logger.error(f"Error getting rule categories: {str(e)}")
            return []

    def get_available_tables(self):
        """Get list of available tables from SQLite database."""
        try:
            with self._get_connection() as conn:
                if conn is not None:
                    query = """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """
                    df = pd.read_sql_query(query, conn)
                    tables = df['name'].tolist()
                    logger.debug(f"Found {len(tables)} available tables")
                    return sorted(tables)
            return []
        except Exception as e:
            logger.error(f"Error getting available tables: {str(e)}")
            return []

    def get_table_columns(self, table_name):
        """Get columns for a specific table from SQLite database."""
        try:
            with self._get_connection() as conn:
                if conn is not None:
                    query = f"PRAGMA table_info({table_name})"
                    df = pd.read_sql_query(query, conn)
                    columns = df['name'].tolist()
                    logger.debug(f"Found {len(columns)} columns for table {table_name}")
                    return columns
            return []
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {str(e)}")
            return []

    def _init_control_tables(self):
        """Initialize control tables for rule execution tracking."""
        try:
            with self._get_connection() as conn:
                if conn is not None:
                    cursor = conn.cursor()
                    # Create tables (same SQL as before)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS rule_execution_control (
                            rule_id TEXT PRIMARY KEY,
                            last_execution_timestamp DATETIME,
                            cache_valid_until DATETIME,
                            execution_count INTEGER DEFAULT 0,
                            last_status TEXT,
                            cache_key TEXT
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS rule_results_cache (
                            cache_key TEXT PRIMARY KEY,
                            rule_id TEXT,
                            result_data TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            valid_until DATETIME,
                            FOREIGN KEY (rule_id) REFERENCES rule_execution_control(rule_id)
                        )
                    """)
                    conn.commit()
                    logger.debug("Control tables initialized")
        except Exception as e:
            logger.error(f"Error initializing control tables: {str(e)}")

    def get_all_rule_configurations(self):
        """Get all rule configurations."""
        try:
            if self._config_cache is None:
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        config_data = json.load(f)
                        self._config_cache = config_data.get('rule_configs', {})
                else:
                    self._config_cache = {}
            return self._config_cache
        except Exception as e:
            logger.error(f"Error loading all rule configurations: {str(e)}")
            return {}