from pydantic import BaseModel, EmailStr
from typing import Optional

class HealthCentreBase(BaseModel):
    name: str
    type: str # PHC/CHC/Hospital
    district: str
    state: str
    total_beds: int = 0
    available_beds: int = 0
    total_staff: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None

class HealthCentreUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    total_beds: Optional[int] = None
    available_beds: Optional[int] = None
    total_staff: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None

class HealthCentreResponse(HealthCentreBase):
    id: int

    model_config = {"from_attributes": True}
