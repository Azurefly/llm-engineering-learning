from fastapi.testclient import TestClient

from app.auth import account_store, user_learning_path
from app.current import app
from app.db import Database, now_iso


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


def _seed_learning(storage_key: str, *, progress: list[tuple[str, str, int, float | None]], exam_scores: list[tuple[float, bool]], code_scores: list[tuple[float, bool]], private_note: str):
    db = Database(user_learning_path(storage_key))
    for lesson_key, status, percent, score in progress:
        db.set_progress(lesson_key, status, percent, score)
    db.save_thought(None, title=private_note, content="private-content", tags="secret", lesson_key="week01", language="zh-CN")

    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS exam_attempts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_key TEXT NOT NULL,
                language TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'started',
                started_at TEXT NOT NULL,
                submitted_at TEXT,
                score REAL,
                max_score REAL,
                percent REAL,
                passed INTEGER,
                pass_score REAL
            );
            CREATE TABLE IF NOT EXISTS code_attempts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_key TEXT NOT NULL,
                challenge_key TEXT NOT NULL,
                source_code TEXT NOT NULL,
                score_percent REAL NOT NULL DEFAULT 0,
                passed INTEGER NOT NULL DEFAULT 0,
                passed_tests INTEGER NOT NULL DEFAULT 0,
                total_tests INTEGER NOT NULL DEFAULT 0,
                stdout TEXT NOT NULL DEFAULT '',
                stderr TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        for index, (percent, passed) in enumerate(exam_scores):
            conn.execute(
                """INSERT INTO exam_attempts(lesson_key,language,status,started_at,submitted_at,score,max_score,percent,passed,pass_score)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                ("week01", "zh-CN", "submitted", now_iso(), now_iso(), percent, 100, percent, 1 if passed else 0, 80),
            )
        for index, (percent, passed) in enumerate(code_scores):
            conn.execute(
                """INSERT INTO code_attempts(lesson_key,challenge_key,source_code,score_percent,passed,passed_tests,total_tests,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                ("week02", f"challenge-{index}", "# private source is not reported", percent, 1 if passed else 0, 1 if passed else 0, 1, now_iso()),
            )


def test_superadmin_report_aggregates_all_progress_without_private_content(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "reporting"))

    admin_client = TestClient(app)
    assert _register(admin_client, "reportadmin", "admin-password-123", "Report Admin").status_code == 303
    assert admin_client.get("/").status_code == 200

    student_client = TestClient(app)
    assert _register(student_client, "learnerone", "learner-password-123", "Learner One").status_code == 303
    assert student_client.get("/").status_code == 200

    store = account_store()
    admin = store.get_user_by_username("reportadmin")
    student = store.get_user_by_username("learnerone")
    assert admin and student and admin["role"] == "superadmin" and student["role"] == "user"

    _seed_learning(
        admin["storage_key"],
        progress=[("week00", "completed", 100, 95), ("week01", "in_progress", 50, None)],
        exam_scores=[(90, True)],
        code_scores=[(100, True)],
        private_note="ADMIN-PRIVATE-NOTE-DO-NOT-LEAK",
    )
    _seed_learning(
        student["storage_key"],
        progress=[("week00", "completed", 100, 86), ("week01", "completed", 100, 88), ("week02", "in_progress", 40, None)],
        exam_scores=[(60, False), (85, True)],
        code_scores=[(50, False), (90, True)],
        private_note="STUDENT-PRIVATE-NOTE-DO-NOT-LEAK",
    )

    response = admin_client.get("/admin/report/data")
    assert response.status_code == 200
    payload = response.json()
    report = payload["report"]
    assert report["kpis"]["total_users"] == 2
    assert report["kpis"]["exam_attempts"] == 3
    assert report["kpis"]["code_attempts"] == 3
    assert len(report["week_stats"]) == 19

    by_username = {row["username"]: row for row in report["users"]}
    assert by_username["reportadmin"]["completed_lessons"] == 1
    assert by_username["learnerone"]["completed_lessons"] == 2
    assert by_username["learnerone"]["exam_attempts"] == 2
    assert by_username["learnerone"]["exam_pass_rate"] == 50.0
    assert by_username["learnerone"]["code_attempts"] == 2
    assert by_username["learnerone"]["code_pass_rate"] == 50.0

    serialized = response.text
    assert "password_hash" not in serialized
    assert "storage_key" not in serialized
    assert "db_path" not in serialized
    assert "ADMIN-PRIVATE-NOTE-DO-NOT-LEAK" not in serialized
    assert "STUDENT-PRIVATE-NOTE-DO-NOT-LEAK" not in serialized
    assert "private source is not reported" not in serialized

    big_screen = admin_client.get("/admin/report")
    assert big_screen.status_code == 200
    assert "Learner One" in big_screen.text
    assert "STUDENT-PRIVATE-NOTE-DO-NOT-LEAK" not in big_screen.text

    detail = admin_client.get(f"/admin/users/{student['id']}/progress")
    assert detail.status_code == 200
    assert "Learner One" in detail.text
    assert "100%" in detail.text
    assert "STUDENT-PRIVATE-NOTE-DO-NOT-LEAK" not in detail.text

    assert student_client.get("/admin/report").status_code == 403
    assert student_client.get("/admin/report/data").status_code == 403
    assert student_client.get(f"/admin/users/{student['id']}/progress").status_code == 403


def test_superadmin_can_stop_and_restart_public_registration_without_restart(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "registration-policy"))

    admin_client = TestClient(app)
    assert _register(admin_client, "policyadmin", "admin-password-123", "Policy Admin").status_code == 303
    admin = account_store().get_user_by_username("policyadmin")
    assert admin and admin["role"] == "superadmin"

    disabled = admin_client.post(
        "/admin/settings/registration",
        data={"action": "disable", "next": "/admin/users"},
        follow_redirects=False,
    )
    assert disabled.status_code == 303

    anonymous = TestClient(app)
    assert anonymous.get("/register").status_code == 403
    blocked = _register(anonymous, "blockeduser", "blocked-password-123", "Blocked")
    assert blocked.status_code == 403

    # Closing public registration does not prevent a superadmin from provisioning accounts.
    created = admin_client.post(
        "/admin/users/create",
        data={
            "username": "inviteduser",
            "display_name": "Invited User",
            "password": "invited-password-123",
            "password_confirm": "invited-password-123",
            "role": "user",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303
    assert account_store().get_user_by_username("inviteduser") is not None

    regular = TestClient(app)
    assert _login(regular, "inviteduser", "invited-password-123").status_code == 303
    assert regular.post(
        "/admin/settings/registration",
        data={"action": "enable", "next": "/"},
        follow_redirects=False,
    ).status_code == 403

    enabled = admin_client.post(
        "/admin/settings/registration",
        data={"action": "enable", "next": "/admin/users"},
        follow_redirects=False,
    )
    assert enabled.status_code == 303
    reopened = TestClient(app)
    assert reopened.get("/register").status_code == 200
    assert _register(reopened, "publicuser", "public-password-123", "Public User").status_code == 303
