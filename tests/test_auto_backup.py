from datetime import datetime, timedelta, timezone

from app.auto_backup import maybe_create_auto_backup
from app.db import Database, now_iso


def test_auto_backup_skips_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv('LLM_AUTO_BACKUP', '1')
    db = Database(tmp_path / 'learning.db')
    assert maybe_create_auto_backup(db, now=datetime(2026, 8, 17, tzinfo=timezone.utc)) is None


def test_auto_backup_is_daily_and_retained(tmp_path, monkeypatch):
    monkeypatch.setenv('LLM_AUTO_BACKUP', '1')
    monkeypatch.setenv('LLM_AUTO_BACKUP_HOURS', '24')
    monkeypatch.setenv('LLM_AUTO_BACKUP_KEEP', '2')
    db = Database(tmp_path / 'learning.db')
    db.save_thought(None, title='backup me', content='content', tags='', lesson_key='week01', language='en')

    base = datetime(2026, 8, 14, 8, 0, 0, tzinfo=timezone.utc)
    first = maybe_create_auto_backup(db, now=base)
    assert first and first.exists()
    assert maybe_create_auto_backup(db, now=base + timedelta(hours=1)) is None
    second = maybe_create_auto_backup(db, now=base + timedelta(days=1, minutes=1))
    third = maybe_create_auto_backup(db, now=base + timedelta(days=2, minutes=2))
    assert second and third
    files = sorted((tmp_path / 'backups').glob('auto-*.json'))
    assert len(files) == 2
    assert first not in files
