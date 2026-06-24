<div align="center">

<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/main_menu.png" width="700" alt="Rofi Package Manager — Main Menu"/>

<h1>Rofi Package Manager</h1>

<p><strong>A unified, terminal-free package management frontend for Arch Linux.</strong><br/>
Manage Pacman, AUR, and Flatpak packages from a single keyboard-driven Rofi interface.</p>

<p>
  <img src="https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Rofi-6E40C9?style=for-the-badge&logo=linux&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-3b82f6?style=for-the-badge"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Pacman-supported-00B4D8?style=flat-square"/>
  <img src="https://img.shields.io/badge/AUR-supported-1793D1?style=flat-square"/>
  <img src="https://img.shields.io/badge/Flatpak-supported-4A90D9?style=flat-square"/>
</p>

</div>

---

## Screenshots

<div align="center">

<table>
<tr>
<td align="center" width="50%">
<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/search.png" width="100%" alt="Package Search"/>
<br/><sub><b>Unified Package Search</b></sub>
</td>
<td align="center" width="50%">
<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/pkg_info.png" width="100%" alt="Package Info"/>
<br/><sub><b>Package Info Card</b></sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/updates.png" width="100%" alt="Update Center"/>
<br/><sub><b>Update Center</b></sub>
</td>
<td align="center" width="50%">
<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/health.png" width="100%" alt="Health Dashboard"/>
<br/><sub><b>Health Dashboard</b></sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/cleanup.png" width="100%" alt="System Cleanup"/>
<br/><sub><b>System Cleanup</b></sub>
</td>
<td align="center" width="50%">
<img src="https://raw.githubusercontent.com/Mohit-Bhole/RofiBasedPackageManager/main/screenshots/main_menu.png" width="100%" alt="Main Menu"/>
<br/><sub><b>Main Menu</b></sub>
</td>
</tr>
</table>

</div>

---

## What is this?

You launch **`rofi-package-manager`** and you get a full package management dashboard — right inside Rofi. No terminal. No typing commands. No forgetting flags.

One interface for:

- **Pacman** — official Arch repos
- **AUR** — via `yay` or `paru`
- **Flatpak** — any remote

---

## Features

| Feature | Details |
|--------|---------|
|  **Unified Search** | Searches Pacman, AUR (HTTP API — no helper needed), and Flatpak **in parallel** |
|  **Browse Installed** | All packages, official, AUR/foreign, Flatpak, explicit, dependency-only, orphans |
|  **Install** | Pacman, AUR helper (`yay`/`paru`/`trizen`), Flatpak — with optional confirm dialogs |
|  **Remove** | Auto-detects source — runs `pacman -Rns` (removes deps + config files) |
|  **Update Center** | Check and apply updates for each source independently, or all at once |
|  **Package Info** | Version, repo, size, install date, packager, dependencies, required-by |
|  **Dependency Explorer** | `pactree` integration — visual tree + reverse-dependency lookup |
|  **Health Dashboard** | Orphan count, broken packages (`pacman -Qk`), foreign package list |
|  **System Cleanup** | Remove orphans, clean pacman / AUR / Flatpak caches — one click |
|  **Statistics** | Per-source package counts, total install size, pending update count |
|  **Settings** | AUR helper, confirm dialogs, cache TTL — all editable inside the app |
|  **Bundled Theme** | Dark Rofi theme: `#0d1117` background, `#58a6ff` accent, JetBrains Mono |

---

## Dependencies

### Required
| Package | Why |
|---------|-----|
| `python3` ≥ 3.10 | The entire app is Python |
| `rofi` | The UI layer |
| `pacman` | Core package management |

### Recommended
| Package | Install | Why |
|---------|---------|-----|
| `yay` or `paru` | AUR | AUR install, remove, update |
| `flatpak` | `sudo pacman -S flatpak` | Flatpak support |
| `pacman-contrib` | `sudo pacman -S pacman-contrib` | `checkupdates` + `pactree` |
| `expac` | `sudo pacman -S expac` | Package size statistics |

### Optional
| Package | Why |
|---------|-----|
| `polkit` | Graphical `pkexec` for privilege escalation |
| `snap` + `snapd` | Snap package detection |

---

## Installation

```bash
git clone https://github.com/Mohit-Bhole/RofiBasedPackageManager.git
cd RofiBasedPackageManager
chmod +x install.sh
./install.sh
```

The installer:
- Copies the project to `/usr/local/lib/rofi-package-manager/`
- Symlinks the launcher → `/usr/local/bin/rofi-package-manager`
- Creates a default config at `~/.config/rofi-package-manager/config.json`

### Run it

```bash
rofi-package-manager
```

Or bind it to a hotkey. Examples:

**Hyprland** (`hyprland.conf`):
```ini
bind = $mainMod, P, exec, rofi-package-manager
```

