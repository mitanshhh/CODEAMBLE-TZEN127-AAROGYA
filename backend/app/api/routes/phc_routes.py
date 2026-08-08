from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.schemas.health_centre import HealthCentreResponse, HealthCentreUpdate, HealthCentreBase
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.core.security import get_password_hash
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
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
    
    # Auto-create Medical Officer account for this new PHC
    if getattr(hc, 'admin_email', None):
        password = secrets.token_urlsafe(8)
        new_user = User(
            username=hc.admin_email,
            email=hc.admin_email,
            hashed_password=get_password_hash(password),
            role=UserRole.MEDICAL_OFFICER,
            hospital_id=hc.id
        )
        db.add(new_user)
        db.commit()
        
        # Send welcome email
        try:
            smtp_user = os.getenv("SMTP_EMAIL")
            smtp_pass = os.getenv("SMTP_PASSWORD")
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            
            if smtp_user and smtp_pass:
                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = hc.admin_email
                msg['Subject'] = f"Welcome to Aarogya Health Engine - {hc.name}"
                
                body = f"""Hello,
                
Your new Health Centre '{hc.name}' has been successfully registered on the Aarogya Health Engine platform.

You can now log in using the following credentials:
Email: {hc.admin_email}
Password: {password}

Please change your password immediately after logging in.

Regards,
Aarogya District Administration
                """
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
        except Exception as e:
            print(f"Failed to send email: {e}")
            
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
