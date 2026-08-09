from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, DailyQRSession, Doctor
from app.models.bed import Bed
from app.models.health_centre import HealthCentre
from app.models.inventory import InventoryItem, InventoryLog
from app.models.patient import Patient, PatientAuditLog
from app.models.user import User, UserRole
from app.services.chat_nlp import ParsedIntent, validate_patient_identifier


PATIENT_INTENTS = {"patient_search", "patient_history", "patient_medicines", "patient_visits"}


@dataclass
class ChatQueryResult:
    success: bool
    intent: str
    message: str
    data: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)


def _iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _allowed_hospital_ids(db: Session, current_user: User, hospital_id: Optional[int]) -> Optional[List[int]]:
    if current_user.role == UserRole.DISTRICT_ADMIN:
        if hospital_id:
            return [hospital_id]
        return None
    if not current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You are not assigned to any health centre.")
    return [current_user.hospital_id]


def _apply_hospital_scope(query, model, allowed_ids: Optional[List[int]]):
    if allowed_ids is None:
        return query
    return query.filter(model.hospital_id.in_(allowed_ids))


def _patient_to_dict(patient: Patient) -> Dict[str, Any]:
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "contact": patient.contact,
        "address": patient.address,
        "medical_history": patient.medical_history,
        "status": patient.status,
        "hospital_id": patient.hospital_id,
        "admitted_at": _iso(patient.admitted_at),
        "discharged_at": _iso(patient.discharged_at),
    }


def _find_patient(db: Session, patient_id: str, allowed_ids: Optional[List[int]]) -> Optional[Patient]:
    query = db.query(Patient).filter(func.lower(Patient.patient_code) == patient_id.lower())
    query = _apply_hospital_scope(query, Patient, allowed_ids)
    return query.first()


def _parse_date(value: Optional[str], fallback: date) -> date:
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError:
        return fallback


def _local_date_window_utc(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    local_tz = ZoneInfo("Asia/Kolkata")
    start_local = datetime.combine(date_from, time.min, tzinfo=local_tz)
    end_local = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=local_tz)
    return (
        start_local.astimezone(timezone.utc).replace(tzinfo=None),
        end_local.astimezone(timezone.utc).replace(tzinfo=None),
    )


def _handle_patient_intent(db: Session, parsed: ParsedIntent, current_user: User, allowed_ids: Optional[List[int]]) -> ChatQueryResult:
    patient_id = validate_patient_identifier(parsed.entities.get("patient_id"))
    if not patient_id:
        return ChatQueryResult(
            success=False,
            intent=parsed.intent,
            message="Please provide the Patient ID / ABHA ID to continue.",
        )

    patient = _find_patient(db, patient_id, allowed_ids)
    if not patient:
        return ChatQueryResult(
            success=False,
            intent=parsed.intent,
            message=f"No patient was found for Patient ID / ABHA ID {patient_id}.",
            context={"patient_id": patient_id},
        )

    context = {"patient_id": patient.patient_code}

    if parsed.intent == "patient_search":
        return ChatQueryResult(
            success=True,
            intent=parsed.intent,
            message=f"Patient {patient.patient_code} was found.",
            data=[_patient_to_dict(patient)],
            summary={"patient_id": patient.patient_code, "status": patient.status},
            context=context,
        )

    if parsed.intent == "patient_history":
        logs = db.query(PatientAuditLog).filter(PatientAuditLog.patient_id == patient.id).order_by(PatientAuditLog.timestamp.desc()).limit(20).all()
        data = [{
            "patient": _patient_to_dict(patient),
            "history": [
                {
                    "action": log.action,
                    "details": log.details,
                    "user_id": log.user_id,
                    "timestamp": _iso(log.timestamp),
                }
                for log in logs
            ],
        }]
        return ChatQueryResult(
            success=True,
            intent=parsed.intent,
            message=f"History for Patient ID / ABHA ID {patient.patient_code}.",
            data=data,
            summary={"patient_id": patient.patient_code, "history_events": len(logs)},
            context=context,
        )

    if parsed.intent == "patient_visits":
        visits = [{
            "patient_code": patient.patient_code,
            "hospital_id": patient.hospital_id,
            "status": patient.status,
            "admitted_at": _iso(patient.admitted_at),
            "discharged_at": _iso(patient.discharged_at),
        }]
        return ChatQueryResult(
            success=True,
            intent=parsed.intent,
            message=f"Recent visit information for Patient ID / ABHA ID {patient.patient_code}.",
            data=visits,
            summary={"patient_id": patient.patient_code, "visits": len(visits)},
            context=context,
        )

    logs = (
        db.query(InventoryLog)
        .join(InventoryItem)
        .filter(InventoryItem.hospital_id == patient.hospital_id)
        .filter(InventoryLog.reason.ilike(f"%{patient.patient_code}%"))
        .order_by(InventoryLog.timestamp.desc())
        .limit(50)
        .all()
    )
    data = [
        {
            "medicine": log.item.name if log.item else f"Item #{log.inventory_id}",
            "quantity": log.change_amount,
            "change_type": log.change_type,
            "reason": log.reason,
            "timestamp": _iso(log.timestamp),
        }
        for log in logs
    ]
    message = (
        f"Medicines found for Patient ID / ABHA ID {patient.patient_code}."
        if data else
        f"No medicine dispensing records were found for Patient ID / ABHA ID {patient.patient_code} in the current inventory logs."
    )
    return ChatQueryResult(
        success=True,
        intent=parsed.intent,
        message=message,
        data=data,
        summary={"patient_id": patient.patient_code, "medicine_records": len(data)},
        context=context,
    )


