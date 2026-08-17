from fastapi.testclient import TestClient

from app.current import app

client = TestClient(app)


def test_data_management_page_exposes_restore_guard():
    response = client.get('/data-management')
    assert response.status_code == 200
    assert 'name="confirm"' in response.text
    assert 'value="replace"' in response.text


def test_restore_requires_explicit_confirmation():
    response = client.post(
        '/data-management/restore',
        files={'file': ('backup.json', b'{"thoughts":[]}', 'application/json')},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert 'confirmation' in response.text.lower()
