#!/usr/bin/env python3
import argparse
import subprocess
import sys
from typing import Dict, List, Optional

class RequirementsInstaller:
    """Handles installation of Python packages from requirements.txt with category support."""
    
    def __init__(self, requirements_file: str = "requirements.txt"):
        self.requirements_file = requirements_file
        self.categories: Dict[str, List[str]] = {}
        self.current_category = None
        self._parse_requirements()

    def _parse_requirements(self) -> None:
        """Parse the requirements file and organize packages by category."""
        try:
            with open(self.requirements_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        # Check if this is a category marker
                        if line.startswith('# '):
                            category = line[2:].lower().replace(' ', '_')
                            if category:
                                self.current_category = category
                                self.categories[category] = []
                        continue
                    
                    if self.current_category:
                        self.categories[self.current_category].append(line)
        except FileNotFoundError:
            print(f"Error: {self.requirements_file} not found!")
            sys.exit(1)

    def list_categories(self) -> None:
        """Display available categories."""
        print("\nAvailable categories:")
        for category in self.categories.keys():
            print(f"- {category}")

    def install_category(self, category: str) -> None:
        """Install packages for a specific category."""
        if category not in self.categories:
            print(f"Error: Category '{category}' not found!")
            self.list_categories()
            return

        packages = self.categories[category]
        if not packages:
            print(f"No packages found for category: {category}")
            return

        print(f"\nInstalling packages for category: {category}")
        for package in packages:
            try:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")

    def install_all(self) -> None:
        """Install all packages from requirements.txt."""
        print("\nInstalling all packages from requirements.txt")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", self.requirements_file])
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Install Python packages from requirements.txt with category support"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Specify a category to install (e.g., data_processing_and_analysis)"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories"
    )
    parser.add_argument(
        "--requirements-file",
        type=str,
        default="requirements.txt",
        help="Path to the requirements file (default: requirements.txt)"
    )

    args = parser.parse_args()
    installer = RequirementsInstaller(args.requirements_file)

    if args.list_categories:
        installer.list_categories()
        return

    if args.category:
        installer.install_category(args.category)
    else:
        installer.install_all()

if __name__ == "__main__":
    main()
