from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from google.cloud import translate_v2 as translate
from app.core.rate_limit import limiter
import os

router = APIRouter()

class TranslateRequest(BaseModel):
    text: str
    target_language: str # e.g. "hi" for Hindi

@router.post("/")
@limiter.limit("20/minute")
def translate_text(
    request: Request,
    req: TranslateRequest
):
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Translation service is not configured for production use.")
        
    translate_client = translate.Client()
    result = translate_client.translate(
        req.text,
        target_language=req.target_language
    )
    return {"translated_text": result["translatedText"]}
