import os
import shutil
import subprocess
from . import hdi_tool
from . import pi_image_hex
from . import bmp_pi_conversor
from . import thdat
from . import th01_extraction_suite

lib_dir = os.path.dirname(os.path.abspath(__file__))
translation_dir = os.path.dirname(lib_dir)
root_dir = os.path.dirname(translation_dir)

dosbox_exe = "dosbox-x"
dosbox_dir = os.path.join(translation_dir, "dosbox-x")
export_dir = os.path.join(translation_dir, "exported_files")
hdi_dir = os.path.join(translation_dir, "hdi")
mod_dir = os.path.join(translation_dir, "mod")
running_game_dir = os.path.join(translation_dir, "running_game")

# ================================================================
# CONVERSORS - PRIVATE FUNCTIONS
# ================================================================

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
def convert_pi_to_bmp(pi_dir, bmp_dir, pi_list=None):
    if pi_list is None:
        pi_list = os.listdir(pi_dir)
    os.makedirs(bmp_dir, exist_ok=True)
    for file in pi_list:
        if file.lower().endswith('.pi'):
            pi_file = os.path.join(pi_dir, file)
            bmp_filename = os.path.splitext(file)[0] + '.bmp'
            bmp_file = os.path.join(bmp_dir, bmp_filename)
            bmp_pi_conversor.pi_to_bmp(pi_file, bmp_file)

# Convert all .bmp files from bmp_dir to .pi in pi_dir
def convert_bmp_to_pi(bmp_dir, pi_dir, bmp_list=None):
    if bmp_list is None:
        bmp_list = os.listdir(bmp_dir)
    os.makedirs(pi_dir, exist_ok=True)
    for file in bmp_list:
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

# ================================================================
# EXTRACTION AND CONVERSION - PRIVATE FUNCTIONS
# ================================================================

def extract_and_convert_th01(file_name, hdi_file):
    gamedata_dir = os.path.join(export_dir, f"{file_name}_gamedata")
    pi_dir = os.path.join(export_dir, f"{file_name}_pi")
    bmp_dir = os.path.join(export_dir, f"{file_name}_bmp")
    
    # Extract all files from .hdi
    hdi_tool.extract_all_files_from_hdi(hdi_file, gamedata_dir)
    
    # Extract .dat contents using thdat
    thdat.extract_th01_archive(gamedata_dir)
    
    convert_grp_to_pi(gamedata_dir, pi_dir)
    convert_pi_to_bmp(pi_dir, bmp_dir)
    
    shutil.rmtree(pi_dir)

