import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))
ndc = os.path.join(base_dir, 'NDC.EXE')

# NDC Partition number for floppy/HDI images
PARTITION_NUMBER = "0"

def run_ndc_command(command):
    """Execute an ndc command and handle errors."""
    try:
        full_command = f'cmd /c chcp 932 >nul && {command}'
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            shell=True,
            encoding='cp932',
            errors='replace'
        )
        if result.returncode != 0:
            print(f"NDC Error: {result.stderr}")
            return False
        if result.stdout:
            print(result.stdout)
        return True
    except Exception as e:
        print(f"Error running NDC command: {e}")
        return False

def hdi_to_img(hdi_path, output_path):
    """Extract raw image from HDI file using ndc."""
    if not os.path.exists(hdi_path):
        print(f"Error: {hdi_path} not found.")
        return False
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    command = f'"{ndc}" BG "{hdi_path}" {PARTITION_NUMBER} "{output_path}"'
    success = run_ndc_command(command)
    if success:
        print(f"Success: {output_path} generated (RAW).")
    return success

def img_to_hdi(img_path, original_hdi_path, final_hdi_path):
    """Insert raw image back into HDI file using ndc."""
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        return False
    
    if not os.path.exists(original_hdi_path):
        print(f"Error: {original_hdi_path} not found.")
        return False
    
    # Create a temporary copy of the original HDI
    import shutil
    shutil.copy(original_hdi_path, final_hdi_path)
    
    command = f'"{ndc}" BP "{final_hdi_path}" {PARTITION_NUMBER} "{img_path}"'
    success = run_ndc_command(command)
    if success:
        print(f"Success: {final_hdi_path} created with preserved header.")
    return success

def recover_shift_jis_name(broken_name):
    """Attempt to recover a Shift-JIS filename from Mojibake bytes."""
    try:
        recovered = broken_name.encode('cp1252').decode('cp932')
    except UnicodeError:
        return None
    if recovered == broken_name:
        return None
    return recovered


def rename_mojibake_names(output_dir):
    """Rename extracted filenames that were mangled by wrong encoding."""
    for root, dirs, files in os.walk(output_dir, topdown=False):
        for name in files + dirs:
            if any(ord(c) > 127 for c in name):
                recovered = recover_shift_jis_name(name)
                if recovered and recovered != name:
                    old_path = os.path.join(root, name)
                    new_path = os.path.join(root, recovered)
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(old_path, new_path)
                    print(f"Renamed mangled filename: {name} -> {recovered}")


def extract_all_files_from_hdi(hdi_path, output_dir):
    """Extract all files from HDI image using ndc."""
    if not os.path.exists(hdi_path):
        print(f"Error: {hdi_path} not found.")
        return False
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Use the long-file-name flag so Japanese filenames are preserved
    command = f'"{ndc}" GL "{hdi_path}" {PARTITION_NUMBER} "" "{output_dir}"'
    success = run_ndc_command(command)
    if success:
        rename_mojibake_names(output_dir)
        print(f"Success: All files extracted from {os.path.basename(hdi_path)} to {output_dir}")
    return success

def insert_files_into_hdi(hdi_path, source_path, destination_folder=""):
    """Insert files or folders into HDI image using ndc."""
    if not os.path.exists(hdi_path):
        print(f"Error: {hdi_path} not found.")
        return False
    
    if not os.path.exists(source_path):
        print(f"Error: {source_path} not found.")
        return False
    
    dest_path = f'"{destination_folder}"' if destination_folder else '""'
    command = f'"{ndc}" P "{hdi_path}" {PARTITION_NUMBER} "{source_path}" {dest_path}'
    success = run_ndc_command(command)
    if success:
        print(f"Success: {os.path.basename(source_path)} inserted into HDI.")
    return success

def list_files_in_hdi(hdi_path, internal_path=""):
    """List files in HDI image using ndc."""
    if not os.path.exists(hdi_path):
        print(f"Error: {hdi_path} not found.")
        return False
    
    internal_path_arg = f'"{internal_path}"' if internal_path else '""'
    command = f'"{ndc}" L "{hdi_path}" {PARTITION_NUMBER} {internal_path_arg}'
    success = run_ndc_command(command)
    return success
