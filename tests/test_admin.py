import sqlite3

from fastapi.testclient import TestClient

from app.auth import AccountStore, account_store, hash_password
from app.current import app


def _register(client: TestClient, username: str, password: str, display_name: str | None = None):
    return client.post(
        "/register",
        data={
            "username": username,
            "display_name": display_name or username,
            "password": password,
            "password_confirm": password,
        },
        follow_redirects=False,
    )


def _login(client: TestClient, username: str, password: str):
    return client.post(
        "/login",
        data={"username": username, "password": password, "next": "/"},
        follow_redirects=False,
    )


def test_first_user_is_superadmin_and_regular_user_cannot_open_admin(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "roles"))

    admin_client = TestClient(app)
    assert _register(admin_client, "rootadmin", "root-password-123", "Root Admin").status_code == 303
    store = account_store()
    root = store.get_user_by_username("rootadmin")
    assert root and root["role"] == "superadmin"
    assert admin_client.get("/admin/users").status_code == 200
    assert "用户管理" in admin_client.get("/admin/users").text or "User Administration" in admin_client.get("/admin/users").text

    user_client = TestClient(app)
    assert _register(user_client, "student", "student-password-123", "Student").status_code == 303
    student = store.get_user_by_username("student")
    assert student and student["role"] == "user"
    assert user_client.get("/admin/users").status_code == 403
    assert user_client.get("/account").status_code == 200


def test_superadmin_can_manage_registration_info_password_status_and_role(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "management"))

    admin_client = TestClient(app)
    assert _register(admin_client, "owner", "owner-password-123", "Owner").status_code == 303
    store = account_store()
    owner = store.get_user_by_username("owner")
    assert owner and owner["role"] == "superadmin"

    create = admin_client.post(
        "/admin/users/create",
        data={
            "username": "learner",
            "display_name": "Learner",
            "password": "learner-password-123",
            "password_confirm": "learner-password-123",
            "role": "user",
        },
        follow_redirects=False,
    )
    assert create.status_code == 303
    learner = store.get_user_by_username("learner")
    assert learner and learner["role"] == "user"

    user_client = TestClient(app)
    assert _login(user_client, "learner", "learner-password-123").status_code == 303
    assert user_client.get("/").status_code == 200

    profile = admin_client.post(
        f"/admin/users/{learner['id']}/profile",
        data={"username": "learner2", "display_name": "Learner Two"},
        follow_redirects=False,
    )
    assert profile.status_code == 303
    renamed = store.get_user_by_username("learner2")
    assert renamed and renamed["display_name"] == "Learner Two"

    reset = admin_client.post(
        f"/admin/users/{learner['id']}/password",
        data={"new_password": "new-password-456", "new_password_confirm": "new-password-456"},
        follow_redirects=False,
    )
    assert reset.status_code == 303
    # Password reset revokes every pre-existing session immediately.
    expired = user_client.get("/", follow_redirects=False)
    assert expired.status_code == 303 and expired.headers["location"].startswith("/login")
    assert _login(TestClient(app), "learner2", "learner-password-123").status_code == 401

    fresh_user = TestClient(app)
    assert _login(fresh_user, "learner2", "new-password-456").status_code == 303

    disable = admin_client.post(
        f"/admin/users/{learner['id']}/status",
        data={"action": "disable"},
        follow_redirects=False,
    )
    assert disable.status_code == 303
    assert fresh_user.get("/", follow_redirects=False).status_code == 303
    assert _login(TestClient(app), "learner2", "new-password-456").status_code == 401

    enable = admin_client.post(
        f"/admin/users/{learner['id']}/status",
        data={"action": "enable"},
        follow_redirects=False,
    )
    assert enable.status_code == 303
    assert _login(TestClient(app), "learner2", "new-password-456").status_code == 303

    promote = admin_client.post(
        f"/admin/users/{learner['id']}/role",
        data={"role": "superadmin"},
        follow_redirects=False,
    )
    assert promote.status_code == 303
    assert store.get_user_by_username("learner2")["role"] == "superadmin"

    # The current superadmin cannot demote or disable itself from the admin panel.
    demote_self = admin_client.post(
        f"/admin/users/{owner['id']}/role",
        data={"role": "user"},
        follow_redirects=False,
    )
    assert demote_self.status_code == 303
    assert store.get_user_by_username("owner")["role"] == "superadmin"
    disable_self = admin_client.post(
        f"/admin/users/{owner['id']}/status",
        data={"action": "disable"},
        follow_redirects=False,
    )
    assert disable_self.status_code == 303
    assert store.get_user_by_username("owner")["is_active"] == 1


def test_user_can_change_own_password_and_all_sessions_are_revoked(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "self-password"))

    client = TestClient(app)
    assert _register(client, "selfuser", "old-password-123", "Self User").status_code == 303
    changed = client.post(
        "/account/password",
        data={
            "current_password": "old-password-123",
            "new_password": "new-password-789",
            "new_password_confirm": "new-password-789",
        },
        follow_redirects=False,
    )
    assert changed.status_code == 303
    assert changed.headers["location"].startswith("/login")
    assert client.get("/", follow_redirects=False).status_code == 303
    assert _login(TestClient(app), "selfuser", "old-password-123").status_code == 401
    assert _login(TestClient(app), "selfuser", "new-password-789").status_code == 303


def test_existing_account_database_is_migrated_to_have_a_superadmin(tmp_path):
    path = tmp_path / "accounts.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                username_key TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                storage_key TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE auth_sessions(
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """INSERT INTO users(username,username_key,display_name,password_hash,storage_key,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?)""",
            ("legacy", "legacy", "Legacy", hash_password("legacy-password-123"), "legacy-storage", "2026-01-01", "2026-01-01"),
        )
    store = AccountStore(path)
    migrated = store.get_user_by_username("legacy")
    assert migrated and migrated["role"] == "superadmin"
