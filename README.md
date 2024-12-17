# Data Engineering with Python and SQL

This comprehensive learning project covers essential skills in data engineering, focusing on Python programming and SQL database management. The project provides hands-on experience with real-world data processing, analysis, and engineering tasks.

## Getting Started for Beginners

If you're new to programming or data engineering, follow these step-by-step instructions:

### Step 1: Set Up Your Computer
1. **Install Required Software**:
   - Download and install [Python 3.8+](https://www.python.org/downloads/) (Click "Windows installer (64-bit)")
   - Download and install [Visual Studio Code](https://code.visualstudio.com/download)
   - Download and install [Git](https://git-scm.com/downloads)

2. **Verify Installation**:
   - Open Command Prompt (search for "cmd" in Windows start menu)
   - Type `python --version` (should show Python 3.8.x or higher)
   - Type `git --version` (should show the Git version)

### Step 2: Get the Project Files
1. **Create a Project Folder**:
   - Open Command Prompt
   - Navigate to your Documents: `cd %USERPROFILE%\Documents`
   - Create a new folder: `mkdir DataEngineering`
   - Go to the folder: `cd DataEngineering`

2. **Download the Project**:
   ```bash
   git clone https://github.com/yourusername/ymo_DE_python_sql.git
   cd ymo_DE_python_sql
   ```

### Step 3: Set Up Your Development Environment
1. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
   Note: Your command prompt should now show `(.venv)` at the beginning

2. **Install Required Packages**:
   The project includes a flexible package installation script that allows you to install either all dependencies or specific categories:

   View available categories:
   ```bash
   python install_requirements.py --list-categories
   ```

   Install all packages:
   ```bash
   python install_requirements.py
   ```

   Install specific category (e.g., data processing):
   ```bash
   python install_requirements.py --category data_processing_and_analysis
   ```

   Available categories include:
   - data_processing_and_analysis
   - data_visualization
   - database_connections
   - data_generation
   - development_environment
   - excel_support
   - date_and_time
   - data_validation_and_quality
   - documentation

### Step 4: Start Learning
1. **Open Visual Studio Code**:
   ```bash
   code .
   ```

2. **Install Recommended Extensions**:
   - When VS Code opens, it may suggest installing Python extensions
   - Click "Install" for any recommended extensions

3. **Begin the Course**:
   - Open the `notebooks` folder
   - Start with the `HR_Data_Quality_Guide.ipynb` for an introduction to data quality concepts
   - Follow the `Continuous_Improvement.ipynb` for best practices in data engineering
   - Progress through other notebooks as needed

### Common Issues and Solutions

1. **Python Not Found**
   - Make sure Python is added to PATH during installation
   - Try restarting your computer

2. **Package Installation Errors**
   - Make sure you're in the virtual environment (see `.venv\Scripts\activate`)
   - Try running: `pip install --upgrade pip`
   - Use the category-based installation to isolate issues: `python install_requirements.py --category <category_name>`

3. **Jupyter Notebook Won't Open**
   - In VS Code, make sure you've selected the correct Python interpreter
   - Try running: `python install_requirements.py --category development_environment`

### Getting Help

If you encounter issues:
1. Check the error message carefully
2. Search the error on Google
3. Visit [Stack Overflow](https://stackoverflow.com) for similar issues
4. Join Python communities on Discord or Reddit for help

## Project Features

### Core Components
- **HR Data Quality Guide**: Comprehensive notebook for data quality assessment and improvement
- **Continuous Improvement Framework**: Tools and methods for ongoing data quality enhancement
- **Flexible Package Management**: Category-based dependency installation
- **Data Validation Suite**: Tools for validating HR data including NINO, dates, and emails
- **Anomaly Detection**: Graph-based approach for detecting potential fraudulent patterns

### Technical Stack
- **Python 3.8+**
- **Key Libraries**:
  - Data Processing: pandas (2.1.4), numpy (1.24.4), polars (1.17.1)
  - Data Visualization: matplotlib (3.9.4), seaborn (0.13.2), plotly (5.24.1)
  - Database: SQLAlchemy (2.0.36), psycopg2-binary (2.9.10)
  - Development: jupyter (1.1.1), jupyterlab (3.6.3)
  - Documentation: mkdocs (1.5.0+)

## Project Structure

```
.
├── notebooks/                 # Jupyter notebooks
│   ├── data quality/         # Data quality assessment notebooks
│   │   ├── HR_Data_Quality_Guide.ipynb
│   │   └── Continuous_Improvement.ipynb
├── data/                     # Data files and sample datasets
├── scripts/                  # Utility scripts
│   └── install_requirements.py  # Package installation script
├── requirements.txt          # Project dependencies
└── docs/                     # Project documentation
```

## Best Practices Implemented

- Modular code organization
- Comprehensive data quality checks
- Flexible dependency management
- Test-driven development
- Error handling and logging
- Performance optimization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
