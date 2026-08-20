from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from .auth import account_store, user_learning_path
from .course import LESSONS


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _max_timestamp(conn: sqlite3.Connection, table: str, column: str) -> str | None:
    if not _table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT MAX({column}) FROM {table}").fetchone()
    return str(row[0]) if row and row[0] else None


def _empty_user_metrics(user: dict[str, Any]) -> dict[str, Any]:
    # Never carry password hashes, storage keys, or any other authentication secrets
    # into reporting payloads. The report is intentionally a progress-only view.
    return {
        "id": int(user["id"]),
        "username": str(user["username"]),
        "display_name": str(user.get("display_name") or user["username"]),
        "role": str(user.get("role") or "user"),
        "is_active": int(user.get("is_active") or 0),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
        "active_sessions": int(user.get("active_sessions") or 0),
        "db_exists": False,
        "overall_progress": 0.0,
        "started_lessons": 0,
        "completed_lessons": 0,
        "current_week": None,
        "exam_attempts": 0,
        "exam_avg": None,
        "exam_best": None,
        "exam_pass_rate": None,
        "code_attempts": 0,
        "code_avg": None,
        "code_best": None,
        "code_pass_rate": None,
        "last_activity": user.get("last_login_at"),
        "lessons": [],
    }


def read_user_progress(user: dict[str, Any]) -> dict[str, Any]:
    result = _empty_user_metrics(user)
    db_path = user_learning_path(str(user["storage_key"]))
    if not db_path.exists():
        return result

    result["db_exists"] = True
    conn = sqlite3.connect(db_path, timeout=3.0)
    conn.row_factory = sqlite3.Row
    try:
        progress_map: dict[str, dict[str, Any]] = {}
        if _table_exists(conn, "lesson_progress"):
            rows = conn.execute("SELECT lesson_key,status,percent,score,updated_at FROM lesson_progress").fetchall()
            progress_map = {str(row["lesson_key"]): dict(row) for row in rows}

        lesson_rows: list[dict[str, Any]] = []
        for lesson in LESSONS:
            row = progress_map.get(lesson.key, {})
            percent = int(row.get("percent") or 0)
            lesson_rows.append(
                {
                    "key": lesson.key,
                    "week": lesson.week,
                    "percent": percent,
                    "status": row.get("status") or "not_started",
                    "score": row.get("score"),
                    "updated_at": row.get("updated_at"),
                }
            )
        result["lessons"] = lesson_rows
        result["overall_progress"] = round(sum(x["percent"] for x in lesson_rows) / max(1, len(lesson_rows)), 1)
        result["started_lessons"] = sum(1 for x in lesson_rows if x["percent"] > 0)
        result["completed_lessons"] = sum(1 for x in lesson_rows if x["status"] == "completed" or x["percent"] >= 100)
        started = [x for x in lesson_rows if x["percent"] > 0]
        result["current_week"] = max((x["week"] for x in started), default=None)

        if _table_exists(conn, "exam_attempts"):
            row = conn.execute(
                """SELECT COUNT(*) AS attempts, AVG(percent) AS avg_score, MAX(percent) AS best_score,
                          SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) AS passed
                   FROM exam_attempts WHERE status='submitted'"""
            ).fetchone()
            attempts = int(row["attempts"] or 0)
            result["exam_attempts"] = attempts
            result["exam_avg"] = round(float(row["avg_score"]), 1) if row["avg_score"] is not None else None
            result["exam_best"] = round(float(row["best_score"]), 1) if row["best_score"] is not None else None
            result["exam_pass_rate"] = round(100.0 * int(row["passed"] or 0) / attempts, 1) if attempts else None

        if _table_exists(conn, "code_attempts"):
            row = conn.execute(
                """SELECT COUNT(*) AS attempts, AVG(score_percent) AS avg_score, MAX(score_percent) AS best_score,
                          SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) AS passed
                   FROM code_attempts"""
            ).fetchone()
            attempts = int(row["attempts"] or 0)
            result["code_attempts"] = attempts
            result["code_avg"] = round(float(row["avg_score"]), 1) if row["avg_score"] is not None else None
            result["code_best"] = round(float(row["best_score"]), 1) if row["best_score"] is not None else None
            result["code_pass_rate"] = round(100.0 * int(row["passed"] or 0) / attempts, 1) if attempts else None

        activity_candidates = [
            user.get("last_login_at"),
            _max_timestamp(conn, "lesson_progress", "updated_at"),
            _max_timestamp(conn, "exam_attempts", "submitted_at"),
            _max_timestamp(conn, "code_attempts", "created_at"),
        ]
        parsed = [(value, _parse_time(value)) for value in activity_candidates if value]
        parsed = [(value, dt) for value, dt in parsed if dt is not None]
        if parsed:
            result["last_activity"] = max(parsed, key=lambda item: item[1])[0]
        return result
    finally:
        conn.close()


