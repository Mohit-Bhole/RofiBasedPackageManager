#!/usr/bin/env python3

import subprocess


def rofi_menu(options, prompt):

    result = subprocess.run(
        ["rofi", "-dmenu", "-p", prompt],
        input=options,
        capture_output=True,
        text=True
    )

    return result.stdout.strip()


# ==========================
# MAIN MENU
# ==========================

package_manager = rofi_menu(
    "Pacman\nFlatpak",
    "Choose Package Manager"
)

# ==========================
# PACMAN
# ==========================

if package_manager.lower() == "pacman":

    pacman_options = (
        "See All Packages\n"
        "See Explicit Packages\n"
        "See Dependency Packages\n"
        "See Orphans\n"
        "Check Official Updates\n"
        "Check AUR Updates"
    )

    choice = rofi_menu(
        pacman_options,
        "Pacman"
    )

    # ----------------------
    # All packages
    # ----------------------

    if choice == "See All Packages":

        packages = subprocess.run(
            ["pacman", "-Qq"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            packages.stdout,
            "All Packages"
        )

    # ----------------------
    # Explicit packages
    # ----------------------

    elif choice == "See Explicit Packages":

        packages = subprocess.run(
            ["pacman", "-Qeq"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            packages.stdout,
            "Explicit Packages"
        )

    # ----------------------
    # Dependency packages
    # ----------------------

    elif choice == "See Dependency Packages":

        packages = subprocess.run(
            ["pacman", "-Qdq"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            packages.stdout,
            "Dependencies"
        )

    # ----------------------
    # Orphans
    # ----------------------

    elif choice == "See Orphans":

        packages = subprocess.run(
            ["pacman", "-Qdtq"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            packages.stdout,
            "Orphans"
        )

    # ----------------------
    # Official Updates
    # ----------------------

    elif choice == "Check Official Updates":

        updates = subprocess.run(
            ["checkupdates"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            updates.stdout,
            "Official Updates"
        )

    # ----------------------
    # AUR Updates
    # ----------------------

    elif choice == "Check AUR Updates":

        updates = subprocess.run(
            ["yay", "-Qua"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            updates.stdout,
            "AUR Updates"
        )

# ==========================
# FLATPAK
# ==========================

elif package_manager.lower() == "flatpak":

    flatpak_options = (
        "See Installed Flatpaks\n"
        "Check Flatpak Updates"
    )

    choice = rofi_menu(
        flatpak_options,
        "Flatpak"
    )

    # ----------------------
    # Installed Flatpaks
    # ----------------------

    if choice == "See Installed Flatpaks":

        packages = subprocess.run(
            ["flatpak", "list", "--app"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            packages.stdout,
            "Installed Flatpaks"
        )

    # ----------------------
    # Updates
    # ----------------------

    elif choice == "Check Flatpak Updates":

        updates = subprocess.run(
            ["flatpak", "remote-ls", "--updates"],
            capture_output=True,
            text=True
        )

        rofi_menu(
            updates.stdout,
            "Flatpak Updates"
        )
