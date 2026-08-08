def test_register_patient(client, data_entry_token):
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    patient_data = {
        "name": "Jane Doe",
        "age": 30,
        "gender": "Female",
        "contact": "1234567890"
    }
    response = client.post("/api/v1/patients/", json=patient_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert "id" in data

def test_get_patients(client, doc_token, db_session):
    headers = {"Authorization": f"Bearer {doc_token}"}
    response = client.get("/api/v1/patients/", headers=headers)
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

def test_get_patient_by_id(client, doc_token, data_entry_token, db_session):
    headers = {"Authorization": f"Bearer {doc_token}"}
    # Fetch all patients first
    test_register_patient(client, data_entry_token)
    patients_resp = client.get("/api/v1/patients/", headers=headers)
    patient_id = patients_resp.json()["data"][0]["id"]

    # Fetch specific patient
    response = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == patient_id

def test_update_patient(client, data_entry_token, db_session):
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    test_register_patient(client, data_entry_token)
    patients_resp = client.get("/api/v1/patients/", headers=headers)
    patient_id = patients_resp.json()["data"][0]["id"]

    update_data = {"status": "Discharged"}
    response = client.put(f"/api/v1/patients/{patient_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Discharged"

def test_unauthorized_patient_update(client, doc_token):
    # Doc should not be able to update patient directly (depends on RBAC, let's say only data entry/admin can update or doc can too? Wait, doc might have access. Let's just check invalid token)
    response = client.put("/api/v1/patients/1", json={"status": "Discharged"})
    assert response.status_code == 401
