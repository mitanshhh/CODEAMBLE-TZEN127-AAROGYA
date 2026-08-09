import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, Optional

from app.core.config import settings

try:
    from dotenv import dotenv_values
except Exception:  # pragma: no cover
    dotenv_values = None


SUPPORTED_INTENTS = {
    "patient_search",
    "patient_history",
    "patient_medicines",
    "patient_visits",
    "patient_footfall",
    "medicine_stock",
    "medicine_low_stock",
    "medicine_out_of_stock",
    "bed_availability",
    "phc_bed_status",
    "doctor_attendance",
    "doctor_absence",
    "doctor_specific_attendance",
    "unsupported",
}


def _env_value(name: str, default: str = "") -> str:
    if name in os.environ:
        return os.environ[name]
    if dotenv_values:
        env_values = dotenv_values(".env")
        value = env_values.get(name)
        if value is not None:
            return str(value)
    return default


PATIENT_ID_RE = re.compile(r"\b(?:ABHA[-_]?[A-Z0-9]+|PT-\d{1,12}|[A-Z]{2,10}\d{3,20})\b", re.IGNORECASE)
DOCTOR_RE = re.compile(r"\bdr\.?\s+([a-z][a-z\s.]{1,40})", re.IGNORECASE)
PHC_RE = re.compile(r"\b(?:phc|hospital|centre|center)\s+([a-z][a-z\s.-]{1,50})", re.IGNORECASE)
FACILITY_BEFORE_TYPE_RE = re.compile(r"\b([a-z][a-z\s.-]{1,50})\s+(?:phc|hospital|centre|center)\b", re.IGNORECASE)


@dataclass
class ParsedIntent:
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)


def validate_patient_identifier(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,40}", cleaned):
        return None
    return cleaned


def _extract_patient_id(message: str) -> Optional[str]:
    match = PATIENT_ID_RE.search(message)
    if not match:
        return None
    return validate_patient_identifier(match.group(0))


def _extract_doctor_name(message: str) -> Optional[str]:
    match = DOCTOR_RE.search(message)
    if not match:
        return None
    return " ".join(match.group(1).strip(" .").split())[:80]


def _extract_phc_name(message: str) -> Optional[str]:
    match = PHC_RE.search(message)
    if match:
        return " ".join(match.group(1).strip(" .").split())[:80]
    match = FACILITY_BEFORE_TYPE_RE.search(message)
    if match:
        prefix = match.group(1).strip(" .")
        prep_match = re.search(r"\b(?:at|in|for)\s+([a-z][a-z\s.-]*)$", prefix, re.IGNORECASE)
        if prep_match:
            prefix = prep_match.group(1).strip(" .")
        words = [word for word in prefix.split() if word.lower() not in {"at", "in", "the", "for"}]
        if words:
            return " ".join(words[-2:])[:80]
    return None


def _extract_medicine_name(message: str, phc_name: Optional[str] = None) -> Optional[str]:
    lowered = message.lower()
    if phc_name:
        lowered = re.sub(re.escape(phc_name.lower()), " ", lowered, flags=re.IGNORECASE)
    stop_words = {
        "show", "medicine", "medicines", "stock", "available", "availability",
        "how", "many", "are", "is", "in", "of", "tablets", "tablet", "capsules",
        "capsule", "need", "needs", "restocking", "which", "low", "out",
        "inventory", "pharmacy", "dispensary", "phc", "hospital", "centre", "center",
        "at", "from", "for", "get", "the", "data", "details", "list",
    }
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", lowered)
    candidates = [t for t in tokens if t not in stop_words]
    return candidates[0] if candidates else None


def _date_filters(message: str) -> Dict[str, str]:
    today = date.today()
    lowered = message.lower()
    if "yesterday" in lowered:
        d = today - timedelta(days=1)
        return {"date_from": d.isoformat(), "date_to": d.isoformat()}
    if "last 7 days" in lowered or "past week" in lowered or "this week" in lowered:
        return {"date_from": (today - timedelta(days=6)).isoformat(), "date_to": today.isoformat()}
    return {"date_from": today.isoformat(), "date_to": today.isoformat()}


