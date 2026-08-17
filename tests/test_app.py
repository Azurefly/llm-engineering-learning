from fastapi.testclient import TestClient
from app.current import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_dashboard():
    r = client.get('/')
    assert r.status_code == 200
    assert 'LLM' in r.text


def test_course():
    r = client.get('/course/week01')
    assert r.status_code == 200
    assert 'Week 1' in r.text


def test_add_thought():
    r = client.post('/thoughts/save', data={'title':'Test thought','content':'# Insight','tags':'test','lesson_key':'week01'}, follow_redirects=False)
    assert r.status_code == 303


def test_add_resource():
    r = client.post('/resources/save', data={'title':'PyTorch','url':'https://pytorch.org','description':'Official','tags':'official','lesson_key':'week02'}, follow_redirects=False)
    assert r.status_code == 303


def test_current_feature_pages():
    for path in ('/coding-labs', '/adaptive', '/adaptive-test', '/data-management', '/question-bank'):
        r = client.get(path)
        assert r.status_code == 200, path
