"""Route-level coverage for the core learning flows (dashboard, course, notes, links)."""

import pytest
from fastapi.testclient import TestClient

from app.current import app
from app.main import db

client = TestClient(app)


def _thought_ids() -> set[int]:
    return {int(item["id"]) for item in db.list_thoughts()}


def _resource_ids() -> set[int]:
    return {int(item["id"]) for item in db.list_resources()}


@pytest.fixture
def thought():
    """A saved note, removed again afterwards."""
    before = _thought_ids()
    client.post(
        "/thoughts/save",
        data={"title": "route test note", "content": "body", "tags": "route", "lesson_key": "week01"},
        follow_redirects=False,
    )
    new_id = max(_thought_ids() - before)
    yield new_id
    db.delete_thought(new_id)


@pytest.fixture
def resource():
    """A saved resource, removed again afterwards."""
    before = _resource_ids()
    client.post(
        "/resources/save",
        data={
            "title": "route test link",
            "url": "https://example.com/route",
            "description": "d",
            "tags": "route",
            "lesson_key": "week01",
        },
        follow_redirects=False,
    )
    new_id = max(_resource_ids() - before)
    yield new_id
    db.delete_resource(new_id)


def test_language_switch_sets_the_cookie_and_redirects():
    response = client.get("/language/en?next=/course/week01", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/course/week01"
    assert response.cookies.get("lang") == "en"


@pytest.mark.parametrize("target", ["//evil.example.com", "https://evil.example.com", "relative/path"])
def test_language_switch_refuses_offsite_redirects(target):
    response = client.get("/language/en", params={"next": target}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_unknown_lesson_returns_404():
    assert client.get("/course/week99").status_code == 404


def test_progress_update_is_clamped_and_recorded():
    lesson_key = "week12"
    original = db.all_progress().get(lesson_key)
    try:
        response = client.post(
            f"/course/{lesson_key}/progress",
            data={"percent": "150"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == f"/course/{lesson_key}"
        stored = db.all_progress()[lesson_key]
        assert stored["percent"] == 99
        assert stored["status"] == "in_progress"

        zero = client.post(f"/course/{lesson_key}/progress", data={"percent": "0"}, follow_redirects=False)
        assert zero.status_code == 303
        assert db.all_progress()[lesson_key]["status"] == "not_started"
    finally:
        if original:
            db.set_progress(lesson_key, original["status"], original["percent"], original.get("score"))
        else:
            with db.connect() as conn:
                conn.execute("DELETE FROM lesson_progress WHERE lesson_key=?", (lesson_key,))


def test_progress_update_rejects_unknown_lessons():
    assert client.post("/course/week99/progress", data={"percent": "10"}, follow_redirects=False).status_code == 404


def test_progress_update_does_not_downgrade_a_completed_lesson():
    lesson_key = "week13"
    original = db.all_progress().get(lesson_key)
    try:
        db.set_progress(lesson_key, "completed", 100, 95.0)
        response = client.post(f"/course/{lesson_key}/progress", data={"percent": "10"}, follow_redirects=False)
        assert response.status_code == 303
        assert db.all_progress()[lesson_key]["status"] == "completed"
        assert db.all_progress()[lesson_key]["percent"] == 100
    finally:
        if original:
            db.set_progress(lesson_key, original["status"], original["percent"], original.get("score"))
        else:
            with db.connect() as conn:
                conn.execute("DELETE FROM lesson_progress WHERE lesson_key=?", (lesson_key,))


def test_thought_pages_list_and_render_forms(thought):
    assert client.get("/thoughts").status_code == 200
    assert client.get("/thoughts", params={"lesson": "week01"}).status_code == 200
    assert client.get("/thoughts/new").status_code == 200
    assert client.get("/thoughts/new", params={"lesson": "week01"}).status_code == 200
    assert client.get(f"/thoughts/{thought}/edit").status_code == 200


def test_editing_an_unknown_thought_returns_404():
    assert client.get("/thoughts/99999999/edit").status_code == 404


def test_thought_can_be_updated_in_place(thought):
    response = client.post(
        "/thoughts/save",
        data={
            "item_id": str(thought),
            "title": "route test note v2",
            "content": "updated",
            "tags": "route",
            "lesson_key": "week01",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/course/week01"
    updated = [item for item in db.list_thoughts() if int(item["id"]) == thought][0]
    assert updated["title"] == "route test note v2"


def test_thought_delete_redirects_to_the_list(thought):
    response = client.post(f"/thoughts/{thought}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/thoughts"
    assert thought not in _thought_ids()


def test_resource_pages_list_and_render_forms(resource):
    assert client.get("/resources").status_code == 200
    assert client.get("/resources", params={"lesson": "week01"}).status_code == 200
    assert client.get("/resources/new").status_code == 200
    assert client.get(f"/resources/{resource}/edit").status_code == 200


def test_editing_an_unknown_resource_returns_404():
    assert client.get("/resources/99999999/edit").status_code == 404


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://example.com/x", "/relative/path", "https://"])
def test_resource_save_rejects_unsafe_urls(url):
    response = client.post(
        "/resources/save",
        data={"title": "bad link", "url": url, "description": "", "tags": "", "lesson_key": ""},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "http" in response.text


def test_resource_can_be_updated_in_place(resource):
    response = client.post(
        "/resources/save",
        data={
            "item_id": str(resource),
            "title": "route test link v2",
            "url": "https://example.com/v2",
            "description": "d2",
            "tags": "route",
            "lesson_key": "week02",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/course/week02"
    updated = [item for item in db.list_resources() if int(item["id"]) == resource][0]
    assert updated["title"] == "route test link v2"
    assert updated["url"] == "https://example.com/v2"


def test_resource_delete_redirects_to_the_list(resource):
    response = client.post(f"/resources/{resource}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/resources"
    assert resource not in _resource_ids()
