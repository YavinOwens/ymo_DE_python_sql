import polars as pl
import sqlite3
from typing import Dict, List, Optional
import json
from sqlalchemy import create_engine, inspect, text
import contextlib
import os
from datetime import datetime
from config import DB_PATH
import pandas as pd
import logging
import numpy as np

class DataLoader:
    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), 'assets', 'data')
        os.makedirs(self.base_path, exist_ok=True)  # Ensure data directory exists
        self.master_config_path = os.path.join(self.base_path, 'master_config.json')
        self._ensure_master_config_exists()
        
    def _ensure_master_config_exists(self):
        """Ensures master config file exists and has all required sections."""
        if not os.path.exists(self.master_config_path):
            default_config = {
                "data_config": {
                    "data_sources": {},
                    "database": {"connection_string": "", "tables": []}
                },
                "rule_templates": [],
                "activities": [],
                "execution_history": [],
                "rule_execution_history": [],
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            self._save_json(self.master_config_path, default_config)
    
    def _load_master_config(self):
        """Load the master configuration file."""
        try:
            self._ensure_master_config_exists()  # Ensure config exists before loading
            with open(self.master_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading master config: {str(e)}")
            return None
    
    def _save_master_config(self, config):
        """Save the master configuration file."""
        config['last_updated'] = datetime.now().isoformat()
        self._save_json(self.master_config_path, config)
    
    def _save_json(self, path, data):
        """Save data to a JSON file with proper formatting."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_data_config(self):
        """Get data configuration."""
        config = self._load_master_config()
        return config.get('data_config', {})
    
    def get_rule_templates(self):
        """Get rule templates."""
        config = self._load_master_config()
        return config.get('rule_templates', [])
    
    def save_rule_templates(self, templates):
        """Save rule templates."""
        config = self._load_master_config()
        config['rule_templates'] = templates
        self._save_master_config(config)
    
    def get_activities(self):
        """Get activities (deprecated)."""
        return []

    def save_activity(self, activity):
        """Save a new activity (deprecated)."""
        pass

    def get_execution_history(self):
        """Get execution history."""
        config = self._load_master_config()
        return config.get('execution_history', [])
    
    def save_execution_history(self, history):
        """Save execution history."""
        config = self._load_master_config()
        config['execution_history'] = history
        self._save_master_config(config)
    
    def get_rule_execution_history(self):
        """Get rule execution history."""
        config = self._load_master_config()
        return config.get('rule_execution_history', [])
    
    def save_rule_execution_history(self, history):
        """Save rule execution history."""
        config = self._load_master_config()
        config['rule_execution_history'] = history
        self._save_master_config(config)
    
    def save_rule_status(self, rule_id, status):
        """Save rule status."""
        config = self._load_master_config()
        templates = config.get('rule_templates', [])
        
        for template in templates:
            if template['id'] == rule_id:
                template['active'] = status
                break
                
        config['rule_templates'] = templates
        self._save_master_config(config)
        return {"success": True}
    
    @contextlib.contextmanager
    def get_connection(self):
        """Create a new connection for each operation."""
        conn = sqlite3.connect(DB_PATH)
        try:
            yield conn
        finally:
            conn.close()
    
    def get_table_names(self) -> List[str]:
        """Get list of available tables from database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting table names: {str(e)}")
            return []
    
    def get_available_tables(self) -> List[str]:
        """Get list of available tables from database."""
        return self.get_table_names()
    
    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get schema information for a table."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = []
                for col in cursor.fetchall():
                    columns.append({
                        'name': col[1],
                        'type': col[2],
                        'notnull': col[3],
                        'default': col[4],
                        'pk': col[5]
                    })
                return columns
        except Exception as e:
            print(f"Error getting schema for {table_name}: {str(e)}")
            return []
    
    def load_table_data(self, table_name: str) -> Dict:
        """Load data from specified database table."""
        try:
            with self.get_connection() as conn:
                # Read table using Polars
                query = f"SELECT * FROM {table_name}"
                df = pl.read_database(query=query, connection=conn)
                
                # Get schema information
                schema = self.get_table_schema(table_name)
                
                # Calculate statistics
                stats = self._calculate_statistics(df)
                
                # Calculate quality metrics
                quality_metrics = self._calculate_quality_metrics(df, schema)
                
                return {
                    'data': df,
                    'schema': schema,
                    'stats': stats,
                    'quality_metrics': quality_metrics,
                    'table_name': table_name
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_statistics(self, df: pl.DataFrame) -> Dict:
        """Calculate basic statistics for the dataframe."""
        try:
            return {
                'row_count': len(df),
                'column_count': len(df.columns),
                'memory_usage': df.estimated_size(),
                'columns': df.columns,
                'dtypes': {col: str(df[col].dtype) for col in df.columns}
            }
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            return {}
    
    def _calculate_quality_metrics(self, df: pl.DataFrame, schema: List[Dict]) -> Dict:
        """Calculate data quality metrics for the dataframe."""
        try:
            total_rows = len(df)
            metrics = {
                'completeness': {},
                'uniqueness': {},
                'validity': {},
                'overall': {}
            }
            
            # Calculate completeness (non-null values)
            for col in df.columns:
                non_null_count = len(df) - df[col].null_count()
                completeness = non_null_count / total_rows if total_rows > 0 else 0
                metrics['completeness'][col] = completeness
            
            # Calculate uniqueness
            for col in df.columns:
                unique_count = df[col].n_unique()
                uniqueness = unique_count / total_rows if total_rows > 0 else 0
                metrics['uniqueness'][col] = uniqueness
            
            # Calculate validity (type conformance)
            for col in df.columns:
                col_schema = next((s for s in schema if s['name'] == col), None)
                if col_schema:
                    expected_type = col_schema['type'].lower()
                    actual_type = str(df[col].dtype).lower()
                    # Map SQLite types to Polars types
                    type_map = {
                        'integer': ['i8', 'i16', 'i32', 'i64', 'u8', 'u16', 'u32', 'u64'],
                        'real': ['f32', 'f64'],
                        'text': ['str'],
                        'blob': ['binary'],
                        'numeric': ['decimal', 'f32', 'f64']
                    }
                    valid_types = []
                    for sqlite_type, polars_types in type_map.items():
                        if sqlite_type in expected_type:
                            valid_types.extend(polars_types)
                    
                    validity = 1.0 if any(t in actual_type for t in valid_types) else 0.0
                    metrics['validity'][col] = validity
            
            # Calculate overall metrics
            metrics['overall'] = {
                'completeness': sum(metrics['completeness'].values()) / len(df.columns),
                'uniqueness': sum(metrics['uniqueness'].values()) / len(df.columns),
                'validity': sum(metrics['validity'].values()) / len(df.columns)
            }
            
            # Calculate total score
            metrics['overall']['total_score'] = (
                metrics['overall']['completeness'] * 0.4 +
                metrics['overall']['uniqueness'] * 0.3 +
                metrics['overall']['validity'] * 0.3
            )
            
            return metrics
        except Exception as e:
            print(f"Error calculating quality metrics: {str(e)}")
            return {}
    
    def get_table_preview(self, table_name: str, limit: int = 100) -> pl.DataFrame:
        """Get a preview of the table data."""
        try:
            with self.get_connection() as conn:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                return pl.read_database(query=query, connection=conn)
        except Exception as e:
            print(f"Error getting preview for {table_name}: {str(e)}")
            return pl.DataFrame()
    
    def get_column_profile(self, table_name: str, column_name: str) -> Dict:
        """Get detailed profile for a specific column."""
        try:
            with self.get_connection() as conn:
                query = f"SELECT {column_name} FROM {table_name} LIMIT 1000"
                df = pl.read_database(query=query, connection=conn)
                
                if column_name not in df.columns:
                    return {'error': f'Column {column_name} not found in {table_name}'}
                
                col_data = df[column_name]
                
                # Get column statistics
                stats = {
                    'name': column_name,
                    'dtype': str(col_data.dtype),
                    'non_null_count': len(df) - col_data.null_count(),
                    'unique_count': col_data.n_unique(),
                }
                
                # Add numeric statistics if applicable
                if col_data.dtype in [pl.Int64, pl.Float64]:
                    stats.update({
                        'min_value': col_data.min(),
                        'max_value': col_data.max(),
                        'mean': col_data.mean(),
                        'std': col_data.std()
                    })
                
                # Get value frequencies
                value_counts = col_data.value_counts()
                stats['frequent_values'] = value_counts.head(5).to_dicts()
                
                return stats
        except Exception as e:
            return {'error': str(e)}

    def get_numerical_distribution(self, table_name, column_name):
        """Get numerical distribution data for a column."""
        try:
            with self.get_connection() as conn:
                query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            return {'error': str(e)}

    def get_numerical_stats(self, table_name, column_name):
        """Get numerical statistics for a column."""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT 
                    MIN({column_name}) as min,
                    MAX({column_name}) as max,
                    AVG({column_name}) as mean,
                    (
                        SELECT {column_name}
                        FROM (
                            SELECT {column_name}, ROW_NUMBER() OVER (ORDER BY {column_name}) as rn,
                                   COUNT(*) OVER () as cnt
                            FROM {table_name}
                            WHERE {column_name} IS NOT NULL
                        )
                        WHERE rn = (cnt + 1)/2
                    ) as median,
                    AVG(({column_name} - (SELECT AVG({column_name}) FROM {table_name})) * ({column_name} - (SELECT AVG({column_name}) FROM {table_name}))) as variance
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                """
                df = pd.read_sql_query(query, conn)
                stats = df.iloc[0].to_dict()
                stats['std'] = stats['variance'] ** 0.5
                return stats
        except Exception as e:
            return {'error': str(e)}

    def get_correlation_matrix(self, table_name, columns):
        """Get correlation matrix for selected columns."""
        try:
            with self.get_connection() as conn:
                columns_str = ', '.join(columns)
                query = f"SELECT {columns_str} FROM {table_name}"
                df = pd.read_sql_query(query, conn)
                return df.corr().round(3)
        except Exception as e:
            return {'error': str(e)}

    def update_rule_status(self, rule_id, active_status):
        """Update a rule's active status."""
        try:
            config = self._load_master_config()
            templates = config.get('rule_templates', [])
            
            for template in templates:
                if template['id'] == rule_id:
                    template['active'] = active_status
                    break
            
            config['rule_templates'] = templates
            self._save_master_config(config)
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_all_rules(self):
        """Get all rules with their current status."""
        try:
            config = self._load_master_config()
            templates = config.get('rule_templates', [])
            
            flat_rules = []
            for template in templates:
                flat_rules.append({
                    'id': template['id'],
                    'name': template['name'],
                    'category': template.get('category', 'N/A'),
                    'description': template['description'],
                    'type': template.get('type', 'N/A'),
                    'severity': template.get('severity', 'N/A'),
                    'active': template.get('active', True)
                })
            return flat_rules
        except Exception as e:
            return {'error': str(e)}

    def load_all_rules(self):
        """Load all rules from the rule templates file."""
        try:
            rule_templates_path = os.path.join(self.base_path, 'rule_templates.json')
            if not os.path.exists(rule_templates_path):
                return []
            
            with open(rule_templates_path, 'r') as f:
                templates = json.load(f)
            
            all_rules = []
            
            # Add GDPR rules
            for rule in templates.get('gdpr_rules', []):
                rule['type'] = 'GDPR'
                all_rules.append(rule)
            
            # Add Data Quality rules
            for rule in templates.get('data_quality_rules', []):
                rule['type'] = 'Data Quality'
                all_rules.append(rule)
            
            # Add Validation rules
            for rule in templates.get('validation_rules', []):
                rule['type'] = 'Validation'
                all_rules.append(rule)
            
            # Add Business rules
            for rule in templates.get('business_rules', []):
                rule['type'] = 'Business'
                all_rules.append(rule)
            
            # Add Table Level rules
            for rule in templates.get('table_level_rules', []):
                rule['type'] = 'Table Level'
                all_rules.append(rule)
            
            return all_rules
        except Exception as e:
            logging.error(f"Error loading rules: {str(e)}")
            return []
    
    def execute_rules(self, table_name):
        """Execute active rules and return results."""
        try:
            # Load table data
            table_data = self.load_table_data(table_name)
            if 'error' in table_data:
                raise Exception(f"Error loading table data: {table_data['error']}")
            
            df = table_data['data']
            
            # Load all rules
            rules = self.load_all_rules()
            active_rules = [rule for rule in rules if rule.get('active', False)]
            
            start_time = datetime.now()
            results = []
            
            for rule in active_rules:
                try:
                    # Skip rules without validation code
                    if not rule.get('validation_code'):
                        continue
                    
                    # Create a safe environment for eval
                    env = {
                        'df': df,
                        'pd': pd,
                        'np': np,
                        'datetime': datetime,
                        'timedelta': pd.Timedelta
                    }
                    
                    # Execute the validation code
                    validation_result = eval(rule['validation_code'], env)
                    
                    result = {
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'rule_type': rule['type'],
                        'passed': bool(validation_result),
                        'execution_time': 0.0,  # Will be updated
                        'message': rule.get('message', 'No message provided'),
                        'severity': rule.get('severity', 'Medium')
                    }
                    
                    results.append(result)
                    
                except Exception as rule_error:
                    logging.error(f"Error executing rule {rule['name']}: {str(rule_error)}")
                    results.append({
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'rule_type': rule['type'],
                        'passed': False,
                        'execution_time': 0.0,
                        'message': f"Error executing rule: {str(rule_error)}",
                        'severity': rule.get('severity', 'Medium')
                    })
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Calculate summary statistics
            total_rules = len(results)
            passed_rules = sum(1 for r in results if r['passed'])
            pass_rate = passed_rules / total_rules if total_rules > 0 else 0
            
            # Store execution history
            execution_summary = {
                'timestamp': datetime.now().isoformat(),
                'rules_executed': total_rules,
                'pass_rate': pass_rate,
                'fail_rate': 1 - pass_rate,
                'duration_seconds': duration,
                'results': results,
                'table_name': table_name
            }
            
            self._store_execution_history(execution_summary)
            
            return execution_summary
            
        except Exception as e:
            logging.error(f"Error in execute_rules: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'table_name': table_name
            }
    
    def _store_execution_history(self, execution_summary):
        """Store rule execution history in a JSON file."""
        try:
            config = self._load_master_config()
            history = config.get('execution_history', [])
            history.append(execution_summary)
            config['execution_history'] = history
            self._save_master_config(config)
        except Exception as e:
            print(f"Error storing execution history: {str(e)}")
    
    def load_execution_history(self) -> List[Dict]:
        """Load execution history from JSON file."""
        try:
            config = self._load_master_config()
            return config.get('execution_history', [])
        except Exception as e:
            print(f"Error loading execution history: {str(e)}")
            return []

    def get_execution_history(self, table_name: Optional[str] = None) -> List[Dict]:
        """
        Get execution history, optionally filtered by table name.
        
        Args:
            table_name (Optional[str]): Filter results for a specific table
        
        Returns:
            List[Dict]: Filtered or full execution history
        """
        try:
            config = self._load_master_config()
            history = config.get('execution_history', [])
            
            # If table_name is provided, filter the history
            if table_name:
                return [run for run in history if run.get('table_name') == table_name]
            
            return history
        except Exception as e:
            print(f"Error getting execution history: {str(e)}")
            return []

    def save_execution_results(self, table_name: str, results: Dict):
        """
        Save execution results to the execution history file.
        
        Args:
            table_name (str): Name of the table being processed
            results (Dict): Execution results dictionary
        """
        try:
            # Load existing history
            config = self._load_master_config()
            history = config.get('execution_history', [])
            
            # Add timestamp to the results
            results['table_name'] = table_name
            results['timestamp'] = datetime.now().isoformat()
            
            # Append new results
            history.append(results)
            
            # Limit history to last 50 entries to prevent file from growing too large
            history = history[-50:]
            
            # Save updated history
            config['execution_history'] = history
            self._save_master_config(config)
        
        except Exception as e:
            print(f"Error saving execution results: {str(e)}")
    
    def add_activity(self, activity):
        """Add a new activity to the activities list (deprecated)."""
        pass

def load_rule_templates() -> Dict:
    """Load rule templates from JSON file."""
    try:
        template_path = "BONUS/assets/data/rule_templates.json"
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading rule templates: {str(e)}")
        return {}
