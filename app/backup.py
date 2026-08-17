from __future__ import annotations

import json
from typing import Any

from .db import Database


def export_all_json(db: Database) -> str:
    """Export all user-owned learning data, including exam attempts and answers."""
    preferred = ["lesson_progress", "thoughts", "resources", "exam_attempts", "exam_answers"]
    payload: dict[str, list[dict[str, Any]]] = {}
    with db.connect() as conn:
        existing = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        for table in preferred:
            if table in existing:
                payload[table] = [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]
    return json.dumps(payload, ensure_ascii=False, indent=2)
