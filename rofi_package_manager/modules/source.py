#!/usr/bin/env python3
"""
modules/source.py
─────────────────
Detect which package manager owns an installed package.

detect_source(name) returns one of:
    "Pacman"   — official repo package
    "AUR"      — foreign/AUR package (pacman -Qm)
    "Flatpak"  — installed Flatpak app
    "Snap"     — snap package (if snap is available)
    "Unknown"  — not found in any source
"""

from utils.commands import run_command, tool_available
from utils.cache import cache


def detect_source(package_name: str) -> str:
    """
    Identify which package manager owns `package_name`.

    Checks are ordered fastest-first:
      1. Flatpak  (exact app-id or name match)
      2. AUR      (pacman -Qm lists foreign packages)
      3. Pacman   (pacman -Q lists all installed repo packages)
      4. Snap     (snap list — only if snap is available)

    Returns a source label string.
    """
    name = package_name.strip()
    if not name:
        return "Unknown"

    # ── Flatpak ──────────────────────────────────────────────────────────────
    if tool_available("flatpak"):
        flatpak_apps = _get_flatpak_apps()
        for app_id, display_name in flatpak_apps:
            if (
                name.lower() == app_id.lower()
                or name.lower() == display_name.lower()
                or name.lower() in app_id.lower()
            ):
                return "Flatpak"

    # ── AUR (foreign packages) ────────────────────────────────────────────────
    aur_pkgs = _get_aur_packages()
    if name in aur_pkgs:
        return "AUR"

    # ── Pacman (official repos) ───────────────────────────────────────────────
    pacman_pkgs = _get_pacman_packages()
    if name in pacman_pkgs:
        return "Pacman"

    # ── Snap ─────────────────────────────────────────────────────────────────
    if tool_available("snap"):
        snap_pkgs = _get_snap_packages()
        if name in snap_pkgs:
            return "Snap"

    return "Unknown"


def get_all_installed() -> list[dict]:
    """
    Return a unified list of all installed packages across all sources.
    Each entry is a dict:
        {
            "name":    str,
            "source":  "Pacman" | "AUR" | "Flatpak" | "Snap",
            "version": str,
        }
    """
    results: list[dict] = []

    # Pacman (official)
    ok, out = run_command(["pacman", "-Qn"])
    if ok:
        for line in out.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                results.append({"name": parts[0], "version": parts[1], "source": "Pacman"})

    # AUR / foreign
    ok, out = run_command(["pacman", "-Qm"])
    if ok:
        for line in out.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                results.append({"name": parts[0], "version": parts[1], "source": "AUR"})

    # Flatpak
    if tool_available("flatpak"):
        ok, out = run_command(
            ["flatpak", "list", "--app", "--columns=application,name,version"]
        )
        if ok:
            for line in out.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    results.append({
                        "name":    parts[1].strip() if len(parts) > 1 else parts[0],
                        "version": parts[2].strip() if len(parts) > 2 else "",
                        "source":  "Flatpak",
                        "app_id":  parts[0].strip(),
                    })

    # Snap
    if tool_available("snap"):
        ok, out = run_command(["snap", "list"])
        if ok:
            for line in out.splitlines()[1:]:  # skip header
                parts = line.split()
                if parts:
                    results.append({"name": parts[0], "version": parts[1] if len(parts) > 1 else "", "source": "Snap"})

    return results


# ── Internal cached fetchers ──────────────────────────────────────────────────

def _get_flatpak_apps() -> list[tuple[str, str]]:
    """Return list of (app_id, display_name) for installed Flatpaks."""
    cached = cache.get("flatpak_apps")
    if cached is not None:
        return cached

    ok, out = run_command(["flatpak", "list", "--app", "--columns=application,name"])
    apps: list[tuple[str, str]] = []
    if ok:
        for line in out.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                apps.append((parts[0].strip(), parts[1].strip()))
            elif parts:
                apps.append((parts[0].strip(), parts[0].strip()))

    cache.set("flatpak_apps", apps)
    return apps


def _get_aur_packages() -> set[str]:
    """Return set of AUR/foreign package names."""
    cached = cache.get("aur_pkg_names")
    if cached is not None:
        return set(cached)

    ok, out = run_command(["pacman", "-Qmq"])
    names: set[str] = set(out.splitlines()) if ok else set()
    cache.set("aur_pkg_names", list(names))
    return names


def _get_pacman_packages() -> set[str]:
    """Return set of official-repo package names."""
    cached = cache.get("pacman_pkg_names")
    if cached is not None:
        return set(cached)

    ok, out = run_command(["pacman", "-Qnq"])
    names: set[str] = set(out.splitlines()) if ok else set()
    cache.set("pacman_pkg_names", list(names))
    return names


def _get_snap_packages() -> set[str]:
    """Return set of snap package names."""
    cached = cache.get("snap_pkg_names")
    if cached is not None:
        return set(cached)

    ok, out = run_command(["snap", "list"])
    names: set[str] = set()
    if ok:
        for line in out.splitlines()[1:]:
            parts = line.split()
            if parts:
                names.add(parts[0])

    cache.set("snap_pkg_names", list(names))
    return names
