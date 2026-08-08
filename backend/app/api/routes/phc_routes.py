from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.schemas.health_centre import HealthCentreResponse, HealthCentreUpdate, HealthCentreBase
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

@router.get("/", response_model=list[HealthCentreResponse])
def get_all_centres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(HealthCentre).all()

@router.post("/", response_model=HealthCentreResponse)
def create_centre(
    centre_data: HealthCentreBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    hc = HealthCentre(**centre_data.model_dump())
    db.add(hc)
    db.commit()
    db.refresh(hc)
    return hc

@router.put("/{hc_id}", response_model=HealthCentreResponse)
def update_centre_by_id(
    hc_id: int,
    update_data: HealthCentreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    hc = db.query(HealthCentre).filter(HealthCentre.id == hc_id).first()
    if not hc:
        raise HTTPException(status_code=404, detail="Health centre not found")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(hc, key, value)
    
    db.commit()
    db.refresh(hc)
    return hc

@router.delete("/{hc_id}")
def delete_centre(
    hc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    hc = db.query(HealthCentre).filter(HealthCentre.id == hc_id).first()
    if not hc:
        raise HTTPException(status_code=404, detail="Health centre not found")
    
    db.delete(hc)
    db.commit()
    return {"message": "Health centre deleted successfully"}
