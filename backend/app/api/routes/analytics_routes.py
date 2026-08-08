from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import json

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.inventory import InventoryItem
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.services.health_score import calculate_health_score
from app.services.gemini_service import get_inventory_insights
from app.core.rate_limit import limiter

from app.models.patient import Patient
from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord
from datetime import date

router = APIRouter()

@router.get("/health-score")
def get_health_score(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    score = calculate_health_score(db, hospital_id)
    return {"health_score": round(score, 2)}

@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    # Live Inventory
    inventory_count = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id).count()
    low_stock = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id, InventoryItem.status == 'Low Stock').count()
    
    # Live Patients Today
    today = date.today()
    patients_today = db.query(Patient).filter(Patient.hospital_id == hospital_id).count() # Approximated to total for now
    waiting = db.query(Patient).filter(Patient.hospital_id == hospital_id, Patient.status == 'Waiting').count()
    
    # Live Doctors Today
    session = db.query(DailyQRSession).filter(DailyQRSession.hospital_id == hospital_id, DailyQRSession.date == today).first()
    total_docs = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).count()
    present_docs = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).count() if session else 0
    
    # Live Beds
    from app.models.bed import Bed
    total_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id).count()
    occupied_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id, Bed.status == 'Occupied').count()
    
    # 7-Day Footfall Trend
    from datetime import timedelta
    from sqlalchemy import func, cast, Date
    
    seven_days_ago = today - timedelta(days=6)
    
    footfall_data = db.query(
        cast(Patient.admitted_at, Date).label('day'),
        func.count(Patient.id).label('patients')
    ).filter(
        Patient.hospital_id == hospital_id,
        cast(Patient.admitted_at, Date) >= seven_days_ago
    ).group_by(cast(Patient.admitted_at, Date)).all()
    
    footfall_dict = {str(r.day): r.patients for r in footfall_data}
    
    footfall_trend = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        date_str = str(d)
        day_name = d.strftime("%a")
        footfall_trend.append({
            "date": day_name,
            "patients": footfall_dict.get(date_str, 0)
        })
    
    return {
        "inventory": {"total": inventory_count, "low_stock": low_stock},
        "patients": {"total_today": patients_today, "waiting": waiting},
        "doctors": {"total": total_docs, "present_today": present_docs},
        "beds": {"total": total_beds, "occupied": occupied_beds},
        "charts": {
            "footfall": footfall_trend
        }
    }

@router.get("/ai-insights")
@limiter.limit("5/minute")
def get_ai_insights(
    request: Request,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    items = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id).limit(50).all()
    data = [{"name": i.name, "quantity": i.quantity, "status": i.status} for i in items]
    
    insights_json = get_inventory_insights(data)
    try:
        # Strip markdown json block if Gemini adds it
        if insights_json.startswith("```json"):
            insights_json = insights_json[7:-3].strip()
        elif insights_json.startswith("```"):
            insights_json = insights_json[3:-3].strip()
        return json.loads(insights_json)
    except Exception:
        return {"raw_insights": insights_json}