def _progress_band(value: float) -> str:
    if value <= 0:
        return "0"
    if value < 25:
        return "1-24"
    if value < 50:
        return "25-49"
    if value < 75:
        return "50-74"
    if value < 100:
        return "75-99"
    return "100"


def collect_admin_report() -> dict[str, Any]:
    users = [read_user_progress(user) for user in account_store().list_users()]
    now = datetime.now(timezone.utc)
    enabled_users = [u for u in users if int(u.get("is_active") or 0) == 1]
    started_users = [u for u in enabled_users if u["started_lessons"] > 0]
    exam_attempts = sum(int(u["exam_attempts"]) for u in users)
    code_attempts = sum(int(u["code_attempts"]) for u in users)

    weighted_exam_pass = sum((u["exam_pass_rate"] or 0) * u["exam_attempts"] for u in users)
    weighted_code_pass = sum((u["code_pass_rate"] or 0) * u["code_attempts"] for u in users)
    active_7d = sum(1 for u in enabled_users if (_parse_time(u.get("last_activity")) or datetime.min.replace(tzinfo=timezone.utc)) >= now - timedelta(days=7))

    week_stats: list[dict[str, Any]] = []
    for lesson in LESSONS:
        rows = [next((x for x in u["lessons"] if x["key"] == lesson.key), None) for u in users]
        rows = [x for x in rows if x is not None]
        average = round(sum(int(x["percent"]) for x in rows) / max(1, len(users)), 1)
        week_stats.append(
            {
                "key": lesson.key,
                "week": lesson.week,
                "average": average,
                "started": sum(1 for x in rows if int(x["percent"]) > 0),
                "completed": sum(1 for x in rows if x["status"] == "completed" or int(x["percent"]) >= 100),
            }
        )

    bands = {"0": 0, "1-24": 0, "25-49": 0, "50-74": 0, "75-99": 0, "100": 0}
    for user in users:
        bands[_progress_band(float(user["overall_progress"]))] += 1

    users_sorted = sorted(users, key=lambda u: (float(u["overall_progress"]), int(u["completed_lessons"]), int(u["exam_attempts"])), reverse=True)
    return {
        "users": users_sorted,
        "week_stats": week_stats,
        "progress_bands": bands,
        "kpis": {
            "total_users": len(users),
            "enabled_users": len(enabled_users),
            "learning_users": len(started_users),
            "active_7d": active_7d,
            "average_progress": round(sum(float(u["overall_progress"]) for u in users) / max(1, len(users)), 1),
            "completed_lessons": sum(int(u["completed_lessons"]) for u in users),
            "exam_attempts": exam_attempts,
            "exam_pass_rate": round(weighted_exam_pass / exam_attempts, 1) if exam_attempts else None,
            "code_attempts": code_attempts,
            "code_pass_rate": round(weighted_code_pass / code_attempts, 1) if code_attempts else None,
        },
    }


def user_progress_report(user_id: int) -> dict[str, Any] | None:
    user = account_store().get_user_by_id(int(user_id))
    if not user:
        return None
    return read_user_progress(user)