**i3 / Sway** (`config`):
```
bindsym $mod+p exec rofi-package-manager
```

**bspwm** (`sxhkdrc`):
```
super + p
    rofi-package-manager
```

---

## Configuration

Config file: `~/.config/rofi-package-manager/config.json`

```json
{
  "aur_helper":        "yay",
  "show_descriptions": true,
  "confirm_removal":   true,
  "confirm_install":   true,
  "cache_ttl_seconds": 300,
  "theme":             "default",
  "terminal":          null
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `aur_helper` | `"yay"` | AUR helper binary (`yay`, `paru`, `trizen`) |
| `show_descriptions` | `true` | Show package descriptions in search results |
| `confirm_removal` | `true` | Yes/No dialog before removing a package |
| `confirm_install` | `true` | Yes/No dialog before installing a package |
| `cache_ttl_seconds` | `300` | How long to cache package lists (seconds) |
| `theme` | `"default"` | Rofi theme name (filename inside `themes/`) |
| `terminal` | `null` | Override terminal emulator (auto-detected if null) |

> All settings are also editable live from **⚙ Settings** inside the app.

---

## Architecture

`main.py` handles **only menus and navigation**. All logic lives in separate modules.

```
rofi_package_manager/
│
├── main.py                  # Entry point — routing ONLY, zero business logic
│
├── modules/
│   ├── search.py            # Parallel search: Pacman, AUR HTTP API, Flatpak
│   ├── install.py           # Install via pacman / AUR helper / flatpak
│   ├── remove.py            # Remove with auto source-detection
│   ├── update.py            # Check + apply updates for all sources
│   ├── info.py              # Package info, dependency trees, system stats
│   ├── source.py            # detect_source() — which PM owns a package?
│   ├── health.py            # Orphans, integrity check, health dashboard
│   └── cleanup.py           # Cache cleaning, orphan removal
│
├── utils/
│   ├── rofi.py              # ALL Rofi subprocess calls — single source of truth
│   ├── commands.py          # run_command, run_privileged, tool_available
│   └── cache.py             # Two-level TTL cache (memory + disk)
│
├── config/
│   └── settings.py          # Reads/writes ~/.config/rofi-package-manager/config.json
│
├── themes/
│   └── default.rasi         # Bundled dark Rofi theme
│
├── rofi-package-manager     # Executable launcher (symlinked to /usr/local/bin)
└── install.sh               # System installer script
```

### Design Principles

- **`main.py` has zero business logic** — it only routes menu choices to modules
- **All Rofi calls go through `utils/rofi.py`** — nothing else calls subprocess with `rofi` directly
- **`BACK` / `EXIT` sentinels** are defined once, imported everywhere — never hardcoded strings
- **Cache is invalidated by the module that mutates state** — install/remove/update each clear their own keys
- **AUR search uses the HTTP API** — `urllib` only, no external dependencies, no AUR helper needed to search

---

## Privilege Escalation

Install, remove, and update operations that need `sudo` open a **real terminal window**. You type your password there naturally, the terminal closes when done.

Resolution order:
1. `pkexec` (polkit graphical dialog) — if available
2. Auto-detected terminal: `kitty` → `alacritty` → `xterm` → `gnome-terminal` → `konsole`

No passwords are stored anywhere.

---

## Caching

Package lists are cached under `~/.cache/rofi-package-manager/` with a configurable TTL (default 5 min). Navigation between menus is instant — no re-running `pacman -Q` every time.

**Two cache levels:**
- **Memory** — in-process dict, fastest, gone on exit
- **Disk** — JSON files, persists between launches, respects TTL

Clear anytime: **⚙ Settings → Clear Package Cache**

---

## Roadmap

- [x] Unified Pacman + AUR + Flatpak search (parallel)
- [x] Full package info card with metadata
- [x] Dependency tree explorer (`pactree`)
- [x] Health dashboard — orphans, broken packages
- [x] System cleanup — caches + orphan removal
- [x] Statistics screen
- [x] Two-level TTL cache
- [x] Custom bundled Rofi theme
- [ ] Snap support
- [ ] Cargo package listing
- [ ] Rofi `modi` integration
- [ ] AUR PKGBUILD viewer
- [ ] Package changelog viewer
- [ ] AUR package on GitHub → submit to AUR helper

---

## Cntributing

PRs welcome! To add a new package manager or feature:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/snap-support`
3. Keep `main.py` logic-free — add a new module in `modules/`
4. Open a PR with screenshots if it changes the UI

---

## License

[MIT](LICENSE) © 2026 Mohit Bhole

---

<div align="center">

**Built for Arch Linux power users who live in Rofi.**

*If this helped you — drop a ⭐ It means a lot.*

</div>
