def test_get_inventory(client, data_entry_token):
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    response = client.get("/api/v1/inventory/", headers=headers)
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

def test_inventory_add_and_mock(client, data_entry_token, db_session):
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    item_data = {
        "name": "Paracetamol",
        "category": "Medicine",
        "quantity": 1000,
        "unit": "Tablets",
        "min_threshold": 200
    }
    response = client.post("/api/v1/inventory/", json=item_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Normal"

def test_inventory_low_stock(client, data_entry_token, db_session):
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    # Create item
    item_data = {
        "name": "Bandages",
        "category": "Consumable",
        "quantity": 50,
        "unit": "Boxes",
        "min_threshold": 100
    }
    response = client.post("/api/v1/inventory/", json=item_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Low Stock"


