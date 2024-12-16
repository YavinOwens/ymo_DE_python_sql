#!/usr/bin/env python3
"""
01_download_offline_packages.py

This script downloads required packages as wheels, including dependencies,
for a data analysis environment into a local directory for offline installation.
It checks if packages are already installed and only downloads missing ones.

Usage:
    python 01_download_offline_packages.py

The script will create an 'offline_packages' directory in the current
folder and download the specified packages into it.
"""

import subprocess
import sys
import argparse
import pkg_resources
from typing import List, Tuple, Set
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Download packages for offline installation.")
    parser.add_argument('--directory', default='offline_packages',
                        help="Directory to store downloaded packages (default: offline_packages)")
    return parser.parse_args()


def create_directory(directory: Path) -> None:
    """
    Create a directory if it doesn't exist.

    Args:
        directory (Path): Path of the directory to create
    """
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")


def get_required_packages() -> List[str]:
    """
    Return a list of required packages for the data analysis environment.

    Returns:
        List[str]: List of package names
    """
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
        'numpy'
    ]


def get_installed_packages() -> Set[str]:
    """
    Get a set of installed packages.

    Returns:
        Set[str]: Set of installed package names
    """
    return {pkg.key for pkg in pkg_resources.working_set}


def download_package(package: str, directory: Path) -> Tuple[bool, str]:
    """
    Download a single package and its dependencies as wheels.

    Args:
        package (str): Name of the package to download
        directory (Path): Directory to store the downloaded package

    Returns:
        Tuple[bool, str]: A tuple containing a success flag and an error message (if any)
    """
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'download',
            '--dest', str(directory),
            '--only-binary=:all:',
            '--platform', 'manylinux1_x86_64',
            '--python-version', f'{sys.version_info.major}.{sys.version_info.minor}',
            '--no-cache-dir',
            package
        ])
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, f"Error downloading {package}: {str(e)}"


def main():
    """
    Main function to orchestrate the package downloading process.
    """
    args = parse_arguments()
    download_dir = Path(args.directory).resolve()
    create_directory(download_dir)

    required_packages = get_required_packages()
    installed_packages = get_installed_packages()

    packages_to_download = [pkg for pkg in required_packages if pkg.lower() not in installed_packages]

    if not packages_to_download:
        print("All required packages are already installed.")
        return

    print(f"Preparing to download {len(packages_to_download)} packages...")

    for package in packages_to_download:
        print(f"Downloading {package} and its dependencies...")
        success, error_message = download_package(package, download_dir)
        if success:
            print(f"Successfully downloaded {package}")
        else:
            print(error_message)

    print("\nDownload process completed.")
    print(f"Packages have been downloaded to: {download_dir}")
    print("\nTo install these packages offline, use:")
    print(f"pip install --no-index --find-links={download_dir} <package_name>")


if __name__ == "__main__":
    main()