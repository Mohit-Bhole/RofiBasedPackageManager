#!/usr/bin/env python3
"""
config/settings.py
──────────────────
Load and persist user configuration from:
    ~/.config/rofi-package-manager/config.json

Access settings anywhere with:
    from config.settings import settings
    helper = settings.get("aur_helper")
    settings.set("aur_helper", "paru")
"""

import json
from pathlib import Path
from typing import Any, Optional

_CONFIG_DIR  = Path.home() / ".config" / "rofi-package-manager"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# Default configuration — all keys and their default values
DEFAULTS: dict[str, Any] = {
    "aur_helper":        "yay",      # yay | paru | trizen
    "show_descriptions": True,       # show package descriptions in search results
    "confirm_removal":   True,       # ask Yes/No before removing a package
    "confirm_install":   True,       # ask Yes/No before installing a package
    "cache_ttl_seconds": 300,        # how long to cache package lists (seconds)
    "theme":             "default",  # name of .rasi theme file under themes/
    "terminal":          None,       # override terminal emulator (None = auto-detect)
}


class Settings:
    """
    Thin wrapper around a JSON config file.
    Always merges with DEFAULTS so new keys are available immediately
    after an upgrade without requiring a config migration step.
    """

    def __init__(
        self,
        config_file: Path = _CONFIG_FILE,
        defaults: dict = DEFAULTS,
    ):
        self._file = config_file
        self._defaults = defaults
        self._data: dict[str, Any] = {}
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str, fallback: Any = None) -> Any:
        """
        Return the value for key.
        Resolution order: user config → DEFAULTS → fallback.
        """
        if key in self._data:
            return self._data[key]
        if key in self._defaults:
            return self._defaults[key]
        return fallback

    def set(self, key: str, value: Any) -> None:
        """Persist a setting to the config file."""
        self._data[key] = value
        self._save()

    def all(self) -> dict[str, Any]:
        """Return a merged view of defaults + user overrides."""
        merged = dict(self._defaults)
        merged.update(self._data)
        return merged

    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._data = {}
        self._save()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._file.exists():
            try:
                self._data = json.loads(self._file.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}
            self._ensure_dir()
            self._save()  # Write default config on first run

    def _save(self) -> None:
        self._ensure_dir()
        try:
            self._file.write_text(json.dumps(self._data, indent=2))
        except OSError:
            pass  # Non-fatal — settings are still available in memory

    def _ensure_dir(self) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)


# Module-level singleton
settings = Settings()
