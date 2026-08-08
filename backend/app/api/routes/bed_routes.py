from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.database import get_db
from app.models.bed import Bed
from app.models.patient import Patient, PatientAuditLog
from app.models.user import User, UserRole
from app.schemas.bed import BedResponse
from app.schemas.common import PaginatedResponse
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id

router = APIRouter()

def log_audit(db: Session, patient_id: int, user_id: int, action: str, details: str = None):
    audit = PatientAuditLog(
        patient_id=patient_id,
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(audit)
    db.commit()

@router.get("/", response_model=PaginatedResponse[BedResponse])
def get_beds(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    status: str = Query(None, description="Filter by status (Available/Occupied/Maintenance)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = db.query(Bed).filter(Bed.hospital_id == hospital_id)
    if status:
        query = query.filter(Bed.status == status)
    
    total = query.count()
    beds = query.offset(offset).limit(limit).all()
    
    return PaginatedResponse(
        data=beds,
        total=total,
        limit=limit,
        offset=offset
    )

@router.post("/admit")
def admit_patient(
    bed_id: int = Query(...),
    patient_id: int = Query(...),
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.RECEPTIONIST, UserRole.DATA_ENTRY, UserRole.MEDICAL_OFFICER]))
):
    bed = db.query(Bed).filter(Bed.id == bed_id, Bed.hospital_id == hospital_id).first()
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.hospital_id == hospital_id).first()
    
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if bed.status != "Available":
        raise HTTPException(status_code=400, detail="Bed is not available")
    if patient.status == "Admitted":
        raise HTTPException(status_code=400, detail="Patient is already admitted")
    
    bed.status = "Occupied"
    bed.patient_id = patient.id
    bed.admitted_at = datetime.now(timezone.utc)
    
    patient.status = "Admitted"
    
    log_audit(db, patient.id, current_user.id, "EDIT", f"Admitted to bed {bed.bed_number}")
    db.commit()
    db.refresh(bed)
    return bed

@router.post("/discharge")
def discharge_patient(
    patient_id: int = Query(...),
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.RECEPTIONIST, UserRole.DATA_ENTRY, UserRole.MEDICAL_OFFICER]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.hospital_id == hospital_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.status != "Admitted":
        raise HTTPException(status_code=400, detail="Patient is not admitted")
    
    bed = db.query(Bed).filter(Bed.patient_id == patient.id, Bed.hospital_id == hospital_id).first()
    if bed:
        bed.status = "Available"
        bed.patient_id = None
        bed.admitted_at = None
    
    patient.status = "Discharged"
    patient.discharged_at = datetime.now(timezone.utc)
    
    log_audit(db, patient.id, current_user.id, "EDIT", "Discharged patient")
    db.commit()
    
    return {"message": "Patient discharged successfully"}
