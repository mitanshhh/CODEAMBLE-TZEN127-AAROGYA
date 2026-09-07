from google import genai
from app.core.config import settings
import json

def get_inventory_insights(inventory_data: list) -> str:
    if not settings.GEMINI_API_KEY:
        return json.dumps({"recommendation": "Gemini API key not configured."})
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = f"""
    As an AI healthcare logistics assistant, analyze the following inventory data and provide detailed, structured insights about EVERY single medicine listed in the data. Do not summarize generally; provide specific analysis for each medicine regarding its current stock, run rate, and restock necessity.
    
    Data: {inventory_data}
    
    Return ONLY a valid JSON object strictly matching this schema:
    {{
        "insights": ["detailed analysis for Medicine A...", "detailed analysis for Medicine B..."],
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

def get_analytics_insights(analytics_data: dict, period_type: str = "Custom Range") -> str:
    if not settings.GEMINI_API_KEY:
        return json.dumps({
            "executive_summary": "Gemini API key not configured.",
            "risks": [],
            "recommendations": [],
            "key_insights": []
        })
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = f"""
    You are an AI healthcare administrator analyzing operational data for a Primary Health Centre.
    You must NOT calculate simple statistics (like totals or percentages) as those have already been calculated.
    Your job is to INTERPRET the data, identify risks, and provide actionable recommendations for the Medical Officer or District Admin.
    
    REPORTING PERIOD: {period_type}
    
    DETERMINISTIC ANALYTICS:
    {json.dumps(analytics_data, indent=2)}
    
    Provide your analysis by returning ONLY a valid JSON object strictly matching this schema:
    {{
        "executive_summary": "A concise 2-3 sentence overview of the most important operational findings.",
        "key_insights": [
            "Insight 1 (e.g. Patient volume peaked on Wed but bed capacity handled it well)",
            "Insight 2",
            "Insight 3"
        ],
        "risks": [
            {{
                "category": "String (e.g., Medicine Stockout Risk, Capacity Utilization)",
                "severity": "High" or "Moderate" or "Low",
                "description": "Specific risk details with evidence from the data"
            }}
        ],
        "recommendations": [
            "Specific, evidence-based, actionable recommendation 1",
            "Actionable recommendation 2"
        ]
    }}
    
    Do NOT output markdown code blocks. Output ONLY raw JSON.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return json.dumps({
            "executive_summary": f"AI Error: {str(e)}", 
            "risks": [], 
            "recommendations": [], 
            "key_insights": []
        })
