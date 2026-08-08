"""
Full Doctor + Attendance Seeder for ALPHA PHC
- Auto-detects the ALPHA PHC hospital_id
- Creates Doctor records if none exist
- Creates User accounts linked to each Doctor
- Creates today's QR session
- Seeds attendance records (mix of present/absent)
"""
import sys
import os
from datetime import date, datetime, timezone
import uuid
import secrets

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.core.security import get_password_hash

DOCTOR_DATA = [
    {"name": "Dr. Ramesh Kumar",    "specialization": "General Physician",  "shift": "Morning", "phone": "9876501001", "email": "dr.ramesh.kumar@alpha.phc.gov"},
    {"name": "Dr. Sunita Sharma",   "specialization": "Pediatrician",       "shift": "Morning", "phone": "9876501002", "email": "dr.sunita.sharma@alpha.phc.gov"},
    {"name": "Dr. Anil Gupta",      "specialization": "Orthopedics",        "shift": "Evening", "phone": "9876501003", "email": "dr.anil.gupta@alpha.phc.gov"},
    {"name": "Dr. Priya Patel",     "specialization": "Gynecology",         "shift": "Morning", "phone": "9876501004", "email": "dr.priya.patel@alpha.phc.gov"},
    {"name": "Dr. Vikram Singh",    "specialization": "Cardiology",         "shift": "Evening", "phone": "9876501005", "email": "dr.vikram.singh@alpha.phc.gov"},
    {"name": "Dr. Meera Nair",      "specialization": "Dermatology",        "shift": "Morning", "phone": "9876501006", "email": "dr.meera.nair@alpha.phc.gov"},
    {"name": "Dr. Sanjay Rao",      "specialization": "ENT",                "shift": "Evening", "phone": "9876501007", "email": "dr.sanjay.rao@alpha.phc.gov"},
]

def seed():
    db = SessionLocal()
    try:
        # ── 1. Find ALPHA PHC ───────────────────────────────────────────
        phc = db.query(HealthCentre).filter(
            HealthCentre.name.ilike("%alpha%")
        ).first()

        if not phc:
            # Fall back to first PHC in DB
            phc = db.query(HealthCentre).first()

        if not phc:
            print("❌  No PHC found in the database. Please create one first via the UI.")
            return

        hospital_id = phc.id
        print(f"✅  Using PHC: '{phc.name}' (id={hospital_id})")

        # ── 2. Create Doctors if none exist ─────────────────────────────
        existing_doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
        if existing_doctors:
            print(f"ℹ️   Found {len(existing_doctors)} existing doctors — skipping doctor creation.")
            doctors = existing_doctors
        else:
            doctors = []
            for doc_data in DOCTOR_DATA:
                # Create linked User account
                existing_user = db.query(User).filter(User.email == doc_data["email"]).first()
                if not existing_user:
                    password = secrets.token_urlsafe(8)
                    user = User(
                        username=doc_data["email"],
                        email=doc_data["email"],
                        hashed_password=get_password_hash(password),
                        role=UserRole.DOCTOR,
                        hospital_id=hospital_id
                    )
                    db.add(user)
                    db.flush()
                    print(f"   👤 Created user: {doc_data['email']}  password: {password}")
                else:
                    user = existing_user
                    print(f"   👤 Reusing existing user: {doc_data['email']}")

                doc = Doctor(
                    hospital_id=hospital_id,
                    name=doc_data["name"],
                    specialization=doc_data["specialization"],
                    shift=doc_data["shift"],
                    phone=doc_data["phone"],
                    email=doc_data["email"],
                    user_id=user.id
                )
                db.add(doc)
                doctors.append(doc)

            db.commit()
            # Re-query to get IDs
            doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
            print(f"✅  Seeded {len(doctors)} doctors.")

        # ── 3. Create today's QR session ────────────────────────────────
        today = date.today()
        session = db.query(DailyQRSession).filter(
            DailyQRSession.hospital_id == hospital_id,
            DailyQRSession.date == today
        ).first()

        if not session:
            session = DailyQRSession(
                hospital_id=hospital_id,
                date=today,
                qr_token=str(uuid.uuid4()),
                is_active=True
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            print(f"✅  Created QR session for {today}")
        else:
            print(f"ℹ️   QR session for {today} already exists.")

        # ── 4. Seed attendance (present for first 4, absent for rest) ───
        existing_records = db.query(AttendanceRecord).filter(
            AttendanceRecord.session_id == session.id
        ).count()

        if existing_records > 0:
            print(f"ℹ️   {existing_records} attendance records already exist for today — skipping.")
        else:
            present_count = min(4, len(doctors))
            for i, doc in enumerate(doctors):
                if i < present_count:
                    record = AttendanceRecord(
                        doctor_id=doc.id,
                        session_id=session.id,
                        status="PRESENT",
                        scanned_via="MOBILE_APP"
                    )
                    db.add(record)
                    print(f"   ✅  {doc.name} — PRESENT")
                else:
                    print(f"   ❌  {doc.name} — ABSENT (no record)")
            db.commit()
            print(f"✅  Seeded attendance: {present_count} present, {len(doctors) - present_count} absent.")

        print("\n🎉  Done! Restart the backend and refresh the Attendance page.")

    except Exception as e:
        print(f"❌  Error: {e}")
        import traceback; traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
