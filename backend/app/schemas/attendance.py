from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class DailyQRSessionResponse(BaseModel):
    id: int
    hospital_id: int
    date: date
    qr_token: str
    is_active: bool

    model_config = {"from_attributes": True}

class AttendanceRecordResponse(BaseModel):
    id: int
    doctor_id: int
    timestamp: datetime
    status: str
    scanned_via: Optional[str] = None

    model_config = {"from_attributes": True}
