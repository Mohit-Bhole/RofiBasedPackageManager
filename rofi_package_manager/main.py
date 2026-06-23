#!/usr/bin/env python3
"""
main.py
───────
Rofi Package Manager — entry point and navigation controller.

Responsibilities:
  • Show the main menu
  • Route to sub-menus
  • Handle Back / Exit sentinels
  • Nothing else — all logic lives in modules/

Sentinel constants (BACK, EXIT) are imported from utils.rofi.
"""

import sys
import os

# Allow running directly from the project root: python3 main.py
sys.path.insert(0, os.path.dirname(__file__))

from utils.rofi import (
    rofi_menu, rofi_input, rofi_confirm,
    show_text, show_info_card, show_message, select_from_list,
    BACK, EXIT, YES, NO,
)
from config.settings import settings


# ── Version ───────────────────────────────────────────────────────────────────
VERSION = "1.0.0"
TITLE   = f"📦 Rofi Package Manager  v{VERSION}"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Application entry point — shows the main menu in a loop."""
    while True:
        choice = rofi_menu(
            [
                "🔍  Package Search",
                "📋  Installed Packages",
                "⬇   Install Package",
                "🔄  Update Packages",
                "🗑   Remove Package",
                "ℹ   Package Information",
                "🩺  Package Health",
                "🧹  System Cleanup",
                "📊  Statistics",
                "⚙   Settings",
                EXIT,
            ],
            TITLE,
        )

        if choice in ("", EXIT):
            sys.exit(0)

        elif "Package Search" in choice:
            menu_search()

        elif "Installed Packages" in choice:
            menu_installed()

        elif "Install Package" in choice:
            menu_install()

        elif "Update Packages" in choice:
            menu_update()

        elif "Remove Package" in choice:
            menu_remove()

        elif "Package Information" in choice:
            menu_info()

        elif "Package Health" in choice:
            menu_health()

        elif "System Cleanup" in choice:
            menu_cleanup()

        elif "Statistics" in choice:
            menu_statistics()

        elif "Settings" in choice:
            menu_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_search() -> None:
    """Sub-menu: search packages across all sources."""
    from modules import search as search_mod

    while True:
        choice = rofi_menu(
            [
                BACK,
                "🌐  Search Everywhere",
                "─── By Source ───────────────────────────",
                "🏛   Search Pacman (Official)",
                "🔧  Search AUR",
                "📦  Search Flatpak",
            ],
            "🔍 Package Search",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK or choice.startswith("───"):
            return

        query = rofi_input("Search query")
        if not query:
            continue

        # Run search
        if "Search Everywhere" in choice:
            results = search_mod.search_everywhere(query)
            _show_search_results(results, query, "🌐 Search Everywhere")

        elif "Search Pacman" in choice:
            results = search_mod.search_pacman(query)
            _show_search_results(results, query, "🏛 Pacman Results")

        elif "Search AUR" in choice:
            results = search_mod.search_aur(query)
            _show_search_results(results, query, "🔧 AUR Results")

        elif "Search Flatpak" in choice:
            results = search_mod.search_flatpak(query)
            _show_search_results(results, query, "📦 Flatpak Results")


def _show_search_results(results: list, query: str, title: str) -> None:
    """Display search results, allow selecting one for info/install."""
    from modules import search as search_mod

    if not results:
        show_text(title, [f"No results for '{query}'"])
        return

    display_lines = search_mod.format_results(results)

    while True:
        selection = select_from_list(f"{title} ({len(results)} results)", display_lines)
        if selection in ("", BACK):
            return

        # Map display line → result dict
        result = search_mod.result_from_display(selection, results)
        if not result:
            continue

        _package_action_menu(result["name"], result.get("source", ""), result)


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLED PACKAGES MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_installed() -> None:
    """Browse all installed packages grouped by source."""
    from modules import source as source_mod
    from utils.commands import run_command, tool_available

    while True:
        choice = rofi_menu(
            [
                BACK,
                "📋  All Packages",
                "🏛   Official (Pacman)",
                "🔧  AUR / Foreign",
                "📦  Flatpak Apps",
                "⭐  Explicitly Installed",
                "🔗  Dependencies Only",
                "💀  Orphans",
            ],
            "📋 Installed Packages",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK:
            return

        if "All Packages" in choice:
            _, out = run_command(["pacman", "-Q"])
            _browse_package_list(out.splitlines() if out else [], "All Packages")

        elif "Official" in choice:
            _, out = run_command(["pacman", "-Qn"])
            _browse_package_list(out.splitlines() if out else [], "Official Packages")

        elif "AUR" in choice:
            _, out = run_command(["pacman", "-Qm"])
            _browse_package_list(out.splitlines() if out else [], "AUR / Foreign")

        elif "Flatpak" in choice:
            from utils.commands import tool_available
            if not tool_available("flatpak"):
                show_text("Flatpak", ["Flatpak is not installed."])
                continue
            _, out = run_command(["flatpak", "list", "--app", "--columns=name,version"])
            _browse_package_list(out.splitlines() if out else [], "Flatpak Apps")

        elif "Explicitly" in choice:
            _, out = run_command(["pacman", "-Qe"])
            _browse_package_list(out.splitlines() if out else [], "Explicitly Installed")

        elif "Dependencies" in choice:
            _, out = run_command(["pacman", "-Qd"])
            _browse_package_list(out.splitlines() if out else [], "Dependency Packages")

        elif "Orphans" in choice:
            _, out = run_command(["pacman", "-Qdt"])
            lines = out.splitlines() if out else ["No orphans found ✔"]
            _browse_package_list(lines, "Orphaned Packages")


def _browse_package_list(lines: list[str], title: str) -> None:
    """Show a package list; selecting a package opens its info screen."""
    if not lines:
        show_text(title, ["(none)"])
        return

    while True:
        selection = select_from_list(f"{title} ({len(lines)})", lines)
        if selection in ("", BACK):
            return

        # Extract package name (first word of the line)
        pkg_name = selection.split()[0] if selection.split() else ""
        if pkg_name:
            _package_action_menu(pkg_name)


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALL MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_install() -> None:
    """Install a package by name."""
    from modules import install as install_mod

    while True:
        choice = rofi_menu(
            [
                BACK,
                "🏛   Install from Official Repos (Pacman)",
                "🔧  Install from AUR",
                "📦  Install Flatpak App",
            ],
            "⬇ Install Package",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK:
            return

        if "Official" in choice:
            name = rofi_input("Package name (Pacman)")
            if not name:
                continue
            if settings.get("confirm_install") and not rofi_confirm(f"Install '{name}' via pacman?"):
                continue
            install_mod.install_pacman(name)

        elif "AUR" in choice:
            name = rofi_input("Package name (AUR)")
            if not name:
                continue
            if settings.get("confirm_install") and not rofi_confirm(f"Install '{name}' from AUR?"):
                continue
            install_mod.install_aur(name)

        elif "Flatpak" in choice:
            name = rofi_input("App ID or name (Flatpak)")
            if not name:
                continue
            if settings.get("confirm_install") and not rofi_confirm(f"Install Flatpak '{name}'?"):
                continue
            install_mod.install_flatpak(name)


# ═══════════════════════════════════════════════════════════════════════════════
# UPDATE MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_update() -> None:
    """Check and apply system updates."""
    from modules import update as update_mod

    while True:
        choice = rofi_menu(
            [
                BACK,
                "🌐  Update Everything",
                "─── Check Updates ───────────────────────",
                "🏛   Check Official Updates",
                "🔧  Check AUR Updates",
                "📦  Check Flatpak Updates",
                "─── Apply Updates ───────────────────────",
                "🏛   Update Official Packages",
                "🔧  Update AUR Packages",
                "📦  Update Flatpak Apps",
            ],
            "🔄 Update Packages",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK or choice.startswith("───"):
            if choice == BACK:
                return
            continue

        if "Update Everything" in choice:
            if rofi_confirm("Update ALL packages (Pacman + AUR + Flatpak)?"):
                update_mod.update_everything()

        elif "Check Official" in choice:
            updates = update_mod.check_pacman_updates()
            lines = update_mod.format_update_lines(updates)
            show_text(f"Official Updates ({len(updates)})", lines or ["No updates available ✔"])

        elif "Check AUR" in choice:
            updates = update_mod.check_aur_updates()
            lines = update_mod.format_update_lines(updates)
            show_text(f"AUR Updates ({len(updates)})", lines or ["No AUR updates available ✔"])

        elif "Check Flatpak" in choice:
            updates = update_mod.check_flatpak_updates()
            lines = update_mod.format_update_lines(updates)
            show_text(f"Flatpak Updates ({len(updates)})", lines or ["No Flatpak updates ✔"])

        elif "Update Official" in choice:
            if rofi_confirm("Run sudo pacman -Syu?"):
                update_mod.update_pacman()

        elif "Update AUR" in choice:
            if rofi_confirm("Run AUR full upgrade?"):
                update_mod.update_aur()

        elif "Update Flatpak" in choice:
            if rofi_confirm("Run flatpak update?"):
                update_mod.update_flatpak()


# ═══════════════════════════════════════════════════════════════════════════════
# REMOVE MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_remove() -> None:
    """Remove a package by name."""
    from modules import remove as remove_mod

    name = rofi_input("Package to remove")
    if not name:
        return

    if settings.get("confirm_removal") and not rofi_confirm(f"Remove '{name}'? (pacman -Rns)"):
        return

    remove_mod.remove(name)


# ═══════════════════════════════════════════════════════════════════════════════
# PACKAGE INFORMATION MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_info() -> None:
    """Look up detailed info for a specific package."""
    name = rofi_input("Package name")
    if not name:
        return
    _package_action_menu(name)


def _package_action_menu(name: str, source: str = "", search_result: dict = None) -> None:
    """
    Show the package action panel:
      - Info card
      - Dependency tree
      - Reverse deps
      - Install / Remove
    """
    from modules import info as info_mod
    from modules import source as source_mod
    from modules import install as install_mod
    from modules import remove as remove_mod

    # Detect source
    if not source:
        source = source_mod.detect_source(name)

    # Fetch info (use search result if already available for speed)
    if search_result and not source_mod.detect_source(name):
        pkg_info = {
            "name":        search_result.get("name", name),
            "source":      search_result.get("source", "Unknown"),
            "version":     search_result.get("version", ""),
            "description": search_result.get("description", ""),
            "repository":  search_result.get("repo", ""),
        }
    else:
        pkg_info = info_mod.get_package_info(name, source)

    fields = info_mod.format_info_fields(pkg_info) if pkg_info.get("name") else {}
    display_name = pkg_info.get("name", name)

    is_installed = source not in ("", "Unknown")

    action_items = [
        "─" * 38,
        "🌳  View Dependency Tree",
        "🔗  View Required By (Reverse Deps)",
    ]
    if is_installed:
        action_items.append("🗑   Remove Package")
    else:
        action_items.append("⬇   Install Package")

    while True:
        selection = show_info_card(
            f"ℹ {display_name}",
            fields if fields else {"Status": "Not installed / not found"},
            extra_items=action_items,
        )

        if selection in ("", BACK):
            return

        elif "Dependency Tree" in selection:
            tree = info_mod.get_dependency_tree(name)
            show_text(f"🌳 {name} — Dependencies", tree.splitlines())

        elif "Required By" in selection:
            rev_deps = info_mod.get_reverse_deps(name)
            show_text(
                f"🔗 {name} — Required By",
                rev_deps if rev_deps else ["No packages depend on this."],
            )

        elif "Remove Package" in selection:
            if settings.get("confirm_removal") and not rofi_confirm(f"Remove '{name}'?"):
                continue
            remove_mod.remove(name, source)
            return

        elif "Install Package" in selection:
            src = search_result.get("source", "") if search_result else ""
            app_id = search_result.get("app_id", name) if search_result else name
            if settings.get("confirm_install") and not rofi_confirm(f"Install '{name}'?"):
                continue
            install_mod.install(app_id, src)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_health() -> None:
    """Package health dashboard."""
    from modules import health as health_mod
    from modules import remove as remove_mod

    while True:
        choice = rofi_menu(
            [
                BACK,
                "🩺  Health Dashboard",
                "─── Details ─────────────────────────────",
                "💀  View Orphaned Packages",
                "🌍  View Foreign / AUR Packages",
                "🔍  Check Package File Integrity",
                "─── Actions ─────────────────────────────",
                "🗑   Remove All Orphans",
            ],
            "🩺 Package Health",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK or choice.startswith("───"):
            if choice == BACK:
                return
            continue

        if "Health Dashboard" in choice:
            summary = health_mod.get_health_summary()
            lines = health_mod.format_health_lines(summary)
            show_text("🩺 Health Dashboard", lines)

        elif "Orphaned Packages" in choice:
            orphans = health_mod.list_orphans()
            if orphans:
                selection = select_from_list(f"💀 Orphans ({len(orphans)})", orphans)
                if selection and selection != BACK:
                    _package_action_menu(selection, "Pacman")
            else:
                show_text("Orphans", ["No orphans found ✔"])

        elif "Foreign" in choice:
            packages = health_mod.list_foreign_packages()
            lines = [f"{p['name']}  {p['version']}" for p in packages]
            show_text(f"🌍 Foreign Packages ({len(packages)})", lines or ["None found"])

        elif "Integrity" in choice:
            integrity = health_mod.check_package_integrity()
            detail_lines = [
                f"  Total packages:  {integrity['total']}",
                f"  OK:              {integrity['ok']}",
                f"  Broken:          {len(integrity['broken'])}",
                "─" * 38,
            ] + (integrity["details"] or ["All package files are intact ✔"])
            show_text("🔍 Package Integrity", detail_lines)

        elif "Remove All Orphans" in choice:
            orphans = health_mod.list_orphans()
            if not orphans:
                show_text("Orphans", ["No orphans to remove ✔"])
                continue
            if rofi_confirm(f"Remove {len(orphans)} orphaned package(s)?"):
                remove_mod.remove_orphans()
                from utils.cache import cache
                cache.invalidate("orphan_list")
                cache.invalidate("health_summary")


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_cleanup() -> None:
    """System cleanup operations."""
    from modules import cleanup as cleanup_mod

    while True:
        choice = rofi_menu(
            [
                BACK,
                "🧹  Full System Cleanup (All)",
                "─── Individual ──────────────────────────",
                "💀  Remove Orphaned Packages",
                "🗂   Clean Pacman Package Cache",
                "🗂   Clean Pacman Cache (All Versions)",
                "🔧  Clean AUR Build Cache",
                "📦  Remove Unused Flatpak Runtimes",
            ],
            "🧹 System Cleanup",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK or choice.startswith("───"):
            if choice == BACK:
                return
            continue

        if "Full System Cleanup" in choice:
            if rofi_confirm("Run full cleanup? (orphans + caches + unused Flatpaks)"):
                cleanup_mod.clean_all()

        elif "Remove Orphaned" in choice:
            from modules import health as health_mod
            orphans = health_mod.list_orphans()
            if not orphans:
                show_text("Orphans", ["No orphans found ✔"])
                continue
            if rofi_confirm(f"Remove {len(orphans)} orphan(s)?"):
                cleanup_mod.remove_orphans()

        elif "All Versions" in choice:
            if rofi_confirm("Remove ALL cached package versions? (cannot undo)"):
                cleanup_mod.clean_pacman_cache_all()

        elif "Pacman Package Cache" in choice:
            if rofi_confirm("Remove old cached package files? (latest kept)"):
                cleanup_mod.clean_pacman_cache()

        elif "AUR Build Cache" in choice:
            if rofi_confirm("Clean AUR build cache?"):
                cleanup_mod.clean_aur_cache()

        elif "Unused Flatpak" in choice:
            if rofi_confirm("Remove unused Flatpak runtimes?"):
                cleanup_mod.clean_flatpak_unused()


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_statistics() -> None:
    """System package statistics dashboard."""
    from modules import info as info_mod

    stats = info_mod.get_system_stats()
    lines = info_mod.format_stats_lines(stats)
    show_text("📊 System Statistics", lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu_settings() -> None:
    """View and edit configuration."""
    while True:
        current = settings.all()
        helper       = current.get("aur_helper", "yay")
        show_desc    = "On" if current.get("show_descriptions") else "Off"
        confirm_rm   = "On" if current.get("confirm_removal") else "Off"
        confirm_inst = "On" if current.get("confirm_install") else "Off"
        ttl          = current.get("cache_ttl_seconds", 300)

        choice = rofi_menu(
            [
                BACK,
                f"🔧  AUR Helper              {helper}",
                f"📄  Show Descriptions       {show_desc}",
                f"⚠   Confirm Removal         {confirm_rm}",
                f"⚠   Confirm Install         {confirm_inst}",
                f"⏱   Cache TTL               {ttl}s",
                "─────────────────────────────────────────",
                "🗑   Clear Package Cache",
                "↩   Reset to Defaults",
            ],
            "⚙ Settings",
        )

        if choice in ("", EXIT):
            sys.exit(0)
        if choice == BACK or choice.startswith("───"):
            if choice == BACK:
                return
            continue

        if "AUR Helper" in choice:
            new_helper = rofi_menu(["yay", "paru", "trizen", BACK], "Select AUR Helper")
            if new_helper and new_helper != BACK:
                settings.set("aur_helper", new_helper)

        elif "Show Descriptions" in choice:
            settings.set("show_descriptions", not current.get("show_descriptions"))

        elif "Confirm Removal" in choice:
            settings.set("confirm_removal", not current.get("confirm_removal"))

        elif "Confirm Install" in choice:
            settings.set("confirm_install", not current.get("confirm_install"))

        elif "Cache TTL" in choice:
            val = rofi_input("Cache TTL in seconds (e.g. 300)")
            if val.isdigit():
                settings.set("cache_ttl_seconds", int(val))

        elif "Clear Package Cache" in choice:
            from utils.cache import cache
            cache.clear()
            show_text("Cache", ["Package cache cleared ✔"])

        elif "Reset to Defaults" in choice:
            if rofi_confirm("Reset all settings to defaults?"):
                settings.reset()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except RuntimeError as exc:
        # rofi not found or similar fatal startup errors
        print(f"Fatal: {exc}", file=sys.stderr)
        sys.exit(1)
