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
├── visualizations/         # Generated visualizations
│   ├── age_distribution.png
│   ├── company_distribution.png
│   └── job_distribution.png
├── HR_Data_Analysis.ipynb  # Jupyter notebook for interactive analysis
└── requirements.txt        # Python package dependencies
```

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
