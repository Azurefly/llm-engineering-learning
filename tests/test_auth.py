import sqlite3

from fastapi.testclient import TestClient

from app.auth import account_store, hash_password, verify_password
from app.current import app


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("correct-horse-battery")
    second = hash_password("correct-horse-battery")
    assert first != second
    assert verify_password("correct-horse-battery", first)
    assert not verify_password("wrong-password", first)


def test_registration_login_and_physical_user_isolation(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/login")

    r = client.post(
        "/register",
        data={
            "username": "alice",
            "display_name": "Alice",
            "password": "alice-password-123",
            "password_confirm": "alice-password-123",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert client.get("/").status_code == 200
    assert client.post(
        "/thoughts/save",
        data={"title": "Alice private note", "content": "alice-secret", "tags": "private", "lesson_key": "week01"},
        follow_redirects=False,
    ).status_code == 303

    assert client.post("/logout", follow_redirects=False).status_code == 303
    assert client.get("/", follow_redirects=False).status_code == 303

    bad = client.post(
        "/login",
        data={"username": "alice", "password": "wrong-password", "next": "/"},
        follow_redirects=False,
    )
    assert bad.status_code == 401

    r = client.post(
        "/register",
        data={
            "username": "bob",
            "display_name": "Bob",
            "password": "bob-password-123",
            "password_confirm": "bob-password-123",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert client.post(
        "/thoughts/save",
        data={"title": "Bob private note", "content": "bob-secret", "tags": "private", "lesson_key": "week02"},
        follow_redirects=False,
    ).status_code == 303

    bob_page = client.get("/thoughts")
    assert "Bob private note" in bob_page.text
    assert "Alice private note" not in bob_page.text

    store = account_store()
    alice = store.get_user_by_username("alice")
    bob = store.get_user_by_username("bob")
    assert alice and bob
    assert alice["storage_key"] != bob["storage_key"]

    alice_db = tmp_path / "users" / alice["storage_key"] / "learning.db"
    bob_db = tmp_path / "users" / bob["storage_key"] / "learning.db"
    assert alice_db.exists() and bob_db.exists() and alice_db != bob_db

    with sqlite3.connect(alice_db) as conn:
        titles = [row[0] for row in conn.execute("SELECT title FROM thoughts ORDER BY id")]
        assert "Alice private note" in titles
        assert "Bob private note" not in titles
    with sqlite3.connect(bob_db) as conn:
        titles = [row[0] for row in conn.execute("SELECT title FROM thoughts ORDER BY id")]
        assert "Bob private note" in titles
        assert "Alice private note" not in titles

    client.post("/logout", follow_redirects=False)
    login = client.post(
        "/login",
        data={"username": "alice", "password": "alice-password-123", "next": "/thoughts"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    alice_page = client.get("/thoughts")
    assert "Alice private note" in alice_page.text
    assert "Bob private note" not in alice_page.text


def test_registration_can_be_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "0")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "closed"))
    client = TestClient(app)
    page = client.get("/register")
    assert page.status_code == 403
    blocked = client.post(
        "/register",
        data={"username": "newuser", "display_name": "New", "password": "password-123", "password_confirm": "password-123"},
    )
    assert blocked.status_code == 403
