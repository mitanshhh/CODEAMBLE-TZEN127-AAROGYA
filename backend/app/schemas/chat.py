from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    scope_all: bool = False


class ChatResponse(BaseModel):
    success: bool
    intent: str
    message: str
    data: List[Dict[str, Any]] = []
    summary: Optional[Dict[str, Any]] = None
    pdf_available: bool = False
    report_id: Optional[str] = None
    context: Dict[str, Any] = {}
