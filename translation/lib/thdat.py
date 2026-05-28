import os
import subprocess
import shutil

thdat = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thdat.exe')

def extract_th01_archive(gamedata_dir):
    # Configuration
    jp_file = "東方靈異.伝"
    jp_folder = "東方靈異伝"
    tmp_file = "th01_tmp.dat"
    tmp_folder = "extract_tmp"
    
    # Construct full paths
    archive_path = os.path.normpath(os.path.join(gamedata_dir, jp_file))
    temp_archive_path = os.path.normpath(os.path.join(gamedata_dir, tmp_file))
    temp_extract_path = os.path.normpath(os.path.join(gamedata_dir, tmp_folder))
    final_extract_path = os.path.normpath(os.path.join(gamedata_dir, jp_folder))
    
    executable = thdat

    # 1. Rename archive to ASCII
    if os.path.exists(archive_path):
        os.rename(archive_path, temp_archive_path)
        os.makedirs(temp_extract_path, exist_ok=True)
    else:
        print(f"Error: Could not find {archive_path}")
        return

    try:
        # 2. Execute thdat
        # We use a list for arguments to avoid shell escaping issues
        cmd = [
            executable, 
            "-C", temp_extract_path, 
            "-x", "1", 
            temp_archive_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"thdat Error: {result.stderr}")

    finally:
        # 3. Cleanup: Restore Japanese names regardless of success or failure
        if os.path.exists(temp_archive_path):
            os.rename(temp_archive_path, archive_path)
        
        if os.path.exists(temp_extract_path):
            # If the output folder already exists, remove it or merge it
            if os.path.exists(final_extract_path):
                shutil.rmtree(final_extract_path)
            os.rename(temp_extract_path, final_extract_path)
            print("Extraction complete and names restored.")

def apply_and_clean_th01_archive(gamedata_dir):
    # Configuration
    jp_file = "東方靈異.伝"
    jp_folder = "東方靈異伝"
    tmp_file = "th01_tmp.dat"
    tmp_folder = "extract_tmp"
    
    # Construct full paths
    archive_path = os.path.normpath(os.path.join(gamedata_dir, jp_file))
    temp_archive_path = os.path.normpath(os.path.join(gamedata_dir, tmp_file))
    temp_extract_path = os.path.normpath(os.path.join(gamedata_dir, tmp_folder))
    final_extract_path = os.path.normpath(os.path.join(gamedata_dir, jp_folder))
    
    executable = thdat

def extract_th02_archive(gamedata_dir):
    """
    Safely renames Japanese files to ASCII, runs thdat, and restores names.
    """
    # Configuration
    jp_file = "東方封魔.録"
    jp_folder = "東方封魔録"
    tmp_file = "th02_tmp.dat"
    tmp_folder = "extract_tmp"
    
    root_dir = "translation"
    
    # Construct full paths
    archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_file))
    temp_archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_file))
    temp_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_folder))
    final_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_folder))
    
    executable = thdat

    # 1. Rename archive to ASCII
    if os.path.exists(archive_path):
        os.rename(archive_path, temp_archive_path)
        os.makedirs(temp_extract_path, exist_ok=True)
    else:
        print(f"Error: Could not find {archive_path}")
        return

    try:
        # 2. Execute thdat
        # We use a list for arguments to avoid shell escaping issues
        cmd = [
            executable, 
            "-C", temp_extract_path, 
            "-x", "1", 
            temp_archive_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"thdat Error: {result.stderr}")

    finally:
        # 3. Cleanup: Restore Japanese names regardless of success or failure
        if os.path.exists(temp_archive_path):
            os.rename(temp_archive_path, archive_path)
        
        if os.path.exists(temp_extract_path):
            # If the output folder already exists, remove it or merge it
            if os.path.exists(final_extract_path):
                shutil.rmtree(final_extract_path)
            os.rename(temp_extract_path, final_extract_path)
            print("Extraction complete and names restored.")

