from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tfidf() -> None:
    response = client.get("/tfidf")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
