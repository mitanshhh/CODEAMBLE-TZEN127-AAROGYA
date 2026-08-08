from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io

from app.db.database import get_db
from app.models.inventory import InventoryItem, InventoryLog
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.schemas.inventory import InventoryItemResponse, InventoryItemCreate, InventoryItemUpdate, InventoryLogResponse
from app.schemas.common import PaginatedResponse
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.services.gemini_service import get_inventory_insights
from app.core.rate_limit import limiter
from fastapi import Request

router = APIRouter()

MAX_CSV_SIZE = 50 * 1024 * 1024 # 50 MB
MAX_CSV_ROWS = 1000

def sanitize_csv_value(val):
    """Prevent CSV injection attacks"""
    if isinstance(val, str) and val.startswith(('=', '+', '-', '@')):
        return "'" + val
    return val

def log_inventory_change(db: Session, inventory_id: int, change_type: str, amount: int, user_id: int, reason: str = None):
    log = InventoryLog(
        inventory_id=inventory_id,
        change_type=change_type,
        change_amount=amount,
        reason=reason,
        performed_by_user_id=user_id
    )
    db.add(log)
    # The caller is responsible for db.commit() to ensure atomicity

@router.get("/", response_model=PaginatedResponse[InventoryItemResponse])
def get_inventory(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    category: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id)
    if category:
        query = query.filter(InventoryItem.category == category)
    
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return PaginatedResponse(data=items, total=total, limit=limit, offset=offset)

@router.post("/", response_model=InventoryItemResponse)
def add_inventory_item(
    item_in: InventoryItemCreate,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.PHARMACIST, UserRole.DATA_ENTRY, UserRole.MEDICAL_OFFICER]))
):
    item_in.hospital_id = hospital_id
    
    status = "Normal"
    if item_in.quantity <= item_in.min_threshold:
        status = "Low Stock"
        
    item_dict = item_in.model_dump(exclude={"status"})
    new_item = InventoryItem(**item_dict, status=status)
    db.add(new_item)
    db.flush()
    
    if status == "Low Stock":
        # Create a notification
        notif = Notification(
            user_id=current_user.id,
            title="Low Stock Alert",
            message=f"Item {new_item.name} is added but below min threshold ({new_item.quantity}/{new_item.min_threshold})."
        )
        db.add(notif)
    
    db.commit()
    db.refresh(new_item)
    
    log_inventory_change(db, new_item.id, "RESTOCK", new_item.quantity, current_user.id, "Initial Add")
    db.commit()
    return new_item

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.PHARMACIST, UserRole.MEDICAL_OFFICER]))
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    contents = await file.read()
    if len(contents) > MAX_CSV_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 50MB.")
        
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
        
    if len(df) > MAX_CSV_ROWS:
        raise HTTPException(status_code=400, detail=f"Too many rows. Max {MAX_CSV_ROWS} rows allowed.")
    
    # Required columns
    required_cols = {'name', 'category', 'quantity', 'unit'}
    if not required_cols.issubset(set(df.columns)):
        raise HTTPException(status_code=400, detail=f"CSV must contain columns: {', '.join(required_cols)}")
    
    items_added = 0
    for _, row in df.iterrows():
        # Sanitize
        name = sanitize_csv_value(row.get('name'))
        cat = sanitize_csv_value(row.get('category'))
        unit = sanitize_csv_value(row.get('unit'))
        qty = int(row.get('quantity', 0))
        min_t = int(row.get('min_threshold', 0))
        
        item = InventoryItem(
            hospital_id=hospital_id,
            name=name,
            category=cat,
            quantity=qty,
            unit=unit,
            min_threshold=min_t,
            status="Normal" if qty > min_t else "Low Stock"
        )
        db.add(item)
        db.flush() # flush to get item.id without committing whole transaction yet
        
        if item.status == "Low Stock":
            notif = Notification(
                user_id=current_user.id,
                title="Low Stock Alert (CSV)",
                message=f"Item {item.name} uploaded with low stock ({item.quantity}/{item.min_threshold})."
            )
            db.add(notif)
        
        log_inventory_change(db, item.id, "RESTOCK", qty, current_user.id, "CSV Bulk Upload")
        items_added += 1
        
    db.commit()
    return {"message": f"Successfully imported {items_added} items."}

@router.post("/analyze-ai")
@limiter.limit("5/minute")
def analyze_inventory_ai(
    request: Request,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.PHARMACIST]))
):
    # Fetch recent logs or current stock for analysis
    items = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id).all()
    data = [{"name": i.name, "qty": i.quantity, "status": i.status} for i in items]
    
    import json
    insights_json = get_inventory_insights(data)
    try:
        if insights_json.startswith("```json"):
            insights_json = insights_json[7:-3].strip()
        elif insights_json.startswith("```"):
            insights_json = insights_json[3:-3].strip()
        return json.loads(insights_json)
    except Exception:
        return {"raw_insights": insights_json}

@router.get("/logs", response_model=PaginatedResponse[InventoryLogResponse])
def get_inventory_logs(
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN, UserRole.PHARMACIST, UserRole.DATA_ENTRY]))
):
    query = db.query(InventoryLog).join(InventoryItem).filter(InventoryItem.hospital_id == hospital_id)
    total = query.count()
    logs = query.order_by(InventoryLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    return PaginatedResponse(data=logs, total=total, limit=limit, offset=offset)
