# Data Engineering with Python and SQL

This comprehensive learning project covers essential skills in data engineering, focusing on Python programming and SQL database management. The project provides hands-on experience with real-world data processing, analysis, and engineering tasks.

## Getting Started for Beginners

If you're new to programming or data engineering, follow these step-by-step instructions:

### Step 1: Set Up Your Computer
1. **Install Required Software**:
   - Download and install [Python 3.8](https://www.python.org/downloads/release/python-388/) (Click "Windows installer (64-bit)")
   - Download and install [Visual Studio Code](https://code.visualstudio.com/download)
   - Download and install [Git](https://git-scm.com/downloads)

2. **Verify Installation**:
   - Open Command Prompt (search for "cmd" in Windows start menu)
   - Type `python --version` (should show Python 3.8.x)
   - Type `git --version` (should show the Git version)

### Step 2: Get the Project Files
1. **Create a Project Folder**:
   - Open Command Prompt
   - Navigate to your Documents: `cd %USERPROFILE%\Documents`
   - Create a new folder: `mkdir DataEngineering`
   - Go to the folder: `cd DataEngineering`

2. **Download the Project**:
   ```bash
   git clone https://github.com/yourusername/ymo_DE_python_sql-1.git
   cd ymo_DE_python_sql-1
   ```

### Step 3: Set Up Your Development Environment
1. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
   Note: Your command prompt should now show `(.venv)` at the beginning

2. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```
   This may take a few minutes to complete.

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
   - Start with `Week_1` materials
   - Open the first notebook (files ending in `.ipynb`)
   - Follow the instructions in each notebook

### Step 5: Weekly Progress
Follow this recommended weekly schedule:

#### Week 1: Basics (2-3 hours per day)
- Day 1-2: Python installation and basics
- Day 3-4: SQL fundamentals
- Day 5-7: Basic data operations

#### Week 2: Data Handling (2-3 hours per day)
- Day 1-2: Database connections
- Day 3-4: Data loading
- Day 5-7: Basic transformations

#### Week 3: Analysis (2-3 hours per day)
- Day 1-2: Data cleaning
- Day 3-4: Analysis techniques
- Day 5-7: Creating visualizations

#### Week 4: Advanced Topics (2-3 hours per day)
- Day 1-2: ETL processes
- Day 3-4: Automation
- Day 5-7: Final project

### Common Issues and Solutions

1. **Python Not Found**
   - Make sure Python is added to PATH during installation
   - Try restarting your computer

2. **Package Installation Errors**
   - Make sure you're in the virtual environment (see `.venv\Scripts\activate`)
   - Try running: `pip install --upgrade pip`

3. **Jupyter Notebook Won't Open**
   - In VS Code, make sure you've selected the correct Python interpreter
   - Try running: `pip install jupyter notebook`

### Getting Help

If you encounter issues:
1. Check the error message carefully
2. Search the error on Google
3. Visit [Stack Overflow](https://stackoverflow.com) for similar issues
4. Join Python communities on Discord or Reddit for help

## Learning Outcomes

### Technical Skills
- **Python Programming**: Advanced data processing using pandas, numpy, and polars
- **Database Management**: Working with multiple databases (SQLite, PostgreSQL, MySQL, DuckDB)
- **Data Quality**: Implementing tests and validation using great-expectations
- **API Development**: Building REST APIs with FastAPI
- **Documentation**: Creating technical documentation with MkDocs
- **Version Control**: Git-based workflow and best practices
- **Testing**: Unit testing with pytest and code coverage analysis

### Professional Skills
- Data pipeline design and implementation
- ETL process development
- Code organization and best practices
- Performance optimization techniques
- Problem-solving and debugging strategies
- Documentation writing
- Project organization

## Project Structure

```
.
├── data/                   # Data files and databases
├── notebooks/             # Jupyter notebooks for learning
│   ├── Week_1/           # Environment Setup and Basics
│   ├── Week_2/           # Data Loading and Database Operations
│   ├── Week_3/           # Data Analysis and Engineering
│   └── Week_4/           # Integration and Advanced Features
├── scripts/               # Utility and setup scripts
├── src/                   # Source code
├── tests/                 # Test files
├── visualizations/        # Generated visualizations
├── archive/              # Archived files and notebooks
└── docs/                 # Project documentation
```

## Weekly Learning Path

### Week 1: Foundation and Setup
- Development environment setup
- Python basics and virtual environments
- Version control with Git
- Package management and requirements
- Basic SQL operations

### Week 2: Data Processing and Storage
- Database connections (SQLite, PostgreSQL, MySQL)
- SQLAlchemy ORM
- Data loading and transformation
- Error handling and validation
- Query optimization

### Week 3: Advanced Data Engineering
- ETL pipeline development
- Data quality checks with great-expectations
- Performance optimization
- Parallel processing
- API development with FastAPI

### Week 4: Integration and Best Practices
- Testing and code coverage
- Documentation with MkDocs
- Logging and monitoring
- Deployment strategies
- Code quality and linting
- Project integration

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Tools and Technologies

### Core Technologies
- Python 3.8+
- SQL (SQLite, PostgreSQL, MySQL)
- Git

### Key Libraries
- **Data Processing**: pandas, numpy, polars
- **Databases**: SQLAlchemy, pyodbc, psycopg2
- **API Development**: FastAPI, uvicorn
- **Testing**: pytest, pytest-cov
- **Documentation**: MkDocs, mkdocs-material
- **Code Quality**: black, flake8, isort

## Best Practices Implemented

- Modular code organization
- Comprehensive documentation
- Test-driven development
- Code quality checks
- Version control workflow
- Project structure standards
- Error handling and logging
- Performance optimization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
