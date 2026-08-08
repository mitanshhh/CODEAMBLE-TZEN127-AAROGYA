from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_login_missing_creds():
    response = client.post("/api/v1/auth/login", data={})
    assert response.status_code == 422 # Unprocessable Entity because missing username/password

def test_unauthorized_access():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
