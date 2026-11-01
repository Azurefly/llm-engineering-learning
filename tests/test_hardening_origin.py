"""Same-origin enforcement for state-changing requests."""

from fastapi import FastAPI
from starlette.requests import Request

from app import hardening


def _request(headers: dict[str, str], method: str = "POST") -> Request:
    raw = [(key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in headers.items()]
    return Request({"type": "http", "method": method, "path": "/x", "query_string": b"", "headers": raw})


def test_cross_site_fetch_metadata_is_rejected():
    assert hardening._same_origin(_request({"host": "testserver", "sec-fetch-site": "cross-site"})) is False


def test_matching_origin_is_accepted():
    assert hardening._same_origin(_request({"host": "testserver", "origin": "http://testserver"})) is True


def test_mismatched_origin_is_rejected():
    assert hardening._same_origin(_request({"host": "testserver", "origin": "http://evil.example"})) is False


def test_malformed_origin_is_rejected():
    assert hardening._same_origin(_request({"host": "testserver", "origin": "http://[::1"})) is False


def test_referer_is_used_when_no_origin_is_sent():
    assert hardening._same_origin(_request({"host": "testserver", "referer": "http://testserver/course"})) is True
    assert hardening._same_origin(_request({"host": "testserver", "referer": "http://evil.example/x"})) is False


def test_malformed_referer_is_rejected():
    assert hardening._same_origin(_request({"host": "testserver", "referer": "http://[::1"})) is False


def test_requests_without_origin_or_referer_are_treated_as_local():
    # CLI clients and local scripts send neither header.
    assert hardening._same_origin(_request({"host": "testserver"})) is True


def test_installing_security_headers_twice_is_a_no_op():
    app = FastAPI()

    hardening.install_security_headers(app)
    hardening.install_security_headers(app)

    assert app.state.security_headers_installed is True


def test_cross_site_write_requests_are_blocked_by_the_middleware():
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.post("/write")
    def write():
        return {"ok": True}

    hardening.install_security_headers(app)
    client = TestClient(app)

    blocked = client.post("/write", headers={"sec-fetch-site": "cross-site"})
    assert blocked.status_code == 403
    assert "blocked" in blocked.text.lower()

    allowed = client.post("/write", headers={"origin": "http://testserver"})
    assert allowed.status_code == 200


def test_sensitive_paths_are_not_cached():
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/backup.json")
    def backup():
        return {"ok": True}

    hardening.install_security_headers(app)
    response = TestClient(app).get("/backup.json")

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
