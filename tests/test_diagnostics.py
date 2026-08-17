from fastapi.testclient import TestClient

from app.current import app
from app.diagnostics import diagnostic_report

client = TestClient(app)


def test_diagnostics_report_is_healthy():
    report = diagnostic_report()
    assert report['database']['integrity'].lower() == 'ok'
    assert report['database']['journal_mode'].lower() == 'wal'
    assert report['question_bank']['ok'] is True
    assert report['question_bank']['total'] >= 180


def test_diagnostics_page_and_api():
    page = client.get('/diagnostics')
    api = client.get('/api/diagnostics')
    assert page.status_code == 200
    assert 'SYSTEM HEALTH' in page.text
    assert api.status_code == 200
    assert api.json()['ok'] is True
