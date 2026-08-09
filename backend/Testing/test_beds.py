from app.models.bed import Bed
from Testing.test_patients import test_register_patient

def test_get_beds(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/beds/?hospital_id=1", headers=headers)
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

def test_admit_patient(client, data_entry_token, db_session, test_hospital):
    # Setup a bed in the DB
    bed = Bed(hospital_id=test_hospital.id, ward="ICU", bed_number="ICU-01", status="Available")
    db_session.add(bed)
    db_session.commit()
    db_session.refresh(bed)

    # Register a patient
    test_register_patient(client, data_entry_token)
    
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    patients_resp = client.get("/api/v1/patients/", headers=headers)
    patient = patients_resp.json()["data"][0]

    response = client.post(
        f"/api/v1/beds/{bed.id}/admit",
        json={
            "action": "admit",
            "patient_name": patient["name"],
            "patient_code": patient["patient_code"],
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Occupied"

def test_discharge_patient(client, data_entry_token, db_session, test_hospital):
    # Setup state
    test_admit_patient(client, data_entry_token, db_session, test_hospital)
    headers = {"Authorization": f"Bearer {data_entry_token}"}
    beds_resp = client.get(f"/api/v1/beds/?hospital_id={test_hospital.id}", headers=headers)
    occupied_bed = next(b for b in beds_resp.json()["data"] if b["status"] == "Occupied")

    response = client.post(f"/api/v1/beds/{occupied_bed['id']}/discharge", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Patient discharged successfully"
