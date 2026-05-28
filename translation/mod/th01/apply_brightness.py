import os
import shutil
import subprocess

# Configuration
TARGET_FOLDER = "brightness_added"
TEMP_LUA_NAME = "_temp_brighten.lua"

# 1. Embedded Lua Script Content
LUA_SCRIPT_CONTENT = """
local spr = app.activeSprite
if not spr then return end

local multiplier = 16.0 
local pal = spr.palettes[1]

for i = 0, #pal - 1 do
    local color = pal:getColor(i)
    local r = math.min(255, math.floor(color.red * multiplier))
    local g = math.min(255, math.floor(color.green * multiplier))
    local b = math.min(255, math.floor(color.blue * multiplier))
    pal:setColor(i, Color{ r=r, g=g, b=b, a=color.alpha })
end

local fullPath = spr.filename
local fileName = fullPath:match("^.+/(.+)$") or fullPath:match("^.+\\\\(.+)$") or fullPath

spr:saveAs("brightness_added/" .. fileName)
spr:close()
"""

def main():
    # 2. Reset the output directory
    if os.path.exists(TARGET_FOLDER):
        print(f"Removing existing '{TARGET_FOLDER}' directory...")
        shutil.rmtree(TARGET_FOLDER)
    os.makedirs(TARGET_FOLDER)

    # 3. Write temporary Lua script
    with open(TEMP_LUA_NAME, "w", encoding="utf-8") as f:
        f.write(LUA_SCRIPT_CONTENT.strip())

    try:
        # 4. Find and process files
        bmp_files = [f for f in os.listdir(".") if f.lower().endswith(".bmp")]
        
        if not bmp_files:
            print("No .bmp files found in the current folder.")
            return

        print(f"Found {len(bmp_files)} files. Starting Aseprite processing...")
        for bmp in bmp_files:
            print(f"Processing: {bmp}")
            # subprocess.run waits automatically for each file to finish execution
            subprocess.run(["aseprite", "-b", bmp, "--script", TEMP_LUA_NAME], check=True)
            
        print(f"\nSuccess! All brightened files stored in '{TARGET_FOLDER}'.")

    finally:
        # 5. Clean up temporary file
        if os.path.exists(TEMP_LUA_NAME):
            os.remove(TEMP_LUA_NAME)

if __name__ == "__main__":
    main()