def _rule_based_parse(message: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
    context = context or {}
    lowered = message.lower()
    entities: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}

    explicit_patient_id = _extract_patient_id(message)
    if explicit_patient_id:
        entities["patient_id"] = explicit_patient_id

    if re.search(r"\b(they|them|that patient|this patient)\b", lowered) and not explicit_patient_id:
        context_patient_id = validate_patient_identifier(str(context.get("patient_id", "")))
        if context_patient_id:
            entities["patient_id"] = context_patient_id

    if "footfall" in lowered or "patient count" in lowered or "patients today" in lowered:
        filters.update(_date_filters(message))
        phc_name = _extract_phc_name(message)
        if phc_name:
            entities["phc_name"] = phc_name
        return ParsedIntent("patient_footfall", entities, filters)

    if any(word in lowered for word in ["patient", "abha", "history", "visit", "visits", "receive", "received", "they", "them"]):
        if "medicine" in lowered or "medicines" in lowered or "receive" in lowered or "received" in lowered:
            return ParsedIntent("patient_medicines", entities, filters)
        if "visit" in lowered or "visits" in lowered:
            return ParsedIntent("patient_visits", entities, filters)
        if "history" in lowered or "all available" in lowered or "all information" in lowered:
            return ParsedIntent("patient_history", entities, filters)
        if "find" in lowered or "show" in lowered or explicit_patient_id:
            return ParsedIntent("patient_search", entities, filters)

    if (
        "medicine" in lowered or "medicines" in lowered or "stock" in lowered
        or "inventory" in lowered or "pharmacy" in lowered or "dispensary" in lowered
        or "restocking" in lowered or "tablet" in lowered or "tablets" in lowered
        or "capsule" in lowered or "capsules" in lowered
    ):
        phc_name = _extract_phc_name(message)
        if phc_name:
            entities["phc_name"] = phc_name
        medicine_name = _extract_medicine_name(message, phc_name)
        if medicine_name:
            entities["medicine_name"] = medicine_name
        if "out of stock" in lowered:
            return ParsedIntent("medicine_out_of_stock", entities, filters)
        if "low" in lowered or "restocking" in lowered or "reorder" in lowered:
            return ParsedIntent("medicine_low_stock", entities, filters)
        return ParsedIntent("medicine_stock", entities, filters)

    if "bed" in lowered or "beds" in lowered:
        if "full" in lowered or "phc" in lowered or "centre" in lowered or "center" in lowered:
            return ParsedIntent("phc_bed_status", entities, filters)
        return ParsedIntent("bed_availability", entities, filters)

    if "doctor" in lowered or "dr " in lowered or "dr." in lowered or "attendance" in lowered or "absent" in lowered:
        filters.update(_date_filters(message))
        doctor_name = _extract_doctor_name(message)
        phc_name = _extract_phc_name(message)
        if doctor_name:
            entities["doctor_name"] = doctor_name
        if phc_name:
            entities["phc_name"] = phc_name
        if "absent" in lowered or "absence" in lowered:
            return ParsedIntent("doctor_absence", entities, filters)
        if doctor_name:
            return ParsedIntent("doctor_specific_attendance", entities, filters)
        return ParsedIntent("doctor_attendance", entities, filters)

    return ParsedIntent("unsupported", entities, filters)


def _gemini_parse(message: str, context: Optional[Dict[str, Any]] = None) -> Optional[ParsedIntent]:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = f"""
Return only JSON for this healthcare chatbot NLP task.
Allowed intents: {sorted(SUPPORTED_INTENTS - {'unsupported'})}.
Never return SQL.
Schema: {{"intent":"...", "entities":{{}}, "filters":{{}}}}
Current context: {json.dumps(context or {})}
Message: {message}
"""
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        data = json.loads(text)
        intent = data.get("intent")
        if intent not in SUPPORTED_INTENTS:
            return None
        entities = data.get("entities") or {}
        filters = data.get("filters") or {}
        if entities.get("patient_id"):
            patient_id = validate_patient_identifier(str(entities["patient_id"]))
            if patient_id:
                entities["patient_id"] = patient_id
            else:
                entities.pop("patient_id", None)
        return ParsedIntent(intent=intent, entities=entities, filters=filters)
    except Exception:
        return None


def parse_chat_intent(message: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
    provider = _env_value("CHAT_NLP_PROVIDER", "rules").lower()
    if provider == "gemini":
        parsed = _gemini_parse(message, context)
        if parsed:
            return parsed
    return _rule_based_parse(message, context)
