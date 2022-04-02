from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

page_url = "https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FTf-idf"
limit = 10


def test_static_tfidf() -> None:
    response = client.get(f"/tfidf?url={page_url}&limit={limit}&dynamic=false")
    assert response.status_code == 200

    result = response.json()
    assert "terms" in result
    assert "idf" in result.get("terms")


def test_dynamic_tfidf() -> None:
    response = client.get(f"/tfidf?url={page_url}&limit={limit}")
    assert response.status_code == 200

    result = response.json()
    assert "terms" in result
    assert "idf" in result.get("terms")


def test_page_content() -> None:
    response = client.get(f"/page_content?url={page_url}")

    assert response.status_code == 200
    assert "tf–idf" in response.json()
