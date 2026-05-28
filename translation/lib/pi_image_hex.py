import os
import shutil

# GRP to PI: P, i
GRP_TO_PI_HEX = [0x50, 0x69]
# PI to GRP: Z, N, EOF, and the PC98 header info
PI_TO_GRP_HEX = [0x5A, 0x4E, 0x1A, 0x00, 0x00, 0x00, 0x00, 0x04, 0x50, 0x43, 0x39, 0x38]
# PI Header cleaning: P, i, EOF, and the PC98 header info
PI_CLEANING_HEX = [0x50, 0x69, 0x1A, 0x00, 0x00, 0x00, 0x00, 0x04, 0x50, 0x43, 0x39, 0x38]

def clean_and_format(file_path, new_ext="PI", output_path=None):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    cur_ext = os.path.splitext(file_path)[1].replace(".", "").upper()
    new_ext = new_ext.upper()
    hex_values = None

    if cur_ext == "PI" and new_ext == "PI":
        hex_values = PI_CLEANING_HEX
    elif cur_ext == "GRP" and new_ext == "PI":
        hex_values = GRP_TO_PI_HEX
    elif cur_ext == "PI" and new_ext == "GRP":
        hex_values = PI_TO_GRP_HEX

    if not hex_values:
        print(f"No logic defined for {cur_ext} to {new_ext} conversion.")
        return None
        
    if output_path is None:
        base = os.path.splitext(file_path)[0]
        output_path = f"{base}.{new_ext}"
    
    shutil.copy(file_path, output_path)
    
    with open(output_path, "r+b") as f:
        f.seek(0)
        f.write(bytes(hex_values))
    
    print(f"Converted: {os.path.basename(file_path)} -> {os.path.basename(output_path)}")
        
    return output_path
        