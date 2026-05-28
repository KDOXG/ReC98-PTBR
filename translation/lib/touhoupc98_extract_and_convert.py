import os
import shutil
import sys
import subprocess
from . import hdi_tool
from . import pi_image_hex
from . import bmp_pi_conversor
from . import thdat

export_dir = os.path.join("translation", "exported_files")
dosbox_dir = os.path.join("translation", "dosbox-x")
mod_dir = os.path.join("translation", "mod")

# Convert all .grp files from grp_dir to .pi in pi_dir
def convert_grp_to_pi(grp_dir, pi_dir):
    os.makedirs(pi_dir, exist_ok=True)
    for file in os.listdir(grp_dir):
        if file.lower().endswith('.grp'):
            grp_file = os.path.join(grp_dir, file)
            pi_filename = os.path.splitext(file)[0] + '.pi'
            pi_file = os.path.join(pi_dir, pi_filename)
            pi_image_hex.clean_and_format(grp_file, 'PI', pi_file)

# Convert all .pi files from pi_dir to .bmp in bmp_dir
def convert_pi_to_bmp(pi_dir, bmp_dir):
    os.makedirs(bmp_dir, exist_ok=True)
    for file in os.listdir(pi_dir):
        if file.lower().endswith('.pi'):
            pi_file = os.path.join(pi_dir, file)
            bmp_filename = os.path.splitext(file)[0] + '.bmp'
            bmp_file = os.path.join(bmp_dir, bmp_filename)
            bmp_pi_conversor.pi_to_bmp(pi_file, bmp_file)

# Convert all .bmp files from bmp_dir to .pi in pi_dir
def convert_bmp_to_pi(bmp_dir, pi_dir):
    os.makedirs(pi_dir, exist_ok=True)
    for file in os.listdir(bmp_dir):
        if file.lower().endswith('.bmp'):
            bmp_file = os.path.join(bmp_dir, file)
            pi_filename = os.path.splitext(file)[0] + '.pi'
            pi_file = os.path.join(pi_dir, pi_filename)
            result = bmp_pi_conversor.bmp_to_pi(bmp_file, pi_file)

# Convert all .pi files from pi_dir to .grp in grp_dir
def convert_pi_to_grp(pi_dir, grp_dir):
    os.makedirs(grp_dir, exist_ok=True)
    for file in os.listdir(pi_dir):
        if file.lower().endswith('.pi'):
            pi_file = os.path.join(pi_dir, file)
            grp_filename = os.path.splitext(file)[0] + '.grp'
            grp_file = os.path.join(grp_dir, grp_filename)
            pi_image_hex.clean_and_format(pi_file, 'GRP', grp_file)

def extract_and_convert_th01(file_name, hdi_file):
    gamedata_dir = os.path.join(export_dir, f"{file_name}_gamedata")
    pi_dir = os.path.join(export_dir, f"{file_name}_pi")
    bmp_dir = os.path.join(export_dir, f"{file_name}_bmp")
    
    # Extract all files from hdi
    hdi_tool.extract_all_files_from_hdi(hdi_file, gamedata_dir)
    
    # Extract the dat contents using thdat
    thdat.extract_th01_archive(gamedata_dir)
    
    convert_grp_to_pi(gamedata_dir, pi_dir)
    
    convert_pi_to_bmp(pi_dir, bmp_dir)

