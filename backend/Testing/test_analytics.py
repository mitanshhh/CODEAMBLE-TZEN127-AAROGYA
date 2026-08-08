def test_analytics_health_score(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/analytics/health-score?hospital_id=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "health_score" in data

def test_translate_mock(client, doc_token):
    headers = {"Authorization": f"Bearer {doc_token}"}
    data = {
        "text": "Hello, how are you?",
        "target_language": "hi"
    }
    response = client.post("/api/v1/translate/", json=data, headers=headers)
    assert response.status_code == 200
    assert "translated_text" in response.json()

def test_generate_pdf_report(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/api/v1/reports/generate-pdf?hospital_id=1", headers=headers)
    assert response.status_code == 200
    assert "message" in response.json()
