from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, and_, or_
import json
import hashlib
from datetime import date, datetime, timedelta

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.inventory import InventoryItem, InventoryLog
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord
from app.models.report import Report
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.services.health_score import calculate_health_score
from app.services.gemini_service import get_analytics_insights
from app.core.rate_limit import limiter
from app.utils.date_utils import get_now_ist

router = APIRouter()

def generate_data_version(data: dict) -> str:
    """Generate a stable hash of the deterministic data to prevent unnecessary AI calls."""
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    now = get_now_ist()
    # Default to past 7 days if no dates provided
    if not end_date:
        end_date = now.date()
    if not start_date:
        start_date = end_date - timedelta(days=6)
        
    health_score = calculate_health_score(db, hospital_id)
    
    # --- PATIENTS ---
    total_patients_period = db.query(Patient).filter(
        Patient.hospital_id == hospital_id,
        cast(Patient.admitted_at, Date) >= start_date,
        cast(Patient.admitted_at, Date) <= end_date
    ).count()
    
    admitted = db.query(Patient).filter(Patient.hospital_id == hospital_id, Patient.status == 'Admitted').count()
    discharged = db.query(Patient).filter(Patient.hospital_id == hospital_id, Patient.status == 'Discharged').count()
    outpatient = db.query(Patient).filter(Patient.hospital_id == hospital_id, Patient.status == 'Waiting').count()
    
    footfall_data = db.query(
        cast(Patient.admitted_at, Date).label('day'),
        func.count(Patient.id).label('patients')
    ).filter(
        Patient.hospital_id == hospital_id,
        cast(Patient.admitted_at, Date) >= start_date,
        cast(Patient.admitted_at, Date) <= end_date
    ).group_by(cast(Patient.admitted_at, Date)).all()
    
    footfall_dict = {str(r.day): r.patients for r in footfall_data}
    footfall_trend = []
    
    delta = end_date - start_date
    for i in range(delta.days + 1):
        d = start_date + timedelta(days=i)
        date_str = str(d)
        patients_val = footfall_dict.get(date_str, 0)
        footfall_trend.append({
            "date": d.strftime("%d %b"),
            "full_date": date_str,
            "patients": patients_val
        })
        
    # --- BEDS ---
    total_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id).count()
    occupied_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id, Bed.status == 'Occupied').count()
    available_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id, Bed.status == 'Available').count()
    maintenance_beds = total_beds - occupied_beds - available_beds
    occupancy_pct = round((occupied_beds / total_beds * 100) if total_beds > 0 else 0)

    # --- DOCTORS ---
    total_docs = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).count()
    
    # Calculate attendance trend for the period
    sessions = db.query(DailyQRSession).filter(
        DailyQRSession.hospital_id == hospital_id,
        DailyQRSession.date >= start_date,
        DailyQRSession.date <= end_date
    ).all()
    
    session_ids = [s.id for s in sessions]
    attendance_records = []
    if session_ids:
        attendance_records = db.query(
            DailyQRSession.date,
            func.count(AttendanceRecord.id).label('present')
        ).join(AttendanceRecord).filter(
            DailyQRSession.id.in_(session_ids)
        ).group_by(DailyQRSession.date).all()
        
    attendance_dict = {str(r.date): r.present for r in attendance_records}
    attendance_trend = []
    
    for i in range(delta.days + 1):
        d = start_date + timedelta(days=i)
        date_str = str(d)
        # Skip future dates or weekends if needed, but for simplicity we report what we have
        present_count = attendance_dict.get(date_str, 0)
        att_pct = round((present_count / total_docs * 100) if total_docs > 0 else 0)
        attendance_trend.append({
            "date": d.strftime("%d %b"),
            "full_date": date_str,
            "attendance_pct": att_pct,
            "present": present_count
        })
        
    present_today = attendance_dict.get(str(end_date), 0)
    attendance_today_pct = round((present_today / total_docs * 100) if total_docs > 0 else 0)

    # --- INVENTORY ---
    total_medicines = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id).count()
    low_stock = db.query(InventoryItem).filter(
        InventoryItem.hospital_id == hospital_id, 
        InventoryItem.quantity <= InventoryItem.min_threshold,
        InventoryItem.quantity > 0
    ).count()
    out_of_stock = db.query(InventoryItem).filter(
        InventoryItem.hospital_id == hospital_id, 
        InventoryItem.quantity == 0
    ).count()
    
    critical_items = db.query(InventoryItem.name, InventoryItem.quantity, InventoryItem.min_threshold).filter(
        InventoryItem.hospital_id == hospital_id,
        InventoryItem.quantity <= InventoryItem.min_threshold
    ).order_by(InventoryItem.name.asc()).limit(5).all()

    payload = {
        "health_score": round(health_score, 2),
        "patients": {
            "total_period": total_patients_period,
            "admitted": admitted,
            "discharged": discharged,
            "outpatient": outpatient,
            "trend": footfall_trend
        },
        "beds": {
            "total": total_beds,
            "occupied": occupied_beds,
            "available": available_beds,
            "maintenance": maintenance_beds,
            "occupancy_pct": occupancy_pct
        },
        "doctors": {
            "total": total_docs,
            "present_today": present_today,
            "attendance_today_pct": attendance_today_pct,
            "trend": attendance_trend
        },
        "inventory": {
            "total": total_medicines,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "critical_items": [{"name": c[0], "quantity": c[1], "threshold": c[2]} for c in critical_items]
        }
    }
    
    payload["data_version"] = generate_data_version(payload)
    return payload


