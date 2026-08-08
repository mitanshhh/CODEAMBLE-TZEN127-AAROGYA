from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date
import os
import json

from app.db.database import get_db
from app.models.report import Report
from app.models.user import User, UserRole
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.services.health_score import calculate_health_score
from app.services.pdf_generator import generate_monthly_report
from app.core.rate_limit import limiter
from fastapi import Request

router = APIRouter()

@router.get("/")
def get_reports(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    reports = db.query(Report).filter(Report.hospital_id == hospital_id).order_by(Report.created_at.desc()).all()
    
    result = []
    for r in reports:
        result.append({
            "id": r.id,
            "month_year": r.month_year,
            "health_score": r.health_score,
            "ai_insights": r.ai_insights_json,
            "created_at": r.created_at,
            "risk_level": "Critical" if r.health_score < 50 else ("Moderate" if r.health_score < 75 else "Good")
        })
    return result


@router.post("/generate-pdf")
@limiter.limit("10/minute")
def trigger_report_generation(
    request: Request,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    from app.models.health_centre import HealthCentre
    from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord
    
    month_year = date.today().strftime("%m-%Y")
    score = calculate_health_score(db, hospital_id)
    
    hc = db.query(HealthCentre).filter(HealthCentre.id == hospital_id).first()
    
    # Calculate Attendance
    today = date.today()
    session = db.query(DailyQRSession).filter(DailyQRSession.hospital_id == hospital_id, DailyQRSession.date == today).first()
    total_docs = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).count()
    present_docs = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).count() if session else 0
    
    insights_str = f"Facility: {hc.name}\n"
    insights_str += f"Bed Capacity: {hc.available_beds}/{hc.total_beds} available.\n"
    insights_str += f"Doctor Attendance Today: {present_docs}/{total_docs} present.\n"
    insights_str += f"Overall AI Health Score implies {'critical attention needed' if score < 50 else 'stable operations'}."
    
    filepath = generate_monthly_report(hospital_id, month_year, score, insights_str)
    
    db_report = Report(
        hospital_id=hospital_id,
        month_year=month_year,
        health_score=score,
        ai_insights_json=json.dumps({"summary": insights_str}),
        pdf_url=filepath # Storing local path securely
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return {"message": "Report generated", "report_id": db_report.id}

@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    # Enforces role/hospital scope inherently via dependencies
    report = db.query(Report).filter(Report.id == report_id, Report.hospital_id == hospital_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")
        
    if not os.path.exists(report.pdf_url):
        raise HTTPException(status_code=404, detail="PDF file missing on server")
        
    return FileResponse(
        path=report.pdf_url,
        filename=os.path.basename(report.pdf_url),
        media_type="application/pdf"
    )
