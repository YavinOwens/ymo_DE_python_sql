# Dask Dashboard Data Loading

This dashboard supports loading data from various sources including CSV files, databases, and Parquet files. The data loading functionality is configured through the `data_config.json` file.

## Configuration

The data loading configuration is managed through `data_config.json`. Here's how to configure different data sources:

### CSV Files
Place your CSV files in the `data/` directory and update the configuration:

```json
{
    "tables": {
        "employees": {
            "type": "csv",
            "path": "data/employees.csv"
        }
    }
}
```

### Database Connection
To load from a database, update the database configuration:

```json
{
    "database": {
        "enabled": true,
        "connection_string": "postgresql://username:password@localhost:5432/database"
    },
    "tables": {
        "employees": {
            "type": "database",
            "path": "SELECT * FROM employees"
        }
    }
}
```

### Parquet Files
For Parquet files, specify the file path:

```json
{
    "tables": {
        "employees": {
            "type": "parquet",
            "path": "data/employees.parquet"
        }
    }
}
```

## Required Tables and Columns

The dashboard expects the following tables with these columns:

1. employees
   - employee_id
   - email
   - salary
   - hire_date
   - phone
   - department_id
   - age
   - job_title
   - manager_id

2. departments
   - department_id
   - department_name
   - location
   - budget
   - manager_id
   - creation_date
   - department_code
   - status

3. salaries
   - salary_id
   - employee_id
   - salary
   - effective_date
   - end_date

4. job_history
   - job_history_id
   - employee_id
   - department_id
   - start_date
   - end_date

5. locations
   - location_id
   - city
   - country_code
   - postal_code

6. dependents
   - dependent_id
   - employee_id
   - first_name
   - last_name
   - relationship
   - birth_date

## Data Loading Process

1. The dashboard first attempts to load data from the configured sources in `data_config.json`
2. For large files (>100MB), it automatically uses Dask for efficient processing
3. If a table is missing or fails to load, an empty DataFrame with the required columns is created
4. All data quality rules and validations are applied to the loaded data

## Error Handling

- If a data source is unavailable, the system will log an error and continue with an empty DataFrame
- Data type mismatches are handled gracefully with appropriate error messages
- Large files are automatically processed using Dask for better performance

## Adding New Data Sources

To add a new data source:

1. Update `data_config.json` with the new table configuration
2. Place the data file in the appropriate location (e.g., CSV files in `data/`)
3. Restart the dashboard to load the new data

## Troubleshooting

If you encounter issues loading data:

1. Check file permissions and paths in `data_config.json`
2. Verify database connection strings if using database sources
3. Ensure CSV files have the required columns with correct names
4. Check the console output for specific error messages