@router.post("/generate-ai")
@limiter.limit("5/minute")
def generate_ai_report(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    """
    Generates the AI report strictly using the deterministic payload to save tokens and ensure accuracy.
    Expects the payload to contain 'data_version' and period metadata.
    """
    data_version = payload.get("data_version")
    period_type = payload.get("period_type", "Custom Range")
    period_start = payload.get("period_start")
    period_end = payload.get("period_end")
    
    # We remove these metadata fields before sending to AI to focus only on analytics
    analytics_data = payload.get("analytics_data", {})
    
    # Execute LLM Call (prompt must be structured for JSON)
    ai_response = get_analytics_insights(analytics_data, period_type)
    
    try:
        parsed = json.loads(ai_response)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return perfect JSON
        parsed = {
            "executive_summary": "Failed to parse AI response.",
            "risks": [{"category": "System Error", "severity": "High", "description": "AI Output format error."}],
            "recommendations": ["Retry analysis."],
            "key_insights": ["Error processing AI output."]
        }
    
    # Save to database
    report = Report(
        hospital_id=hospital_id,
        period_type=period_type,
        period_start=datetime.fromisoformat(period_start) if period_start else get_now_ist(),
        period_end=datetime.fromisoformat(period_end) if period_end else get_now_ist(),
        data_version=data_version,
        generated_by=current_user.id,
        health_score=analytics_data.get("health_score", 0),
        executive_summary=parsed.get("executive_summary", ""),
        risk_analysis=json.dumps(parsed.get("risks", [])),
        recommendations=json.dumps(parsed.get("recommendations", [])),
        key_insights=json.dumps(parsed.get("key_insights", []))
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Generate the PDF file
    from app.services.pdf_generator import generate_analytics_report_pdf
    hospital_name = current_user.hospital.name if current_user.hospital else f"Hospital {hospital_id}"
    try:
        pdf_url = generate_analytics_report_pdf(report, hospital_name, analytics_data)
        report.pdf_url = pdf_url
        db.commit()
        db.refresh(report)
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
    
    return report

@router.get("/reports")
def get_reports(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    reports = db.query(Report).filter(Report.hospital_id == hospital_id).order_by(Report.generated_at.desc()).all()
    return reports

@router.get("/reports/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    report = db.query(Report).filter(Report.id == report_id, Report.hospital_id == hospital_id).first()
    return report
