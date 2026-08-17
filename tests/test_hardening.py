from fastapi.testclient import TestClient

from app.current import app

client = TestClient(app)


def test_security_headers_are_present():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert 'camera=()' in response.headers['permissions-policy']


def test_cross_site_write_is_blocked():
    response = client.post(
        '/thoughts/save',
        data={'title':'blocked','content':'x','tags':'','lesson_key':''},
        headers={'Origin':'https://evil.example', 'Sec-Fetch-Site':'cross-site'},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_same_origin_write_remains_allowed():
    response = client.post(
        '/thoughts/save',
        data={'title':'same-origin-hardening-test','content':'x','tags':'','lesson_key':''},
        headers={'Origin':'http://testserver'},
        follow_redirects=False,
    )
    assert response.status_code == 303
