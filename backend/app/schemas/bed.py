from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.patient import PatientResponse

class BedBase(BaseModel):
    bed_number: str
    ward: str
    status: str = "Available"

class BedCreate(BedBase):
    hospital_id: int

class BedUpdate(BaseModel):
    status: Optional[str] = None
    patient_id: Optional[int] = None
    admitted_at: Optional[datetime] = None
    bed_number: Optional[str] = None
    ward: Optional[str] = None
    bed_type: Optional[str] = None

class BedResponse(BedBase):
    id: int
    hospital_id: int
    patient_id: Optional[int] = None
    admitted_at: Optional[datetime] = None
    patient: Optional[PatientResponse] = None

    model_config = {"from_attributes": True}
