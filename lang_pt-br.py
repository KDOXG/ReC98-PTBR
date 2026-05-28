import os
import sys
from translation.lib.touhoupc98_extract_and_convert import convert_mod_to_game, extract_and_convert_game_to_mod, set_and_play_running_game

# ====================== CROSS-PLATFORM KEY DETECTION ======================
if os.name == 'nt':  # Windows
    import msvcrt

    def get_key():
        key = msvcrt.getch()
        if key in [b'\x00', b'\xe0']:
            msvcrt.getch()
        return key

else:  # Linux / macOS
    import termios
    import tty

    def get_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
            if key == '\x1b':
                key += sys.stdin.read(2) if sys.stdin else ''
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key.encode('utf-8') if isinstance(key, str) else key


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# ============================ MENU PRINT FUNCTIONS ============================

def print_main_menu():
    clear_screen()
    print("=" * 60)
    print("     TOUHOU PC98 TRANSLATION MOD TOOL")
    print("=" * 60)
    print("1. Touhou 1 Reiiden")
    print("2. Touhou 2 Fuumaroku")
    print("3. Touhou 3 Yumejikuu")
    print("4. Touhou 4 Gensoukyou")
    print("5. Touhou 5 Kaikidan")
    print("0. Exit")
    print("=" * 60)
    print("\nPress the number key (no Enter needed)...")

def print_touhou_menu(game_name):
    clear_screen()
    print("=" * 60)
    print(f"     TOUHOU PC98 TRANSLATION MOD - {game_name}")
    print("=" * 60)
    print("1. Test Game from Game Folder")
    print("2. Full Extract and Convert for Modding")
    print("3. Convert Mod to Game Format and Apply to Game Folder")
    print("0. Go Back to Main Menu")
    print("=" * 60)
    print("\nPress the number key (no Enter needed)...")


# ============================ SUBMENU FUNCTIONS ============================

def touhou1_menu():
    game_name = "Touhou 1 Reiiden"
    file_name = "th01"
    game_menu(game_name, file_name)


def touhou2_menu():
    game_name = "Touhou 2 Fuumaroku"
    file_name = "th02"
    game_menu(game_name, file_name)


def touhou3_menu():
    game_name = "Touhou 3 Yumejikuu"
    file_name = "th03"
    game_menu(game_name, file_name)


def touhou4_menu():
    game_name = "Touhou 4 Gensoukyou"
    file_name = "th04"
    game_menu(game_name, file_name)


def touhou5_menu():
    game_name = "Touhou 5 Kaikidan"
    file_name = "th05"
    game_menu(game_name, file_name)


# ============================ MENUS ============================

def main_menu():
    while True:
        print_main_menu()
        match get_key():
            case b'0' | b'q' | b'Q' | b'\x1b':
                clear_screen()
                sys.exit(0)
            case b'1':
                touhou1_menu()
            case b'2':
                touhou2_menu()
            case b'3':
                touhou3_menu()
            case b'4':
                touhou4_menu()
            case b'5':
                touhou5_menu()
            # else: invalid key → refresh main menu

def game_menu(game_name, file_name):
    while True:
        print_touhou_menu(game_name)
        match get_key():
            case b'0' | b'q' | b'Q':
                return
            case b'1':
                clear_screen()
                print(f"Testing {game_name} from the Game Folder...")
                set_and_play_running_game(file_name)
                input("\nPress Enter to continue...")
            case b'2':
                clear_screen()
                print(f"Starting Full Extract and Convert for {game_name}...")
                extract_and_convert_game_to_mod(file_name)
                print(f"Finished process.")
                input("\nPress Enter to continue...")
            case b'3':
                clear_screen()
                print(f"Converting Mod → Game Format for {game_name}...")
                convert_mod_to_game(file_name)
                print(f"Finished process.")
                input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        clear_screen()
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")