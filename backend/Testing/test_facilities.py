def test_data_entry_cannot_access_district_admin_routes(client, data_entry_token):
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    response = client.get("/api/v1/district/map-data", headers=headers)
    assert response.status_code == 403

def test_admin_can_access_district_routes(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/district/map-data?hospital_id=1", headers=headers)
    assert response.status_code == 200

def test_get_my_centre(client, admin_token, test_hospital):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/phc/my-centre?hospital_id=1", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == test_hospital.name

def test_update_my_centre(client, admin_token, test_hospital):
    headers = {"Authorization": f"Bearer {admin_token}"}
    update_data = {"total_beds": 50}
    response = client.put("/api/v1/phc/update?hospital_id=1", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["total_beds"] == 50
