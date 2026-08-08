import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.attendance import Doctor
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import secrets

def seed_doctor_users():
    db = SessionLocal()
    try:
        hospital_id = 1
        doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
        
        count = 0
        for doc in doctors:
            email = f"{doc.name.lower().replace(' ', '.').replace('dr.', 'dr')}@alpha.phc.gov"
            existing_user = db.query(User).filter(User.email == email).first()
            if not existing_user:
                password = secrets.token_urlsafe(8)
                user = User(
                    username=email,
                    email=email,
                    hashed_password=get_password_hash(password),
                    role=UserRole.DOCTOR,
                    hospital_id=hospital_id
                )
                db.add(user)
                count += 1
                print(f"Created user for {doc.name}: {email} / {password}")
        
        db.commit()
        print(f"Successfully seeded {count} doctor users.")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_doctor_users()
