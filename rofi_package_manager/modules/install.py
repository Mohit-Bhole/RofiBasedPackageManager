#!/usr/bin/env python3
"""
modules/install.py
──────────────────
Install packages via Pacman, AUR helper, Flatpak, or Snap.

All install functions open a terminal window so the user can interact
with confirmations, password prompts, and build output directly.
"""

from utils.commands import run_command, run_in_terminal, run_privileged, tool_available
from config.settings import settings
from utils.cache import cache


def install(name: str, source: str = "") -> tuple[bool, str]:
    """
    Install a package, auto-detecting the source if not given.

    Args:
        name:   Package name or Flatpak app-id.
        source: "Pacman" | "AUR" | "Flatpak" | "Snap" | "" (auto)

    Returns:
        (success, message)
    """
    if not source:
        source = _guess_source(name)

    if source == "Pacman":
        return install_pacman(name)
    elif source == "AUR":
        return install_aur(name)
    elif source == "Flatpak":
        return install_flatpak(name)
    elif source == "Snap":
        return install_snap(name)
    else:
        # Default to AUR helper (handles both official and AUR)
        return install_aur(name)


def install_pacman(name: str) -> tuple[bool, str]:
    """
    Install via `sudo pacman -S --noconfirm <name>`.
    Opens a terminal for password entry and output.
    """
    cache.invalidate_prefix("pacman_")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["sudo", "pacman", "-S", "--needed", name],
        title=f"Installing {name} (Pacman)",
    )


def install_aur(name: str) -> tuple[bool, str]:
    """
    Install via the configured AUR helper (`yay -S <name>` by default).
    Opens a terminal — AUR builds may need interaction.
    """
    helper = _get_aur_helper()
    if not helper:
        return False, "No AUR helper found. Install yay or paru."
    cache.invalidate_prefix("aur_")
    cache.invalidate_prefix("pacman_")
    cache.invalidate("system_stats")
    return run_in_terminal(
        [helper, "-S", name],
        title=f"Installing {name} (AUR via {helper})",
    )


def install_flatpak(app_id: str) -> tuple[bool, str]:
    """
    Install via `flatpak install --user -y <app_id>`.
    """
    if not tool_available("flatpak"):
        return False, "Flatpak is not installed."
    cache.invalidate("flatpak_apps")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["flatpak", "install", "--user", "-y", app_id],
        title=f"Installing {app_id} (Flatpak)",
    )


def install_snap(name: str) -> tuple[bool, str]:
    """
    Install via `snap install <name>`.
    Requires snapd to be running.
    """
    if not tool_available("snap"):
        return False, "Snap is not installed."
    cache.invalidate("snap_pkg_names")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["sudo", "snap", "install", name],
        title=f"Installing {name} (Snap)",
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_aur_helper() -> str:
    helper = settings.get("aur_helper", "yay")
    if tool_available(helper):
        return helper
    for h in ("yay", "paru", "trizen"):
        if tool_available(h):
            return h
    return ""


def _guess_source(name: str) -> str:
    """
    Heuristic source guess for uninstalled packages:
    - Flatpak app-ids contain dots (e.g. org.mozilla.firefox)
    - Everything else defaults to AUR (the AUR helper handles both
      official repos and AUR transparently)
    """
    if "." in name and name.count(".") >= 2:
        return "Flatpak"
    return "AUR"
