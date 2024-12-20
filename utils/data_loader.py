import json
import pandas as pd
import logging
from pathlib import Path
from functools import lru_cache
import os
import sqlite3  # or your preferred database connector

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   'assets', 'data', 'hr_database.sqlite')
        self.rules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      'assets', 'data', 'rule_templates.json')
        self.results_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          'assets', 'data', 'validation_results.json')
        self.rule_config_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                'assets', 'data', 'rule_configurations.json')
        self._ensure_directories()
        self._ensure_tables()
        self.rules = self._load_rules()
        
        if os.path.exists(self.db_path):
            logger.info(f"Database found at {self.db_path}")
        else:
            logger.warning(f"Database not found at {self.db_path}")

        self.clear_cache()

    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(os.path.dirname(self.rules_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @lru_cache(maxsize=1)
    def _load_rules(self):
        """Load and cache rule templates from JSON file."""
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, 'r') as f:
                    rules = json.load(f)
                logger.info("Successfully loaded rule templates")
                return rules
            else:
                # Create default rules if file doesn't exist
                default_rules = {
                    "data_quality_rules": [
                        {
                            "id": "dq_001",
                            "name": "Null Check",
                            "description": "Check for null values",
                            "severity": "High",
                            "active": True
                        }
                    ]
                }
                with open(self.rules_path, 'w') as f:
                    json.dump(default_rules, f, indent=4)
                logger.info(f"Created default rule templates at {self.rules_path}")
                return default_rules
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return {}

    def get_available_tables(self):
        """Get list of available tables from hr_database."""
        try:
            # First try to connect to the database
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' 
                        AND name NOT LIKE 'sqlite_%'
                    """)
                    tables = cursor.fetchall()
                    table_list = [table[0] for table in tables]
                    logger.info(f"Found tables: {table_list}")
                    return table_list
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return []
        except Exception as e:
            logger.error(f"Error getting available tables: {str(e)}")
            return []

    def get_table_columns(self, table_name):
        """Get list of columns for a specific table."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    logger.info(f"Found columns for {table_name}: {column_names}")
                    return column_names
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return []
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {str(e)}")
            return []

    def get_table_data(self, table_name, columns=None):
        """Get data from specified table and columns."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    column_str = '*' if not columns else ', '.join(columns)
                    query = f"SELECT {column_str} FROM {table_name}"
                    df = pd.read_sql_query(query, conn)
                    logger.info(f"Retrieved {len(df)} rows from {table_name}")
                    return df
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting data from table {table_name}: {str(e)}")
            return pd.DataFrame()

    def get_rule_execution_results(self):
        """Get results of rule executions from the database."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    query = """
                    SELECT r.rule_id, r.name, r.description, r.severity,
                           CASE 
                               WHEN re.failed_count = 0 THEN 'passed'
                               ELSE 'failed'
                           END as status,
                           re.failed_count,
                           re.passed_count
                    FROM rules r
                    LEFT JOIN rule_executions re ON r.rule_id = re.rule_id
                    WHERE re.execution_date = (
                        SELECT MAX(execution_date) 
                        FROM rule_executions
                    )
                    """
                    df = pd.read_sql_query(query, conn)
                    return df.to_dict('records')
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return []
        except Exception as e:
            logger.error(f"Error getting rule execution results: {str(e)}")
            return []

    def get_rule_failed_records(self, rule_id):
        """Get failed records for a specific rule."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    query = f"""
                    SELECT *
                    FROM rule_validation_results
                    WHERE rule_id = ? AND status = 'failed'
                    """
                    return pd.read_sql_query(query, conn, params=(rule_id,))
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting failed records for rule {rule_id}: {str(e)}")
            return pd.DataFrame()

    def get_rule_passed_records(self, rule_id):
        """Get passed records for a specific rule."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    query = f"""
                    SELECT *
                    FROM rule_validation_results
                    WHERE rule_id = ? AND status = 'passed'
                    """
                    return pd.read_sql_query(query, conn, params=(rule_id,))
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting passed records for rule {rule_id}: {str(e)}")
            return pd.DataFrame()

    def _load_rules(self):
        """Load and cache rule templates from JSON file."""
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, 'r') as f:
                    rules = json.load(f)
                logger.info("Successfully loaded rule templates")
                return rules
            else:
                logger.warning(f"Rules file not found: {self.rules_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return {}

    def get_rules(self, category=None):
        """Get rules, optionally filtered by category."""
        if category and category in self.rules:
            return self.rules[category]
        return self.rules

    def get_rule_categories(self):
        """Get list of available rule categories."""
        return list(self.rules.keys())

    def refresh_rules(self):
        """Force refresh of cached rules."""
        self._load_rules.cache_clear()
        self.rules = self._load_rules()
        return self.rules

    def _ensure_rule_validation_table(self):
        """Ensure rule_validation_results and rule_execution_status tables exist."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Create rule_validation_results if not exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS rule_validation_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rule_id TEXT NOT NULL,
                            table_name TEXT NOT NULL,
                            column_name TEXT,
                            record_id TEXT,
                            status TEXT NOT NULL,
                            error_message TEXT,
                            validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            validation_value TEXT,
                            additional_info TEXT
                        )
                    """)
                    
                    # Create rule_execution_status if not exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS rule_execution_status (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rule_id TEXT NOT NULL,
                            rule_category TEXT NOT NULL,
                            last_execution_date TIMESTAMP,
                            execution_status TEXT,
                            error_message TEXT,
                            execution_count INTEGER DEFAULT 0,
                            UNIQUE(rule_id)
                        )
                    """)
                    
                    conn.commit()
                    logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")

    def get_rules(self):
        """Load rules from rule_templates.json with proper structure."""
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, 'r') as f:
                    rule_templates = json.load(f)
                
                all_rules = []
                
                # Process GDPR rules
                if 'gdpr_rules' in rule_templates:
                    all_rules.extend(rule_templates['gdpr_rules'])
                
                # Process validation rules
                if 'validation_rules' in rule_templates:
                    all_rules.extend(rule_templates['validation_rules'])
                
                # Process business rules
                if 'business_rules' in rule_templates:
                    all_rules.extend(rule_templates['business_rules'])
                
                # Process table-specific rules
                if 'table_specific_rules' in rule_templates:
                    for table_rules in rule_templates['table_specific_rules'].values():
                        all_rules.extend(table_rules)
                
                # Process cross-table rules
                if 'cross_table_rules' in rule_templates:
                    all_rules.extend(rule_templates['cross_table_rules'])
                
                # Process complex business rules
                if 'complex_business_rules' in rule_templates:
                    all_rules.extend(rule_templates['complex_business_rules'])
                
                logger.info(f"Loaded {len(all_rules)} rules from templates")
                return all_rules
            else:
                logger.error(f"Rule templates file not found: {self.rules_path}")
                return []
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return []

    def update_rule_execution_status(self, rule_id, category, status, error_message=None):
        """Update the execution status of a rule."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO rule_execution_status 
                        (rule_id, rule_category, last_execution_date, execution_status, error_message, execution_count)
                        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, 1)
                        ON CONFLICT(rule_id) DO UPDATE SET
                        last_execution_date = CURRENT_TIMESTAMP,
                        execution_status = ?,
                        error_message = ?,
                        execution_count = execution_count + 1
                    """, (rule_id, category, status, error_message, status, error_message))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error updating rule execution status: {str(e)}")

    def execute_rule(self, rule, df):
        """Execute a single rule and handle errors."""
        try:
            if not rule.get('active', True):
                return None
            
            validation_code = rule.get('validation_code')
            if not validation_code:
                raise ValueError("No validation code provided")
            
            # Execute the rule
            result = eval(validation_code)
            
            # Update execution status
            self.update_rule_execution_status(
                rule['id'],
                rule.get('category', 'unknown'),
                'success'
            )
            
            return result
        except Exception as e:
            error_msg = f"Error executing rule: {str(e)}"
            logger.error(error_msg)
            
            # Update execution status with error
            self.update_rule_execution_status(
                rule['id'],
                rule.get('category', 'unknown'),
                'failed',
                error_msg
            )
            return None

    def get_failed_rules(self):
        """Get list of rules that failed execution."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    query = """
                    SELECT rule_id, rule_category, last_execution_date, 
                           execution_status, error_message, execution_count
                    FROM rule_execution_status
                    WHERE execution_status = 'failed'
                    ORDER BY last_execution_date DESC
                    """
                    return pd.read_sql_query(query, conn)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting failed rules: {str(e)}")
            return pd.DataFrame()

    def _ensure_tables(self):
        """Ensure all necessary tables exist."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Create validation_results table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS validation_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rule_id TEXT NOT NULL,
                            table_name TEXT NOT NULL,
                            column_name TEXT,
                            record_id TEXT,
                            status TEXT NOT NULL,
                            error_message TEXT,
                            validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            validation_value TEXT,
                            additional_info TEXT
                        )
                    """)
                    
                    # Create rule_configurations table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS rule_configurations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rule_id TEXT NOT NULL,
                            table_name TEXT NOT NULL,
                            column_name TEXT,
                            active BOOLEAN DEFAULT TRUE,
                            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            configuration_json TEXT,
                            UNIQUE(rule_id, table_name, column_name)
                        )
                    """)
                    
                    # Create rule_execution_status table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS rule_execution_status (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rule_id TEXT NOT NULL,
                            rule_category TEXT NOT NULL,
                            last_execution_date TIMESTAMP,
                            execution_status TEXT,
                            error_message TEXT,
                            execution_count INTEGER DEFAULT 0,
                            UNIQUE(rule_id)
                        )
                    """)
                    
                    conn.commit()
                    logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")

    def save_validation_results(self, results):
        """Save validation results to database or JSON."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.executemany("""
                        INSERT INTO validation_results 
                        (rule_id, table_name, column_name, record_id, status, 
                         error_message, validation_value, additional_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        (r['rule_id'], r['table_name'], r.get('column_name'), 
                         r.get('record_id'), r['status'], r.get('error_message'),
                         str(r.get('validation_value')), json.dumps(r.get('additional_info', {})))
                        for r in results
                    ])
                    conn.commit()
                    logger.info(f"Saved {len(results)} validation results to database")
            else:
                self._save_results_to_json(results)
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            self._save_results_to_json(results)

    def save_rule_configuration(self, rule_id, table_name, column_name, configuration=None):
        """Save rule configuration to database."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO rule_configurations 
                        (rule_id, table_name, column_name, configuration_json, last_modified)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(rule_id, table_name, column_name) 
                        DO UPDATE SET 
                            configuration_json = ?,
                            last_modified = CURRENT_TIMESTAMP
                    """, (rule_id, table_name, column_name, 
                          json.dumps(configuration or {}),
                          json.dumps(configuration or {})))
                    conn.commit()
                    logger.info(f"Saved configuration for rule {rule_id}")
            else:
                self._save_configuration_to_json(rule_id, table_name, column_name, configuration)
        except Exception as e:
            logger.error(f"Error saving rule configuration: {str(e)}")
            self._save_configuration_to_json(rule_id, table_name, column_name, configuration)

    def get_table_rules(self, table_name):
        """Get rules configured for a specific table."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    query = """
                    SELECT r.* 
                    FROM rule_configurations rc
                    JOIN rule_templates r ON rc.rule_id = r.id
                    WHERE rc.table_name = ?
                    """
                    return pd.read_sql_query(query, conn, params=(table_name,)).to_dict('records')
            return []
        except Exception as e:
            logger.error(f"Error getting table rules: {str(e)}")
            return []

    def get_rule_configuration(self, rule_id):
        """Get configuration for a specific rule."""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    query = """
                    SELECT * FROM rule_configurations
                    WHERE rule_id = ?
                    """
                    result = pd.read_sql_query(query, conn, params=(rule_id,))
                    return result.to_dict('records')[0] if not result.empty else None
            return None
        except Exception as e:
            logger.error(f"Error getting rule configuration: {str(e)}")
            return None

    def process_validation_result(self, rule, df, validation_result, table_name):
        """Process validation results and format for storage."""
        results = []
        if isinstance(validation_result, pd.Series):
            failed_indices = df[~validation_result].index
            passed_indices = df[validation_result].index
            
            column_name = rule.get('column_name')
            
            # Process failed records
            for idx in failed_indices:
                results.append({
                    'rule_id': rule['id'],
                    'table_name': table_name,
                    'column_name': column_name,
                    'record_id': str(df.iloc[idx].name),
                    'status': 'failed',
                    'error_message': rule.get('message', 'Validation failed'),
                    'validation_value': str(df.iloc[idx][column_name]) if column_name else None,
                    'additional_info': {
                        'rule_category': rule.get('category'),
                        'rule_type': rule.get('type'),
                        'severity': rule.get('severity')
                    }
                })
            
            # Process passed records
            for idx in passed_indices:
                results.append({
                    'rule_id': rule['id'],
                    'table_name': table_name,
                    'column_name': column_name,
                    'record_id': str(df.iloc[idx].name),
                    'status': 'passed',
                    'validation_value': str(df.iloc[idx][column_name]) if column_name else None,
                    'additional_info': {
                        'rule_category': rule.get('category'),
                        'rule_type': rule.get('type'),
                        'severity': rule.get('severity')
                    }
                })
        
        return results

    def clear_cache(self):
        """Clear any cached data and connections."""
        try:
            # Clear any existing database connections
            if hasattr(self, '_conn'):
                self._conn.close()
                delattr(self, '_conn')
            
            # Clear cached rules
            if hasattr(self, '_rules_cache'):
                delattr(self, '_rules_cache')
            
            # Clear method caches if they exist
            for method in ['get_rules', 'get_table_columns', 'get_available_tables']:
                if hasattr(self, f'_{method}_cache'):
                    delattr(self, f'_{method}_cache')
            
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")