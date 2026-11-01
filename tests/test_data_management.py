import pytest
from fastapi.testclient import TestClient

from app import data_management
from app.backup import BackupError
from app.current import app

client = TestClient(app)


def _restore(files, confirm="replace"):
    return client.post(
        "/data-management/restore",
        files=files,
        data={"confirm": confirm},
        follow_redirects=False,
    )


def test_data_management_page_exposes_restore_guard():
    response = client.get("/data-management")
    assert response.status_code == 200
    assert 'name="confirm"' in response.text
    assert 'value="replace"' in response.text


def test_restore_requires_explicit_confirmation():
    response = client.post(
        "/data-management/restore",
        files={"file": ("backup.json", b'{"thoughts":[]}', "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "confirmation" in response.text.lower()


def test_restore_rejects_non_json_uploads():
    response = _restore({"file": ("backup.zip", b'{"thoughts":[]}', "application/zip")})
    assert response.status_code == 400
    assert "JSON" in response.text


def test_restore_rejects_oversized_uploads(monkeypatch):
    monkeypatch.setattr(data_management, "_restore_limit_bytes", lambda: 8)
    response = _restore({"file": ("backup.json", b'{"thoughts": [1]}', "application/json")})
    assert response.status_code == 413
    assert "exceeds" in response.text


def test_restore_rejects_non_utf8_uploads():
    response = _restore({"file": ("backup.json", b"\xff\xfe\x00\x00", "application/json")})
    assert response.status_code == 400
    assert "UTF-8" in response.text


def test_restore_surfaces_backup_errors_as_bad_request(monkeypatch):
    def reject(db, text, replace=False):
        raise BackupError("unknown table: users")

    monkeypatch.setattr(data_management, "restore_from_json", reject)
    response = _restore({"file": ("backup.json", b'{"users": []}', "application/json")})
    assert response.status_code == 400
    assert "unknown table" in response.text


def test_restore_surfaces_unexpected_failures_as_conflict(monkeypatch):
    def explode(db, text, replace=False):
        raise RuntimeError("disk is full")

    monkeypatch.setattr(data_management, "restore_from_json", explode)
    response = _restore({"file": ("backup.json", b'{"thoughts": []}', "application/json")})
    assert response.status_code == 409
    assert "disk is full" in response.text


def test_restore_redirects_with_the_restored_row_count(monkeypatch):
    def accept(db, text, replace=False):
        assert replace is True
        return {"thoughts": 2, "resources": 1}

    monkeypatch.setattr(data_management, "restore_from_json", accept)
    response = _restore({"file": ("backup.json", b'{"thoughts": [], "resources": []}', "application/json")})
    assert response.status_code == 303
    assert response.headers["location"] == "/data-management?status=restored-3"


def test_restore_limit_defaults_to_50mb(monkeypatch):
    monkeypatch.delenv("LLM_RESTORE_MAX_MB", raising=False)
    assert data_management._restore_limit_bytes() == 50 * 1024 * 1024


@pytest.mark.parametrize(
    ("configured", "expected_mb"),
    [
        ("not-a-number", 50),
        ("0", 1),
        ("9999", 500),
        ("12", 12),
    ],
)
def test_restore_limit_is_parsed_and_clamped(monkeypatch, configured, expected_mb):
    monkeypatch.setenv("LLM_RESTORE_MAX_MB", configured)
    assert data_management._restore_limit_bytes() == expected_mb * 1024 * 1024
