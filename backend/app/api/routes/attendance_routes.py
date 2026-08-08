from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
import uuid

from app.db.database import get_db
from app.models.attendance import DailyQRSession, AttendanceRecord, Doctor
from app.models.user import User, UserRole
from app.schemas.attendance import DailyQRSessionResponse, AttendanceRecordResponse
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id

router = APIRouter()

@router.post("/qr/generate", response_model=DailyQRSessionResponse)
def generate_qr_session(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    today = date.today()
    existing_session = db.query(DailyQRSession).filter(
        DailyQRSession.hospital_id == hospital_id,
        DailyQRSession.date == today
    ).first()
    
    if existing_session:
        return existing_session
        
    new_token = str(uuid.uuid4())
    session = DailyQRSession(
        hospital_id=hospital_id,
        date=today,
        qr_token=new_token,
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.post("/scan")
def scan_qr_attendance(
    qr_token: str,
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DailyQRSession).filter(DailyQRSession.qr_token == qr_token, DailyQRSession.is_active == True).first()
    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired QR token")
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.hospital_id == session.hospital_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found in this hospital")
        
    existing_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.doctor_id == doctor_id
    ).first()
    
    if existing_record:
        return {"message": "Attendance already recorded for today"}
        
    record = AttendanceRecord(
        doctor_id=doctor_id,
        session_id=session.id,
        status="PRESENT",
        scanned_via="MOBILE_APP"
    )
    db.add(record)
    db.commit()
    
    return {"message": "Attendance recorded successfully"}

@router.get("/dashboard")
def get_attendance_dashboard(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER]))
):
    today = date.today()
    session = db.query(DailyQRSession).filter(
        DailyQRSession.hospital_id == hospital_id,
        DailyQRSession.date == today
    ).first()
    
    total_doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).count()
    
    present_count = 0
    if session:
        present_count = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).count()
        
    return {
        "date": today,
        "total_doctors": total_doctors,
        "present_doctors": present_count,
        "absent_doctors": total_doctors - present_count
    }
