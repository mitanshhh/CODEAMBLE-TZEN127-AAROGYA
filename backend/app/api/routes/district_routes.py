from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.district import ResourceRequest
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.models.notification import Notification
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

@router.get("/overview")
def get_district_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    phcs = db.query(HealthCentre).filter(HealthCentre.type == "PHC").count()
    chcs = db.query(HealthCentre).filter(HealthCentre.type == "CHC").count()
    
    total_beds = 0
    total_staff = 0
    for centre in db.query(HealthCentre).all():
        total_beds += centre.total_beds or 0
        total_staff += centre.total_staff or 0
        
    return {
        "total_phcs": phcs,
        "total_chcs": chcs,
        "total_beds": total_beds,
        "total_staff": total_staff,
        "critical_alerts": 2 # Mock critical alerts
    }

@router.get("/requests", response_model=List[ResourceRequestResponse])
def get_all_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]))
):
    return db.query(ResourceRequest).all()

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
        
    if update_in.status:
        req.status = update_in.status
    if update_in.admin_note:
        req.admin_note = update_in.admin_note
        
    # Trigger a notification to the PHC
    admin_action = "Approved" if req.status == "APPROVED" else "Rejected" if req.status == "REJECTED" else req.status
    
    # We should notify users at the requesting PHC. For simplicity, we just create a broadcast notification 
    # for that PHC or the PHC_ADMIN role.
    # But since Notification model in this app might not support hospital_id targeting natively, we will 
    # just create a generic one for now (or let the PHC staff poll requests). 
    # Find an appropriate user to notify (e.g., any user at that PHC)
    target_user = db.query(User).filter(User.hospital_id == req.requesting_phc_id).first()
    if target_user:
        notif = Notification(
            user_id=target_user.id,
            title=f"Resource Request {admin_action}",
            message=f"Request for {req.resource_name}: {update_in.admin_note or 'No notes provided.'}"
        )
        db.add(notif)
    
    db.commit()
    db.refresh(req)
    return req
