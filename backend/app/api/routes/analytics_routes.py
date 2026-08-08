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

router = APIRouter()

@router.get("/health-score")
def get_health_score(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    score = calculate_health_score(db, hospital_id)
    return {"health_score": round(score, 2)}

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
