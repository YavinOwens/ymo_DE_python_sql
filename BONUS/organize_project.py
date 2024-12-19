import os
import shutil

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Base directories
base_dir = os.path.dirname(os.path.abspath(__file__))
dash_app_dir = os.path.join(base_dir, 'dash_app')
streamlit_app_dir = os.path.join(base_dir, 'streamlit_app')

# Create main directories
create_directory(dash_app_dir)
create_directory(streamlit_app_dir)

# Create Dash app structure
dash_dirs = [
    os.path.join(dash_app_dir, 'pages'),
    os.path.join(dash_app_dir, 'components'),
    os.path.join(dash_app_dir, 'assets', 'css'),
    os.path.join(dash_app_dir, 'assets', 'data'),
    os.path.join(dash_app_dir, 'utils'),
]

# Create Streamlit app structure
streamlit_dirs = [
    os.path.join(streamlit_app_dir, 'pages'),
    os.path.join(streamlit_app_dir, 'utils'),
]

# Create all directories
for dir_path in dash_dirs + streamlit_dirs:
    create_directory(dir_path)

# Move files to Dash app
dash_files = {
    'app.py': 'app.py',
    'config.py': 'config.py',
    'data_loader.py': 'data_loader.py',
    'requirements.txt': 'requirements.txt',
    os.path.join('pages', '*'): os.path.join('pages'),
    os.path.join('components', '*'): os.path.join('components'),
    os.path.join('assets', 'css', '*'): os.path.join('assets', 'css'),
    os.path.join('assets', 'data', '*'): os.path.join('assets', 'data'),
    os.path.join('utils', '*'): os.path.join('utils'),
}

# Move files to Streamlit app
streamlit_files = {
    os.path.join('streamlit_pages', '*'): os.path.join('pages'),
    'config.py': 'config.py',
    'requirements.txt': 'requirements.txt',
}

def copy_files(source_dir, target_dir, file_mapping):
    for src, dst in file_mapping.items():
        src_path = os.path.join(source_dir, src)
        dst_path = os.path.join(target_dir, dst)
        
        if '*' in src:
            # Handle directory copying
            src_dir = os.path.dirname(src_path)
            if os.path.exists(src_dir):
                for item in os.listdir(src_dir):
                    item_src = os.path.join(src_dir, item)
                    item_dst = os.path.join(dst_path, item)
                    if os.path.isfile(item_src):
                        shutil.copy2(item_src, item_dst)
        else:
            # Handle single file copying
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)

# Copy files to their new locations
copy_files(base_dir, dash_app_dir, dash_files)
copy_files(base_dir, streamlit_app_dir, streamlit_files)

print("Project structure reorganized successfully!") 