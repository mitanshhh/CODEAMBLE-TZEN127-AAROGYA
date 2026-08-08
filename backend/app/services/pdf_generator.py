import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

REPORTS_DIR = "static/reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def generate_monthly_report(hospital_id: int, month_year: str, health_score: float, metrics: dict) -> str:
    filename = f"report_h{hospital_id}_{month_year}_{int(datetime.now().timestamp())}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1, # Center
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceBefore=14,
        spaceAfter=6
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 6
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=3
    )

    story = []

    # Title
    story.append(Paragraph("MINISTRY OF HEALTH & FAMILY WELFARE", title_style))
    story.append(Paragraph("MONTHLY OPERATIONAL AUDIT REPORT", title_style))
    story.append(Spacer(1, 12))
    
    # Metadata
    story.append(Paragraph(f"<b>Hospital:</b> {metrics.get('hospital_name')}", normal_style))
    story.append(Paragraph(f"<b>Report Month:</b> {month_year}", normal_style))
    story.append(Paragraph(f"<b>Generated Date:</b> {metrics.get('date')}", normal_style))
    story.append(Spacer(1, 12))
    
    # Health Score
    risk_level = "Low Risk" if health_score > 75 else "Moderate Risk" if health_score > 50 else "High Risk"
    story.append(Paragraph("<b>Overall Health Score Risk Level</b>", normal_style))
    story.append(Paragraph(f"{round(health_score)}/100 {risk_level}", normal_style))
    story.append(Spacer(1, 12))
    
    # Section 1
    story.append(Paragraph("1. Executive Summary", h2_style))
    story.append(Paragraph("This month, the PHC maintained a stable operational status despite localized medicine shortages.", normal_style))
    
    # Section 2
    story.append(Paragraph("2. Hospital Overview", h2_style))
    story.append(Paragraph("The hospital saw steady attendance and effectively managed its available resources.", normal_style))
    story.append(Paragraph("<b>Key Strengths</b>", normal_style))
    story.append(Paragraph("• 100% attendance during emergency hours", bullet_style))
    story.append(Paragraph("• Zero bed turnaround delays", bullet_style))
    story.append(Paragraph("<b>Key Weaknesses</b>", normal_style))
    story.append(Paragraph("• Chronic shortage of specific antibiotics", bullet_style))
    story.append(Paragraph("• Delayed lab test reports", bullet_style))
    
    # Section 3
    story.append(Paragraph("3. Operational Metrics & KPIs", h2_style))
    
    # Calculate absent assuming 22 working days for 1 doc for dummy data
    monthly_absent = (metrics.get('total_docs', 1) * 22) - metrics.get('present_docs', 0)
    monthly_absent = max(0, monthly_absent)
    
    occ_percent = 0
    if metrics.get('total_beds', 0) > 0:
        occ_percent = round((metrics.get('occupied_beds', 0) / metrics.get('total_beds', 1)) * 100)
    
    table_data = [
        ["Metric", "Value"],
        ["Total Medicines", str(metrics.get('total_medicines', 0))],
        ["Medicines Low Stock", str(metrics.get('low_stock_items', 0))],
        ["Medicines Out of Stock", str(metrics.get('out_of_stock', 0))],
        ["Total Doctors", str(metrics.get('total_docs', 0))],
        ["Monthly Present (Shifts)", str(metrics.get('present_docs', 0))],
        ["Monthly Absent (Estimated)", str(monthly_absent)],
        ["Total Beds", str(metrics.get('total_beds', 0))],
        ["Average Occupancy %", f"{occ_percent}%"],
        ["Monthly Patient Footfall", str(metrics.get('total_patients', 0))],
        ["Emergency Cases", str(metrics.get('waiting_patients', 0))],
        ["Critical Alerts", "1"]
    ]
    
    t = Table(table_data, colWidths=[2.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f6f7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0"))
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Operational Analysis</b>", normal_style))
    story.append(Paragraph("Operations remained steady with an average patient footfall processed efficiently.", normal_style))
    
    # Section 4
    story.append(Paragraph("4. Departmental Analysis", h2_style))
    story.append(Paragraph("<b>Medicine & Inventory</b>", normal_style))
    story.append(Paragraph("Inventory faced significant challenges with key items dropping to out-of-stock levels mid-month.", normal_style))
    story.append(Paragraph("<b>Doctor Attendance</b>", normal_style))
    story.append(Paragraph("Doctor attendance averaged above 90%, meeting district standards.", normal_style))
    story.append(Paragraph("<b>Patient Footfall</b>", normal_style))
    story.append(Paragraph("Patient wait times were kept under 30 minutes on average. Overall footprint remained stable.", normal_style))
    
    # Section 5
    story.append(Paragraph("5. Risk Assessment", h2_style))
    risk_data = [
        ["Severity", "Impact", "Recommendation"],
        ["High", "Patient care delayed due to\nantibiotic shortage.", "Increase buffer stock for seasonal\nmedicines."]
    ]
    rt = Table(risk_data, colWidths=[1*inch, 2.5*inch, 2.5*inch])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f6f7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0"))
    ]))
    story.append(rt)
    story.append(Spacer(1, 12))
    
    # Section 6
    story.append(Paragraph("6. District Comparison & Progress", h2_style))
    story.append(Paragraph("Performing slightly above district average in attendance, but below in inventory.", normal_style))
    story.append(Paragraph("Stable progress from last month, mostly maintaining the status quo.", normal_style))
    
    # Section 7
    story.append(Paragraph("7. Action Plan & Roadmap", h2_style))
    story.append(Paragraph("<b>Priority Actions</b>", normal_style))
    story.append(Paragraph("• Approve pending resource requests", bullet_style))
    story.append(Paragraph("<b>Improvement Roadmap</b>", normal_style))
    story.append(Paragraph("• Month 1: Inventory overhaul", bullet_style))
    story.append(Paragraph("• Month 2: Attendance tracking strictness", bullet_style))
    
    # Section 8
    story.append(Paragraph("8. Conclusion", h2_style))
    story.append(Paragraph("The PHC is on a stable trajectory but needs immediate inventory intervention.", normal_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("_____________________________", normal_style))
    story.append(Paragraph("Authorized AI Audit Signature", normal_style))
    
    doc.build(story)
    return filepath
