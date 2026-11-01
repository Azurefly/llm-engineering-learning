"""Validation and refusal branches of the account and administration forms."""

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app import admin
from app.auth import account_store
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


@pytest.fixture
def admin_client(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_AUTH_TEST_BYPASS", "0")
    monkeypatch.setenv("LLM_ALLOW_REGISTRATION", "1")
    monkeypatch.setenv("LLM_LEARNING_DATA_DIR", str(tmp_path / "admin-errors"))
    client = TestClient(app)
    assert _register(client, "ownerx", "owner-password-123").status_code == 303
    return client


@pytest.fixture
def learner(admin_client):
    response = admin_client.post(
        "/admin/users/create",
        data={
            "username": "learnerx",
            "display_name": "Learner X",
            "password": "learner-password-123",
            "password_confirm": "learner-password-123",
            "role": "user",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    return account_store().get_user_by_username("learnerx")


def test_redirect_helpers_encode_status_and_errors():
    assert admin._account_redirect(status="saved").headers["location"] == "/account?status=saved"
    assert admin._account_redirect(error="bad name").headers["location"].startswith("/account?error=")
    assert admin._admin_redirect(status="created").headers["location"] == "/admin/users?status=created"
    assert admin._admin_redirect(error="bad name").headers["location"].startswith("/admin/users?error=")


def test_user_helper_requires_authentication():
    request = Request({"type": "http", "method": "GET", "path": "/account", "headers": [], "query_string": b""})

    with pytest.raises(Exception) as excinfo:
        admin._user(request)

    assert "Authentication required" in str(excinfo.value)


def test_account_profile_rejects_invalid_usernames(admin_client):
    response = admin_client.post(
        "/account/profile",
        data={"username": "a b", "display_name": "n"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/account?error=")


def test_account_profile_saves_a_valid_change(admin_client):
    response = admin_client.post(
        "/account/profile",
        data={"username": "ownerx2", "display_name": "Owner Two"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/account?status=profile-saved"
    assert account_store().get_user_by_username("ownerx2")["display_name"] == "Owner Two"


def test_account_profile_reports_a_taken_username(admin_client, learner):
    response = admin_client.post(
        "/account/profile",
        data={"username": "learnerx", "display_name": "Copycat"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/account?error=")


def test_account_password_rejects_short_passwords(admin_client):
    response = admin_client.post(
        "/account/password",
        data={"current_password": "owner-password-123", "new_password": "short", "new_password_confirm": "short"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/account?error=")


def test_account_password_rejects_mismatched_confirmation(admin_client):
    response = admin_client.post(
        "/account/password",
        data={
            "current_password": "owner-password-123",
            "new_password": "new-password-123",
            "new_password_confirm": "different-password",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/account?error=")


def test_account_password_rejects_a_wrong_current_password(admin_client):
    response = admin_client.post(
        "/account/password",
        data={
            "current_password": "wrong-password-999",
            "new_password": "new-password-123",
            "new_password_confirm": "new-password-123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/account?error=")


def test_admin_create_user_rejects_invalid_input(admin_client):
    short = admin_client.post(
        "/admin/users/create",
        data={"username": "ab", "password": "learner-password-123", "password_confirm": "learner-password-123"},
        follow_redirects=False,
    )
    assert short.headers["location"].startswith("/admin/users?error=")

    mismatch = admin_client.post(
        "/admin/users/create",
        data={"username": "newuser", "password": "learner-password-123", "password_confirm": "other-password"},
        follow_redirects=False,
    )
    assert mismatch.headers["location"].startswith("/admin/users?error=")

    bad_role = admin_client.post(
        "/admin/users/create",
        data={
            "username": "newuser",
            "password": "learner-password-123",
            "password_confirm": "learner-password-123",
            "role": "root",
        },
        follow_redirects=False,
    )
    assert bad_role.headers["location"].startswith("/admin/users?error=")


def test_admin_can_create_a_user_with_an_elevated_role(admin_client):
    response = admin_client.post(
        "/admin/users/create",
        data={
            "username": "deputy",
            "display_name": "Deputy",
            "password": "deputy-password-123",
            "password_confirm": "deputy-password-123",
            "role": "superadmin",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/users?status=created"
    assert account_store().get_user_by_username("deputy")["role"] == "superadmin"


def test_admin_create_user_reports_duplicate_usernames(admin_client, learner):
    response = admin_client.post(
        "/admin/users/create",
        data={
            "username": "learnerx",
            "password": "learner-password-123",
            "password_confirm": "learner-password-123",
            "role": "user",
        },
        follow_redirects=False,
    )
    assert response.headers["location"].startswith("/admin/users?error=")


def test_admin_update_profile_rejects_invalid_and_duplicate_usernames(admin_client, learner):
    invalid = admin_client.post(
        f"/admin/users/{learner['id']}/profile",
        data={"username": "a b", "display_name": "x"},
        follow_redirects=False,
    )
    assert invalid.headers["location"].startswith("/admin/users?error=")

    duplicate = admin_client.post(
        f"/admin/users/{learner['id']}/profile",
        data={"username": "ownerx", "display_name": "x"},
        follow_redirects=False,
    )
    assert duplicate.headers["location"].startswith("/admin/users?error=")


def test_admin_status_action_must_be_enable_or_disable(admin_client, learner):
    response = admin_client.post(
        f"/admin/users/{learner['id']}/status",
        data={"action": "explode"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/users?error=")


def test_admin_cannot_reset_its_own_password_from_the_panel(admin_client):
    owner = account_store().get_user_by_username("ownerx")

    response = admin_client.post(
        f"/admin/users/{owner['id']}/password",
        data={"new_password": "another-password-123", "new_password_confirm": "another-password-123"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/users?error=")


def test_admin_password_reset_validates_input_and_targets(admin_client, learner):
    short = admin_client.post(
        f"/admin/users/{learner['id']}/password",
        data={"new_password": "short", "new_password_confirm": "short"},
        follow_redirects=False,
    )
    assert short.headers["location"].startswith("/admin/users?error=")

    mismatch = admin_client.post(
        f"/admin/users/{learner['id']}/password",
        data={"new_password": "reset-password-123", "new_password_confirm": "other-password-123"},
        follow_redirects=False,
    )
    assert mismatch.headers["location"].startswith("/admin/users?error=")

    missing_user = admin_client.post(
        "/admin/users/99999999/password",
        data={"new_password": "reset-password-123", "new_password_confirm": "reset-password-123"},
        follow_redirects=False,
    )
    assert missing_user.headers["location"].startswith("/admin/users?error=")
