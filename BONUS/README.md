# Data Quality Management Dashboard

This dashboard provides a comprehensive interface for managing data quality rules and monitoring data validation across your data pipeline. Built with Dash and Python, it offers an intuitive way to manage and configure data quality rules.

## Features

### Rule Management
- View and manage all data quality rules in one place
- Toggle rules between active and inactive states
- Filter rules by category, severity, and status
- Real-time status updates with visual feedback
- Comprehensive statistics on rule usage and distribution

### Rule Categories
The system supports multiple types of data quality rules:

1. GDPR Rules
   - Personal data detection
   - Data privacy compliance
   - Sensitive information monitoring

2. Table Level Rules
   - Structure validation
   - Relationship checks
   - Performance monitoring
   - Data integrity verification

3. Data Quality Rules
   - Missing value detection
   - Format validation
   - Data type checking

4. Business Rules
   - Business logic validation
   - Cross-table relationships
   - Custom business constraints

## Configuration

### Rule Templates
Rules are configured through `rule_templates.json`. Each rule has the following structure:

```json
{
    "id": "rule_001",
    "name": "Rule Name",
    "description": "Rule Description",
    "category": "Category",
    "type": "Rule Type",
    "severity": "Critical|High|Medium|Low",
    "validation_code": "Python validation code",
    "message": "Error message",
    "active": true|false
}
```

### Adding New Rules
To add new rules:

1. Update `rule_templates.json` with your rule definition
2. Follow the existing rule structure
3. Ensure unique rule IDs
4. Restart the application to load new rules

## Installation

1. Clone the repository
2. Install required packages:
```bash
pip install dash dash-bootstrap-components pandas polars sqlite3
```

3. Configure your environment:
   - Set up database connections in `config.py`
   - Customize rule templates in `rule_templates.json`

## Project Structure

```
project/
├── BONUS/
│   ├── main_app.py        # Main dashboard application
│   ├── data_loader.py     # Data loading and rule management
│   ├── config.py          # Configuration settings
│   └── rule_templates.json # Rule definitions
```

## Running the Application

1. Navigate to the project directory
2. Run the application:
```bash
python BONUS/main_app.py
```
3. Access the dashboard at `http://127.0.0.1:8050`

## Rule Management Interface

The Rule Management page provides:

1. Statistics Dashboard
   - Total number of rules
   - Active rules count
   - Category distribution
   - Severity breakdown

2. Filtering Options
   - Filter by category
   - Filter by severity level
   - Filter by rule status

3. Rule Actions
   - Toggle rule status
   - View rule details
   - Monitor rule statistics

## Error Handling

- Visual feedback for rule status changes
- Error messages for failed operations
- Graceful handling of missing data
- Safe rule status persistence

## Contributing

To contribute:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with your changes
4. Ensure all existing tests pass

## Troubleshooting

If you encounter issues:

1. Check the console for error messages
2. Verify rule template format
3. Ensure all required packages are installed
4. Check database connections if applicable

## License

This project is licensed under the MIT License - see the LICENSE file for details.
