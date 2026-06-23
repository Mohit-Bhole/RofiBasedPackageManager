#!/usr/bin/env python3
"""
modules/cleanup.py
──────────────────
System cleanup operations — orphan removal, cache cleaning, unused runtimes.

All destructive operations require explicit confirmation and open a terminal.
"""

from utils.commands import run_command, run_in_terminal, tool_available
from config.settings import settings
from utils.cache import cache


def remove_orphans() -> tuple[bool, str]:
    """
    Remove all orphaned packages (pacman -Qdtq | xargs sudo pacman -Rns).

    Returns (False, "no orphans") if the list is empty.
    """
    ok, out = run_command(["pacman", "-Qdtq"])
    orphans = out.strip().splitlines() if ok and out.strip() else []

    if not orphans:
        return False, "No orphaned packages found."

    cache.invalidate_prefix("pacman_")
    cache.invalidate("orphan_list")
    cache.invalidate("health_summary")
    cache.invalidate("system_stats")

    return run_in_terminal(
        ["sudo", "pacman", "-Rns"] + orphans,
        title=f"Removing {len(orphans)} orphan(s)",
    )


def clean_pacman_cache() -> tuple[bool, str]:
    """
    Remove all cached package files except the latest version.
    Runs: sudo pacman -Sc --noconfirm
    """
    return run_in_terminal(
        ["sudo", "pacman", "-Sc", "--noconfirm"],
        title="Cleaning Pacman Package Cache",
    )


def clean_pacman_cache_all() -> tuple[bool, str]:
    """
    Remove ALL cached package files (including all versions).
    Runs: sudo pacman -Scc --noconfirm
    (More aggressive than clean_pacman_cache)
    """
    return run_in_terminal(
        ["sudo", "pacman", "-Scc", "--noconfirm"],
        title="Cleaning Pacman Cache (All Versions)",
    )


def clean_aur_cache() -> tuple[bool, str]:
    """
    Clean the AUR helper's build cache.
    Runs: <helper> -Sc --noconfirm
    """
    helper = _get_aur_helper()
    if not helper:
        return False, "No AUR helper found."
    return run_in_terminal(
        [helper, "-Sc", "--noconfirm"],
        title=f"Cleaning AUR Cache (via {helper})",
    )


def clean_flatpak_unused() -> tuple[bool, str]:
    """
    Remove unused Flatpak runtimes and extensions.
    Runs: flatpak uninstall --unused -y
    """
    if not tool_available("flatpak"):
        return False, "Flatpak is not installed."
    cache.invalidate("flatpak_apps")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["flatpak", "uninstall", "--unused", "-y"],
        title="Removing Unused Flatpak Runtimes",
    )


def clean_all() -> tuple[bool, str]:
    """
    Run all cleanup operations in sequence:
      1. Remove orphans
      2. Clean pacman cache (latest version kept)
      3. Clean AUR cache
      4. Remove unused Flatpaks

    All steps run in a single terminal session.
    """
    cmds: list[str] = []

    # Orphans
    _, orphan_out = run_command(["pacman", "-Qdtq"])
    orphans = orphan_out.strip().split() if orphan_out.strip() else []
    if orphans:
        cmds.append("sudo pacman -Rns " + " ".join(orphans))

    # Pacman cache
    cmds.append("sudo pacman -Sc --noconfirm")

    # AUR cache
    helper = _get_aur_helper()
    if helper:
        cmds.append(f"{helper} -Sc --noconfirm")

    # Flatpak
    if tool_available("flatpak"):
        cmds.append("flatpak uninstall --unused -y")

    if not cmds:
        return False, "Nothing to clean."

    cache.clear()

    shell_script = "\n".join(cmds)
    return run_in_terminal(
        ["bash", "-c", shell_script],
        title="Full System Cleanup",
    )


def get_cache_sizes() -> dict:
    """
    Return estimated sizes of various package caches.

    {
        "pacman_cache_mb":  float,
        "aur_cache_mb":     float,
    }
    """
    import shutil

    result = {
        "pacman_cache_mb": 0.0,
        "aur_cache_mb":    0.0,
    }

    try:
        import os
        pacman_cache = "/var/cache/pacman/pkg"
        if os.path.isdir(pacman_cache):
            total = sum(
                f.stat().st_size
                for f in __import__("pathlib").Path(pacman_cache).rglob("*")
                if f.is_file()
            )
            result["pacman_cache_mb"] = round(total / (1024 * 1024), 1)
    except (OSError, PermissionError):
        pass

    return result


# ── Internal ──────────────────────────────────────────────────────────────────

def _get_aur_helper() -> str:
    helper = settings.get("aur_helper", "yay")
    if tool_available(helper):
        return helper
    for h in ("yay", "paru", "trizen"):
        if tool_available(h):
            return h
    return ""
