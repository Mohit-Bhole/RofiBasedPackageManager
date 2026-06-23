#!/usr/bin/env python3
"""
modules/info.py
───────────────
Package information, dependency trees, and system statistics.

Key functions:
    get_package_info(name, source)  → dict of package details
    get_dependency_tree(name)       → formatted tree string (pactree)
    get_reverse_deps(name)          → list of packages that need this one
    get_system_stats()              → dict of system-wide package stats
    format_info_fields(info)        → ordered dict for show_info_card()
"""

import re
from utils.commands import run_command, tool_available
from utils.cache import cache
from modules.source import detect_source


# ── Public API ────────────────────────────────────────────────────────────────

def get_package_info(name: str, source: str = "") -> dict:
    """
    Return a dict of package details.
    Auto-detects source if not provided.

    Keys always present (may be empty string):
        name, version, source, description, install_date,
        installed_size, repository, dependencies, required_by,
        url, packager, build_date, install_reason
    """
    if not source:
        source = detect_source(name)

    if source == "Flatpak":
        return _get_flatpak_info(name)
    elif source in ("Pacman", "AUR"):
        return _get_pacman_info(name, source)
    else:
        # Try pacman first, then flatpak
        info = _get_pacman_info(name, "Pacman")
        if not info.get("name"):
            info = _get_flatpak_info(name)
        return info


def get_dependency_tree(name: str, depth: int = 3) -> str:
    """
    Return a formatted dependency tree string using pactree.
    Falls back to pacman -Qi if pactree is unavailable.
    """
    if tool_available("pactree"):
        ok, out = run_command(["pactree", f"--depth={depth}", name], timeout=30)
        if ok and out:
            return out

    # Fallback: list deps from pacman -Qi
    ok, out = run_command(["pacman", "-Qi", name])
    if ok:
        for line in out.splitlines():
            if line.startswith("Depends On"):
                deps = line.split(":", 1)[1].strip()
                if deps == "None":
                    return f"{name}\n  (no dependencies)"
                dep_list = deps.split()
                tree = f"{name}\n"
                for dep in dep_list:
                    tree += f"  ├── {dep}\n"
                return tree

    return f"(pactree not available — install pacman-contrib)"


def get_reverse_deps(name: str) -> list[str]:
    """
    Return list of packages that depend on `name` (required-by).
    Uses pactree -r if available, else parses pacman -Qi.
    """
    if tool_available("pactree"):
        ok, out = run_command(["pactree", "-r", "--depth=1", name], timeout=30)
        if ok and out:
            # First line is the package itself, rest are reverse deps
            lines = out.splitlines()[1:]
            return [l.strip().lstrip("├─└│ ") for l in lines if l.strip()]

    # Fallback: pacman -Qi Required By
    ok, out = run_command(["pacman", "-Qi", name])
    if ok:
        for line in out.splitlines():
            if line.startswith("Required By"):
                val = line.split(":", 1)[1].strip()
                if val == "None":
                    return []
                return val.split()
    return []


def get_system_stats() -> dict:
    """
    Return a dict of system-wide package statistics.

    Keys:
        total, pacman_official, aur_foreign, flatpak, snap,
        orphans, available_updates_pacman, available_updates_aur,
        available_updates_flatpak, total_installed_size_mb
    """
    cached = cache.get("system_stats")
    if cached:
        return cached

    stats: dict = {
        "total":                    0,
        "pacman_official":          0,
        "aur_foreign":              0,
        "flatpak":                  0,
        "snap":                     0,
        "orphans":                  0,
        "available_updates_pacman": 0,
        "available_updates_aur":    0,
        "available_updates_flatpak": 0,
        "total_installed_size_mb":  0,
    }

    # Official pacman packages
    ok, out = run_command(["pacman", "-Qnq"])
    if ok:
        stats["pacman_official"] = len(out.splitlines())

    # AUR/foreign
    ok, out = run_command(["pacman", "-Qmq"])
    if ok:
        stats["aur_foreign"] = len(out.splitlines())

    stats["total"] = stats["pacman_official"] + stats["aur_foreign"]

    # Flatpak
    if tool_available("flatpak"):
        ok, out = run_command(["flatpak", "list", "--app", "--columns=application"])
        if ok:
            stats["flatpak"] = len([l for l in out.splitlines() if l.strip()])

    # Snap
    if tool_available("snap"):
        ok, out = run_command(["snap", "list"])
        if ok:
            snap_lines = out.splitlines()
            stats["snap"] = max(0, len(snap_lines) - 1)  # skip header

    # Orphans
    ok, out = run_command(["pacman", "-Qdtq"])
    if ok and out:
        stats["orphans"] = len(out.splitlines())

    # Official updates
    if tool_available("checkupdates"):
        ok, out = run_command(["checkupdates"])
        # checkupdates exits 1 when no updates — that's normal
        if out:
            stats["available_updates_pacman"] = len(out.splitlines())

    # AUR updates
    aur_helper = _get_aur_helper()
    if aur_helper:
        ok, out = run_command([aur_helper, "-Qua"])
        if ok and out:
            stats["available_updates_aur"] = len(out.splitlines())

    # Flatpak updates
    if tool_available("flatpak"):
        ok, out = run_command(["flatpak", "remote-ls", "--updates"])
        if ok and out:
            stats["available_updates_flatpak"] = len(out.splitlines())

    # Total installed size (via expac if available)
    if tool_available("expac"):
        ok, out = run_command(["expac", "-s", "%m"])
        if ok and out:
            total_bytes = sum(int(s) for s in out.splitlines() if s.strip().isdigit())
            stats["total_installed_size_mb"] = round(total_bytes / (1024 * 1024), 1)

    cache.set("system_stats", stats, ttl=120)
    return stats


