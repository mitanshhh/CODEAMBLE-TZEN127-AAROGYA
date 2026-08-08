from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PatientBase(BaseModel):
    name: str
    age: int
    gender: str
    contact: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None

class PatientCreate(PatientBase):
    hospital_id: int

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    status: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    hospital_id: int
    status: str
    admitted_at: datetime
    discharged_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
