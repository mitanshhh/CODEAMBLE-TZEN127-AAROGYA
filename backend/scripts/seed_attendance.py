import sys
import os
from datetime import date
import uuid

# Add the backend root directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord

def seed_attendance():
    db = SessionLocal()
    try:
        hospital_id = 1  # Targeting Alpha PHC
        
        # 1. Create a DailyQRSession for today
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
            print("Created new DailyQRSession")
        else:
            print("DailyQRSession already exists")
            
        # 2. Check if doctors exist, otherwise create them
        doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
        if not doctors:
            doctor_data = [
                {"name": "Dr. Ramesh Kumar", "specialization": "General Physician", "shift": "Morning"},
                {"name": "Dr. Sunita Sharma", "specialization": "Pediatrician", "shift": "Morning"},
                {"name": "Dr. Anil Gupta", "specialization": "Orthopedics", "shift": "Evening"},
                {"name": "Dr. Priya Patel", "specialization": "Gynecology", "shift": "Morning"},
                {"name": "Dr. Vikram Singh", "specialization": "Cardiology", "shift": "Evening"}
            ]
            for doc in doctor_data:
                new_doc = Doctor(
                    hospital_id=hospital_id,
                    name=doc["name"],
                    specialization=doc["specialization"],
                    shift=doc["shift"]
                )
                db.add(new_doc)
            db.commit()
            print("Seeded 5 dummy doctors")
            doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
        else:
            print(f"Found {len(doctors)} existing doctors")
            
        # 3. Mark 3 of them as present
        existing_records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).count()
        if existing_records == 0:
            for i in range(min(3, len(doctors))):
                record = AttendanceRecord(
                    doctor_id=doctors[i].id,
                    session_id=session.id,
                    status="PRESENT",
                    scanned_via="MOBILE_APP"
                )
                db.add(record)
            db.commit()
            print("Seeded attendance records for 3 doctors")
        else:
            print("Attendance records already exist for today")
            
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_attendance()
