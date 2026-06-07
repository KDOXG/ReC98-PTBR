import os
import subprocess
import shutil

thdat = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thdat.exe')

# Shared configurations for each extraction function keyed by short name
CONFIGS = {
    "th01": {
        "jp_files": ["東方靈異.伝"],
        "jp_folders": ["東方靈異伝"],
        "tmp_files": ["th01_tmp.dat"],
        "tmp_folders": ["extract_tmp"],
        "version": "1",
    },
    "th02": {
        "jp_files": ["東方封魔.録"],
        "jp_folders": ["東方封魔録"],
        "tmp_files": ["th02_tmp.dat"],
        "tmp_folders": ["extract_tmp"],
        "version": "2",
    },
    "th03": {
        "jp_files": ["夢時空1.DAT", "夢時空2.DAT"],
        "jp_folders": ["夢時空1", "夢時空2"],
        "tmp_files": ["th03_tmp1.dat", "th03_tmp2.dat"],
        "tmp_folders": ["extract_tmp1", "extract_tmp2"],
        "version": "3",
    },
    "th04": {
        "jp_files": ["東方幻想.郷", "幻想郷ED.DAT"],
        "jp_folders": ["東方幻想郷", "幻想郷ED"],
        "tmp_files": ["th04_tmp.dat", "th04ed_tmp.dat"],
        "tmp_folders": ["extract_tmp", "extract_ed_tmp"],
        "version": "4",
    },
    "th05": {
        "jp_files": ["怪綺談1.DAT", "怪綺談2.DAT"],
        "jp_folders": ["怪綺談1", "怪綺談2"],
        "tmp_files": ["th05_tmp1.dat", "th05_tmp2.dat"],
        "tmp_folders": ["extract_tmp1", "extract_tmp2"],
        "version": "5",
    },
}

def run_extract(gamedata_dir, config):
    executable = thdat

    jp_files = config.get("jp_files", [])
    jp_folders = config.get("jp_folders", [])
    tmp_files = config.get("tmp_files", [])
    tmp_folders = config.get("tmp_folders", [])
    version = config.get("version", "d")

    # Normalize lists to same length
    count = min(len(jp_files), len(jp_folders), len(tmp_files), len(tmp_folders))
    for i in range(count):
        jp_file = jp_files[i]
        jp_folder = jp_folders[i]
        tmp_file = tmp_files[i]
        tmp_folder = tmp_folders[i]

        archive_file_path = os.path.normpath(os.path.join(gamedata_dir, jp_file))
        temp_archive_file_path = os.path.normpath(os.path.join(gamedata_dir, tmp_file))
        temp_extract_folder_path = os.path.normpath(os.path.join(gamedata_dir, tmp_folder))
        final_extract_folder_path = os.path.normpath(os.path.join(gamedata_dir, jp_folder))

        # 1. Rename archive to ASCII
        if os.path.exists(archive_file_path):
            os.rename(archive_file_path, temp_archive_file_path)
            os.makedirs(temp_extract_folder_path, exist_ok=True)
        else:
            print(f"Error: Could not find {archive_file_path}")
            continue

        try:
            # 2. Execute thdat
            cmd = [
                executable,
                "-C", temp_extract_folder_path,
                "-x", version,
                temp_archive_file_path,
            ]
            print(f"Running thdat extract for {jp_file} (version {version})...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"thdat Error: {result.stderr}")

        finally:
            # 3. Cleanup and restore Japanese names
            if os.path.exists(temp_archive_file_path):
                os.rename(temp_archive_file_path, archive_file_path)

            if os.path.exists(temp_extract_folder_path):
                if os.path.exists(final_extract_folder_path):
                    shutil.rmtree(final_extract_folder_path)
                os.rename(temp_extract_folder_path, final_extract_folder_path)
                print(f"{jp_file} extraction complete and names restored.")

def run_create(gamedata_dir, mod_dir, config):
    executable = thdat

    jp_files = config.get("jp_files", [])
    jp_folders = config.get("jp_folders", [])
    tmp_files = config.get("tmp_files", [])
    tmp_folders = config.get("tmp_folders", [])
    version = config.get("version", "d")

    # Normalize lists to same length
    count = min(len(jp_files), len(jp_folders), len(tmp_files), len(tmp_folders))
    for i in range(count):
        jp_file = jp_files[i]
        jp_folder = jp_folders[i]
        tmp_file = tmp_files[i]
        tmp_folder = tmp_folders[i]

        gamedata_folder_path = os.path.normpath(os.path.join(gamedata_dir, jp_folder))
        mod_folder_path = os.path.normpath(os.path.join(mod_dir, jp_folder))
        temp_create_folder_path = os.path.normpath(os.path.join(mod_dir, tmp_folder))
        temp_archive_file_path = os.path.normpath(os.path.join(mod_dir, tmp_file))
        final_create_file_path = os.path.normpath(os.path.join(mod_dir, jp_file))
        
        if os.path.exists(final_create_file_path):
            os.remove(final_create_file_path)
        
        os.makedirs(temp_create_folder_path, exist_ok=True)
        
        for f in os.listdir(gamedata_folder_path):
            src = os.path.join(gamedata_folder_path, f)
            dst = os.path.join(temp_create_folder_path, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        
        for f in os.listdir(mod_folder_path):
            src = os.path.join(mod_folder_path, f)
            dst = os.path.join(temp_create_folder_path, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        try:
            # Execute thdat
            cmd = [
                executable,
                "-c", version,
                temp_archive_file_path,
                temp_create_folder_path,
            ]
            print(f"Running thdat create for {jp_file} (version {version})...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"thdat Error: {result.stderr}")

        finally:
            # Cleanup and restore Japanese names
            if os.path.exists(temp_archive_file_path):
                os.rename(temp_archive_file_path, final_create_file_path)
            shutil.rmtree(temp_create_folder_path)
            print(f"{jp_file} creation complete and names restored.")

def extract_th01_archive(gamedata_dir):
    config = CONFIGS.get("th01")
    run_extract(gamedata_dir, config)

def create_th01_archive(gamedata_dir, mod_dir):
    config = CONFIGS.get("th01")
    run_create(gamedata_dir, mod_dir, config)

def extract_th02_archive(gamedata_dir):
    config = CONFIGS.get("th02")
    run_extract(gamedata_dir, config)

def create_th02_archive(gamedata_dir, mod_dir):
    config = CONFIGS.get("th02")
    run_create(gamedata_dir, mod_dir, config)

def extract_th03_archive(gamedata_dir):
    config = CONFIGS.get("th03")
    run_extract(gamedata_dir, config)

def create_th03_archive(gamedata_dir, mod_dir):
    config = CONFIGS.get("th03")
    run_create(gamedata_dir, mod_dir, config)

def extract_th04_archive(gamedata_dir):
    config = CONFIGS.get("th04")
    run_extract(gamedata_dir, config)

def create_th04_archive(gamedata_dir, mod_dir):
    config = CONFIGS.get("th04")
    run_create(gamedata_dir, mod_dir, config)

def extract_th05_archive(gamedata_dir):
    config = CONFIGS.get("th05")
    run_extract(gamedata_dir, config)

def create_th05_archive(gamedata_dir, mod_dir):
    config = CONFIGS.get("th05")
    run_create(gamedata_dir, mod_dir, config)

# Example usage:
# create_th01_archive("C:/TouhouProjectTranslation/PC98Project/ReC98-PTBR/translation/exported_files/th01_gamedata", "C:/TouhouProjectTranslation/PC98Project/ReC98-PTBR/translation/mod/th01")