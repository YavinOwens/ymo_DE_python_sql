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
    """Return a list of required packages."""
    return [
        'pandas',
        'faker',
        'sqlalchemy',
        'psycopg2-binary',
        'polars',
        'seaborn',
        'plotly',
        'pyspark',
        'jupyter',
        'matplotlib',
        'numpy',
        'pyarrow',  # Added for better compatibility with pandas and polars
        'ipykernel',  # Added for Jupyter support
        'notebook'  # Added for Jupyter notebook
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

    # Now we can safely import the required packages
    import pandas as pd
    from faker import Faker
    import numpy as np
    import polars as pl
    import seaborn as sns
    import matplotlib.pyplot as plt
    import plotly.express as px
    from pyspark.sql import SparkSession

    # Create dummy_data folder
    dummy_data_folder = output_dir / "dummy_data"
    create_directory(dummy_data_folder)

    # Initialize Faker
    fake = Faker()

    # Generate NINO (National Insurance Number)
    def generate_nino():
        return f"{fake.random_letter()}{fake.random_letter()}{fake.random_int(min=100000, max=999999)}{fake.random_letter()}"

    # Create dummy data
    people_data = []
    for _ in range(1000):
        people_data.append({
            'name': fake.name(),
            'nino': generate_nino(),
            'job': fake.job(),
            'company': fake.company(),
            'date_of_birth': fake.date_of_birth()
        })

    # Save people data
    df_people = pd.DataFrame(people_data)
    date_str = datetime.now().strftime("%Y%m%d")
    people_filename = f"PER_ALL_PEOPLE_F_{date_str}.csv"
    df_people.to_csv(dummy_data_folder / people_filename, index=False)
    logging.info(f"Created dummy data file: {people_filename}")

    # Example visualizations
    # Seaborn
    sns.set_theme()
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df_people, x='job')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / 'job_distribution.png')
    plt.close()

    # Plotly
    fig = px.histogram(df_people, x='job', title='Job Distribution')
    fig.write_html(output_dir / "job_distribution.html")

    # PySpark example
    spark = SparkSession.builder \
        .master("local[*]") \
        .appName("Local Spark") \
        .getOrCreate()

    df_spark = spark.createDataFrame(df_people)
    df_spark.createOrReplaceTempView("people")
    spark.sql("SELECT job, COUNT(*) as count FROM people GROUP BY job ORDER BY count DESC LIMIT 5").show()
    
    spark.stop()

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

    # Final message
    print("\nSetup process completed!")
    print(f"1. Offline packages have been downloaded to: {offline_packages_dir}")
    print("2. Data analysis environment has been set up")
    print("3. Example data and visualizations have been generated in the 'setup_outputs' directory")
    print("\nTo install packages offline on another machine:")
    print(f"pip install --no-index --find-links={offline_packages_dir} <package_name>")
    print("\nCheck setup_log.log for detailed information about the setup process.")

if __name__ == "__main__":
    main()
