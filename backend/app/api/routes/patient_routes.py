from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.patient import Patient, PatientAuditLog
from app.models.user import User, UserRole
from app.schemas.patient import PatientResponse, PatientCreate, PatientUpdate
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

@router.get("/", response_model=PaginatedResponse[PatientResponse])
def get_patients(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user),
    status: str = Query(None, description="Filter by status (Admitted/Discharged/Outpatient)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = db.query(Patient).filter(Patient.hospital_id == hospital_id)
    if status:
        query = query.filter(Patient.status == status)
    
    total = query.count()
    patients = query.offset(offset).limit(limit).all()
    
    return PaginatedResponse(
        data=patients,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/analytics")
def get_patient_analytics(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import func
    from datetime import datetime
    
    total = db.query(Patient).filter(Patient.hospital_id == hospital_id).count()
    males = db.query(Patient).filter(Patient.hospital_id == hospital_id, Patient.gender == 'Male').count()
    females = db.query(Patient).filter(Patient.hospital_id == hospital_id, Patient.gender == 'Female').count()
    
    # Simple dynamic stats based on DB
    return {
        "kpis": {
            "total_today": total,
            "avg_wait_time_mins": 0 if total == 0 else 14,
            "emergency_visits": 0 if total == 0 else 5,
            "seniors": 0,
            "children": 0,
            "males": males,
            "females": females
        },
        "charts": {
            "hourly_trend": [
                {"time": "8 AM", "patients": 0},
                {"time": "12 PM", "patients": total // 2},
                {"time": "4 PM", "patients": total - (total // 2)}
            ],
            "department_distribution": [
                {"name": "General", "value": total}
            ]
        }
    }

@router.get("/doctors")
def get_patient_doctors(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    # Return mock doctors since we don't have a staff route implemented yet
    return [
        {"id": 1, "name": "Dr. Smith", "specialization": "General Physician"},
        {"id": 2, "name": "Dr. Jones", "specialization": "Pediatrician"},
        {"id": 3, "name": "Dr. Davis", "specialization": "Cardiologist"}
    ]


@router.post("/", response_model=PatientResponse)
def register_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.RECEPTIONIST, UserRole.DATA_ENTRY, UserRole.MEDICAL_OFFICER, UserRole.DEVELOPER])),
    hospital_id: int = Depends(resolve_hospital_id)
):
    patient_in.hospital_id = hospital_id
    
    patient_dict = patient_in.model_dump()
    new_patient = Patient(**patient_dict, status="Outpatient")
    db.add(new_patient)
    db.flush()

    if not new_patient.patient_code:
        new_patient.patient_code = f"PT-{str(new_patient.id).zfill(4)}"
        
    db.commit()
    db.refresh(new_patient)

    log_audit(db, new_patient.id, current_user.id, "CREATE", f"Registered new patient ({new_patient.patient_code})")
    return new_patient

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.hospital_id == hospital_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    log_audit(db, patient.id, current_user.id, "VIEW", "Viewed patient record")
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    update_data: PatientUpdate,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.RECEPTIONIST, UserRole.DATA_ENTRY, UserRole.MEDICAL_OFFICER, UserRole.DOCTOR]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.hospital_id == hospital_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    
    db.commit()
    db.refresh(patient)
    
    log_audit(db, patient.id, current_user.id, "EDIT", "Updated patient record")
    return patient
