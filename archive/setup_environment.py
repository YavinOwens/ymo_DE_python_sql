import os
import subprocess
import sys
import platform
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def create_virtual_env(venv_path):
    """Create a virtual environment."""
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment at {venv_path}...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    else:
        print(f"Virtual environment already exists at {venv_path}")

def get_pip_command(venv_path):
    """Get the correct pip command based on the operating system."""
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
    return pip_path

def upgrade_pip(pip_path):
    """Upgrade pip to the latest version."""
    subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)

def install_packages(pip_path, offline=False, offline_dir="offline_packages"):
    """Install packages either online or offline."""
    base_cmd = [pip_path, "install", "-r", "requirements.txt"]
    
    if offline:
        if not os.path.exists(offline_dir):
            print(f"Error: Offline packages directory '{offline_dir}' not found")
            sys.exit(1)
        base_cmd.extend(["--no-index", "--find-links", offline_dir])
    
    try:
        subprocess.run(base_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def download_packages(pip_path, offline_dir="offline_packages"):
    """Download packages for offline installation."""
    if not os.path.exists(offline_dir):
        os.makedirs(offline_dir)
    
    # Clean up old packages
    for file in os.listdir(offline_dir):
        os.remove(os.path.join(offline_dir, file))
    
    try:
        subprocess.run([
            pip_path, "download",
            "-r", "requirements.txt",
            "--dest", offline_dir,
            "--platform", "win_amd64",
            "--python-version", "3.8",
            "--only-binary=:all:"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading packages: {e}")
        sys.exit(1)

def setup_jupyter_kernel(venv_path, project_name):
    """Set up Jupyter kernel for the virtual environment."""
    if platform.system() == "Windows":
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
    
    try:
        subprocess.run([
            python_path, "-m", "ipykernel", "install",
            "--user", "--name", project_name,
            "--display-name", f"Python ({project_name})"
        ], check=True)
        print(f"Jupyter kernel '{project_name}' installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up Jupyter kernel: {e}")

def main():
    parser = argparse.ArgumentParser(description="Setup Python environment for the project")
    parser.add_argument("--offline", action="store_true", help="Install packages in offline mode")
    parser.add_argument("--download", action="store_true", help="Download packages for offline installation")
    parser.add_argument("--venv", default=".venv", help="Virtual environment path")
    parser.add_argument("--project", default="de_python_sql", help="Project name for Jupyter kernel")
    args = parser.parse_args()

    # Check Python version
    check_python_version()

    # Create virtual environment
    venv_path = os.path.abspath(args.venv)
    create_virtual_env(venv_path)

    # Get pip path
    pip_path = get_pip_command(venv_path)

    # Upgrade pip
    upgrade_pip(pip_path)

    if args.download:
        print("Downloading packages for offline installation...")
        download_packages(pip_path)
        print("Packages downloaded successfully")
    else:
        print("Installing packages...")
        install_packages(pip_path, offline=args.offline)
        print("Packages installed successfully")

        # Setup Jupyter kernel
        setup_jupyter_kernel(venv_path, args.project)

if __name__ == "__main__":
    main()
