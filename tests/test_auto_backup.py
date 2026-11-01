from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.auto_backup import _parse_stamp, maybe_create_auto_backup
from app.db import Database


def test_auto_backup_skips_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_AUTO_BACKUP", "1")
    db = Database(tmp_path / "learning.db")
    assert maybe_create_auto_backup(db, now=datetime(2026, 8, 17, tzinfo=UTC)) is None


def test_auto_backup_is_daily_and_retained(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_AUTO_BACKUP", "1")
    monkeypatch.setenv("LLM_AUTO_BACKUP_HOURS", "24")
    monkeypatch.setenv("LLM_AUTO_BACKUP_KEEP", "2")
    db = Database(tmp_path / "learning.db")
    db.save_thought(None, title="backup me", content="content", tags="", lesson_key="week01", language="en")

    base = datetime(2026, 8, 14, 8, 0, 0, tzinfo=UTC)
    first = maybe_create_auto_backup(db, now=base)
    assert first and first.exists()
    assert maybe_create_auto_backup(db, now=base + timedelta(hours=1)) is None
    second = maybe_create_auto_backup(db, now=base + timedelta(days=1, minutes=1))
    third = maybe_create_auto_backup(db, now=base + timedelta(days=2, minutes=2))
    assert second and third
    files = sorted((tmp_path / "backups").glob("auto-*.json"))
    assert len(files) == 2
    assert first not in files


def test_auto_backup_can_be_switched_off(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_AUTO_BACKUP", "off")
    db = Database(tmp_path / "learning.db")
    db.save_thought(None, title="t", content="c", tags="", lesson_key="week01", language="en")

    assert maybe_create_auto_backup(db) is None


def test_parse_stamp_ignores_unexpected_file_names():
    assert _parse_stamp(Path("auto-not-a-timestamp.json")) is None
    assert _parse_stamp(Path("auto-20260817-101010.json")) == datetime(2026, 8, 17, 10, 10, 10, tzinfo=UTC)


def test_invalid_hours_setting_falls_back_to_daily(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_AUTO_BACKUP", "1")
    monkeypatch.setenv("LLM_AUTO_BACKUP_HOURS", "not-a-number")
    db = Database(tmp_path / "learning.db")
    db.save_thought(None, title="t", content="c", tags="", lesson_key="week01", language="en")

    base = datetime(2026, 8, 17, 8, 0, 0, tzinfo=UTC)
    assert maybe_create_auto_backup(db, now=base) is not None
    assert maybe_create_auto_backup(db, now=base + timedelta(hours=1)) is None
    assert maybe_create_auto_backup(db, now=base + timedelta(hours=25)) is not None


def test_invalid_keep_setting_falls_back_to_ten(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_AUTO_BACKUP", "1")
    monkeypatch.setenv("LLM_AUTO_BACKUP_KEEP", "not-a-number")
    db = Database(tmp_path / "learning.db")
    db.save_thought(None, title="t", content="c", tags="", lesson_key="week01", language="en")

    backups = tmp_path / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    (backups / "auto-broken.json").write_text("{}", encoding="utf-8")
    for month in range(1, 13):
        (backups / f"auto-2020{month:02d}01-000000.json").write_text("{}", encoding="utf-8")

    created = maybe_create_auto_backup(db, now=datetime(2026, 8, 17, tzinfo=UTC))

    assert created is not None
    assert len(sorted(backups.glob("auto-*.json"))) == 10
