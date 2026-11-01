"""Helpers behind the superadmin progress report."""

import sqlite3
from datetime import UTC, datetime

import pytest

from app import admin_reporting
from app.admin_reporting import _max_timestamp, _parse_time, _progress_band, read_user_progress


@pytest.mark.parametrize("value", [None, "", "   ", "not-a-date", "2026-13-45"])
def test_parse_time_returns_none_for_unusable_values(value):
    assert _parse_time(value) is None


def test_parse_time_accepts_zulu_suffix_and_naive_values():
    assert _parse_time("2026-08-17T10:00:00Z") == datetime(2026, 8, 17, 10, 0, 0, tzinfo=UTC)
    assert _parse_time("2026-08-17T10:00:00") == datetime(2026, 8, 17, 10, 0, 0, tzinfo=UTC)


def test_max_timestamp_returns_none_when_the_table_is_missing():
    conn = sqlite3.connect(":memory:")
    try:
        assert _max_timestamp(conn, "no_such_table", "created_at") is None
    finally:
        conn.close()


def test_max_timestamp_reads_the_latest_value():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE t(created_at TEXT)")
        conn.executemany("INSERT INTO t(created_at) VALUES(?)", [("2026-01-01",), ("2026-05-05",)])
        assert _max_timestamp(conn, "t", "created_at") == "2026-05-05"
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("value", "band"),
    [
        (0, "0"),
        (-5, "0"),
        (1, "1-24"),
        (24, "1-24"),
        (25, "25-49"),
        (50, "50-74"),
        (75, "75-99"),
        (99, "75-99"),
        (100, "100"),
        (140, "100"),
    ],
)
def test_progress_bands(value, band):
    assert _progress_band(value) == band


def test_reading_a_user_without_a_database_returns_an_empty_report(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path))
    user = {
        "id": 7,
        "username": "ghost",
        "display_name": "Ghost",
        "role": "user",
        "is_active": 1,
        "storage_key": "no-such-storage-key",
    }

    report = read_user_progress(user)

    assert report["db_exists"] is False
    assert report["overall_progress"] == 0.0
    assert report["username"] == "ghost"
    assert "storage_key" not in report


def test_collect_admin_report_marks_learners_without_activity(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path))
    report = admin_reporting.collect_admin_report()

    assert {"users", "week_stats", "progress_bands", "kpis"} <= set(report)
    assert report["kpis"]["total_users"] == 0
    assert report["users"] == []
