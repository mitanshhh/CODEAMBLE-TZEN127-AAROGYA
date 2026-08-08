from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.district import ResourceRequest
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.schemas.district import ResourceRequestResponse, ResourceRequestCreate, ResourceRequestUpdate
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id

router = APIRouter()

@router.get("/map-data")
def get_map_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN]))
):
    centres = db.query(HealthCentre).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "type": c.type,
            "district": c.district,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "total_beds": c.total_beds,
            "available_beds": c.available_beds
        }
        for c in centres
    ]

@router.post("/resource-request", response_model=ResourceRequestResponse)
def create_resource_request(
    request_in: ResourceRequestCreate,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER]))
):
    new_req = ResourceRequest(
        requesting_phc_id=hospital_id,
        **request_in.model_dump()
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

@router.put("/resource-request/{request_id}", response_model=ResourceRequestResponse)
def update_resource_request(
    request_id: int,
    update_in: ResourceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN]))
):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Resource request not found")
        
    req.status = update_in.status
    db.commit()
    db.refresh(req)
    return req
