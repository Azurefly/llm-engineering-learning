from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .db import Database

BACKUP_FORMAT_VERSION = 2
TABLE_ORDER = [
    "lesson_progress",
    "thoughts",
    "resources",
    "exam_attempts",
    "exam_answers",
    "exam_v2_meta",
    "exam_attempt_questions",
    "exam_question_snapshots",
    "exam_runtime",
    "code_attempts",
    "adaptive_sessions",
    "adaptive_session_items",
]


class BackupError(ValueError):
    pass


def _table_payload(db: Database) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {}
    with db.connect() as conn:
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for table in TABLE_ORDER:
            if table in existing:
                tables[table] = [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]
    return tables


def export_all_json(db: Database) -> str:
    """Export all learning data while preserving the original top-level table shape."""
    payload: dict[str, Any] = _table_payload(db)
    payload["_meta"] = {
        "format": "llm-engineering-learning-backup",
        "version": BACKUP_FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _validate_rows(table: str, rows: list[dict[str, Any]]) -> None:
    if table == "resources":
        for index, row in enumerate(rows, 1):
            url = str(row.get("url") or "").strip()
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise BackupError(f"resources row {index} contains an unsafe URL")
    elif table == "lesson_progress":
        for index, row in enumerate(rows, 1):
            if "percent" in row:
                try:
                    percent = int(row["percent"])
                except (TypeError, ValueError) as exc:
                    raise BackupError(f"lesson_progress row {index} has invalid percent") from exc
                if percent < 0 or percent > 100:
                    raise BackupError(f"lesson_progress row {index} percent must be between 0 and 100")
    elif table == "adaptive_sessions":
        for index, row in enumerate(rows, 1):
            if "max_items" in row:
                try:
                    max_items = int(row["max_items"])
                except (TypeError, ValueError) as exc:
                    raise BackupError(f"adaptive_sessions row {index} has invalid max_items") from exc
                if max_items < 1 or max_items > 100:
                    raise BackupError(f"adaptive_sessions row {index} max_items is outside the safe range")


def parse_backup_json(text: str) -> dict[str, list[dict[str, Any]]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BackupError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise BackupError("Backup root must be a JSON object")

    if payload.get("format") == "llm-engineering-learning-backup" and "tables" in payload:
        version = int(payload.get("version") or 0)
        if version < 1 or version > BACKUP_FORMAT_VERSION:
            raise BackupError(f"Unsupported backup version: {version}")
        tables = payload.get("tables")
    else:
        meta = payload.get("_meta")
        if meta is not None:
            if not isinstance(meta, dict) or meta.get("format") != "llm-engineering-learning-backup":
                raise BackupError("Invalid backup metadata")
            version = int(meta.get("version") or 0)
            if version < 1 or version > BACKUP_FORMAT_VERSION:
                raise BackupError(f"Unsupported backup version: {version}")
        tables = {key: value for key, value in payload.items() if key != "_meta"}

    if not isinstance(tables, dict):
        raise BackupError("Backup tables must be a JSON object")
    unknown = sorted(set(tables) - set(TABLE_ORDER))
    if unknown:
        raise BackupError("Backup contains unsupported tables: " + ", ".join(unknown))

    normalized: dict[str, list[dict[str, Any]]] = {}
    for table, rows in tables.items():
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise BackupError(f"Table {table} must contain a list of objects")
        _validate_rows(table, rows)
        normalized[table] = rows
    return normalized


def write_safety_snapshot(db: Database) -> Path:
    backup_dir = db.path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = backup_dir / f"pre-restore-{stamp}.json"
    path.write_text(export_all_json(db), encoding="utf-8")
    return path


def restore_from_json(db: Database, text: str, *, replace: bool = True) -> dict[str, int]:
    tables = parse_backup_json(text)
    write_safety_snapshot(db)
    restored: dict[str, int] = {}
    with db.connect() as conn:
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.execute("BEGIN IMMEDIATE")
            if replace:
                for table in reversed(TABLE_ORDER):
                    if table in existing:
                        conn.execute(f"DELETE FROM {table}")
            for table in TABLE_ORDER:
                rows = tables.get(table)
                if rows is None or table not in existing:
                    continue
                allowed_columns = [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                for row in rows:
                    columns = [col for col in allowed_columns if col in row]
                    if not columns:
                        continue
                    placeholders = ",".join("?" for _ in columns)
                    column_sql = ",".join(columns)
                    values = [row[col] for col in columns]
                    conn.execute(f"INSERT OR REPLACE INTO {table} ({column_sql}) VALUES ({placeholders})", values)
                restored[table] = len(rows)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
    return restored
