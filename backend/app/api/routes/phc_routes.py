from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.schemas.health_centre import HealthCentreCreateResponse, HealthCentreResponse, HealthCentreUpdate, HealthCentreBase
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.core.security import get_password_hash
from app.services.email_service import send_onboarding_email
import secrets

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

@router.post("/", response_model=HealthCentreCreateResponse)
def create_centre(
    centre_data: HealthCentreBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    hc = HealthCentre(**centre_data.model_dump())
    db.add(hc)
    db.commit()
    db.refresh(hc)

    admin_user_created = False
    email_sent = False
    email_detail = "No admin email provided; onboarding email was not sent."
    
    # Auto-create Medical Officer account for this new PHC
    if getattr(hc, 'admin_email', None):
        admin_email = str(hc.admin_email)
        existing_user = (
            db.query(User)
            .filter(or_(User.email == admin_email, User.username == admin_email))
            .first()
        )
        if existing_user:
            email_detail = "Admin user already exists for this email; onboarding email was not sent."
        else:
            password = secrets.token_urlsafe(12)
            new_user = User(
                username=admin_email,
                email=admin_email,
                hashed_password=get_password_hash(password),
                role=UserRole.MEDICAL_OFFICER,
                hospital_id=hc.id
            )
            db.add(new_user)
            db.flush()

            delivery = send_onboarding_email(
                email_to=admin_email,
                username=admin_email,
                raw_password=password,
                centre_name=hc.name,
            )
            email_sent = delivery.sent
            email_detail = delivery.detail
            if email_sent:
                db.commit()
                admin_user_created = True
            else:
                db.rollback()

    response = HealthCentreCreateResponse.model_validate(hc).model_dump()
    response.update({
        "admin_user_created": admin_user_created,
        "email_sent": email_sent,
        "email_detail": email_detail,
    })
    return response

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
