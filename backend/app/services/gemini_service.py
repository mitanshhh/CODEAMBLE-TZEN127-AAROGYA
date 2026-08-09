from google import genai
from app.core.config import settings
import json

def get_inventory_insights(inventory_data: list) -> str:
    if not settings.GEMINI_API_KEY:
        return json.dumps({"recommendation": "Gemini API key not configured."})
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = f"""
    As an AI healthcare logistics assistant, analyze the following inventory data and provide structured insights:
    - Identify critical stock depletion alerts.
    - Recommend resource reallocation.
    
    Data: {inventory_data}
    
    Return ONLY a valid JSON object strictly matching this schema:
    {{
        "insights": ["insight string 1", "insight string 2"],
        "risk_factors": ["risk string 1"],
        "recommendations": ["recommendation string 1"]
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_analytics_insights(metrics: dict) -> str:
    if not settings.GEMINI_API_KEY:
        return json.dumps({
            "executive_summary": "Gemini API key not configured.",
            "risks": [],
            "recommendations": []
        })
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = f"""
    As an AI healthcare administrator, analyze the following PHC dashboard metrics and provide a structured operational overview.
    
    Metrics: {metrics}
    
    Return ONLY a valid JSON object strictly matching this schema:
    {{
        "executive_summary": "A 2-3 sentence overview of the current operational health.",
        "risks": [
            {{"category": "Staffing/Inventory/Capacity", "severity": "High" or "Moderate" or "Low", "description": "Specific risk details"}}
        ],
        "recommendations": ["Actionable recommendation 1", "Actionable recommendation 2"]
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return json.dumps({"executive_summary": f"AI Error: {str(e)}", "risks": [], "recommendations": []})
