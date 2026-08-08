from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.schemas.health_centre import HealthCentreResponse, HealthCentreUpdate
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id

router = APIRouter()

@router.get("/my-centre", response_model=HealthCentreResponse)
def get_my_centre(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id)
):
    hc = db.query(HealthCentre).filter(HealthCentre.id == hospital_id).first()
    if not hc:
        raise HTTPException(status_code=404, detail="Health centre not found")
    return hc

@router.put("/update", response_model=HealthCentreResponse)
def update_my_centre(
    update_data: HealthCentreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN])),
    hospital_id: int = Depends(resolve_hospital_id)
):
    hc = db.query(HealthCentre).filter(HealthCentre.id == hospital_id).first()
    if not hc:
        raise HTTPException(status_code=404, detail="Health centre not found")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(hc, key, value)
    
    db.commit()
    db.refresh(hc)
    return hc