def _handle_medicine_intent(db: Session, parsed: ParsedIntent, allowed_ids: Optional[List[int]]) -> ChatQueryResult:
    query = db.query(InventoryItem).join(HealthCentre, InventoryItem.hospital_id == HealthCentre.id)
    query = _apply_hospital_scope(query, InventoryItem, allowed_ids)
    if parsed.entities.get("phc_name"):
        phc = parsed.entities["phc_name"]
        query = query.filter((HealthCentre.name.ilike(f"%{phc}%")) | (HealthCentre.district.ilike(f"%{phc}%")))
    medicine_name = parsed.entities.get("medicine_name")
    if medicine_name:
        query = query.filter(InventoryItem.name.ilike(f"%{medicine_name}%"))
    if parsed.intent == "medicine_low_stock":
        query = query.filter(InventoryItem.quantity <= InventoryItem.min_threshold)
    elif parsed.intent == "medicine_out_of_stock":
        query = query.filter(InventoryItem.quantity <= 0)

    items = query.order_by(InventoryItem.name.asc()).limit(50).all()
    data = [
        {
            "id": item.id,
            "hospital_id": item.hospital_id,
            "name": item.name,
            "category": item.category,
            "quantity": item.quantity,
            "unit": item.unit,
            "price": item.price,
            "min_threshold": item.min_threshold,
            "expiry_date": _iso(item.expiry_date),
            "batch_number": item.batch_number,
            "status": item.status,
        }
        for item in items
    ]
    if parsed.intent == "medicine_low_stock":
        message = "Medicines needing restocking." if data else "No low-stock medicines were found."
    elif parsed.intent == "medicine_out_of_stock":
        message = "Out-of-stock medicines." if data else "No out-of-stock medicines were found."
    else:
        message = "Current medicine stock." if data else "No matching medicine stock was found."
    return ChatQueryResult(True, parsed.intent, message, data, {"count": len(data)})


