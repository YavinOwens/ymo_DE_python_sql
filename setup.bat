@echo off
echo Setting up Python environment for Data Engineering Learning Project...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create scripts directory if it doesn't exist
if not exist "scripts" mkdir scripts

REM Run the setup script
echo Installing packages...
python scripts/setup_environment.py %*

if errorlevel 1 (
    echo Error: Installation failed
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo To activate the virtual environment, run: .venv\Scripts\activate
echo.
pause
