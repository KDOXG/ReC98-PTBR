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