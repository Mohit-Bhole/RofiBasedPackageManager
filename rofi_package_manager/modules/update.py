#!/usr/bin/env python3
"""
modules/update.py
─────────────────
Check for available updates and apply them.

Check functions return lists of pending updates without installing anything.
Apply functions open a terminal window to run the actual upgrade.
"""

from utils.commands import run_command, run_in_terminal, tool_available
from config.settings import settings
from utils.cache import cache


# ── Check functions (read-only) ───────────────────────────────────────────────

def check_pacman_updates() -> list[dict]:
    """
    Return list of pending official updates via `checkupdates`.

    Each entry: { "name": str, "current": str, "new": str }

    checkupdates exits 1 when there are no updates — that's expected behaviour,
    not an error. We handle the output regardless of exit code.
    """
    cached = cache.get("updates_pacman")
    if cached is not None:
        return cached

    # checkupdates doesn't need root and uses a safe temp DB
    _, out = run_command(["checkupdates"])
    results = _parse_update_lines(out, source="Pacman")
    cache.set("updates_pacman", results, ttl=120)
    return results


def check_aur_updates() -> list[dict]:
    """
    Return list of pending AUR updates via `<helper> -Qua`.

    Each entry: { "name": str, "current": str, "new": str, "source": "AUR" }
    """
    cached = cache.get("updates_aur")
    if cached is not None:
        return cached

    helper = _get_aur_helper()
    if not helper:
        return []

    ok, out = run_command([helper, "-Qua"], timeout=60)
    results = _parse_update_lines(out, source="AUR") if out else []
    cache.set("updates_aur", results, ttl=120)
    return results


def check_flatpak_updates() -> list[dict]:
    """
    Return list of pending Flatpak updates via `flatpak remote-ls --updates`.

    Each entry: { "name": str, "current": str, "new": str, "source": "Flatpak" }
    """
    if not tool_available("flatpak"):
        return []

    cached = cache.get("updates_flatpak")
    if cached is not None:
        return cached

    ok, out = run_command(
        ["flatpak", "remote-ls", "--updates", "--columns=application,version"],
        timeout=30,
    )
    results: list[dict] = []
    if ok and out:
        for line in out.splitlines():
            parts = line.split()
            if parts:
                results.append({
                    "name":    parts[0],
                    "current": "",
                    "new":     parts[1] if len(parts) > 1 else "",
                    "source":  "Flatpak",
                })
    cache.set("updates_flatpak", results, ttl=120)
    return results


def check_all_updates() -> dict:
    """
    Return a combined dict of all pending updates.

    {
        "pacman":  [ { name, current, new, source } ],
        "aur":     [ ... ],
        "flatpak": [ ... ],
        "total":   int,
    }
    """
    pacman  = check_pacman_updates()
    aur     = check_aur_updates()
    flatpak = check_flatpak_updates()
    return {
        "pacman":  pacman,
        "aur":     aur,
        "flatpak": flatpak,
        "total":   len(pacman) + len(aur) + len(flatpak),
    }


def format_update_lines(updates: list[dict]) -> list[str]:
    """Format update dicts into Rofi display lines."""
    lines = []
    for u in updates:
        badge = {
            "Pacman":  "[Pacman] ",
            "AUR":     "[AUR]    ",
            "Flatpak": "[Flatpak]",
        }.get(u.get("source", ""), "[?]      ")

        name    = u.get("name", "")
        current = u.get("current", "")
        new     = u.get("new", "")

        if current and new:
            lines.append(f"{badge}  {name:<30} {current} → {new}")
        elif new:
            lines.append(f"{badge}  {name:<30} → {new}")
        else:
            lines.append(f"{badge}  {name}")
    return lines


# ── Apply functions (open terminal) ──────────────────────────────────────────

def update_pacman() -> tuple[bool, str]:
    """Full system upgrade via `sudo pacman -Syu`."""
    cache.clear()
    return run_in_terminal(
        ["sudo", "pacman", "-Syu"],
        title="System Upgrade (Pacman)",
    )


def update_aur() -> tuple[bool, str]:
    """Full AUR upgrade via `<helper> -Syu`."""
    helper = _get_aur_helper()
    if not helper:
        return False, "No AUR helper found."
    cache.clear()
    return run_in_terminal(
        [helper, "-Syu"],
        title=f"AUR Upgrade (via {helper})",
    )


def update_flatpak() -> tuple[bool, str]:
    """Update all Flatpak apps via `flatpak update -y`."""
    if not tool_available("flatpak"):
        return False, "Flatpak is not installed."
    cache.invalidate("flatpak_apps")
    cache.invalidate("updates_flatpak")
    cache.invalidate("system_stats")
    return run_in_terminal(
        ["flatpak", "update", "-y"],
        title="Flatpak Update",
    )


def update_everything() -> tuple[bool, str]:
    """
    Update everything — Pacman, AUR, and Flatpak in one terminal session.
    Uses the AUR helper (which also upgrades official packages) + flatpak.
    """
    helper = _get_aur_helper()
    cache.clear()

    cmds: list[str] = []
    if helper:
        cmds.append(f"{helper} -Syu")
    else:
        cmds.append("sudo pacman -Syu")

    if tool_available("flatpak"):
        cmds.append("flatpak update -y")

    # Chain commands with && so Flatpak only runs if pacman/yay succeeded
    shell_script = " && ".join(cmds)
    return run_in_terminal(
        ["bash", "-c", shell_script],
        title="Full System Update",
    )


# ── Internal ──────────────────────────────────────────────────────────────────

def _parse_update_lines(output: str, source: str) -> list[dict]:
    """
    Parse update lines of the form:
        name current_version -> new_version
        name current_version => new_version
    """
    results: list[dict] = []
    if not output:
        return results

    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] in ("->", "=>"):
            results.append({
                "name":    parts[0],
                "current": parts[1],
                "new":     parts[3],
                "source":  source,
            })
        elif len(parts) >= 2:
            results.append({
                "name":    parts[0],
                "current": parts[1] if len(parts) > 1 else "",
                "new":     parts[3] if len(parts) > 3 else "",
                "source":  source,
            })
    return results


def _get_aur_helper() -> str:
    helper = settings.get("aur_helper", "yay")
    if tool_available(helper):
        return helper
    for h in ("yay", "paru", "trizen"):
        if tool_available(h):
            return h
    return ""
