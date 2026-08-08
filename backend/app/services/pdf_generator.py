from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime

REPORTS_DIR = "static/reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def generate_monthly_report(hospital_id: int, month_year: str, health_score: float, insights: str) -> str:
    filename = f"report_h{hospital_id}_{month_year}_{int(datetime.now().timestamp())}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    c.drawString(100, 750, f"Aarogya Health Engine - Monthly Report")
    c.drawString(100, 730, f"Hospital ID: {hospital_id}")
    c.drawString(100, 710, f"Month: {month_year}")
    c.drawString(100, 690, f"Overall Health Score: {health_score}/100")
    
    c.drawString(100, 650, "AI Insights Summary:")
    
    # Simple word wrap for insights
    textobject = c.beginText(100, 630)
    textobject.setFont("Helvetica", 10)
    for line in insights.split('\n'):
        textobject.textLine(line[:100]) # crude wrap
    c.drawText(textobject)
    
    c.save()
    return filepath
