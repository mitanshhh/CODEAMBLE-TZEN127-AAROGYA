import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.report import Report
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.services.chat_query import ChatQueryResult


CHAT_REPORTS_DIR = "static/reports/chat"
os.makedirs(CHAT_REPORTS_DIR, exist_ok=True)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:500]


def _flatten_row(row: Dict[str, Any], intent: str) -> Dict[str, Any]:
    if "patient" in row and isinstance(row["patient"], dict):
        patient = row["patient"]
        return {
            "patient_code": patient.get("patient_code"),
            "name": patient.get("name"),
            "age": patient.get("age"),
            "gender": patient.get("gender"),
            "status": patient.get("status"),
            "hospital_id": patient.get("hospital_id"),
            "history_events": len(row.get("history", [])),
        }
    if intent.startswith("patient"):
        allowed = {"patient_code", "name", "age", "gender", "status", "hospital_id", "admitted_at", "discharged_at", "medical_history"}
        patient_row = {k: v for k, v in row.items() if k in allowed}
        return patient_row or row
    return row


def _build_table_data(data: List[Dict[str, Any]], intent: str) -> List[List[str]]:
    rows = [_flatten_row(row, intent) for row in data[:25]]
    if not rows:
        return [["Result", "No records found"]]

    preferred_columns = {
        "patient_search": ["patient_code", "name", "age", "gender", "status", "hospital_id"],
        "patient_history": ["patient_code", "name", "status", "hospital_id", "history_events"],
        "patient_visits": ["patient_code", "status", "hospital_id", "admitted_at", "discharged_at"],
        "patient_footfall": ["phc_name", "district", "date_from", "date_to", "patient_footfall", "admitted", "outpatient", "discharged"],
        "patient_medicines": ["medicine", "quantity", "change_type", "timestamp"],
        "medicine_stock": ["name", "category", "quantity", "unit", "min_threshold", "status", "hospital_id"],
        "medicine_low_stock": ["name", "quantity", "unit", "min_threshold", "status", "hospital_id"],
        "medicine_out_of_stock": ["name", "quantity", "unit", "min_threshold", "status", "hospital_id"],
        "bed_availability": ["name", "type", "district", "total_beds", "occupied_beds", "available_beds", "occupancy_percentage"],
        "phc_bed_status": ["name", "type", "district", "total_beds", "occupied_beds", "available_beds", "occupancy_percentage"],
        "doctor_attendance": ["date", "doctor_name", "specialization", "hospital_id", "status", "timestamp"],
        "doctor_absence": ["date", "doctor_name", "specialization", "hospital_id", "status"],
        "doctor_specific_attendance": ["date", "doctor_name", "specialization", "hospital_id", "status", "timestamp"],
    }
    columns = preferred_columns.get(intent) or list(rows[0].keys())[:6]
    table = [[col.replace("_", " ").title() for col in columns]]
    for row in rows:
        table.append([_safe_text(row.get(col)) for col in columns])
    return table


def create_chat_report(
    db: Session,
    current_user: User,
    query: str,
    result: ChatQueryResult,
    hospital_id: Optional[int],
) -> Optional[str]:
    if not result.success or not result.data:
        return None

    timestamp = datetime.now(timezone.utc)
    filename = f"chat_report_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(CHAT_REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=44,
        leftMargin=44,
        topMargin=44,
        bottomMargin=44,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ChatReportTitle", parent=styles["Heading1"], fontSize=15, alignment=1, spaceAfter=10)
    section_style = ParagraphStyle("ChatReportSection", parent=styles["Heading2"], fontSize=11, spaceBefore=10, spaceAfter=6)
    normal = styles["Normal"]
    normal.fontSize = 9

    story = [
        Paragraph("Aarogya", title_style),
        Paragraph("AI Healthcare Report", title_style),
        Spacer(1, 8),
        Paragraph(f"<b>Query:</b> {_safe_text(query)}", normal),
        Paragraph(f"<b>Generated:</b> {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}", normal),
        Paragraph(f"<b>Intent:</b> {result.intent}", normal),
        Spacer(1, 8),
        Paragraph("Summary", section_style),
        Paragraph(_safe_text(result.message), normal),
    ]

    if result.summary:
        summary_table = [["Field", "Value"]] + [
            [key.replace("_", " ").title(), _safe_text(value)]
            for key, value in result.summary.items()
        ]
        story.append(Table(summary_table, colWidths=[2.0 * inch, 4.0 * inch], style=[
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c2c6d5")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f6f7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

    story.extend([Spacer(1, 10), Paragraph("Retrieved Data", section_style)])
    table_data = _build_table_data(result.data, result.intent)
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c2c6d5")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0058bd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    doc.build(story)

    report_hospital_id = hospital_id or current_user.hospital_id
    if not report_hospital_id and result.data:
        report_hospital_id = result.data[0].get("hospital_id")
    if not report_hospital_id:
        first_centre = db.query(HealthCentre).order_by(HealthCentre.id.asc()).first()
        report_hospital_id = first_centre.id if first_centre else None
    if not report_hospital_id:
        return None

    report = Report(
        hospital_id=report_hospital_id,
        month_year=f"chat-{timestamp.strftime('%m-%Y')}",
        health_score=None,
        ai_insights_json=json.dumps({
            "query": query,
            "intent": result.intent,
            "summary": result.summary,
        }),
        pdf_url=filepath,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return create_chat_report_token(report.id, current_user.id, report.hospital_id)


def create_chat_report_token(report_id: int, user_id: int, hospital_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "report_id": report_id,
        "hospital_id": hospital_id,
        "scope": "chat_report",
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def get_report_from_token(db: Session, token: str, current_user: User) -> Report:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise PermissionError("Invalid or expired report token")

    if payload.get("scope") != "chat_report":
        raise PermissionError("Invalid report token")
    if str(current_user.id) != str(payload.get("sub")) and current_user.role != UserRole.DEVELOPER:
        raise PermissionError("Report token does not belong to this user")

    report = db.query(Report).filter(Report.id == payload.get("report_id")).first()
    if not report:
        raise FileNotFoundError("Report not found")
    if report.hospital_id != payload.get("hospital_id"):
        raise PermissionError("Report token mismatch")
    if current_user.role not in [UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER] and current_user.hospital_id != report.hospital_id:
        raise PermissionError("Report access denied")
    return report
