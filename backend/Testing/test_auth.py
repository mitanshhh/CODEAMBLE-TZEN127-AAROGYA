def test_login_success(client, doc_user):
    response = client.post("/api/v1/auth/login", data={
        "username": "testdoc",
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials(client, doc_user):
    response = client.post("/api/v1/auth/login", data={
        "username": "testdoc",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_me(client, doc_token):
    headers = {"Authorization": f"Bearer {doc_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testdoc"

def test_unauthorized_access(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
