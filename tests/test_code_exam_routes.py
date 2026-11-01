"""Coding-lab routes: challenge lookup, size limits and result ownership."""

from fastapi.testclient import TestClient

from app.code_exam import CHALLENGES
from app.current import app

client = TestClient(app)

LESSON_KEY = next(iter(CHALLENGES))


def test_coding_lab_page_renders_a_known_challenge():
    challenge = CHALLENGES[LESSON_KEY]
    response = client.get(f"/coding-labs/{LESSON_KEY}")

    assert response.status_code == 200
    assert challenge.starter[:20] in response.text
    assert f"/coding-labs/{LESSON_KEY}/run" in response.text


def test_coding_lab_page_rejects_unknown_challenges():
    assert client.get("/coding-labs/week99").status_code == 404


def test_running_an_unknown_challenge_is_not_found():
    response = client.post("/coding-labs/week99/run", data={"source_code": "x = 1"}, follow_redirects=False)
    assert response.status_code == 404


def test_oversized_source_code_is_rejected():
    response = client.post(
        f"/coding-labs/{LESSON_KEY}/run",
        data={"source_code": "x" * 20_001},
        follow_redirects=False,
    )
    assert response.status_code == 413
    assert "too large" in response.text.lower()


def test_result_page_rejects_unknown_challenges():
    assert client.get("/coding-labs/week99/result/1").status_code == 404


def test_result_page_rejects_unknown_attempts():
    assert client.get(f"/coding-labs/{LESSON_KEY}/result/99999999").status_code == 404
