# HR Data Analysis Project

This project analyzes HR data stored in a SQLite database, providing insights about employee demographics, job distributions, and geographic information.

## Project Structure

```
.
├── data/                   # Data files
│   └── hr_database.sqlite  # SQLite database containing HR data
├── src/                    # Source code
│   ├── hr_data_loader.py  # Database connection and data loading functions
│   ├── hr_analysis.py     # Analysis and visualization functions
│   └── etl_process.py     # ETL process implementation
├── notebooks/             # Jupyter notebooks organized by week
│   ├── Week_1/           # Environment Setup and Basics
│   ├── Week_2/           # Data Loading and Database
│   ├── Week_3/           # Data Analysis and Visualization
│   └── Week_4/           # Integration and Advanced Features
├── visualizations/         # Generated visualizations
│   ├── age_distribution.png
│   ├── company_distribution.png
│   └── job_distribution.png
├── Python_learning_Plan.xlsx  # 30-day learning curriculum
├── HR_Data_Analysis.ipynb    # Jupyter notebook for interactive analysis
└── requirements.txt          # Python package dependencies
```

## Learning Plan

This project follows a structured 30-day learning plan divided into four weeks:

### Week 1: Environment Setup and Basics
- Python Environment Setup
- SQLite Basics
- Package Management
- Virtual Environments
- Git Basics
- IDE Setup
- Directory Structure

### Week 2: Data Loading and Database
- SQLAlchemy Basics
- Database Design
- Data Loading Scripts
- Error Handling
- Data Validation
- Database Relationships
- Query Optimization

### Week 3: Data Analysis and Visualization
- Pandas Basics
- Data Cleaning
- Data Analysis
- Matplotlib
- Seaborn
- Plotly
- Dashboard Creation

### Week 4: Integration and Advanced Features
- Code Integration
- Testing
- Documentation
- Logging
- Performance Optimization
- Deployment
- Automation
- Best Practices
- Final Review

## Getting Started

1. Review the learning plan in `Python_learning_Plan.xlsx`
2. Navigate to `notebooks/Week_1` to begin with environment setup
3. Follow each notebook sequentially within each week
4. Track your progress in the learning plan spreadsheet

## Setup

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the analysis:
   ```bash
   python src/hr_analysis.py
   ```

## Features

- Comprehensive HR data analysis
- Interactive visualizations
- Geographic distribution analysis
- Age and job statistics
- Company distribution analysis
- Structured learning path with hands-on exercises
- Progressive skill development through weekly modules