def _handle_patient_footfall(db: Session, parsed: ParsedIntent, allowed_ids: Optional[List[int]]) -> ChatQueryResult:
    today = date.today()
    date_from = _parse_date(parsed.filters.get("date_from"), today)
    date_to = _parse_date(parsed.filters.get("date_to"), date_from)
    if date_to < date_from:
        date_to = date_from
    start_utc, end_utc = _local_date_window_utc(date_from, date_to)

    centre_query = db.query(HealthCentre)
    if allowed_ids is not None:
        centre_query = centre_query.filter(HealthCentre.id.in_(allowed_ids))
    if parsed.entities.get("phc_name"):
        phc = parsed.entities["phc_name"]
        centre_query = centre_query.filter((HealthCentre.name.ilike(f"%{phc}%")) | (HealthCentre.district.ilike(f"%{phc}%")))

    centres = centre_query.order_by(HealthCentre.name.asc()).limit(50).all()
    data = []
    for centre in centres:
        patient_query = db.query(Patient).filter(
            Patient.hospital_id == centre.id,
            Patient.admitted_at >= start_utc,
            Patient.admitted_at < end_utc,
        )
        total = patient_query.count()
        admitted = patient_query.filter(Patient.status == "Admitted").count()
        outpatient = patient_query.filter(Patient.status == "Outpatient").count()
        discharged = patient_query.filter(Patient.status == "Discharged").count()
        data.append({
            "hospital_id": centre.id,
            "phc_name": centre.name,
            "district": centre.district,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "patient_footfall": total,
            "admitted": admitted,
            "outpatient": outpatient,
            "discharged": discharged,
        })

    total_footfall = sum(row["patient_footfall"] for row in data)
    if not data:
        message = "No matching PHC was found for that footfall request."
    elif total_footfall == 0:
        message = "No patient footfall was recorded for the selected date range."
    else:
        message = "Patient footfall for the selected PHC/date range."
    return ChatQueryResult(
        True,
        parsed.intent,
        message,
        data,
        {"centres": len(data), "patient_footfall": total_footfall, "date_from": date_from.isoformat(), "date_to": date_to.isoformat()},
    )


def _bed_summary_for_centres(db: Session, centres: List[HealthCentre]) -> List[Dict[str, Any]]:
    data = []
    for centre in centres:
        total = db.query(Bed).filter(Bed.hospital_id == centre.id).count()
        occupied = db.query(Bed).filter(Bed.hospital_id == centre.id, Bed.status == "Occupied").count()
        available = db.query(Bed).filter(Bed.hospital_id == centre.id, Bed.status == "Available").count()
        maintenance = db.query(Bed).filter(Bed.hospital_id == centre.id, Bed.status == "Maintenance").count()
        occupancy = round((occupied / total) * 100, 2) if total else 0
        data.append({
            "hospital_id": centre.id,
            "name": centre.name,
            "type": centre.type,
            "district": centre.district,
            "total_beds": total,
            "occupied_beds": occupied,
            "available_beds": available,
            "maintenance_beds": maintenance,
            "occupancy_percentage": occupancy,
            "is_full": total > 0 and available == 0,
        })
    return data


def _handle_bed_intent(db: Session, parsed: ParsedIntent, allowed_ids: Optional[List[int]]) -> ChatQueryResult:
    centre_query = db.query(HealthCentre)
    if allowed_ids is not None:
        centre_query = centre_query.filter(HealthCentre.id.in_(allowed_ids))
    centres = centre_query.order_by(HealthCentre.name.asc()).limit(100).all()
    data = _bed_summary_for_centres(db, centres)
    if parsed.intent == "phc_bed_status":
        lowered_message = parsed.filters.get("raw_message", "")
        if "full" in lowered_message:
            data = [row for row in data if row["is_full"]]
        elif "available" in lowered_message:
            data = [row for row in data if row["available_beds"] > 0]
    totals = {
        "centres": len(data),
        "total_beds": sum(row["total_beds"] for row in data),
        "occupied_beds": sum(row["occupied_beds"] for row in data),
        "available_beds": sum(row["available_beds"] for row in data),
    }
    message = "PHC bed availability." if data else "No bed records were found."
    return ChatQueryResult(True, parsed.intent, message, data[:50], totals)


