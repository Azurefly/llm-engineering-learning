from fastapi.testclient import TestClient

from app.current import app
from app.exam_v2 import db

client = TestClient(app)


def test_search_finds_course_content():
    response = client.get('/search?q=Transformer')
    assert response.status_code == 200
    assert 'Transformer' in response.text


def test_search_finds_personal_thought_and_resource():
    thought_id = db.save_thought(None, title='Unique adaptive insight', content='cat-selection-signal-987', tags='cat', lesson_key='week12', language='en')
    resource_id = db.save_resource(None, title='Unique retrieval reference', url='https://example.com/retrieval-987', description='hybrid-search-signal-987', tags='retrieval', lesson_key='week09', language='en')
    try:
        thought = client.get('/search?q=cat-selection-signal-987')
        resource = client.get('/search?q=hybrid-search-signal-987')
        assert thought.status_code == 200 and 'Unique adaptive insight' in thought.text
        assert resource.status_code == 200 and 'Unique retrieval reference' in resource.text
    finally:
        db.delete_thought(thought_id)
        db.delete_resource(resource_id)
