from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone, timedelta
import uuid

from app.db.database import get_db
from app.models.attendance import DailyQRSession, AttendanceRecord, Doctor, RandomAttendanceCheck
from app.models.user import User, UserRole
from app.models.health_centre import HealthCentre
from app.schemas.attendance import DailyQRSessionResponse, AttendanceRecordResponse, QRScanRequest, QRGenerateRequest
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
import math
from app.core.scheduler import schedule_random_check
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.post("/qr/generate", response_model=DailyQRSessionResponse)
def generate_qr_session(
    req: QRGenerateRequest,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DEVELOPER]))
):
    today = date.today()
    existing_session = db.query(DailyQRSession).filter(
        DailyQRSession.hospital_id == hospital_id,
        DailyQRSession.date == today
    ).first()
    
    if existing_session:
        existing_session.qr_token = str(uuid.uuid4())
        existing_session.device_lat = req.lat
        existing_session.device_lng = req.lng
        existing_session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing_session)
        return existing_session
        
    new_token = str(uuid.uuid4())
    session = DailyQRSession(
        hospital_id=hospital_id,
        date=today,
        qr_token=new_token,
        is_active=True,
        device_lat=req.lat,
        device_lng=req.lng
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.post("/scan")
def scan_qr_attendance(
    req: QRScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DailyQRSession).filter(DailyQRSession.qr_token == req.qr_token, DailyQRSession.is_active == True).first()
    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired QR token")
        
    # Enforce 5-minute QR validity
    updated_at_aware = session.updated_at.replace(tzinfo=timezone.utc) if session.updated_at.tzinfo is None else session.updated_at
    if datetime.now(timezone.utc) - updated_at_aware > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="QR code has expired. Please ask the Medical Officer to refresh it.")
    
    doctor = db.query(Doctor).filter(Doctor.id == req.doctor_id, Doctor.hospital_id == session.hospital_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found in this hospital")
        
    if session.device_lat is not None and session.device_lng is not None:
        dist = haversine(req.lat, req.lng, session.device_lat, session.device_lng)
        if dist > 100:
            raise HTTPException(status_code=400, detail=f"You are too far from the scanning device ({int(dist)}m away). Must be within 100m.")
    else:
        # Fallback to PHC location if available
        phc = db.query(HealthCentre).filter(HealthCentre.id == session.hospital_id).first()
        if phc and hasattr(phc, 'latitude') and phc.latitude and phc.longitude:
            dist = haversine(req.lat, req.lng, float(phc.latitude), float(phc.longitude))
            if dist > 100:
                raise HTTPException(status_code=400, detail=f"You are too far from the PHC ({int(dist)}m away). Must be within 100m.")
    
    # 1. Check if this is a random verification response
    pending_check = db.query(RandomAttendanceCheck).filter(
        RandomAttendanceCheck.doctor_id == req.doctor_id,
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
        AttendanceRecord.doctor_id == req.doctor_id
    ).first()
    
    if existing_record:
        return {"message": "Attendance already recorded for today"}
        
    record = AttendanceRecord(
        doctor_id=req.doctor_id,
        session_id=session.id,
        status="PRESENT",
        scanned_via="MOBILE_APP"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # Schedule random check for later today
    schedule_random_check(req.doctor_id, session.id)
    
    return {"message": "Attendance recorded successfully"}

@router.get("/doctor/me")
def get_my_doctor_dashboard(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.MEDICAL_OFFICER, UserRole.DEVELOPER]))
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found for the current user.")
    
    return get_doctor_dashboard_logic(doctor.id, db, hospital_id, current_user)

@router.get("/doctor/dashboard")
def get_doctor_dashboard(
    doctor_id: int,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    return get_doctor_dashboard_logic(doctor_id, db, hospital_id, current_user)

def get_doctor_dashboard_logic(doctor_id, db, hospital_id, current_user):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.hospital_id == hospital_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Fetch last 30 days history
    thirty_days_ago = date.today() - timedelta(days=30)
    sessions = db.query(DailyQRSession).filter(DailyQRSession.hospital_id == hospital_id, DailyQRSession.date >= thirty_days_ago).all()
    session_ids = [s.id for s in sessions]
    
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.doctor_id == doctor_id,
        AttendanceRecord.session_id.in_(session_ids)
    ).all()
    
    record_map = {r.session_id: r for r in records}
    
    history = []
    present_count = 0
    late_count = 0
    leaves_taken = 0
    
    # Sort sessions newest first
    sessions.sort(key=lambda x: x.date, reverse=True)
    
    current_streak = 0
    counting_streak = True
    
    for s in sessions:
        r = record_map.get(s.id)
        status = "Absent"
        if r:
            status = r.status
            if status == "PRESENT":
                present_count += 1
                if counting_streak:
                    current_streak += 1
            elif status == "LATE":
                late_count += 1
                if counting_streak:
                    current_streak += 1
            elif status == "LEAVE":
                leaves_taken += 1
                counting_streak = False
        else:
            if s.date < date.today():
                counting_streak = False
        
        history.append({
            "date": s.date.isoformat(),
            "status": status.capitalize(),
            "check_in": r.timestamp.isoformat() if r and r.timestamp else None,
            "gps_verified": True if r and r.scanned_via == "MOBILE_APP" else False,
            "qr_scanned": True if r and r.scanned_via == "MOBILE_APP" else False,
        })

    attendance_percentage = 0
    if len(sessions) > 0:
        attendance_percentage = int(((present_count + late_count) / len(sessions)) * 100)
    
    return {
        "doctor": {
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization or "General",
            "calendar_linked": False
        },
        "stats": {
            "attendance_percentage": attendance_percentage,
            "streak": current_streak,
            "late_count": late_count,
            "leaves_taken": leaves_taken
        },
        "history": history
    }

@router.get("/dashboard")
def get_attendance_dashboard(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
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
    filter_date: date = Query(default_factory=date.today),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    session = db.query(DailyQRSession).filter(
        DailyQRSession.hospital_id == hospital_id,
        DailyQRSession.date == filter_date
    ).first()
    
    doctors_query = db.query(Doctor).filter(Doctor.hospital_id == hospital_id)
    
    total = doctors_query.count()
    doctors = doctors_query.offset(offset).limit(limit).all()
    
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
            "doctor_name": doc.name or (doc.user.username if doc.user else f"Doctor {doc.id}"),
            "specialization": doc.specialization or "General",
            "status": doc_status,
            "timestamp": timestamp,
            "scanned_via": scanned_via
        })
        
    return PaginatedResponse(
        data=results,
        total=total,
        limit=limit,
        offset=offset
    )

