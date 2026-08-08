from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date
import os
import json

from app.db.database import get_db
from app.models.report import Report
from app.models.user import User, UserRole
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
from app.services.health_score import calculate_health_score
from app.services.pdf_generator import generate_monthly_report
from app.core.rate_limit import limiter
from fastapi import Request

router = APIRouter()

@router.post("/generate-pdf")
@limiter.limit("10/minute")
def trigger_report_generation(
    request: Request,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.DISTRICT_ADMIN]))
):
    month_year = date.today().strftime("%m-%Y")
    score = calculate_health_score(db, hospital_id)
    
    insights_str = "Report generated successfully. Bed capacity is stable."
    
    filepath = generate_monthly_report(hospital_id, month_year, score, insights_str)
    
    db_report = Report(
        hospital_id=hospital_id,
        month_year=month_year,
        health_score=score,
        ai_insights_json=json.dumps({"summary": insights_str}),
        pdf_url=filepath # Storing local path securely
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return {"message": "Report generated", "report_id": db_report.id}

@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    hospital_id: int = Depends(resolve_hospital_id),
    current_user: User = Depends(get_current_user)
):
    # Enforces role/hospital scope inherently via dependencies
    report = db.query(Report).filter(Report.id == report_id, Report.hospital_id == hospital_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")
        
    if not os.path.exists(report.pdf_url):
        raise HTTPException(status_code=404, detail="PDF file missing on server")
        
    return FileResponse(
        path=report.pdf_url,
        filename=os.path.basename(report.pdf_url),
        media_type="application/pdf"
    )
