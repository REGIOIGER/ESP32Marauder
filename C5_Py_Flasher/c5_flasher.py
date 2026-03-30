# === ESP32-C5 Auto Flasher Script By: AWOK ===

import sys
import subprocess
import os
import platform   # Placeholder for possible OS checks
import glob
import time
import shutil
import argparse

def ensure_package(pkg):
    try:
        __import__(pkg if pkg != 'gitpython' else 'git')
    except ImportError:
        print(f"Installing missing package: {pkg}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', pkg])

try:
    import serial.tools.list_ports
except ImportError:
    ensure_package('pyserial')
try:
    import esptool
except ImportError:
    ensure_package('esptool')
try:
    from colorama import Fore, Style
except ImportError:
    ensure_package('colorama')

# Dependency check and install if needed
REQUIRED_PACKAGES = [
    'pyserial',
    'esptool',
    'colorama'
]

def ensure_requirements():
    for pkg in REQUIRED_PACKAGES:
        ensure_package(pkg)
ensure_requirements()

# Finds the first file from a list of possible names in the bins folder
def find_file(name_options, bins_dir):
    for name in name_options:
        files = glob.glob(os.path.join(bins_dir, name))
        if files:
            return files[0]
    return None

def main():
    parser = argparse.ArgumentParser(description="ESP32-C5 Auto Flasher (bins subdir)")
    parser.parse_args()

    bins_dir = os.path.join(os.path.dirname(__file__), 'bins')
    if not os.path.isdir(bins_dir):
        print(Fore.RED + f"Bins directory not found: {bins_dir}\nPlease create a 'bins' folder with your .bin files." + Style.RESET_ALL)
        exit(1)

    # Logo and splash, both centered and purple
    terminal_width = shutil.get_terminal_size((100, 20)).columns
    def center(text): return text.center(terminal_width)
    logo_lines = [
        "                                            @@@@@@                              ",
        "                                @@@@@@@@  @@@@@ @@@@                            ",
        "                               @@@    @@@@@@@     @@@     @@@@@@@@              ",
        "                    @@@@@@@@@@@@@      @@@@@       @@@  @@@@    @@@             ",
        "                   @@@      @@@@@       @@@         @@@@@@       @@@            ",
        "                  @@@         @@@        @@         @@@@         @@@            ",
        "         @@@@@@@@@@@@          @@        @          @@@         @@@     @@      ",
        "        @@@     @@@@@           @@           @@@    @@          @@@@@@@@@@@@@@  ",
        "       @@@         @@@           @@          @@@               @@@@@        @@@@",
        "       @@@           @@                     @@@@              @@@            @@@",
        "      @@@@@            @@                   @@@@                             @@@",
        "   @@@@@@  @@                @@         @   @@@                            @@@@ ",
        "  @@@                         @@       @@         @                     @@@@@@  ",
        " @@@                           @@     @@@        @@            @@@@@@@@@@@@@@@  ",
        "@@@       @@@@      @          @@@@  @@@@@     @@@        @      @@@@  @@@ @@@  ",
        "@@@       @@@@@@@    @@@       @@@@@@@@@@@@@@@@@@@       @@        @@@ @@@      ",
        "@@@        @@@@@ @@@  @@@@@  @@@@ @@@@  @@@@@@@@@@      @@@@        @@@         ",
        "@@@@            @@@@@@@@@@@@@@@@  @@@   @@@ @@  @@@@@@@@@@@@         @@@        ",
        " @@@@          @@@@@@@@@@@@@@@@   @@@       @@   @@@@@@@@@@@@        @@@        ",
        "  @@@@@@     @@@@@   @@@     @@    @               @@  @@  @@@@    @@@@         ",
        "   @@@@@@@@@@@@@     @@@     @@                    @@  @@   @@@@@@@@@@@         ",
        "   @@@@@@@@@@@@      @@@     @@                   @@@  @     @@@@@@@@           ",
        "        @@  @@                                    @@@        @@  @@@            ",
        "        @   @@                                               @@  @@@            ",
        "           @@@                                                   @@@            ",
        "           @@@                                                                  ",
        ""
    ]
    splash_lines = [
        "--  ESP32 C5 Flasher --",
        "By AWOK",
        "Inspired from LordSkeletonMans ESP32 FZEasyFlasher",
        "Shout out to JCMK for the inspiration on setting up the C5",
        ""
    ]
    print(Fore.MAGENTA + "\n" + "\n".join(center(line) for line in logo_lines + splash_lines) + Style.RESET_ALL)

    # Wait for ESP32 device to show up as a new serial port
    existing_ports = set([port.device for port in serial.tools.list_ports.comports()])
    print(Fore.YELLOW + "Waiting for ESP32-C5 device to be connected..." + Style.RESET_ALL)
    while True:
        current_ports = set([port.device for port in serial.tools.list_ports.comports()])
        new_ports = current_ports - existing_ports
        if new_ports:
            serial_port = new_ports.pop()
            break
        time.sleep(0.5)
    print(Fore.GREEN + f"Detected ESP32-C5 on port: {serial_port}" + Style.RESET_ALL)

    # === Prefer merged.bin (flash at 0x0 — safest, avoids all offset mistakes) ===
    merged_bin = find_file(['*.merged.bin', 'merged.bin'], bins_dir)

    # Individual component bins (fallback)
    bootloader = find_file(['bootloader.bin'], bins_dir)
    partitions = find_file(['partition-table.bin', 'partitions.bin'], bins_dir)
    ota_data   = find_file(['ota_data_initial.bin'], bins_dir)

    # Main firmware: largest bin that is not bootloader, partition, OTA, or merged
    all_bins = glob.glob(os.path.join(bins_dir, "*.bin"))
    exclude = {bootloader, partitions, ota_data, merged_bin}
    firmware_bins = [f for f in all_bins if f not in exclude and os.path.isfile(f)]
    app_bin = max(firmware_bins, key=lambda f: os.path.getsize(f)) if firmware_bins else None

    # --- Print summary ---
    if merged_bin:
        print(Fore.CYAN + f"\n[MODE] Flashing merged binary (recommended)")
        print(f"Merged:       {merged_bin}\n" + Style.RESET_ALL)
    else:
        print(Fore.CYAN + f"\n[MODE] Flashing individual binaries")
        print(f"Bootloader:   {bootloader or 'NOT FOUND'}")
        print(f"Partitions:   {partitions or 'NOT FOUND'}")
        print(f"OTA Data:     {ota_data or 'NOT FOUND'}")
        print(f"App (main):   {app_bin or 'NOT FOUND'}\n" + Style.RESET_ALL)

        if not (bootloader and partitions and app_bin):
            print(Fore.RED + "Missing files. Need bootloader.bin + partition-table.bin + app .bin." + Style.RESET_ALL)
            print(Fore.YELLOW + "TIP: Copy the *.merged.bin from your arduino build output for the easiest flash." + Style.RESET_ALL)
            exit(1)

    confirm = input(Fore.YELLOW + "Ready to flash these files to ESP32-C5? (y/N): " + Style.RESET_ALL)
    if confirm.strip().lower() != 'y':
        print("Aborting.")
        exit(0)

    # === Build esptool command ===
    # ESP32-C5 (RISC-V) requires flash_mode=dio
    # Bootloader offset for C5: 0x2000 (confirmed via BOOTLOADER_OFFSET_IN_FLASH in sdkconfig)
    base_args = [
        '--chip', 'esp32c5',
        '--port', serial_port,
        '--baud', '921600',
        '--before', 'default_reset',
        '--after', 'hard_reset',
        'write_flash',
        '--flash_mode', 'dio',
        '--flash_freq', '80m',
        '--flash_size', '4MB',
        '-z',
    ]

    if merged_bin:
        # Single merged image at offset 0x0 — includes bootloader, partitions, and app
        esptool_args = base_args + ['0x0', merged_bin]
        print(Fore.YELLOW + "Flashing merged binary at offset 0x0..." + Style.RESET_ALL)
    else:
        # Individual bins at their correct C5 offsets
        # Bootloader: 0x2000 | Partitions: 0x8000 | OTA data: 0xD000 | App: 0x10000
        esptool_args = base_args + [
            '0x2000', bootloader,
            '0x8000', partitions,
        ]
        if ota_data:
            esptool_args += ['0xD000', ota_data]
        esptool_args += ['0x10000', app_bin]
        print(Fore.YELLOW + "Flashing individual binaries at correct C5 offsets..." + Style.RESET_ALL)

    try:
        esptool.main(esptool_args)
        print(Fore.GREEN + "Flashing complete!" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Flashing failed: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()