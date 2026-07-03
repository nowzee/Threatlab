"""Admin-configurable application settings and timezone helpers."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from module.database.db_manager import DatabaseManagerHoneypot

DEFAULT_TIMEZONE = "Europe/Paris"

_SETTINGS_TABLE_READY = False
_TZ_CACHE = {"name": None, "at": 0.0}
_TZ_CACHE_TTL = 30.0

DISPLAY_FMT = "%d/%m/%Y %H:%M:%S"


def _ensure_settings_table(db) -> None:
    """Create the app_settings table if missing (covers pre-existing deployments)."""
    global _SETTINGS_TABLE_READY
    if _SETTINGS_TABLE_READY:
        return
    db.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key   VARCHAR(64) PRIMARY KEY,
            setting_value TEXT,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    _SETTINGS_TABLE_READY = True


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read a setting value, or ``default`` if unset / on error."""
    try:
        with DatabaseManagerHoneypot() as db:
            _ensure_settings_table(db)
            db.execute("SELECT setting_value FROM app_settings WHERE setting_key = %s", (key,))
            row = db.fetchone()
            if row and row.get("setting_value") is not None:
                return row["setting_value"]
    except Exception as e:
        print(f"[settings] read error for {key}: {e}")
    return default


def set_setting(key: str, value: str) -> bool:
    """Upsert a setting value. Returns True on success."""
    try:
        with DatabaseManagerHoneypot() as db:
            _ensure_settings_table(db)
            db.execute("""
                INSERT INTO app_settings (setting_key, setting_value)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """, (key, value))
        return True
    except Exception as e:
        print(f"[settings] write error for {key}: {e}")
        return False


def is_valid_timezone(name: str) -> bool:
    """True if ``name`` is a resolvable IANA timezone (e.g. 'Europe/Paris')."""
    if not name:
        return False
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def get_timezone_name(use_cache: bool = True) -> str:
    """Configured display timezone name (validated), default ``Europe/Paris``."""
    now = time.time()
    if use_cache and _TZ_CACHE["name"] and (now - _TZ_CACHE["at"] < _TZ_CACHE_TTL):
        return _TZ_CACHE["name"]
    name = get_setting("timezone", DEFAULT_TIMEZONE) or DEFAULT_TIMEZONE
    if not is_valid_timezone(name):
        name = DEFAULT_TIMEZONE
    _TZ_CACHE["name"] = name
    _TZ_CACHE["at"] = now
    return name


def set_timezone(name: str) -> bool:
    """Validate and persist the display timezone. Returns False if invalid."""
    if not is_valid_timezone(name):
        return False
    ok = set_setting("timezone", name)
    if ok:
        _TZ_CACHE["name"] = name
        _TZ_CACHE["at"] = time.time()
        try:
            from module.database.db_manager import invalidate_tz_cache
            invalidate_tz_cache()
        except Exception:
            pass
    return ok


def get_tz():
    """The configured timezone as a tzinfo, falling back to UTC if unavailable."""
    try:
        return ZoneInfo(get_timezone_name())
    except Exception as e:
        print(f"[settings] timezone unavailable, falling back to UTC: {e}")
        return timezone.utc


def current_utc_offset() -> str:
    """Configured tz's current UTC offset as a string, e.g. ``+02:00``."""
    off = datetime.now(get_tz()).strftime("%z")
    if not off:
        return "+00:00"
    return f"{off[:3]}:{off[3:]}"


_COMMON = [
    "UTC", "Europe/Paris", "Europe/London", "Europe/Berlin", "Europe/Madrid",
    "Europe/Rome", "Europe/Brussels", "Europe/Amsterdam", "Europe/Zurich",
    "Europe/Lisbon", "Europe/Athens", "Europe/Moscow", "America/New_York",
    "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Sao_Paulo",
    "Africa/Casablanca", "Asia/Dubai", "Asia/Kolkata", "Asia/Shanghai",
    "Asia/Tokyo", "Asia/Singapore", "Australia/Sydney",
]


def list_timezones() -> List[str]:
    """All valid IANA timezone names, with common ones first."""
    try:
        alltz = sorted(available_timezones())
    except Exception:
        alltz = sorted(_COMMON)
    common = [t for t in _COMMON if t in alltz]
    seen = set(common)
    rest = [t for t in alltz if t not in seen]
    return common + rest
