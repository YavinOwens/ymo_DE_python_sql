#!/usr/bin/env python3
"""
00_initial_setup_ymo_env.py

This script performs two main functions:
1. Downloads required packages as wheels for offline installation
2. Sets up a complete data analysis environment with example code

Usage:
    python 00_initial_setup_ymo_env.py [--offline-packages-dir DIRECTORY]
"""

import subprocess
import sys
import os
import argparse
import pkg_resources
from pathlib import Path
import logging
from typing import List, Tuple, Set
from datetime import datetime

# Set up logging
logging.basicConfig(filename='setup_log.log', level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Setup data analysis environment and download packages.")
    parser.add_argument('--offline-packages-dir', default='offline_packages',
                       help="Directory to store downloaded packages (default: offline_packages)")
    return parser.parse_args()

def get_required_packages() -> List[str]:
    """Return a list of required packages with versions."""
    return [
        'pandas>=1.3.0',
        'numpy>=1.21.0',
        'matplotlib>=3.4.0',
        'seaborn>=0.11.0',
        'plotly>=5.1.0',
        'faker',  # For generating dummy data
        'sqlalchemy',  # For database operations
        'sqlite3',  # For SQLite database
        'jupyter',  # For notebook support
        'ipykernel',  # For Jupyter kernel
        'notebook',  # For Jupyter notebook
        'pyarrow',  # For better data handling
        'openpyxl',  # For Excel support
        'python-dateutil>=2.8.2',  # For date handling
        'pytz>=2020.1',  # For timezone support
        'six>=1.5',  # Common dependencies
        'cycler>=0.10',  # For matplotlib
        'kiwisolver>=1.0.1',  # For matplotlib
        'pyparsing>=2.2.1',  # For matplotlib
        'pillow>=6.2.0',  # For image handling
    ]

def create_directory(directory: Path) -> None:
    """Create a directory if it doesn't exist."""
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {directory}")
    else:
        logging.info(f"Directory already exists: {directory}")

def download_package(package: str, directory: Path) -> Tuple[bool, str]:
    """Download a package and its dependencies as wheels."""
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'download',
            '--dest', str(directory),
            '--only-binary=:all:',
            '--platform', 'win_amd64',  # Changed to Windows platform
            '--python-version', f'{sys.version_info.major}.{sys.version_info.minor}',
            '--no-cache-dir',
            package
        ])
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, f"Error downloading {package}: {str(e)}"

def install_package(package: str) -> None:
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logging.info(f"Successfully installed {package}")
    except Exception as e:
        logging.error(f"Failed to install {package}: {str(e)}")

def setup_data_analysis_environment():
    """Set up the data analysis environment with example data and code."""
    # Create output directory
    output_dir = Path("setup_outputs")
    create_directory(output_dir)
    
    # Create src directory for Python modules
    src_dir = Path("src")
    create_directory(src_dir)
    
    # Create directories for data and visualizations
    data_dir = Path("data")
    vis_dir = Path("visualizations")
    create_directory(data_dir)
    create_directory(vis_dir)

    # Now we can safely import the required packages
    import pandas as pd
    from faker import Faker
    import numpy as np
    import sqlite3
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Initialize Faker
    fake = Faker()

    # Generate NINO (National Insurance Number)
    def generate_nino():
        return f"{fake.random_letter()}{fake.random_letter()}{fake.random_int(min=100000, max=999999)}{fake.random_letter()}"

    # Create dummy data
    people_data = []
    for _ in range(1000):
        person = {
            'name': fake.name(),
            'nino': generate_nino(),
            'job': fake.job(),
            'company': fake.company(),
            'date_of_birth': fake.date_of_birth(),
            'per_id': _ + 1,
            'age': fake.random_int(min=18, max=70)
        }
        people_data.append(person)

    # Create addresses data
    addresses_data = []
    for i in range(1000):
        address = {
            'street_address': fake.street_address(),
            'city': fake.city(),
            'country': fake.country(),
            'postcode': fake.postcode(),
            'hr_id': i + 1
        }
        addresses_data.append(address)

    # Create SQLite database
    conn = sqlite3.connect(data_dir / 'hr_database.sqlite')
    
    # Convert to DataFrames and save to SQLite
    df_people = pd.DataFrame(people_data)
    df_addresses = pd.DataFrame(addresses_data)
    
    df_people.to_sql('per', conn, if_exists='replace', index=False)
    df_people.to_sql('assignments', conn, if_exists='replace', index=False)
    df_addresses.to_sql('addresses', conn, if_exists='replace', index=False)
    
    conn.close()
    logging.info("Created SQLite database with dummy data")

    # Create example visualizations
    plt.figure(figsize=(10, 6))
    plt.hist(df_people['age'], bins=30, edgecolor='black')
    plt.title('Age Distribution')
    plt.xlabel('Age')
    plt.ylabel('Count')
    plt.savefig(vis_dir / 'age_distribution.png')
    plt.close()

    logging.info("Data analysis environment setup completed successfully")

def main():
    """Main function to orchestrate the setup process."""
    args = parse_arguments()
    offline_packages_dir = Path(args.offline_packages_dir).resolve()
    
    # Step 1: Download packages for offline installation
    logging.info("Starting package download process...")
    create_directory(offline_packages_dir)
    
    required_packages = get_required_packages()
    for package in required_packages:
        logging.info(f"Downloading {package}...")
        success, error_message = download_package(package, offline_packages_dir)
        if success:
            logging.info(f"Successfully downloaded {package}")
        else:
            logging.error(error_message)

    # Step 2: Install packages
    logging.info("Installing required packages...")
    for package in required_packages:
        install_package(package)

    # Step 3: Set up the data analysis environment
    logging.info("Setting up data analysis environment...")
    setup_data_analysis_environment()

    # Create requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(required_packages))
    logging.info("Created requirements.txt")

    # Final message
    print("\nSetup process completed!")
    print(f"1. Offline packages have been downloaded to: {offline_packages_dir}")
    print("2. Data analysis environment has been set up")
    print("3. Example data and visualizations have been generated")
    print("\nProject structure created:")
    print("  - /data: Contains the SQLite database")
    print("  - /src: Contains Python source files")
    print("  - /visualizations: Contains generated plots")
    print("  - requirements.txt: Lists all package dependencies")
    print("\nTo install packages offline on another machine:")
    print(f"pip install --no-index --find-links={offline_packages_dir} -r requirements.txt")
    print("\nCheck setup_log.log for detailed information about the setup process.")

if __name__ == "__main__":
    main()
