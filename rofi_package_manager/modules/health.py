#!/usr/bin/env python3
"""
modules/health.py
─────────────────
Package health checks and system integrity analysis.

Functions:
    check_package_integrity()   → run pacman -Qk, return broken package list
    list_orphans()              → packages with no dependents
    list_foreign_packages()     → AUR/manually-installed packages
    get_health_summary()        → dict with all health metrics
    format_health_lines()       → Rofi-displayable lines for the dashboard
"""

from utils.commands import run_command, tool_available
from utils.cache import cache


def check_package_integrity() -> dict:
    """
    Run `pacman -Qk` (check package file integrity).

    Returns:
        {
            "ok":      int  — packages with all files present,
            "broken":  list[str]  — package names with missing/altered files,
            "details": list[str]  — raw warning lines from pacman
        }
    """
    ok, out = run_command(["pacman", "-Qk", "--nocolor"], timeout=120)
    # pacman -Qk exits 0 even with warnings; issues appear in stdout
    details: list[str] = []
    broken: list[str] = []

    for line in (out or "").splitlines():
        line = line.strip()
        if "warning" in line.lower() or "error" in line.lower():
            details.append(line)
            # Extract package name: usually "warning: <pkg>: ..."
            parts = line.split(":")
            if len(parts) >= 2:
                pkg = parts[1].strip().split()[0]
                if pkg not in broken:
                    broken.append(pkg)

    # Count total packages
    _, all_out = run_command(["pacman", "-Qq"])
    total = len(all_out.splitlines()) if all_out else 0

    return {
        "ok":      total - len(broken),
        "broken":  broken,
        "details": details,
        "total":   total,
    }


def list_orphans() -> list[str]:
    """
    Return list of orphaned packages (installed as deps, no longer needed).
    Uses `pacman -Qdtq`.
    """
    cached = cache.get("orphan_list")
    if cached is not None:
        return cached

    ok, out = run_command(["pacman", "-Qdtq"])
    orphans = out.splitlines() if ok and out else []
    cache.set("orphan_list", orphans, ttl=60)
    return orphans


def list_foreign_packages() -> list[dict]:
    """
    Return list of foreign (non-repo, typically AUR) packages.
    Uses `pacman -Qm`.

    Each entry: { "name": str, "version": str }
    """
    cached = cache.get("foreign_pkgs")
    if cached is not None:
        return cached

    ok, out = run_command(["pacman", "-Qm"])
    packages: list[dict] = []
    if ok and out:
        for line in out.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                packages.append({"name": parts[0], "version": parts[1]})

    cache.set("foreign_pkgs", packages, ttl=120)
    return packages


def list_explicitly_installed() -> list[dict]:
    """
    Return packages installed explicitly (not as dependencies).
    Uses `pacman -Qeq`.

    Each entry: { "name": str, "version": str }
    """
    ok, out = run_command(["pacman", "-Qe"])
    packages: list[dict] = []
    if ok and out:
        for line in out.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                packages.append({"name": parts[0], "version": parts[1]})
    return packages


def list_dependency_packages() -> list[dict]:
    """
    Return packages installed as dependencies.
    Uses `pacman -Qdq`.
    """
    ok, out = run_command(["pacman", "-Qd"])
    packages: list[dict] = []
    if ok and out:
        for line in out.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                packages.append({"name": parts[0], "version": parts[1]})
    return packages


def get_health_summary() -> dict:
    """
    Return a complete health snapshot.

    {
        "orphans":          int,
        "orphan_names":     list[str],
        "foreign":          int,
        "broken":           list[str],
        "total_packages":   int,
        "pacman_updates":   int,
        "aur_updates":      int,
        "flatpak_updates":  int,
    }
    """
    cached = cache.get("health_summary")
    if cached:
        return cached

    summary: dict = {
        "orphans":         0,
        "orphan_names":    [],
        "foreign":         0,
        "broken":          [],
        "total_packages":  0,
        "pacman_updates":  0,
        "aur_updates":     0,
        "flatpak_updates": 0,
    }

    # Orphans
    orphans = list_orphans()
    summary["orphans"] = len(orphans)
    summary["orphan_names"] = orphans

    # Foreign
    foreign = list_foreign_packages()
    summary["foreign"] = len(foreign)

    # Total packages
    _, out = run_command(["pacman", "-Qq"])
    if out:
        summary["total_packages"] = len(out.splitlines())

    # Updates (non-blocking: best-effort, don't slow down the menu)
    if tool_available("checkupdates"):
        _, upd_out = run_command(["checkupdates"])
        if upd_out:
            summary["pacman_updates"] = len(upd_out.splitlines())

    from config.settings import settings
    helper = settings.get("aur_helper", "yay")
    if tool_available(helper):
        ok, upd_out = run_command([helper, "-Qua"])
        if ok and upd_out:
            summary["aur_updates"] = len(upd_out.splitlines())

    if tool_available("flatpak"):
        ok, upd_out = run_command(["flatpak", "remote-ls", "--updates"])
        if ok and upd_out:
            summary["flatpak_updates"] = len(upd_out.splitlines())

    cache.set("health_summary", summary, ttl=120)
    return summary


def format_health_lines(summary: dict) -> list[str]:
    """Format a health summary dict into Rofi display lines."""
    total_updates = (
        summary.get("pacman_updates", 0)
        + summary.get("aur_updates", 0)
        + summary.get("flatpak_updates", 0)
    )

    def status_icon(count: int, good_when_zero: bool = True) -> str:
        if good_when_zero:
            return "✔" if count == 0 else "⚠"
        return "✔" if count > 0 else "✖"

    orphan_count  = summary.get("orphans", 0)
    foreign_count = summary.get("foreign", 0)
    broken_count  = len(summary.get("broken", []))

    lines = [
        "─" * 38,
        f"  {'Total Packages':<28}{summary.get('total_packages', 0)}",
        "─" * 38,
        f"  {status_icon(orphan_count)}  {'Orphaned Packages':<26}{orphan_count}",
        f"  {status_icon(broken_count)}  {'Broken Packages':<26}{broken_count}",
        f"  {'ℹ'  }  {'Foreign / AUR Packages':<26}{foreign_count}",
        "─" * 38,
        f"  {'🔄'  }  {'Available Updates':<26}{total_updates}",
        f"      {'↳ Official (Pacman)':<24}{summary.get('pacman_updates', 0)}",
        f"      {'↳ AUR':<24}{summary.get('aur_updates', 0)}",
        f"      {'↳ Flatpak':<24}{summary.get('flatpak_updates', 0)}",
    ]

    if broken_count > 0:
        lines += ["─" * 38, "  ⚠ Broken packages:"]
        for pkg in summary.get("broken", [])[:10]:
            lines.append(f"      • {pkg}")

    return lines
