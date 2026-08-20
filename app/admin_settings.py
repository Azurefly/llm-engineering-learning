from __future__ import annotations

import os
from typing import Any

from .auth import _now_iso, account_store

SETTING_ALLOW_REGISTRATION = "allow_registration"


def _env_registration_default() -> bool:
    return os.getenv("LLM_ALLOW_REGISTRATION", "1").strip().lower() not in {"0", "false", "no", "off"}


def _ensure_settings_table() -> None:
    with account_store().connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_settings(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER
            )
            """
        )


def get_setting(key: str) -> dict[str, Any] | None:
    _ensure_settings_table()
    with account_store().connect() as conn:
        row = conn.execute("SELECT * FROM system_settings WHERE key=?", (key,)).fetchone()
    return dict(row) if row else None


def set_setting(key: str, value: str, *, actor_id: int | None = None) -> None:
    _ensure_settings_table()
    with account_store().connect() as conn:
        conn.execute(
            """INSERT INTO system_settings(key,value,updated_at,updated_by)
               VALUES(?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at,updated_by=excluded.updated_by""",
            (key, value, _now_iso(), actor_id),
        )


def registration_enabled() -> bool:
    row = get_setting(SETTING_ALLOW_REGISTRATION)
    if row is None:
        return _env_registration_default()
    return str(row["value"]).strip().lower() in {"1", "true", "yes", "on"}


def set_registration_enabled(enabled: bool, *, actor_id: int) -> None:
    set_setting(SETTING_ALLOW_REGISTRATION, "1" if enabled else "0", actor_id=actor_id)
