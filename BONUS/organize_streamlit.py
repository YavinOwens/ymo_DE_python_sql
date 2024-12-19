import os
import shutil

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def main():
    # Base paths
    streamlit_app_path = "streamlit_app"
    pages_path = os.path.join(streamlit_app_path, "pages")
    utils_path = os.path.join(streamlit_app_path, "utils")
    
    # Create directories
    create_directory(streamlit_app_path)
    create_directory(pages_path)
    create_directory(utils_path)
    
    # Move existing files
    files_to_move = {
        "1_Overview.py": os.path.join(pages_path, "1_Overview.py"),
        "2_Quality_Analysis.py": os.path.join(pages_path, "2_Quality_Analysis.py"),
        "3_Column_Analysis.py": os.path.join(pages_path, "3_Column_Analysis.py"),
        "4_Data_Catalogue.py": os.path.join(pages_path, "4_Data_Catalogue.py"),
        "5_Rule_Management.py": os.path.join(pages_path, "5_Rule_Management.py"),
        "main_app.py": os.path.join(streamlit_app_path, "Home.py"),
        "config.py": os.path.join(streamlit_app_path, "config.py"),
        "requirements.txt": os.path.join(streamlit_app_path, "requirements.txt")
    }
    
    for src, dst in files_to_move.items():
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Moved {src} to {dst}")
    
    # Copy utils files
    utils_files = ["data_loader.py", "utils.py", "__init__.py"]
    for file in utils_files:
        src = os.path.join("utils", file)
        dst = os.path.join(utils_path, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {src} to {dst}")

if __name__ == "__main__":
    os.chdir("BONUS")  # Change to BONUS directory first
    main()
    print("Streamlit app structure organized successfully!") 