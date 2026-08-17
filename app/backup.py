from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .db import Database

BACKUP_FORMAT_VERSION = 2


def export_all_json(db: Database) -> str:
    """Export user-owned learning data with a versioned envelope."""
    preferred = [
        "lesson_progress",
        "thoughts",
        "resources",
        "exam_attempts",
        "exam_answers",
        "exam_v2_meta",
        "exam_attempt_questions",
        "exam_runtime",
        "code_attempts",
        "adaptive_sessions",
        "adaptive_session_items",
    ]
    tables: dict[str, list[dict[str, Any]]] = {}
    with db.connect() as conn:
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for table in preferred:
            if table in existing:
                tables[table] = [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]
    payload = {
        "format": "llm-engineering-learning-backup",
        "version": BACKUP_FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tables": tables,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
