from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResourceRequestBase(BaseModel):
    target_district: str
    resource_type: str
    quantity: int
    urgency: str
    notes: Optional[str] = None

class ResourceRequestCreate(ResourceRequestBase):
    pass

class ResourceRequestUpdate(BaseModel):
    status: str # PENDING/APPROVED/REJECTED/FULFILLED

class ResourceRequestResponse(ResourceRequestBase):
    id: int
    requesting_phc_id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