def convert_and_prepare_th01(file_name):
    mod_root_dir = os.path.join(mod_dir, f"{file_name}")
    gamedata_dir = os.path.join(export_dir, f"{file_name}_gamedata")
    modded_dir = os.path.join(export_dir, f"{file_name}_modded")
    pi_from_bmp_dir = os.path.join(export_dir, f"{file_name}_pi_from_bmp")
    grp_from_pi_dir = os.path.join(export_dir, f"{file_name}_grp_from_pi")
    
    if not (os.path.exists(gamedata_dir) and os.path.exists(mod_root_dir)):
        print(f"Error: Directories for mod not found.")
        return 1
    
    # Build and convert modded .dat file
    thdat.create_th01_archive(gamedata_dir,mod_root_dir)
    
    # Create output modded folder
    os.makedirs(modded_dir, exist_ok=True)
    
    # Copy all original files to modded folder as base
    for item in os.listdir(gamedata_dir):
        src = os.path.join(gamedata_dir, item)
        dst = os.path.join(modded_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
    
    # Get list of all original files and mod files, for checking which ones are valid mods in mod folder
    modded_files = os.listdir(mod_root_dir)
    modded_files = [f.lower() for f in modded_files]
    gamedata_files = os.listdir(gamedata_dir)
    gamedata_files = [f.lower() for f in gamedata_files] + ["anniv.exe"]
    gamedata_files = [f for f in gamedata_files if f in modded_files or
                      (f.endswith('.grp') and os.path.splitext(f)[0] + '.bmp' in modded_files)]
    
    # Copy all miscellaneous mods to modded folder
    for item in os.listdir(mod_root_dir):
        if item.lower() not in gamedata_files:
            continue
        src = os.path.join(mod_root_dir, item)
        dst = os.path.join(modded_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
    
    # Get list of all modded .bmp files that are valid mods (have a corresponding .grp in original files list)
    bmp_files = [f for f in modded_files if f.endswith('.bmp') and
                 (os.path.splitext(f)[0] + '.grp' in gamedata_files)]
    
    # Convert and copy modded .grp files that are valid mods to modded folder
    convert_bmp_to_pi(mod_root_dir, pi_from_bmp_dir, bmp_files)
    convert_pi_to_grp(pi_from_bmp_dir, grp_from_pi_dir)
    for f in os.listdir(grp_from_pi_dir):
        src = os.path.join(grp_from_pi_dir, f)
        dst = os.path.join(modded_dir, f)
        if os.path.isfile(src):
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)
    
    # Clean temp folders
    shutil.rmtree(pi_from_bmp_dir)
    shutil.rmtree(grp_from_pi_dir)
    
    return 0
    
def extract_and_convert_th02(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 2 Fuumaroku is not yet implemented.")

def convert_and_prepare_th02(file_name):
    print(f"Error: Extraction and conversion for Touhou 2 Fuumaroku is not yet implemented.")
    return 1
    
def extract_and_convert_th03(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 3 Yumejikuu is not yet implemented.")

def convert_and_prepare_th03(file_name):
    print(f"Error: Extraction and conversion for Touhou 3 Yumejikuu is not yet implemented.")
    return 1
    
def extract_and_convert_th04(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 4 Gensoukyou is not yet implemented.")

def convert_and_prepare_th04(file_name):
    print(f"Error: Extraction and conversion for Touhou 4 Gensoukyou is not yet implemented.")
    return 1
    
def extract_and_convert_th05(file_name, hdi_file):
    print(f"Error: Extraction and conversion for Touhou 5 Kaikidan is not yet implemented.")

def convert_and_prepare_th05(file_name):
    print(f"Error: Extraction and conversion for Touhou 5 Kaikidan is not yet implemented.")
    return 1

# ================================================================
# SET AND PLAY - PRIVATE FUNCTION
# ================================================================

def set_and_play_running_game(file_name):
    game_folder_name = file_name + "_modded"
    game_folder = os.path.normpath(os.path.join(export_dir, game_folder_name))
    
    # if not os.path.exists(game_folder):
    #     print(f"Error: Game folder {game_folder_name} not found. Please extract and convert the game first.")
    #     return
    
    # Reset running game directory to have the files of only one game
    if os.path.exists(running_game_dir):
        shutil.rmtree(running_game_dir)
    os.makedirs(running_game_dir, exist_ok=True)
    if os.path.exists(game_folder):
        for item in os.listdir(game_folder):
            src_path = os.path.join(game_folder, item)
            dst_path = os.path.join(running_game_dir, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

    try:
        print(f"Launching {game_folder_name} with DOSBox-X...")
        subprocess.run(dosbox_exe, cwd=dosbox_dir, shell=True)
    except Exception as e:
        print(f"Failed to launch DOSBox-X: {e}")

# ================================================================
# EXTRACTION AND CONVERSION - PUBLIC FUNCTIONS
# ================================================================

def extract_and_convert_game_to_mod(file_name = ""):
    hdi_file = os.path.join(hdi_dir, file_name + ".hdi")
    
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

def set_and_play_modded_game(file_name = ""):
    hdi_file = os.path.join(hdi_dir, file_name + ".hdi")
    
    if not os.path.exists(hdi_file):
        print(f"Error: {hdi_file} not found.")
        return
    
    match file_name:
        case "th01":
            error = convert_and_prepare_th01(file_name)
        case "th02":
            error = convert_and_prepare_th02(file_name)
        case "th03":
            error = convert_and_prepare_th03(file_name)
        case "th04":
            error = convert_and_prepare_th04(file_name)
        case "th05":
            error = convert_and_prepare_th05(file_name)
        case _:
            print(f"Error: Unsupported file name {file_name}. No extraction or conversion performed.")
            return
    if error:
        print(f"Error: Failed to prepare modded game. Please check the mod files and try again.")
        return
    set_and_play_running_game(file_name)

def convert_modded_game_to_hdi(file_name = ""):
    print(f"Error: Conversion from Mod + Game to HDI is not yet implemented.")