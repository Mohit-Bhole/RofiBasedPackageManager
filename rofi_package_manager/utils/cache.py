#!/usr/bin/env python3
"""
utils/cache.py
──────────────
Simple TTL-based in-memory + on-disk cache for package list results.

Avoids re-running expensive commands (pacman -Q, flatpak list, etc.)
on every menu navigation. Cache entries expire after a configurable TTL.

Usage:
    from utils.cache import cache

    data = cache.get("pacman_all")
    if data is None:
        _, data = run_command(["pacman", "-Qq"])
        cache.set("pacman_all", data, ttl=300)
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional


_CACHE_DIR = Path.home() / ".cache" / "rofi-package-manager"


class PackageCache:
    """
    Two-level cache:
      - Level 1: In-process dict (fastest, lost on exit)
      - Level 2: JSON files on disk under ~/.cache/rofi-package-manager/
                 (survives between launches, honoured by TTL)
    """

    def __init__(self, cache_dir: Path = _CACHE_DIR, default_ttl: int = 300):
        self._dir = cache_dir
        self._default_ttl = default_ttl
        self._mem: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """
        Return cached value for key, or None if missing / expired.
        Checks memory first, then disk.
        """
        now = time.time()

        # L1: memory
        if key in self._mem:
            value, expires_at = self._mem[key]
            if now < expires_at:
                return value
            del self._mem[key]

        # L2: disk
        path = self._key_path(key)
        if path.exists():
            try:
                entry = json.loads(path.read_text())
                if now < entry["expires_at"]:
                    value = entry["value"]
                    # Promote back to memory
                    self._mem[key] = (value, entry["expires_at"])
                    return value
                path.unlink(missing_ok=True)
            except (json.JSONDecodeError, KeyError, OSError):
                path.unlink(missing_ok=True)

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value under key with the given TTL (seconds).
        Falls back to default_ttl if not specified.
        """
        ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + ttl

        # L1: memory
        self._mem[key] = (value, expires_at)

        # L2: disk (best-effort)
        try:
            entry = {"value": value, "expires_at": expires_at}
            self._key_path(key).write_text(json.dumps(entry))
        except OSError:
            pass  # disk write failure is non-fatal

    def invalidate(self, key: str) -> None:
        """Remove a single cache entry from both levels."""
        self._mem.pop(key, None)
        try:
            self._key_path(key).unlink(missing_ok=True)
        except OSError:
            pass

    def clear(self) -> None:
        """Wipe all cache entries from both levels."""
        self._mem.clear()
        try:
            for f in self._dir.glob("*.json"):
                f.unlink(missing_ok=True)
        except OSError:
            pass

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all cache keys that start with prefix."""
        for key in list(self._mem):
            if key.startswith(prefix):
                del self._mem[key]
        try:
            for f in self._dir.glob("*.json"):
                # Reverse the filename to key and check prefix
                # Keys are hashed, so we store a companion .key file
                key_file = f.with_suffix(".key")
                if key_file.exists():
                    stored_key = key_file.read_text()
                    if stored_key.startswith(prefix):
                        f.unlink(missing_ok=True)
                        key_file.unlink(missing_ok=True)
        except OSError:
            pass

    # ── Internal ──────────────────────────────────────────────────────────────

    def _key_path(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode()).hexdigest()[:16]
        # Write companion key file for prefix-invalidation
        key_file = self._dir / f"{safe}.key"
        try:
            if not key_file.exists():
                key_file.write_text(key)
        except OSError:
            pass
        return self._dir / f"{safe}.json"


# Module-level singleton — import and use directly:
#   from utils.cache import cache
cache = PackageCache()
