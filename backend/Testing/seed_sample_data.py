import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.health_centre import HealthCentre
from app.models.inventory import InventoryItem, InventoryLog
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.attendance import DailyQRSession, AttendanceRecord, Doctor
from app.models.district import ResourceRequest
from app.models.notification import Notification
from app.models.report import Report
from datetime import date, datetime, timezone

def seed_db():
    print("Initializing Database Seeding...")
    db: Session = SessionLocal()
    
    # 1. Health Centre
    phc = db.query(HealthCentre).filter_by(name="City Central PHC").first()
    if not phc:
        phc = HealthCentre(
            name="City Central PHC",
            type="PHC",
            district="Central District",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            total_beds=50,
            available_beds=49
        )
        db.add(phc)
        db.commit()
        db.refresh(phc)
        print("Created PHC.")
    else:
        print("PHC already exists.")

    # 2. RBAC Roles (Users)
    roles = [
        ("admin", UserRole.DISTRICT_ADMIN, None),
        ("mofficer", UserRole.MEDICAL_OFFICER, phc.id),
        ("doc", UserRole.DOCTOR, phc.id),
        ("reception", UserRole.RECEPTIONIST, phc.id),
        ("pharma", UserRole.PHARMACIST, phc.id),
        ("lab", UserRole.LAB_TECHNICIAN, phc.id),
        ("data", UserRole.DATA_ENTRY, phc.id),
        ("dev", UserRole.DEVELOPER, None),
    ]
    
    hashed_pw = get_password_hash("testpassword123")
    
    for username, role, h_id in roles:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=f"{username}@example.com",
                hashed_password=hashed_pw,
                role=role,
                hospital_id=h_id
            )
            db.add(user)
    db.commit()
    print("Created RBAC Users.")
    
    doc_user = db.query(User).filter_by(username="doc").first()

    # 3. Doctor Profile
    doctor = db.query(Doctor).filter_by(user_id=doc_user.id).first()
    if not doctor:
        doctor = Doctor(
            user_id=doc_user.id,
            hospital_id=phc.id,
            name="Dr. Sharma",
            specialization="Cardiologist",
            shift_start="09:00",
            shift_end="17:00"
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        print("Created Doctor Profile.")

    # 4. Inventory & Medicine
    med = db.query(InventoryItem).filter_by(name="Paracetamol 500mg", hospital_id=phc.id).first()
    if not med:
        med = InventoryItem(
            hospital_id=phc.id,
            name="Paracetamol 500mg",
            category="Medicine",
            quantity=500,
            unit="Tablets",
            min_threshold=100,
            status="Normal"
        )
        db.add(med)
        db.commit()
        db.refresh(med)
        
        log = InventoryLog(
            inventory_id=med.id,
            change_type="RESTOCK",
            change_amount=500,
            reason="Initial Seed",
            performed_by_user_id=doc_user.id
        )
        db.add(log)
        db.commit()
        print("Created Inventory & Log.")

    # 5. Bed & Patient
    patient = db.query(Patient).filter_by(name="John Doe").first()
    if not patient:
        patient = Patient(
            hospital_id=phc.id,
            name="John Doe",
            age=45,
            gender="Male",
            contact="9876543210",
            status="Admitted"
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        bed = Bed(
            hospital_id=phc.id,
            bed_number="Ward A - Bed 1",
            ward="Ward A",
            status="Occupied",
            patient_id=patient.id,
            admitted_at=datetime.now(timezone.utc)
        )
        db.add(bed)
        db.commit()
        print("Created Patient & Bed.")

    # 6. Attendance
    today = date.today()
    session = db.query(DailyQRSession).filter_by(hospital_id=phc.id, date=today).first()
    if not session:
        session = DailyQRSession(
            hospital_id=phc.id,
            date=today,
            qr_token="sample-qr-token-123",
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        record = db.query(AttendanceRecord).filter_by(doctor_id=doctor.id, session_id=session.id).first()
        if not record:
            record = AttendanceRecord(
                doctor_id=doctor.id,
                session_id=session.id,
                status="PRESENT",
                scanned_via="MOBILE_APP"
            )
            db.add(record)
            db.commit()
        print("Created Attendance QR & Record.")

    # 7. Resource Request
    req = db.query(ResourceRequest).filter_by(requesting_phc_id=phc.id).first()
    if not req:
        req = ResourceRequest(
            requesting_phc_id=phc.id,
            target_district="Central District",
            resource_type="Oxygen Cylinders",
            quantity=10,
            urgency="HIGH",
            status="PENDING"
        )
        db.add(req)
        db.commit()
        print("Created Resource Request.")

    # 8. Notification & Report
    notif = db.query(Notification).filter_by(user_id=doc_user.id).first()
    if not notif:
        notif = Notification(
            user_id=doc_user.id,
            title="Welcome",
            message="Welcome to the Aarogya platform.",
            is_read=False
        )
        db.add(notif)
        
        report = Report(
            hospital_id=phc.id,
            month_year="08-2026",
            health_score=85.5,
            ai_insights_json='{"insight": "Doing well"}',
            pdf_url="static/reports/dummy.pdf"
        )
        db.add(report)
        db.commit()
        print("Created Notification & Report.")

    print("✅ Seeding Complete!")

if __name__ == "__main__":
    seed_db()