def format_info_fields(info: dict) -> dict:
    """
    Convert a raw info dict into a display-ready ordered dict for show_info_card().
    Empty fields are omitted.
    """
    field_map = [
        ("Source",          info.get("source",         "")),
        ("Version",         info.get("version",        "")),
        ("Repository",      info.get("repository",     "")),
        ("Description",     info.get("description",    "")),
        ("URL",             info.get("url",            "")),
        ("Install Date",    info.get("install_date",   "")),
        ("Installed Size",  info.get("installed_size", "")),
        ("Install Reason",  info.get("install_reason", "")),
        ("Packager",        info.get("packager",       "")),
        ("Build Date",      info.get("build_date",     "")),
        ("Dependencies",    info.get("dependencies",   "")),
        ("Required By",     info.get("required_by",    "")),
    ]
    return {k: v for k, v in field_map if v and v != "None"}


def format_stats_lines(stats: dict) -> list[str]:
    """Format system stats dict into Rofi display lines."""
    total_updates = (
        stats["available_updates_pacman"]
        + stats["available_updates_aur"]
        + stats["available_updates_flatpak"]
    )
    lines = [
        "─" * 38,
        f"  {'Total Packages':<26}{stats['total']}",
        f"  {'Official (Pacman)':<26}{stats['pacman_official']}",
        f"  {'AUR / Foreign':<26}{stats['aur_foreign']}",
        f"  {'Flatpak Apps':<26}{stats['flatpak']}",
    ]
    if stats["snap"]:
        lines.append(f"  {'Snap Packages':<26}{stats['snap']}")
    lines += [
        "─" * 38,
        f"  {'Orphans':<26}{stats['orphans']}",
        f"  {'Available Updates':<26}{total_updates}",
        f"    {'↳ Official':<24}{stats['available_updates_pacman']}",
        f"    {'↳ AUR':<24}{stats['available_updates_aur']}",
        f"    {'↳ Flatpak':<24}{stats['available_updates_flatpak']}",
    ]
    if stats.get("total_installed_size_mb"):
        lines.append("─" * 38)
        lines.append(f"  {'Total Install Size':<26}{stats['total_installed_size_mb']} MB")
    return lines


# ── Internal parsers ──────────────────────────────────────────────────────────

def _get_pacman_info(name: str, source: str = "Pacman") -> dict:
    """Parse `pacman -Qi <name>` output into a dict."""
    ok, out = run_command(["pacman", "-Qi", name])
    if not ok:
        return {"name": "", "source": source}

    info = {"name": name, "source": source}
    for line in out.splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            _KEY_MAP = {
                "Name":           "name",
                "Version":        "version",
                "Description":    "description",
                "Architecture":   "architecture",
                "URL":            "url",
                "Licenses":       "licenses",
                "Groups":         "groups",
                "Provides":       "provides",
                "Depends On":     "dependencies",
                "Optional Deps":  "optional_deps",
                "Required By":    "required_by",
                "Optional For":   "optional_for",
                "Conflicts With": "conflicts_with",
                "Replaces":       "replaces",
                "Installed Size": "installed_size",
                "Packager":       "packager",
                "Build Date":     "build_date",
                "Install Date":   "install_date",
                "Install Reason": "install_reason",
                "Install Script": "install_script",
                "Validated By":   "validated_by",
                "Repository":     "repository",
            }
            mapped = _KEY_MAP.get(key)
            if mapped:
                info[mapped] = val

    # Detect AUR vs official via repo field
    if not info.get("repository"):
        if source == "AUR":
            info["repository"] = "AUR"

    return info


def _get_flatpak_info(name: str) -> dict:
    """Parse `flatpak info <app_id>` output into a dict."""
    # Try by name or app-id
    ok, out = run_command(["flatpak", "info", name])
    if not ok:
        return {"name": "", "source": "Flatpak"}

    info = {"name": name, "source": "Flatpak"}
    for line in out.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            _KEY_MAP = {
                "ID":          "app_id",
                "Ref":         "ref",
                "Arch":        "architecture",
                "Branch":      "branch",
                "Version":     "version",
                "License":     "licenses",
                "Origin":      "repository",
                "Collection":  "collection",
                "Description": "description",
                "URL":         "url",
                "Installed":   "installed_size",
            }
            mapped = _KEY_MAP.get(key)
            if mapped:
                info[mapped] = val

    if not info.get("name") or info["name"] == name:
        # Try to extract display name from the ref line
        ref = info.get("ref", "")
        if "/" in ref:
            info["name"] = ref.split("/")[0]

    return info


def _get_aur_helper() -> str:
    """Return configured AUR helper or first available."""
    from config.settings import settings
    helper = settings.get("aur_helper", "yay")
    if tool_available(helper):
        return helper
    for h in ("yay", "paru", "trizen"):
        if tool_available(h):
            return h
    return ""
