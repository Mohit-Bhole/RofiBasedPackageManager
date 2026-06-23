#!/usr/bin/env python3
"""
modules/search.py
─────────────────
Package search across Pacman, AUR, and Flatpak.

All functions return a list of result dicts with a common schema:
    {
        "name":        str,
        "version":     str,
        "source":      "Pacman" | "AUR" | "Flatpak",
        "description": str,
        "installed":   bool,
        "repo":        str,   # Pacman repo or Flatpak remote
    }

The display helpers format these dicts into Rofi-displayable strings.
"""

import re
import urllib.request
import urllib.parse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from utils.commands import run_command, tool_available
from config.settings import settings


# ── Badge constants ───────────────────────────────────────────────────────────
_BADGE = {
    "Pacman":  "[Pacman] ",
    "AUR":     "[AUR]    ",
    "Flatpak": "[Flatpak]",
    "Snap":    "[Snap]   ",
}


# ── Public search functions ───────────────────────────────────────────────────

def search_pacman(query: str) -> list[dict]:
    """
    Search official Arch repos using `pacman -Ss`.

    Returns a list of result dicts.
    """
    ok, out = run_command(["pacman", "-Ss", query], timeout=30)
    if not ok or not out:
        return []
    return _parse_pacman_ss(out)


def search_aur(query: str) -> list[dict]:
    """
    Search the AUR via the HTTP RPC API (no AUR helper needed for search).
    Falls back to `yay -Ss` if the HTTP request fails.

    Returns a list of result dicts.
    """
    try:
        return _search_aur_api(query)
    except Exception:
        return _search_aur_fallback(query)


def search_flatpak(query: str) -> list[dict]:
    """
    Search Flatpak remotes using `flatpak search`.

    Returns a list of result dicts.
    """
    if not tool_available("flatpak"):
        return []
    ok, out = run_command(["flatpak", "search", "--columns=application,name,version,description", query], timeout=30)
    if not ok or not out:
        return []
    return _parse_flatpak_search(out)


def search_everywhere(query: str) -> list[dict]:
    """
    Search Pacman, AUR, and Flatpak in parallel and return a combined list,
    sorted by source order (Pacman first, then AUR, then Flatpak).
    """
    results: list[dict] = []
    sources = {
        "Pacman":  lambda: search_pacman(query),
        "AUR":     lambda: search_aur(query),
        "Flatpak": lambda: search_flatpak(query),
    }

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn): src for src, fn in sources.items()}
        for future in as_completed(futures):
            try:
                results += future.result()
            except Exception:
                pass

    # Sort: Pacman → AUR → Flatpak, then alphabetically by name
    order = {"Pacman": 0, "AUR": 1, "Flatpak": 2}
    results.sort(key=lambda r: (order.get(r["source"], 9), r["name"].lower()))
    return results


# ── Display formatters ────────────────────────────────────────────────────────

def format_result(result: dict, show_descriptions: Optional[bool] = None) -> str:
    """
    Format a single result dict into a Rofi display string.

    Format:  [Source]  name  version  — description (if enabled)
    """
    if show_descriptions is None:
        show_descriptions = settings.get("show_descriptions", True)

    badge   = _BADGE.get(result["source"], "[?]      ")
    name    = result.get("name", "")
    version = result.get("version", "")
    desc    = result.get("description", "")
    installed_marker = " ✔" if result.get("installed") else ""

    if show_descriptions and desc:
        return f"{badge}  {name}{installed_marker}  ({version})  — {desc}"
    return f"{badge}  {name}{installed_marker}  ({version})"


def format_results(results: list[dict], show_descriptions: Optional[bool] = None) -> list[str]:
    """Format a list of result dicts into Rofi display strings."""
    return [format_result(r, show_descriptions) for r in results]


def result_from_display(display_line: str, results: list[dict]) -> Optional[dict]:
    """
    Reverse-map a Rofi display line back to its result dict.
    Matches by extracting the package name from the display line.
    """
    # Name is the second whitespace-token after the badge
    parts = display_line.strip().split()
    if len(parts) < 2:
        return None
    # parts[0] = badge like "[Pacman]", parts[1] = name (possibly with ✔)
    name_candidate = parts[1].rstrip("✔").strip()
    for r in results:
        if r.get("name") == name_candidate:
            return r
    return None


# ── Internal parsers ──────────────────────────────────────────────────────────

def _parse_pacman_ss(output: str) -> list[dict]:
    """
    Parse `pacman -Ss` output.

    Format:
        repo/name version [installed]
            description
    """
    results: list[dict] = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Header lines start without leading whitespace
        if line and not line[0].isspace():
            parts = line.split()
            if "/" in parts[0] and len(parts) >= 2:
                repo_name = parts[0]
                version   = parts[1]
                installed = "[installed]" in line

                slash_pos = repo_name.find("/")
                repo = repo_name[:slash_pos]
                name = repo_name[slash_pos + 1:]

                desc = ""
                if i + 1 < len(lines) and lines[i + 1].startswith("    "):
                    desc = lines[i + 1].strip()
                    i += 1

                results.append({
                    "name":        name,
                    "version":     version,
                    "source":      "Pacman",
                    "description": desc,
                    "installed":   installed,
                    "repo":        repo,
                })
        i += 1
    return results


def _search_aur_api(query: str) -> list[dict]:
    """
    Query the AUR RPC v5 search endpoint.
    Uses urllib (stdlib only — no requests dependency).
    """
    encoded = urllib.parse.quote(query)
    url = f"https://aur.archlinux.org/rpc/v5/search/{encoded}?by=name-desc"

    req = urllib.request.Request(url, headers={"User-Agent": "rofi-package-manager/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    results = []
    for pkg in data.get("results", []):
        results.append({
            "name":        pkg.get("Name", ""),
            "version":     pkg.get("Version", ""),
            "source":      "AUR",
            "description": pkg.get("Description", ""),
            "installed":   False,   # AUR API doesn't report install status
            "repo":        "aur",
            "votes":       pkg.get("NumVotes", 0),
            "popularity":  pkg.get("Popularity", 0.0),
            "maintainer":  pkg.get("Maintainer", ""),
            "url":         pkg.get("URL", ""),
        })

    # Sort by popularity descending
    results.sort(key=lambda r: r.get("popularity", 0), reverse=True)
    return results


def _search_aur_fallback(query: str) -> list[dict]:
    """
    Fallback: use the configured AUR helper's search if the API call failed.
    """
    helper = settings.get("aur_helper", "yay")
    if not tool_available(helper):
        return []

    ok, out = run_command([helper, "-Ss", "--aur", query], timeout=30)
    if not ok or not out:
        return []

    # yay/paru output looks like pacman -Ss output
    raw = _parse_pacman_ss(out)
    for r in raw:
        r["source"] = "AUR"
    return raw


def _parse_flatpak_search(output: str) -> list[dict]:
    """
    Parse `flatpak search --columns=application,name,version,description` output.
    Columns are tab-separated.
    """
    results: list[dict] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            app_id  = parts[0].strip()
            name    = parts[1].strip()
            version = parts[2].strip() if len(parts) > 2 else ""
            desc    = parts[3].strip() if len(parts) > 3 else ""
            results.append({
                "name":        name,
                "version":     version,
                "source":      "Flatpak",
                "description": desc,
                "installed":   False,
                "repo":        "",
                "app_id":      app_id,
            })
    return results
