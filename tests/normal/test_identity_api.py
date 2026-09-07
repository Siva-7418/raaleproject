import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_list_identities(temp_db, monkeypatch):
    monkeypatch.setattr("backend.app.api.routes_identities.get_connection", lambda: __import__("backend.app.db.database", fromlist=["get_connection"]).get_connection(temp_db))
    
    response = client.get("/api/identities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 150

def test_filter_identities_by_department(temp_db, monkeypatch):
    monkeypatch.setattr("backend.app.api.routes_identities.get_connection", lambda: __import__("backend.app.db.database", fromlist=["get_connection"]).get_connection(temp_db))
    
    response = client.get("/api/identities?department=Biology")
    assert response.status_code == 200
    data = response.json()
    assert all(i["department"] == "Biology" for i in data)
