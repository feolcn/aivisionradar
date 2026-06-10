import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.seed import seed_all

TEST_DB_URL = "sqlite:///./data/test_aivisionradar.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    import os
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    seed_all(db)
    db.close()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("./data/test_aivisionradar.db")
    except FileNotFoundError:
        pass


class TestItemsAPI:
    def test_list_items_returns_200(self, client):
        response = client.get("/api/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)

    def test_list_items_pagination(self, client):
        response = client.get("/api/items?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    def test_get_nonexistent_item(self, client):
        response = client.get("/api/items/99999")
        assert response.status_code == 404

    def test_list_items_filter_type(self, client):
        response = client.get("/api/items?item_type=article")
        assert response.status_code == 200


class TestSourcesAPI:
    def test_list_sources(self, client):
        response = client.get("/api/sources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_create_source(self, client):
        payload = {
            "name": "Test Source",
            "type": "rss",
            "url": "https://example.com/feed.xml",
            "category": "test",
            "enabled": True,
        }
        response = client.post("/api/sources", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Source"
        assert data["type"] == "rss"
        assert data["id"] > 0

    def test_update_source(self, client):
        sources = client.get("/api/sources").json()
        if not sources:
            pytest.skip("No sources available")
        source_id = sources[0]["id"]
        response = client.put(f"/api/sources/{source_id}", json={"enabled": False})
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_delete_nonexistent_source(self, client):
        response = client.delete("/api/sources/99999")
        assert response.status_code == 404


class TestKeywordsAPI:
    def test_list_keywords(self, client):
        response = client.get("/api/keywords")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_create_keyword(self, client):
        payload = {
            "keyword": "test_unique_keyword_xyz",
            "category": "test",
            "weight": 2.5,
            "enabled": True,
        }
        response = client.post("/api/keywords", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["keyword"] == "test_unique_keyword_xyz"

    def test_create_duplicate_keyword(self, client):
        payload = {"keyword": "defect detection", "weight": 1.0}
        response = client.post("/api/keywords", json=payload)
        assert response.status_code == 409


class TestWebPages:
    def test_dashboard_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "AIVisionRadar" in response.text

    def test_items_page_loads(self, client):
        response = client.get("/items")
        assert response.status_code == 200

    def test_sources_page_loads(self, client):
        response = client.get("/sources")
        assert response.status_code == 200

    def test_keywords_page_loads(self, client):
        response = client.get("/keywords")
        assert response.status_code == 200

    def test_daily_report_page_loads(self, client):
        response = client.get("/reports/daily")
        assert response.status_code == 200
