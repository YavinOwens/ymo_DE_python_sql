import pandas as pd
import numpy as np
from datetime import datetime

class DataQualityChecks:
    def __init__(self, df):
        self.df = df
        
    def get_basic_stats(self):
        """Get basic statistics about the dataset"""
        return {
            'row_count': len(self.df),
            'column_count': len(self.df.columns),
            'memory_usage': self.df.memory_usage(deep=True).sum(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'dtypes': self.df.dtypes.astype(str).to_dict()
        }
    
    def _get_default_checks_config(self, column):
        """Get default checks configuration based on column type"""
        dtype = str(self.df[column].dtype)
        checks = []
        
        # Basic checks for all types
        checks.append({
            'name': 'missing_values',
            'description': 'Check for missing values',
            'function': lambda x: x.isnull().sum() == 0
        })
        
        # Numeric checks
        if 'int' in dtype or 'float' in dtype:
            checks.extend([
                {
                    'name': 'negative_values',
                    'description': 'Check for negative values',
                    'function': lambda x: (x >= 0).all()
                },
                {
                    'name': 'zero_values',
                    'description': 'Check for zero values',
                    'function': lambda x: (x != 0).all()
                }
            ])
        
        # String checks
        if 'object' in dtype or 'string' in dtype:
            checks.extend([
                {
                    'name': 'empty_strings',
                    'description': 'Check for empty strings',
                    'function': lambda x: x.str.strip().str.len().gt(0).all()
                },
                {
                    'name': 'special_characters',
                    'description': 'Check for special characters',
                    'function': lambda x: x.str.match('^[a-zA-Z0-9\s]*$').all()
                }
            ])
        
        return checks
    
    def run_column_checks(self, column, checks):
        """Run a series of checks on a specific column"""
        results = {
            'column': column,
            'checks': []
        }
        
        for check in checks:
            try:
                result = check['function'](self.df[column])
                results['checks'].append({
                    'check_name': check['name'],
                    'description': check['description'],
                    'success': bool(result),
                    'result': {
                        'passed': bool(result),
                        'details': f"Check {'passed' if result else 'failed'}"
                    }
                })
            except Exception as e:
                results['checks'].append({
                    'check_name': check['name'],
                    'description': check['description'],
                    'success': False,
                    'result': {
                        'passed': False,
                        'error': str(e)
                    }
                })
        
        return results
    
    def check_relationship(self, col1, col2):
        """Check relationship between two numeric columns"""
        correlation = self.df[col1].corr(self.df[col2])
        return {
            'column1': col1,
            'column2': col2,
            'correlation': correlation,
            'relationship': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak'
        }
    
    def run_rule_validation(self, rule):
        """Run validation for a custom rule"""
        try:
            validation_code = rule['python_code']
            violations_mask = eval(validation_code, {'__builtins__': {}}, {'df': self.df, 'pd': pd, 'np': np})
            
            if isinstance(violations_mask, pd.Series):
                total_records = len(self.df)
                violations = (~violations_mask).sum()
                compliance_rate = (1 - violations/total_records) * 100
                
                return {
                    'rule_id': rule['rule_id'],
                    'severity': rule['severity'],
                    'total_records': total_records,
                    'violations': violations,
                    'compliance_rate': compliance_rate,
                    'validation_code': validation_code
                }
            else:
                return {
                    'rule_id': rule['rule_id'],
                    'severity': rule['severity'],
                    'error': 'Validation code did not return a boolean mask'
                }
                
        except Exception as e:
            return {
                'rule_id': rule['rule_id'],
                'severity': rule['severity'],
                'error': str(e)
            }
