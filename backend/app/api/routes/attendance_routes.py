from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone, timedelta
import uuid

from app.db.database import get_db
from app.models.attendance import DailyQRSession, AttendanceRecord, Doctor, RandomAttendanceCheck
from app.models.user import User, UserRole
from app.schemas.attendance import DailyQRSessionResponse, AttendanceRecordResponse
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.core.scheduler import schedule_random_check

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
        existing_session.qr_token = str(uuid.uuid4())
        existing_session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing_session)
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
        
    # Enforce 5-minute QR validity
    updated_at_aware = session.updated_at.replace(tzinfo=timezone.utc) if session.updated_at.tzinfo is None else session.updated_at
    if datetime.now(timezone.utc) - updated_at_aware > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="QR code has expired. Please ask the Medical Officer to refresh it.")
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.hospital_id == session.hospital_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found in this hospital")
        
    # 1. Check if this is a random verification response
    pending_check = db.query(RandomAttendanceCheck).filter(
        RandomAttendanceCheck.doctor_id == doctor_id,
        RandomAttendanceCheck.session_id == session.id,
        RandomAttendanceCheck.status == "PENDING"
    ).first()
    
    if pending_check:
        pending_check.status = "COMPLETED"
        db.commit()
        return {"message": "Random verification completed successfully"}
        
    # 2. Otherwise, standard morning check-in
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
    db.refresh(record)
    
    # Schedule random check for later today
    schedule_random_check(doctor_id, session.id)
    
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

@router.get("/records")
def get_attendance_records(
    status: str = "All",
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    today = date.today()
    session = db.query(DailyQRSession).filter(
        DailyQRSession.hospital_id == hospital_id,
        DailyQRSession.date == today
    ).first()
    
    doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
    records_by_doctor = {}
    if session:
        records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).all()
        for r in records:
            records_by_doctor[r.doctor_id] = r
            
    results = []
    for doc in doctors:
        record = records_by_doctor.get(doc.id)
        doc_status = "Absent"
        timestamp = None
        scanned_via = None
        
        if record:
            doc_status = "Present" if record.status == "PRESENT" else "Absent"
            timestamp = record.timestamp.isoformat() if record.timestamp else None
            scanned_via = record.scanned_via
            
        if status != "All" and doc_status != status:
            continue
            
        results.append({
            "id": doc.id,
            "doctor_name": doc.user.username if doc.user else f"Doctor {doc.id}",
            "specialization": doc.specialization or "General",
            "status": doc_status,
            "timestamp": timestamp,
            "scanned_via": scanned_via
        })
        
    return results

