import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from ydata_quality import DataQuality
from ydata_quality.profiling import Profiling

class DataQualityWorker:
    def __init__(self):
        self.dq = None
        self.profiler = Profiling()
    
    def initialize_data(self, df: pd.DataFrame) -> None:
        """Initialize the DataQuality object with a dataframe"""
        self.dq = DataQuality(df)
        self.df = df
    
    def run_table_assessment(self) -> Dict[str, Any]:
        """Run comprehensive table-level assessment"""
        if self.dq is None:
            raise ValueError("Data not initialized. Call initialize_data first.")
            
        results = {
            'profile': self.profiler.profile(self.df),
            'quality_metrics': self.dq.evaluate(),
            'basic_stats': {
                'row_count': len(self.df),
                'column_count': len(self.df.columns),
                'missing_values': self.df.isnull().sum().to_dict(),
                'duplicates': self.df.duplicated().sum()
            }
        }
        
        # Add correlation analysis for numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            results['correlations'] = self.df[numeric_cols].corr().to_dict()
            
        return results
    
    def run_column_assessment(self, column_name: str) -> Dict[str, Any]:
        """Run detailed assessment for a specific column"""
        if self.dq is None:
            raise ValueError("Data not initialized. Call initialize_data first.")
            
        if column_name not in self.df.columns:
            raise ValueError(f"Column {column_name} not found in dataframe")
            
        column_data = self.df[column_name]
        
        results = {
            'profile': self.profiler.profile(self.df).get_column_stats(column_name),
            'quality_metrics': self.dq.evaluate_column(column_name),
            'basic_stats': {
                'dtype': str(column_data.dtype),
                'unique_values': column_data.nunique(),
                'missing_values': column_data.isnull().sum(),
                'sample_values': column_data.head().tolist()
            }
        }
        
        # Add type-specific analysis
        if pd.api.types.is_numeric_dtype(column_data):
            results['numeric_stats'] = {
                'mean': column_data.mean(),
                'median': column_data.median(),
                'std': column_data.std(),
                'min': column_data.min(),
                'max': column_data.max()
            }
        elif pd.api.types.is_string_dtype(column_data):
            results['string_stats'] = {
                'avg_length': column_data.str.len().mean(),
                'max_length': column_data.str.len().max(),
                'empty_strings': (column_data == '').sum()
            }
            
        return results
    
    def run_rule_validation(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run validation for a specific rule"""
        if self.dq is None:
            raise ValueError("Data not initialized. Call initialize_data first.")
            
        try:
            column_name = rule_data['column_name']
            validation_code = rule_data['python_code']
            
            # Replace column references
            validation_code = validation_code.replace('df[name]', f"self.df['{column_name}']")
            validation_code = validation_code.replace('name', f"'{column_name}'")
            
            # Handle negation
            is_negated = validation_code.startswith('~')
            if is_negated:
                validation_code = validation_code[1:]
            
            # Create execution environment
            local_dict = {
                'self': self,
                'pd': pd,
                'np': np,
                'datetime': datetime
            }
            
            # Execute validation
            result = eval(validation_code, {'__builtins__': {}}, local_dict)
            
            if isinstance(result, pd.Series):
                if is_negated:
                    result = ~result
                violations = result.sum() if isinstance(result.iloc[0], bool) else len(result[result == True])
            elif isinstance(result, bool):
                violations = len(self.df) if result else 0
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")
            
            total_records = len(self.df)
            compliance_rate = ((total_records - violations) / total_records) * 100 if total_records > 0 else 100
            
            return {
                'rule_id': rule_data['rule_id'],
                'description': rule_data['description'],
                'severity': rule_data['severity'],
                'violations': violations,
                'total_records': total_records,
                'compliance_rate': compliance_rate,
                'column_name': column_name,
                'validation_code': validation_code,
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'rule_id': rule_data['rule_id'],
                'description': rule_data['description'],
                'severity': rule_data['severity'],
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get a high-level summary of the data"""
        if self.dq is None:
            raise ValueError("Data not initialized. Call initialize_data first.")
            
        return {
            'row_count': len(self.df),
            'column_count': len(self.df.columns),
            'memory_usage': self.df.memory_usage(deep=True).sum(),
            'dtypes': self.df.dtypes.astype(str).to_dict(),
            'missing_values_summary': self.df.isnull().sum().to_dict(),
            'timestamp': datetime.now().isoformat()
        }