def convert_and_prepare_th01(file_name):
    modded_dir = os.path.join(mod_dir, f"{file_name}")
    gamedata_dir = os.path.join(export_dir, f"{file_name}_gamedata")
    bmp_dir = os.path.join(export_dir, f"{file_name}_bmp")
    pi_from_bmp_dir = os.path.join(export_dir, f"{file_name}_pi_from_bmp")
    grp_from_pi_dir = os.path.join(export_dir, f"{file_name}_grp_from_pi")
    
    if not os.path.exists(bmp_dir):
        print(f"BMP input directory {bmp_dir} not found.")
        return
    
    convert_bmp_to_pi(bmp_dir, pi_from_bmp_dir)
    
    convert_bmp_to_pi(modded_dir, pi_from_bmp_dir)
    
    convert_pi_to_grp(pi_from_bmp_dir, grp_from_pi_dir)
    
    # Apply and clean the dat contents using thdat
    thdat.apply_and_clean_th01_archive(gamedata_dir)
    
    # Clean and apply all converted files to the game folder
    for f in os.listdir(grp_from_pi_dir):
        src = os.path.join(grp_from_pi_dir, f)
        dst = os.path.join(gamedata_dir, f)
        if os.path.isfile(src):
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)
    shutil.rmtree(pi_from_bmp_dir)
    shutil.rmtree(grp_from_pi_dir)
    
def extract_and_convert_th02(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 2 Fuumaroku is not yet implemented.")

def convert_and_prepare_th02(file_name):
    print(f"Error: Extraction and conversion for Touhou 2 Fuumaroku is not yet implemented.")
    
def extract_and_convert_th03(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 3 Yumejikuu is not yet implemented.")

def convert_and_prepare_th03(file_name):
    print(f"Error: Extraction and conversion for Touhou 3 Yumejikuu is not yet implemented.")
    
def extract_and_convert_th04(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 4 Gensoukyou is not yet implemented.")

def convert_and_prepare_th04(file_name):
    print(f"Error: Extraction and conversion for Touhou 4 Gensoukyou is not yet implemented.")
    
def extract_and_convert_th05(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 5 Kaikidan is not yet implemented.")

def convert_and_prepare_th05(file_name):
    print(f"Error: Extraction and conversion for Touhou 5 Kaikidan is not yet implemented.")

def set_and_play_running_game(file_name):
    running_game_dir = "running_game"
    dosbox_dir = "dosbox-x"
    dosbox_exe = os.path.join(dosbox_dir, "dosbox-x.exe" if os.name == 'nt' else "dosbox-x")
    game_folder = os.path.join("exported_files", file_name + "_gamedata")
    
    if os.path.exists(running_game_dir):
        shutil.rmtree(running_game_dir)
    os.makedirs(running_game_dir, exist_ok=True)
    
    if os.path.exists(game_folder):
        for item in os.listdir(game_folder):
            src_path = os.path.join(game_folder, item)
            dst_path = os.path.join(running_game_dir, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

    if os.path.exists(dosbox_exe):
        try:
            subprocess.Popen([dosbox_exe], cwd=dosbox_dir)
        except Exception as e:
            print(f"Failed to launch dosbox-x: {e}")

def extract_and_convert_game_to_mod(file_name = ""):
    hdi_file = "hdi/" + file_name + ".hdi"
    
    if not os.path.exists(hdi_file):
        print(f"Error: {hdi_file} not found.")
        return
    
    match file_name:
        case "th01":
            extract_and_convert_th01(file_name, hdi_file)
        case "th02":
            extract_and_convert_th02(file_name, hdi_file)
        case "th03":
            extract_and_convert_th03(file_name, hdi_file)
        case "th04":
            extract_and_convert_th04(file_name, hdi_file)
        case "th05":
            extract_and_convert_th05(file_name, hdi_file)
        case _:
            print(f"Error: Unsupported file name {file_name}. No extraction or conversion performed.")

def convert_mod_to_game(file_name = ""):
    hdi_file = "hdi/" + file_name + ".hdi"
    
    if not os.path.exists(hdi_file):
        print(f"Error: {hdi_file} not found.")
        sys.exit(1)
    
    match file_name:
        case "th01":
            convert_and_prepare_th01(file_name)
        case "th02":
            convert_and_prepare_th02(file_name)
        case "th03":
            convert_and_prepare_th03(file_name)
        case "th04":
            convert_and_prepare_th04(file_name)
        case "th05":
            convert_and_prepare_th05(file_name)
        case _:
            print(f"Error: Unsupported file name {file_name}. No extraction or conversion performed.")