#!/usr/bin/env python3
"""
modules/remove.py
─────────────────
Remove packages via Pacman, AUR helper, Flatpak, or Snap.

All removal functions auto-detect the package source when possible,
and open a terminal for password entry / confirmation.
"""

from utils.commands import run_command, run_in_terminal, tool_available
from modules.source import detect_source
from config.settings import settings
from utils.cache import cache


def remove(name: str, source: str = "") -> tuple[bool, str]:
    """
    Remove a package, auto-detecting source if not provided.

    Args:
        name:   Package name or Flatpak app-id.
        source: "Pacman" | "AUR" | "Flatpak" | "Snap" | "" (auto)

    Returns:
        (success, message)
    """
    if not source:
        source = detect_source(name)

    if source == "Flatpak":
        return remove_flatpak(name)
    elif source == "Snap":
        return remove_snap(name)
    elif source in ("Pacman", "AUR"):
        return remove_pacman(name)
    else:
        # Last resort — try pacman
        return remove_pacman(name)


def remove_pacman(name: str) -> tuple[bool, str]:
    """
    Remove via `sudo pacman -Rns <name>`.
    -Rns removes the package, its unneeded dependencies, and its config files.
    """
    cache.invalidate_prefix("pacman_")
    cache.invalidate_prefix("aur_")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["sudo", "pacman", "-Rns", name],
        title=f"Removing {name} (Pacman)",
    )


def remove_aur(name: str) -> tuple[bool, str]:
    """
    Remove an AUR package via the configured AUR helper.
    Equivalent to remove_pacman since AUR packages are managed by pacman.
    """
    helper = _get_aur_helper()
    if helper:
        cache.invalidate_prefix("aur_")
        cache.invalidate_prefix("pacman_")
        cache.invalidate("system_stats")
        return run_in_terminal(
            [helper, "-Rns", name],
            title=f"Removing {name} (via {helper})",
        )
    return remove_pacman(name)


def remove_flatpak(app_id: str) -> tuple[bool, str]:
    """
    Remove via `flatpak uninstall --user -y <app_id>`.
    """
    if not tool_available("flatpak"):
        return False, "Flatpak is not installed."
    cache.invalidate("flatpak_apps")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["flatpak", "uninstall", "--user", "-y", app_id],
        title=f"Removing {app_id} (Flatpak)",
    )


def remove_snap(name: str) -> tuple[bool, str]:
    """Remove via `snap remove <name>`."""
    if not tool_available("snap"):
        return False, "Snap is not installed."
    cache.invalidate("snap_pkg_names")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["sudo", "snap", "remove", name],
        title=f"Removing {name} (Snap)",
    )


def remove_orphans() -> tuple[bool, str]:
    """
    Remove all orphaned packages.
    Runs: sudo pacman -Rns $(pacman -Qdtq)
    Returns (False, "no orphans") if the orphan list is empty.
    """
    ok, out = run_command(["pacman", "-Qdtq"])
    if not ok or not out.strip():
        return False, "No orphans to remove."

    orphans = out.strip().split()
    cache.invalidate_prefix("pacman_")
    cache.invalidate("system_stats")

    return run_in_terminal(
        ["sudo", "pacman", "-Rns"] + orphans,
        title=f"Removing {len(orphans)} orphan(s)",
    )


# ── Internal ──────────────────────────────────────────────────────────────────

def _get_aur_helper() -> str:
    helper = settings.get("aur_helper", "yay")
    if tool_available(helper):
        return helper
    for h in ("yay", "paru", "trizen"):
        if tool_available(h):
            return h
    return ""
