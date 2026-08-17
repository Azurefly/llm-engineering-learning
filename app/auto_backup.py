from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .backup import export_all_json
from .db import Database


def _parse_stamp(path: Path) -> datetime | None:
    try:
        stamp = path.stem.removeprefix("auto-")
        return datetime.strptime(stamp, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def maybe_create_auto_backup(db: Database, *, now: datetime | None = None) -> Path | None:
    if os.getenv("LLM_AUTO_BACKUP", "1").strip().lower() in {"0", "false", "no", "off"}:
        return None
    now = now or datetime.now(timezone.utc)
    backup_dir = db.path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(backup_dir.glob("auto-*.json"), reverse=True)
    latest = _parse_stamp(files[0]) if files else None
    try:
        interval_hours = max(1, min(int(os.getenv("LLM_AUTO_BACKUP_HOURS", "24")), 168))
    except ValueError:
        interval_hours = 24
    if latest and now - latest < timedelta(hours=interval_hours):
        return None

    # Avoid creating meaningless files before the user has any learning data.
    with db.connect() as conn:
        has_data = any(
            int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) > 0
            for table in ("lesson_progress", "thoughts", "resources")
        )
    if not has_data:
        return None

    path = backup_dir / f"auto-{now.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(export_all_json(db), encoding="utf-8")
    try:
        keep = max(2, min(int(os.getenv("LLM_AUTO_BACKUP_KEEP", "10")), 50))
    except ValueError:
        keep = 10
    all_files = sorted(backup_dir.glob("auto-*.json"), reverse=True)
    for old in all_files[keep:]:
        old.unlink(missing_ok=True)
    return path