def _handle_attendance_intent(db: Session, parsed: ParsedIntent, allowed_ids: Optional[List[int]]) -> ChatQueryResult:
    today = date.today()
    date_from = _parse_date(parsed.filters.get("date_from"), today)
    date_to = _parse_date(parsed.filters.get("date_to"), date_from)
    if date_to < date_from:
        date_to = date_from

    doctor_query = db.query(Doctor).join(HealthCentre, Doctor.hospital_id == HealthCentre.id)
    if allowed_ids is not None:
        doctor_query = doctor_query.filter(Doctor.hospital_id.in_(allowed_ids))
    if parsed.entities.get("doctor_name"):
        doctor_query = doctor_query.filter(Doctor.name.ilike(f"%{parsed.entities['doctor_name']}%"))
    if parsed.entities.get("phc_name"):
        phc = parsed.entities["phc_name"]
        doctor_query = doctor_query.filter((HealthCentre.name.ilike(f"%{phc}%")) | (HealthCentre.district.ilike(f"%{phc}%")))

    doctors = doctor_query.order_by(Doctor.name.asc()).limit(100).all()
    data: List[Dict[str, Any]] = []
    current = date_from
    while current <= date_to:
        sessions = db.query(DailyQRSession).filter(DailyQRSession.date == current)
        if allowed_ids is not None:
            sessions = sessions.filter(DailyQRSession.hospital_id.in_(allowed_ids))
        sessions_by_hospital = {s.hospital_id: s for s in sessions.all()}
        for doctor in doctors:
            session = sessions_by_hospital.get(doctor.hospital_id)
            record = None
            if session:
                record = db.query(AttendanceRecord).filter(
                    AttendanceRecord.session_id == session.id,
                    AttendanceRecord.doctor_id == doctor.id,
                ).first()
            status = "Absent"
            timestamp = None
            scanned_via = None
            if record:
                status = "Present" if record.status == "PRESENT" else record.status.title()
                timestamp = _iso(record.timestamp)
                scanned_via = record.scanned_via
            if parsed.intent == "doctor_absence" and status != "Absent":
                continue
            data.append({
                "date": current.isoformat(),
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "specialization": doctor.specialization,
                "hospital_id": doctor.hospital_id,
                "status": status,
                "timestamp": timestamp,
                "scanned_via": scanned_via,
            })
        current = date.fromordinal(current.toordinal() + 1)

    present = sum(1 for row in data if row["status"] == "Present")
    absent = sum(1 for row in data if row["status"] == "Absent")
    message = "Doctor attendance records." if data else "No matching doctor attendance records were found."
    return ChatQueryResult(True, parsed.intent, message, data[:100], {"present": present, "absent": absent, "records": len(data)})


def run_controlled_chat_query(
    db: Session,
    parsed: ParsedIntent,
    current_user: User,
    hospital_id: Optional[int] = None,
) -> ChatQueryResult:
    if parsed.intent not in {
        "patient_search", "patient_history", "patient_medicines", "patient_visits",
        "patient_footfall",
        "medicine_stock", "medicine_low_stock", "medicine_out_of_stock",
        "bed_availability", "phc_bed_status",
        "doctor_attendance", "doctor_absence", "doctor_specific_attendance",
    }:
        return ChatQueryResult(
            success=False,
            intent="unsupported",
            message="I can help with patients, patient history, medicines, bed availability, and doctor attendance. Please ask one of those operational questions.",
        )

    allowed_ids = _allowed_hospital_ids(db, current_user, hospital_id)
    if parsed.intent == "patient_footfall":
        return _handle_patient_footfall(db, parsed, allowed_ids)
    if parsed.intent in PATIENT_INTENTS:
        return _handle_patient_intent(db, parsed, current_user, allowed_ids)
    if parsed.intent.startswith("medicine"):
        return _handle_medicine_intent(db, parsed, allowed_ids)
    if parsed.intent in {"bed_availability", "phc_bed_status"}:
        return _handle_bed_intent(db, parsed, allowed_ids)
    return _handle_attendance_intent(db, parsed, allowed_ids)
