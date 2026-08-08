import sys
import os
from datetime import date
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.models.health_centre import HealthCentre
from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord
from app.services.health_score import calculate_health_score
from app.services.pdf_generator import generate_monthly_report

def test_generate():
    db = SessionLocal()
    hospital_id = 2
    try:
        month_year = date.today().strftime("%m-%Y")
        print("Calculating score...")
        score = calculate_health_score(db, hospital_id)
        print("Score:", score)
        
        hc = db.query(HealthCentre).filter(HealthCentre.id == hospital_id).first()
        print("HC:", hc.name)
        
        # Calculate Attendance
        today = date.today()
        session = db.query(DailyQRSession).filter(DailyQRSession.hospital_id == hospital_id, DailyQRSession.date == today).first()
        total_docs = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).count()
        present_docs = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).count() if session else 0
        
        insights_str = f"Facility: {hc.name}\n"
        insights_str += f"Bed Capacity: {hc.available_beds}/{hc.total_beds} available.\n"
        insights_str += f"Doctor Attendance Today: {present_docs}/{total_docs} present.\n"
        insights_str += f"Overall AI Health Score implies {'critical attention needed' if score < 50 else 'stable operations'}."
        print("Insights:", insights_str)
        
        print("Generating PDF...")
        filepath = generate_monthly_report(hospital_id, month_year, score, insights_str)
        print("Generated PDF at", filepath)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_generate()
