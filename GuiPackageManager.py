#!/usr/bin/env python3

import subprocess
import sys


def rofi_menu(options, prompt):

    result = subprocess.run(
        ["rofi", "-dmenu", "-p", prompt],
        input="\n".join(options),
        capture_output=True,
        text=True
    )

    return result.stdout.strip()


while True:

    main_choice = rofi_menu(
        [
            "Pacman",
            "Flatpak",
            "Exit"
        ],
        "Package Manager"
    )

    if main_choice in ["", "Exit"]:
        sys.exit()

    # =====================
    # PACMAN MENU
    # =====================

    if main_choice == "Pacman":

        while True:

            pacman_choice = rofi_menu(
                [
                    "← Back",
                    "See All Packages",
                    "See Explicit Packages",
                    "See Dependency Packages",
                    "See Orphans",
                    "Check Official Updates",
                    "Check AUR Updates",
                    "Exit"
                ],
                "Pacman"
            )

            if pacman_choice in ["", "Exit"]:
                sys.exit()

            if pacman_choice == "← Back":
                break

            elif pacman_choice == "See All Packages":

                packages = subprocess.run(
                    ["pacman", "-Qq"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    packages.stdout.splitlines(),
                    "All Packages"
                )

            elif pacman_choice == "See Explicit Packages":

                packages = subprocess.run(
                    ["pacman", "-Qeq"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    packages.stdout.splitlines(),
                    "Explicit Packages"
                )

            elif pacman_choice == "See Dependency Packages":

                packages = subprocess.run(
                    ["pacman", "-Qdq"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    packages.stdout.splitlines(),
                    "Dependencies"
                )

            elif pacman_choice == "See Orphans":

                packages = subprocess.run(
                    ["pacman", "-Qdtq"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    packages.stdout.splitlines(),
                    "Orphans"
                )

            elif pacman_choice == "Check Official Updates":

                updates = subprocess.run(
                    ["checkupdates"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    updates.stdout.splitlines(),
                    "Official Updates"
                )

            elif pacman_choice == "Check AUR Updates":

                updates = subprocess.run(
                    ["yay", "-Qua"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    updates.stdout.splitlines(),
                    "AUR Updates"
                )

    # =====================
    # FLATPAK MENU
    # =====================

    elif main_choice == "Flatpak":

        while True:

            flatpak_choice = rofi_menu(
                [
                    "← Back",
                    "See Installed Flatpaks",
                    "Check Flatpak Updates",
                    "Exit"
                ],
                "Flatpak"
            )

            if flatpak_choice in ["", "Exit"]:
                sys.exit()

            if flatpak_choice == "← Back":
                break

            elif flatpak_choice == "See Installed Flatpaks":

                packages = subprocess.run(
                    ["flatpak", "list", "--app"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    packages.stdout.splitlines(),
                    "Installed Flatpaks"
                )

            elif flatpak_choice == "Check Flatpak Updates":

                updates = subprocess.run(
                    ["flatpak", "remote-ls", "--updates"],
                    capture_output=True,
                    text=True
                )

                rofi_menu(
                    ["← Back"] +
                    updates.stdout.splitlines(),
                    "Flatpak Updates"
                )