def extract_th03_archive(gamedata_dir):
    """
    Safely renames Japanese files to ASCII, runs thdat, and restores names.
    """
    # Configuration
    jp_files = ["夢時空1.DAT", "夢時空2.DAT"]
    jp_folders = ["夢時空1", "夢時空2"]
    tmp_files = ["th03_tmp1.dat", "th03_tmp2.dat"]
    tmp_folders = ["extract_tmp1", "extract_tmp2"]
    
    root_dir = "translation"
    
    # Construct full paths
    archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_file))
    temp_archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_file))
    temp_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_folder))
    final_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_folder))
    
    executable = thdat

    # 1. Rename archive to ASCII
    if os.path.exists(archive_path):
        os.rename(archive_path, temp_archive_path)
        os.makedirs(temp_extract_path, exist_ok=True)
    else:
        print(f"Error: Could not find {archive_path}")
        return

    try:
        # 2. Execute thdat
        # We use a list for arguments to avoid shell escaping issues
        cmd = [
            executable, 
            "-C", temp_extract_path, 
            "-x", "1", 
            temp_archive_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"thdat Error: {result.stderr}")

    finally:
        # 3. Cleanup: Restore Japanese names regardless of success or failure
        if os.path.exists(temp_archive_path):
            os.rename(temp_archive_path, archive_path)
        
        if os.path.exists(temp_extract_path):
            # If the output folder already exists, remove it or merge it
            if os.path.exists(final_extract_path):
                shutil.rmtree(final_extract_path)
            os.rename(temp_extract_path, final_extract_path)
            print("Extraction complete and names restored.")

def extract_th04_archive(gamedata_dir):
    """
    Safely renames Japanese files to ASCII, runs thdat, and restores names.
    """
    # Configuration
    jp_files = ["東方幻想.郷", "幻想郷ED.DAT"]
    jp_folders = ["東方幻想郷", "幻想郷ED"]
    tmp_files = ["th04_tmp.dat", "th04ed_tmp.dat"]
    tmp_folders = ["extract_tmp", "extract_ed_tmp"]
    
    root_dir = "translation"
    
    # Construct full paths
    archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_file))
    temp_archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_file))
    temp_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_folder))
    final_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_folder))
    
    executable = thdat

    # 1. Rename archive to ASCII
    if os.path.exists(archive_path):
        os.rename(archive_path, temp_archive_path)
        os.makedirs(temp_extract_path, exist_ok=True)
    else:
        print(f"Error: Could not find {archive_path}")
        return

    try:
        # 2. Execute thdat
        # We use a list for arguments to avoid shell escaping issues
        cmd = [
            executable, 
            "-C", temp_extract_path, 
            "-x", "1", 
            temp_archive_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"thdat Error: {result.stderr}")

    finally:
        # 3. Cleanup: Restore Japanese names regardless of success or failure
        if os.path.exists(temp_archive_path):
            os.rename(temp_archive_path, archive_path)
        
        if os.path.exists(temp_extract_path):
            # If the output folder already exists, remove it or merge it
            if os.path.exists(final_extract_path):
                shutil.rmtree(final_extract_path)
            os.rename(temp_extract_path, final_extract_path)
            print("Extraction complete and names restored.")

def extract_th05_archive(gamedata_dir):
    """
    Safely renames Japanese files to ASCII, runs thdat, and restores names.
    """
    # Configuration
    jp_files = ["怪綺談1.DAT", "怪綺談2.DAT"]
    jp_folders = ["怪綺談1", "怪綺談2"]
    tmp_files = ["th05_tmp1.dat", "th05_tmp2.dat"]
    tmp_folders = ["extract_tmp1", "extract_tmp2"]
    
    root_dir = "translation"
    
    # Construct full paths
    archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_file))
    temp_archive_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_file))
    temp_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, tmp_folder))
    final_extract_path = os.path.normpath(os.path.join(root_dir, gamedata_dir, jp_folder))
    
    executable = thdat

    # 1. Rename archive to ASCII
    if os.path.exists(archive_path):
        os.rename(archive_path, temp_archive_path)
        os.makedirs(temp_extract_path, exist_ok=True)
    else:
        print(f"Error: Could not find {archive_path}")
        return

    try:
        # 2. Execute thdat
        # We use a list for arguments to avoid shell escaping issues
        cmd = [
            executable, 
            "-C", temp_extract_path, 
            "-x", "1", 
            temp_archive_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"thdat Error: {result.stderr}")

    finally:
        # 3. Cleanup: Restore Japanese names regardless of success or failure
        if os.path.exists(temp_archive_path):
            os.rename(temp_archive_path, archive_path)
        
        if os.path.exists(temp_extract_path):
            # If the output folder already exists, remove it or merge it
            if os.path.exists(final_extract_path):
                shutil.rmtree(final_extract_path)
            os.rename(temp_extract_path, final_extract_path)
            print("Extraction complete and names restored.")

# Example usage:
# root = r"C:\TouhouProjectTranslation\PC98Project\[BUILDING]"
# extract_th01_archive(root, r"lib\thdat.exe", "th01_gamedata")