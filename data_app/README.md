# Data Engineering with Python and SQL

> **Note**: This documentation was last updated on December 18, 2024.

This repository showcases a comprehensive learning journey in data engineering, culminating in a production-ready Data Quality Management Dashboard. The project demonstrates both educational content and practical implementation of data engineering concepts.

## Part 1: Learning Journey

### Course Structure
The course is organized into weekly modules, each focusing on specific data engineering concepts:

#### Week 1: Foundations
- Python programming fundamentals
- Data structures and algorithms
- Basic SQL operations
- Development environment setup

#### Week 2: Data Processing
- Advanced data manipulation with Pandas and Polars
- ETL pipeline development
- Data cleaning and preprocessing
- Performance optimization techniques

#### Week 3: Data Quality
- Data validation frameworks
- Quality metrics and monitoring
- Error handling and logging
- Testing strategies

#### Week 4: Advanced Concepts
- Database design and optimization
- Data warehouse concepts
- Real-time data processing
- Data visualization techniques

#### Final Project
- Integration of learned concepts
- Real-world problem solving
- Project documentation
- Code quality and best practices

### Transferable Skills Developed

1. **Technical Skills**
   - Python programming
   - SQL database management
   - ETL pipeline development
   - Data quality assessment
   - Performance optimization
   - Version control with Git

2. **Data Engineering Practices**
   - Data modeling
   - Quality assurance
   - Error handling
   - Documentation
   - Testing methodologies
   - CI/CD principles

3. **Analytical Skills**
   - Problem decomposition
   - Performance analysis
   - Data validation
   - Pattern recognition
   - Anomaly detection

4. **Professional Skills**
   - Project management
   - Technical documentation
   - Code review practices
   - Collaborative development
   - Best practices implementation

## Part 2: Data Quality Management Dashboard

### Features

#### Data Quality Monitoring
- Interactive dashboard for monitoring data quality metrics
- Real-time validation of data against defined rules
- Failed data visualization and analysis
- Comprehensive data quality reporting

#### Rule Management
- Create and manage data quality rules
- Toggle rules between active and inactive states
- Filter and search rules by various criteria
- Visual feedback for rule status changes
- Rule execution history tracking

#### Data Analysis
- Column-level analysis with statistical insights
- Data distribution visualization
- Pattern detection and anomaly highlighting
- Temporal trend analysis
- Custom visualization options

### Project Structure

```
project/
├── notebooks/                # Learning materials and exercises
│   ├── Week_1/             # Foundation concepts
│   ├── Week_2/             # Data processing
│   ├── Week_3/             # Data quality
│   ├── Week_4/             # Advanced concepts
│   └── final project/      # Capstone project materials
├── BONUS/                   # Data Quality Dashboard
│   ├── assets/
│   │   ├── css/            # Stylesheets
│   │   ├── data/           # JSON data files
│   │   ├── config/         # Configuration files
│   │   └── logs/           # Application logs
│   ├── main_app.py         # Main dashboard application
│   ├── data_loader.py      # Data loading and processing
│   └── config.py           # Configuration settings
├── dummy_data/             # Test datasets
└── requirements.txt        # Project dependencies
```

## Getting Started

### Prerequisites
1. Python 3.8+
2. Git
3. Basic understanding of Python and SQL

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd ymo_DE_python_sql
```

2. Create and activate virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Learning Path
1. Start with the notebooks in sequential order (Week 1 to Week 4)
2. Complete exercises in each module
3. Work on the final project
4. Explore the BONUS dashboard implementation

### Running the Dashboard
```bash
python BONUS/main_app.py
```
Access at `http://127.0.0.1:8050`

## Dashboard Configuration

### Data Quality Rules
Rules are configured through JSON templates:

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

### Features
- Modern, responsive design
- Customizable themes
- Mobile-friendly interface
- Comprehensive error handling
- Detailed logging system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request
4. Ensure code quality and testing

## Support

For support:
1. Check the notebook documentation
2. Review the dashboard configuration
3. Open an issue for specific problems
4. Contribute to the documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*This project demonstrates the practical application of data engineering concepts through both educational content and a production-ready dashboard implementation.*
