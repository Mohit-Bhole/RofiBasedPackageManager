# RofiBasedPackageManager

A lightweight package manager frontend for Arch Linux built with **Python** and **Rofi**.

RofiBasedPackageManager provides a simple menu-driven interface for viewing and managing packages installed through different package managers without opening a terminal.

## Features (v0.1)

### Pacman

* View all installed packages
* View explicitly installed packages
* View dependency packages
* View orphan packages
* Check official repository updates
* Check AUR updates

### Flatpak

* View installed Flatpak applications
* Check available Flatpak updates

### Interface

* Fast Rofi-based navigation
* Keyboard-driven workflow
* Lightweight and minimal dependencies

## Screenshots

*Screenshots coming soon.*

## Requirements

* Python 3
* Rofi
* Pacman
* Yay (for AUR update checking)
* Flatpak (optional)

## Installation

Clone the repository:

```bash
git clone https://github.com/Mohit-Bhole/RofiBasedPackageManager.git
cd RofiBasedPackageManager
```

Make the setup script executable:

```bash
chmod +x setup.sh
./setup.sh
```

Or install dependencies manually:

```bash
sudo pacman -S rofi python
```

## Usage

Run:

```bash
python GuiPackageManager.py
```

or

```bash
chmod +x GuiPackageManager.py
./GuiPackageManager.py
```

## Roadmap

### v0.2

* Package information viewer
* Display package metadata using `pacman -Qi`
* View package versions and installation details

### v0.3

* Dependency tree viewer
* Reverse dependency viewer
* Package file listing

### v0.4

* Package removal support
* Package reinstall support
* Confirmation dialogs

### Future Goals

* Support for Paru
* Support for Snap packages
* Search functionality
* Package statistics dashboard
* Installation source detection
* Package size analysis
* GUI package management actions

## Project Goal

The long-term goal of this project is to provide a lightweight Arch Linux package management interface capable of managing packages installed through:

* Pacman
* Yay
* Paru
* Flatpak
* Snap

while keeping the speed and simplicity of Rofi.

## License

This project is licensed under the MIT License.
