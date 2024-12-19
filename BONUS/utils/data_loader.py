import polars as pl
import json
import os
from typing import Dict, List, Optional
import sqlite3
import logging
from datetime import datetime
import re
from config import (
    DB_PATH, RULE_TEMPLATES_PATH, DEFAULT_PATTERNS, QUALITY_THRESHOLDS,
    MASTER_CONFIG_PATH, DATA_CONFIG_PATH, EXECUTION_HISTORY_PATH,
    RULE_EXECUTION_HISTORY_PATH, COLUMN_STATS_CACHE_PATH,
    RULE_MANAGEMENT_CACHE_PATH, RULE_EXECUTION_CACHE_PATH,
    RULES_PROCESSING_CACHE_PATH, DATA_DIR
)

class DataLoader:
    """Data loader class to handle database operations and rule validation."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.rule_templates_path = RULE_TEMPLATES_PATH
        self.patterns = DEFAULT_PATTERNS
        self.thresholds = QUALITY_THRESHOLDS
        self._initialize_paths()
        self._verify_database_connection()
    
    def _initialize_paths(self):
        """Initialize all necessary paths and create directories if needed."""
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Initialize JSON files if they don't exist
        self._initialize_json_file(self.rule_templates_path, {
            "gdpr_rules": [],
            "data_quality_rules": [],
            "validation_rules": [],
            "business_rules": [],
            "table_level_rules": []
        })
        
        self._initialize_json_file(MASTER_CONFIG_PATH, {
            "database": {"name": "data_quality", "version": "1.0"},
            "tables": {},
            "rules": {},
            "validation_settings": {}
        })
        
        self._initialize_json_file(DATA_CONFIG_PATH, {
            "source_tables": [],
            "data_types": {},
            "validation_rules": {}
        })
        
        # Initialize cache files
        self._initialize_json_file(COLUMN_STATS_CACHE_PATH, {})
        self._initialize_json_file(RULE_MANAGEMENT_CACHE_PATH, {})
        self._initialize_json_file(RULE_EXECUTION_CACHE_PATH, {})
        self._initialize_json_file(RULES_PROCESSING_CACHE_PATH, {})
        
        # Initialize history files
        self._initialize_json_file(EXECUTION_HISTORY_PATH, {"executions": []})
        self._initialize_json_file(RULE_EXECUTION_HISTORY_PATH, {"rule_executions": []})
    
    def _initialize_json_file(self, file_path: str, default_content: Dict):
        """Initialize a JSON file with default content if it doesn't exist."""
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_content, f, indent=4)
    
    def load_json_file(self, file_path: str) -> Dict:
        """Load and return contents of a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading JSON file {file_path}: {str(e)}")
            return {}
    
    def save_json_file(self, file_path: str, content: Dict):
        """Save content to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving JSON file {file_path}: {str(e)}")

    def get_master_config(self) -> Dict:
        """Get the master configuration."""
        return self.load_json_file(MASTER_CONFIG_PATH)
    
    def get_data_config(self) -> Dict:
        """Get the data configuration."""
        return self.load_json_file(DATA_CONFIG_PATH)
    
    def get_rule_templates(self) -> Dict:
        """Get the rule templates."""
        return self.load_json_file(RULE_TEMPLATES_PATH)
    
    def update_execution_history(self, execution_result: Dict):
        """Update the execution history."""
        history = self.load_json_file(EXECUTION_HISTORY_PATH)
        history["executions"].append({
            **execution_result,
            "timestamp": datetime.now().isoformat()
        })
        self.save_json_file(EXECUTION_HISTORY_PATH, history)
    
    def update_rule_execution_history(self, rule_result: Dict):
        """Update the rule execution history."""
        history = self.load_json_file(RULE_EXECUTION_HISTORY_PATH)
        history["rule_executions"].append({
            **rule_result,
            "timestamp": datetime.now().isoformat()
        })
        self.save_json_file(RULE_EXECUTION_HISTORY_PATH, history)
    
    def cache_column_stats(self, table_name: str, stats: Dict):
        """Cache column statistics."""
        cache = self.load_json_file(COLUMN_STATS_CACHE_PATH)
        cache[table_name] = {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        self.save_json_file(COLUMN_STATS_CACHE_PATH, cache)
    
    def get_cached_column_stats(self, table_name: str) -> Optional[Dict]:
        """Get cached column statistics."""
        cache = self.load_json_file(COLUMN_STATS_CACHE_PATH)
        return cache.get(table_name, {}).get("stats")
    
    def _verify_database_connection(self):
        """Verify database connection and log available tables."""
        try:
            with self.connection as conn:
                tables = self.get_table_names()
                logging.info(f"Successfully connected to database. Available tables: {', '.join(tables)}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            raise
    
    @property
    def connection(self):
        """Create a new database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_table_names(self) -> List[str]:
        """Get list of available tables from database."""
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting table names: {str(e)}")
            return []
    
    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get schema information for a table."""
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name});")
                return [
                    {
                        'name': col[1],
                        'type': col[2],
                        'notnull': bool(col[3]),
                        'pk': bool(col[5])
                    }
                    for col in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Error getting schema for {table_name}: {str(e)}")
            return []
    
    def get_table_data(self, table_name: str) -> pl.DataFrame:
        """Get data from specified table using Polars."""
        try:
            with self.connection as conn:
                query = f"SELECT * FROM {table_name}"
                return pl.read_database(query=query, connection=conn)
        except Exception as e:
            logging.error(f"Error getting data for {table_name}: {str(e)}")
            return pl.DataFrame()
    
    def get_column_stats(self, table_name: str, column_name: str) -> Dict:
        """Get detailed statistics for a specific column."""
        try:
            df = self.get_table_data(table_name)
            if column_name not in df.columns:
                raise ValueError(f"Column {column_name} not found in table {table_name}")
            
            col_series = df[column_name]
            stats = {
                'name': column_name,
                'type': str(col_series.dtype),
                'null_count': col_series.null_count(),
                'unique_count': col_series.n_unique()
            }
            
            if pl.datatypes.is_numeric(col_series.dtype):
                stats.update({
                    'min': float(col_series.min()),
                    'max': float(col_series.max()),
                    'mean': float(col_series.mean()),
                    'std': float(col_series.std())
                })
            
            return stats
        except Exception as e:
            logging.error(f"Error getting stats for {table_name}.{column_name}: {str(e)}")
            return {}
    
    def run_validation_rules(self, table_name: str) -> Dict:
        """Run validation rules on specified table."""
        try:
            # Load data and rules
            df = self.get_table_data(table_name)
            if df.is_empty():
                raise ValueError(f"No data found in table {table_name}")
            
            with open(self.rule_templates_path, 'r') as f:
                rules = json.load(f)
            
            results = {
                'table_name': table_name,
                'timestamp': datetime.now().isoformat(),
                'total_rules': 0,
                'failed_rules': 0,
                'rule_results': []
            }
            
            # Run each type of rule
            for rule_type, rule_list in rules.items():
                for rule in rule_list:
                    if not rule.get('active', True):
                        continue
                    
                    results['total_rules'] += 1
                    try:
                        # Create validation context
                        validation_context = {
                            'df': df,
                            'pl': pl,
                            're': re,
                            'con': self.connection,
                            'table_name': table_name
                        }
                        
                        # Execute validation code
                        validation_result = eval(rule['validation_code'], validation_context)
                        
                        if isinstance(validation_result, pl.Series):
                            failed_count = validation_result.sum()
                            passed = failed_count == 0
                        else:
                            failed_count = 0 if validation_result else 1
                            passed = validation_result
                        
                        if not passed:
                            results['failed_rules'] += 1
                        
                        results['rule_results'].append({
                            'rule_id': rule['id'],
                            'rule_name': rule['name'],
                            'category': rule['category'],
                            'severity': rule['severity'],
                            'passed': passed,
                            'failed_count': int(failed_count),
                            'message': rule['message']
                        })
                        
                    except Exception as rule_error:
                        logging.error(f"Error executing rule {rule['name']}: {str(rule_error)}")
                        results['failed_rules'] += 1
                        results['rule_results'].append({
                            'rule_id': rule['id'],
                            'rule_name': rule['name'],
                            'category': rule['category'],
                            'severity': rule['severity'],
                            'passed': False,
                            'failed_count': 0,
                            'message': f"Error: {str(rule_error)}"
                        })
            
            # Save results
            self._save_validation_results(results)
            return results
            
        except Exception as e:
            logging.error(f"Error running validation rules: {str(e)}")
            return {
                'table_name': table_name,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _save_validation_results(self, results: Dict):
        """Save validation results to file."""
        try:
            results_dir = os.path.join('BONUS', 'assets', 'data', 'validation_results')
            os.makedirs(results_dir, exist_ok=True)
            
            file_path = os.path.join(
                results_dir,
                f"{results['table_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=4)
                
        except Exception as e:
            logging.error(f"Error saving validation results: {str(e)}")
    
    def get_validation_history(self, table_name: Optional[str] = None) -> List[Dict]:
        """Get validation history for specified table or all tables."""
        try:
            results_dir = os.path.join('BONUS', 'assets', 'data', 'validation_results')
            if not os.path.exists(results_dir):
                return []
            
            history = []
            for file_name in os.listdir(results_dir):
                if file_name.endswith('.json'):
                    with open(os.path.join(results_dir, file_name), 'r') as f:
                        result = json.load(f)
                        if not table_name or result['table_name'] == table_name:
                            history.append(result)
            
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logging.error(f"Error getting validation history: {str(e)}")
            return []
    
    def get_table_metadata(self, table_name: str) -> Dict:
        """Get comprehensive metadata about a table."""
        try:
            schema = self.get_table_schema(table_name)
            df = self.get_table_data(table_name)
            
            return {
                'name': table_name,
                'row_count': len(df),
                'column_count': len(df.columns),
                'schema': schema,
                'columns': [
                    {
                        'name': col,
                        'type': str(df[col].dtype),
                        'null_count': df[col].null_count(),
                        'unique_count': df[col].n_unique()
                    }
                    for col in df.columns
                ],
                'last_validated': self._get_last_validation_time(table_name)
            }
        except Exception as e:
            logging.error(f"Error getting metadata for {table_name}: {str(e)}")
            return {}
    
    def _get_last_validation_time(self, table_name: str) -> Optional[str]:
        """Get the timestamp of the last validation run for a table."""
        history = self.get_validation_history(table_name)
        return history[0]['timestamp'] if history else None