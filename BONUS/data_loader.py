import polars as pl
import sqlite3
from typing import Dict, List, Optional
import json
from sqlalchemy import create_engine, inspect, text
from config import DB_URI, DB_PATH
import pandas as pd
import contextlib
import os

class DataLoader:
    def __init__(self):
        self.db_path = DB_PATH
    
    @contextlib.contextmanager
    def get_connection(self):
        """Create a new connection for each operation."""
        conn = sqlite3.connect(self.db_path)
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
            with open('rule_templates.json', 'r') as f:
                rules = json.loads(f.read())
            
            # Find and update the rule
            rule_found = False
            for category, rule_list in rules.items():
                if isinstance(rule_list, list):
                    for rule in rule_list:
                        if rule['id'] == rule_id:
                            rule['active'] = active_status
                            rule_found = True
                            break
                    if rule_found:
                        break
            
            if not rule_found:
                return {'error': f'Rule {rule_id} not found'}
            
            # Write back to file
            with open('rule_templates.json', 'w') as f:
                json.dump(rules, f, indent=4)
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_all_rules(self):
        """Get all rules with their current status."""
        try:
            with open('rule_templates.json', 'r') as f:
                rules = json.loads(f.read())
            
            flat_rules = []
            for category, rule_list in rules.items():
                if isinstance(rule_list, list):
                    category_name = category.replace('_', ' ').title()
                    for rule in rule_list:
                        flat_rules.append({
                            'id': rule['id'],
                            'name': rule['name'],
                            'category': category_name,
                            'description': rule['description'],
                            'type': rule.get('type', 'N/A'),
                            'severity': rule.get('severity', 'N/A'),
                            'active': rule.get('active', True)
                        })
            return flat_rules
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def load_all_rules():
        """Load all rules from the rule templates file."""
        try:
            rule_file_path = os.path.join(os.path.dirname(__file__), 'rule_templates.json')
            with open(rule_file_path, 'r') as f:
                rules_data = json.load(f)
            
            # Flatten all rules into a single list
            all_rules = []
            
            # Add rules from each category
            for category, rules in rules_data.items():
                if isinstance(rules, list):
                    for rule in rules:
                        rule['category'] = category.replace('_rules', '')
                        all_rules.append(rule)
                elif isinstance(rules, dict):
                    for subcategory, subrules in rules.items():
                        for rule in subrules:
                            rule['category'] = f"{category.replace('_rules', '')}/{subcategory.replace('_rules', '')}"
                            all_rules.append(rule)
            
            return all_rules
        except Exception as e:
            return {'error': f"Error loading rules: {str(e)}"}

    def save_rule_status(self, rule_id: str, new_status: bool) -> dict:
        """Save the updated rule status to the rule templates file."""
        try:
            rule_file_path = os.path.join(os.path.dirname(__file__), 'rule_templates.json')
            with open(rule_file_path, 'r') as f:
                rules_data = json.load(f)
            
            # Update rule status in the appropriate category
            for category, rules in rules_data.items():
                if isinstance(rules, list):
                    for rule in rules:
                        if rule['id'] == rule_id:
                            rule['active'] = new_status
                            break
                elif isinstance(rules, dict):
                    for subcategory, subrules in rules.items():
                        for rule in subrules:
                            if rule['id'] == rule_id:
                                rule['active'] = new_status
                                break
            
            # Save updated rules back to file
            with open(rule_file_path, 'w') as f:
                json.dump(rules_data, f, indent=4)
            
            return {'success': True}
        except Exception as e:
            return {'error': f"Error saving rule status: {str(e)}"}

def load_rule_templates() -> Dict:
    """Load rule templates from JSON file."""
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'rule_templates.json')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}
