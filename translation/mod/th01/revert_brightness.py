import os
import subprocess

# Configuration
SOURCE_FOLDER = "brightness_added"
TEMP_LUA_NAME = "_temp_darken.lua"

# 1. Embedded Reverse Lua Script Content
LUA_SCRIPT_CONTENT = """
local spr = app.activeSprite
if not spr then return end

local divisor = 16.0 
local pal = spr.palettes[1]

for i = 0, #pal - 1 do
    local color = pal:getColor(i)
    local r = math.floor(color.red / divisor)
    local g = math.floor(color.green / divisor)
    local b = math.floor(color.blue / divisor)
    pal:setColor(i, Color{ r=r, g=g, b=b, a=color.alpha })
end

local fullPath = spr.filename
local fileName = fullPath:match("^.+/(.+)$") or fullPath:match("^.+\\\\(.+)$") or fullPath

-- Saves directly to parent directory, overwriting original file
spr:saveAs(fileName)
spr:close()
"""

def main():
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Error: Target directory '{SOURCE_FOLDER}' does not exist.")
        return

    with open(TEMP_LUA_NAME, "w", encoding="utf-8") as f:
        f.write(LUA_SCRIPT_CONTENT.strip())

    try:
        target_path = os.path.join(".", SOURCE_FOLDER)
        bmp_files = [f for f in os.listdir(target_path) if f.lower().endswith(".bmp")]
        
        if not bmp_files:
            print(f"No .bmp files found inside '{SOURCE_FOLDER}'.")
            return

        print(f"Found {len(bmp_files)} files to revert. Starting process...")
        for bmp in bmp_files:
            relative_path = os.path.join(SOURCE_FOLDER, bmp)
            print(f"Reverting: {bmp}")
            
            # Run Aseprite on the nested file
            subprocess.run(["aseprite", "-b", relative_path, "--script", TEMP_LUA_NAME], check=True)
            
        print("\nSuccess! Main directory files replaced with original base brightness values.")

    finally:
        # 4. Clean up temporary file
        if os.path.exists(TEMP_LUA_NAME):
            os.remove(TEMP_LUA_NAME)

if __name__ == "__main__":
    main()