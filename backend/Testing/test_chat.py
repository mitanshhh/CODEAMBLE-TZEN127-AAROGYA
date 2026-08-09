from datetime import date

import pytest

from app.models.attendance import AttendanceRecord, DailyQRSession, Doctor
from app.models.bed import Bed
from app.models.health_centre import HealthCentre
from app.models.inventory import InventoryItem, InventoryLog
from app.models.patient import Patient, PatientAuditLog
from app.models.user import User, UserRole
from app.core.security import create_access_token
from app.services.chat_groq_sql import validate_generated_sql


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def disable_groq_for_deterministic_tests(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")


def seed_patient(db_session, test_hospital):
    patient = Patient(
        hospital_id=test_hospital.id,
        patient_code="ABHA12345",
        name="Asha Sharma",
        age=34,
        gender="Female",
        contact="9999999999",
        address="Jalna",
        medical_history="Fever",
        status="Outpatient",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def test_chat_patient_search(client, data_entry_token, db_session, test_hospital):
    seed_patient(db_session, test_hospital)
    response = client.post("/api/v1/chat/", json={"message": "Find patient ABHA12345"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["intent"] == "patient_search"
    assert body["data"][0]["patient_code"] == "ABHA12345"


def test_chat_patient_history(client, data_entry_token, data_entry_user, db_session, test_hospital):
    patient = seed_patient(db_session, test_hospital)
    db_session.add(PatientAuditLog(patient_id=patient.id, user_id=data_entry_user.id, action="VIEW", details="Viewed patient record"))
    db_session.commit()
    response = client.post("/api/v1/chat/", json={"message": "Show history of ABHA12345"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "patient_history"
    assert body["summary"]["history_events"] == 1


def test_chat_patient_medicines(client, data_entry_token, data_entry_user, db_session, test_hospital):
    seed_patient(db_session, test_hospital)
    item = InventoryItem(hospital_id=test_hospital.id, name="Paracetamol", category="Medicine", quantity=20, unit="tablets")
    db_session.add(item)
    db_session.flush()
    db_session.add(InventoryLog(inventory_id=item.id, change_type="DISPENSE", change_amount=2, reason="Billed to patient: Asha (ID: ABHA12345)", performed_by_user_id=data_entry_user.id))
    db_session.commit()
    response = client.post("/api/v1/chat/", json={"message": "What medicines did ABHA12345 receive?"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "patient_medicines"
    assert body["data"][0]["medicine"] == "Paracetamol"


def test_chat_patient_footfall_at_named_phc(client, admin_token, db_session, test_hospital):
    test_hospital.name = "Alpha PHC"
    seed_patient(db_session, test_hospital)
    db_session.commit()
    response = client.post(
        "/api/v1/chat/",
        json={"message": "Whats the patient footfall today at Alpha PHC"},
        headers=auth(admin_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["intent"] == "patient_footfall"
    assert body["summary"]["patient_footfall"] == 1
    assert body["data"][0]["phc_name"] == "Alpha PHC"


def test_chat_low_medicine_stock(client, data_entry_token, db_session, test_hospital):
    db_session.add(InventoryItem(hospital_id=test_hospital.id, name="ORS", category="Medicine", quantity=1, unit="packs", min_threshold=5))
    db_session.commit()
    response = client.post("/api/v1/chat/", json={"message": "Which medicines need restocking?"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "medicine_low_stock"
    assert body["data"][0]["name"] == "ORS"


def test_chat_inventory_word_maps_to_stock_at_named_phc(client, data_entry_token, db_session, test_hospital):
    test_hospital.name = "Alpha PHC"
    db_session.add(InventoryItem(hospital_id=test_hospital.id, name="Paracetamol", category="Medicine", quantity=20, unit="tablets", min_threshold=5))
    db_session.commit()
    response = client.post(
        "/api/v1/chat/",
        json={"message": "get data from Inventory at Alpha PHC"},
        headers=auth(data_entry_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["intent"] == "medicine_stock"
    assert body["data"][0]["name"] == "Paracetamol"


def test_chat_out_of_stock_medicines(client, data_entry_token, db_session, test_hospital):
    db_session.add(InventoryItem(hospital_id=test_hospital.id, name="Amoxicillin", category="Medicine", quantity=0, unit="strips", min_threshold=3))
    db_session.commit()
    response = client.post("/api/v1/chat/", json={"message": "Which medicines are out of stock?"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "medicine_out_of_stock"
    assert body["data"][0]["quantity"] == 0


def test_chat_bed_availability(client, data_entry_token, db_session, test_hospital):
    db_session.add(Bed(hospital_id=test_hospital.id, bed_number="G-01", ward="General", status="Available"))
    db_session.add(Bed(hospital_id=test_hospital.id, bed_number="G-02", ward="General", status="Occupied"))
    db_session.commit()
    response = client.post("/api/v1/chat/", json={"message": "How many beds are available?"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "bed_availability"
    assert body["summary"]["available_beds"] == 1


def test_chat_doctor_attendance(client, admin_token, db_session, test_hospital):
    doctor = Doctor(hospital_id=test_hospital.id, name="Dr Sharma", specialization="General")
    db_session.add(doctor)
    db_session.flush()
    session = DailyQRSession(hospital_id=test_hospital.id, date=date.today(), qr_token="qr-token")
    db_session.add(session)
    db_session.flush()
    db_session.add(AttendanceRecord(doctor_id=doctor.id, session_id=session.id, status="PRESENT", scanned_via="MOBILE_APP"))
    db_session.commit()
    response = client.post("/api/v1/chat/?hospital_id=1", json={"message": "Show today's doctor attendance"}, headers=auth(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "doctor_attendance"
    assert body["summary"]["present"] == 1


def test_chat_doctor_absence(client, admin_token, db_session, test_hospital):
    db_session.add(Doctor(hospital_id=test_hospital.id, name="Dr Rao", specialization="ENT"))
    db_session.commit()
    response = client.post("/api/v1/chat/?hospital_id=1", json={"message": "Which doctors are absent today?"}, headers=auth(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "doctor_absence"
    assert body["data"][0]["doctor_name"] == "Dr Rao"


def test_chat_patient_not_found(client, data_entry_token):
    response = client.post("/api/v1/chat/", json={"message": "Find patient ABHA99999"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "No patient was found" in body["message"]


def test_chat_unsupported_query(client, data_entry_token):
    response = client.post("/api/v1/chat/", json={"message": "What is the weather?"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "unsupported"


def test_chat_missing_patient_id(client, data_entry_token):
    response = client.post("/api/v1/chat/", json={"message": "Show patient history"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "Patient ID / ABHA ID" in body["message"]


def test_chat_conversation_context(client, data_entry_token, db_session, test_hospital):
    seed_patient(db_session, test_hospital)
    response = client.post(
        "/api/v1/chat/",
        json={"message": "What medicines did they receive?", "context": {"patient_id": "ABHA12345"}},
        headers=auth(data_entry_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "patient_medicines"
    assert body["summary"]["patient_id"] == "ABHA12345"


def test_chat_pdf_generation_and_download(client, data_entry_token, db_session, test_hospital):
    seed_patient(db_session, test_hospital)
    response = client.post("/api/v1/chat/", json={"message": "Find patient ABHA12345"}, headers=auth(data_entry_token))
    body = response.json()
    assert body["pdf_available"] is True
    assert body["report_id"]
    download = client.get(f"/api/v1/chat/reports/{body['report_id']}/download", headers=auth(data_entry_token))
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


def test_chat_unauthorized(client):
    response = client.post("/api/v1/chat/", json={"message": "Show medicine stock"})
    assert response.status_code == 401


def test_chat_role_not_allowed(client, db_session):
    user = User(
        username="labchat",
        email="labchat@example.com",
        hashed_password="test",
        role=UserRole.LAB_TECHNICIAN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    response = client.post("/api/v1/chat/", json={"message": "Show medicine stock"}, headers=auth(create_access_token(user.id)))
    assert response.status_code == 403
    assert "Chatbot access" in response.json()["detail"]


def test_chat_staff_cannot_access_other_phc_patient(client, data_entry_token, db_session, test_hospital):
    other_hospital = HealthCentre(name="Beta PHC", type="PHC", district="Other District", state="Test State", total_beds=5)
    db_session.add(other_hospital)
    db_session.commit()
    db_session.refresh(other_hospital)
    db_session.add(Patient(
        hospital_id=other_hospital.id,
        patient_code="ABHA77777",
        name="Other Patient",
        age=42,
        gender="Male",
        status="Outpatient",
    ))
    db_session.commit()

    response = client.post("/api/v1/chat/", json={"message": "Find patient ABHA77777"}, headers=auth(data_entry_token))
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "No patient was found" in body["message"]


def test_chat_district_admin_scope_all_can_access_any_phc_patient(client, admin_token, db_session, test_hospital):
    other_hospital = HealthCentre(name="Beta PHC", type="PHC", district="Other District", state="Test State", total_beds=5)
    db_session.add(other_hospital)
    db_session.commit()
    db_session.refresh(other_hospital)
    db_session.add(Patient(
        hospital_id=other_hospital.id,
        patient_code="ABHA88888",
        name="District Visible Patient",
        age=39,
        gender="Female",
        status="Outpatient",
    ))
    db_session.commit()

    response = client.post(
        "/api/v1/chat/?hospital_id=1",
        json={"message": "Find patient ABHA88888", "scope_all": True},
        headers=auth(admin_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["patient_code"] == "ABHA88888"


def test_chat_sql_injection_style_input_is_not_executed(client, data_entry_token, db_session, test_hospital):
    seed_patient(db_session, test_hospital)
    response = client.post(
        "/api/v1/chat/",
        json={"message": "Find patient ABHA12345'; DROP TABLE patients; --"},
        headers=auth(data_entry_token),
    )
    assert response.status_code == 200
    assert db_session.query(Patient).count() == 1


def test_groq_sql_validator_allows_scoped_select():
    sql = validate_generated_sql("SELECT patient_code, name FROM chat_patients WHERE patient_code ILIKE 'ABHA%'")
    assert sql.endswith("LIMIT 50")


def test_groq_sql_validator_rejects_base_tables():
    try:
        validate_generated_sql("SELECT patient_code FROM patients")
    except ValueError as exc:
        assert "base tables" in str(exc)
    else:
        raise AssertionError("base table SQL should be rejected")


def test_groq_sql_validator_rejects_write_sql():
    try:
        validate_generated_sql("DROP TABLE patients")
    except ValueError as exc:
        assert "SELECT" in str(exc) or "disallowed" in str(exc)
    else:
        raise AssertionError("write SQL should be rejected")


def test_groq_sql_validator_rejects_multiple_statements():
    try:
        validate_generated_sql("SELECT * FROM chat_patients; SELECT * FROM chat_beds")
    except ValueError as exc:
        assert "one" in str(exc)
    else:
        raise AssertionError("multiple statements should be rejected")
