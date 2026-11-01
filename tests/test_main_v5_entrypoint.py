"""The V5 versioned entrypoint stays importable as a compatibility layer."""

from fastapi.testclient import TestClient

from app.main_v5 import app as v5_app


def test_v5_entrypoint_serves_the_adaptive_routes():
    client = TestClient(v5_app)

    assert client.get("/adaptive").status_code == 200
    assert client.get("/adaptive-test").status_code == 200


def test_v5_entrypoint_keeps_the_earlier_assessment_layers():
    client = TestClient(v5_app)

    for path in ("/", "/exam-lab", "/coding-labs", "/question-bank"):
        assert client.get(path).status_code == 200, path
