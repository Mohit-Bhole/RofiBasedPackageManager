#!/usr/bin/env python3
"""
utils/rofi.py
─────────────
All Rofi interaction primitives.

Every UI function in the project goes through this module — nothing else
should call subprocess with "rofi" directly. This keeps the theme, flags,
and return-code handling in one place.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional

# Sentinels that modules can import and compare against
BACK = "← Back"
EXIT = "✕ Exit"
YES  = "✔ Yes"
NO   = "✖ No"

# Path to the bundled theme (resolved relative to this file's package root)
_PKG_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_THEME = _PKG_ROOT / "themes" / "default.rasi"


def _theme_args(theme: Optional[str] = None) -> list[str]:
    """Return rofi -theme flag list if a theme file exists."""
    path = Path(theme) if theme else _DEFAULT_THEME
    if path.exists():
        return ["-theme", str(path)]
    return []


def rofi_menu(
    options: list[str],
    prompt: str,
    theme: Optional[str] = None,
    extra_args: Optional[list[str]] = None,
) -> str:
    """
    Show a Rofi dmenu with the given options.

    Args:
        options:    List of items to show.
        prompt:     Text shown in the Rofi prompt bar.
        theme:      Path to a .rasi file (uses default if None).
        extra_args: Extra flags forwarded to rofi.

    Returns:
        The selected string, or "" if the user dismissed / pressed Escape.
    """
    args = [
        "rofi", "-dmenu",
        "-i",                    # case-insensitive filter
        "-p", prompt,
        "-no-fixed-num-lines",
    ]
    args += _theme_args(theme)
    if extra_args:
        args += extra_args

    try:
        result = subprocess.run(
            args,
            input="\n".join(options),
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("rofi not found. Please install rofi.")
    except Exception as exc:
        raise RuntimeError(f"rofi error: {exc}") from exc


def rofi_input(prompt: str, theme: Optional[str] = None) -> str:
    """
    Open Rofi in dmenu mode with no options — acts as a text-input box.

    Returns:
        Whatever the user typed, or "" if dismissed.
    """
    args = [
        "rofi", "-dmenu",
        "-p", prompt,
        "-no-fixed-num-lines",
    ]
    args += _theme_args(theme)

    try:
        result = subprocess.run(
            args,
            input="",
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("rofi not found. Please install rofi.")
    except Exception as exc:
        raise RuntimeError(f"rofi error: {exc}") from exc


def rofi_confirm(
    message: str,
    theme: Optional[str] = None,
    default_yes: bool = False,
) -> bool:
    """
    Show a Yes/No confirmation dialog in Rofi.

    Args:
        message:     The question / warning to display as the prompt.
        default_yes: If True, YES is the first option (highlighted).

    Returns:
        True if the user chose Yes, False otherwise.
    """
    options = [YES, NO] if default_yes else [NO, YES]
    choice = rofi_menu(options, message, theme=theme)
    return choice == YES


def show_text(
    title: str,
    lines: list[str],
    theme: Optional[str] = None,
) -> None:
    """
    Display a scrollable read-only list in Rofi.
    Always prepends a ← Back entry; the return value is ignored.

    Args:
        title: Rofi prompt label.
        lines: Content lines to display.
    """
    if not lines:
        lines = ["(no results)"]
    rofi_menu([BACK] + lines, title, theme=theme)


def show_info_card(
    title: str,
    fields: dict,
    extra_items: Optional[list[str]] = None,
    theme: Optional[str] = None,
) -> str:
    """
    Display a formatted key→value card in Rofi.

    Args:
        title:       Prompt label.
        fields:      Ordered dict of { "Label": "Value" }.
        extra_items: Extra selectable items appended after the fields
                     (e.g. action buttons).

    Returns:
        Whatever the user selected (could be BACK, an extra_item, or a field line).
    """
    lines = [BACK]
    lines.append("─" * 40)
    for key, value in fields.items():
        if value:
            lines.append(f"  {key:<22}{value}")
    lines.append("─" * 40)
    if extra_items:
        lines += extra_items

    return rofi_menu(lines, title, theme=theme)


def show_message(
    title: str,
    message: str,
    theme: Optional[str] = None,
) -> None:
    """
    Show a single-message dialog (error, success notice, etc.).
    """
    lines = message.splitlines() if message else ["(no message)"]
    show_text(title, lines, theme=theme)


def select_from_list(
    title: str,
    items: list[str],
    theme: Optional[str] = None,
) -> str:
    """
    Show a selectable list with a ← Back option.

    Returns:
        The selected item string, BACK, or "" if dismissed.
    """
    return rofi_menu([BACK] + items, title, theme=theme)
