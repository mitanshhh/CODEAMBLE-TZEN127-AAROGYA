import os
import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from supabase import create_client, Client
from app.models.report import Report
from app.utils.date_utils import get_now_ist

REPORTS_DIR = "static/reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)


from app.core.config import settings

def _get_supabase_client() -> Client | None:
    """Initialization of Supabase client using central app settings."""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if url and key:
        try:
            return create_client(url, key)
        except Exception as e:
            print(f"Failed to create Supabase client: {e}")
            return None
    print(f"Supabase credentials missing in settings. URL={'set' if url else 'MISSING'}, KEY={'set' if key else 'MISSING'}")
    return None


def safe_json_loads(data_str):
    try:
        return json.loads(data_str) if data_str else []
    except:
        return []

def create_chart_image(fig, width=6.5*inch, height=3*inch):
    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight', dpi=150)
    img_data.seek(0)
    plt.close(fig)
    return Image(img_data, width=width, height=height)

def generate_analytics_report_pdf(report: Report, hospital_name: str, metrics: dict) -> str:
    now = get_now_ist()
    filename = f"analytics_h{report.hospital_id}_{now.strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    brand_color = colors.HexColor("#1e3a8a")
    dark_gray = colors.HexColor("#334155")
    light_gray = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, spaceAfter=4, textColor=brand_color)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=dark_gray)
    h1_style = ParagraphStyle('H1Style', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, spaceBefore=20, spaceAfter=10, textColor=brand_color)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, spaceBefore=10, spaceAfter=6, textColor=dark_gray)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, spaceAfter=6, leading=14, textColor=dark_gray)
    bold_style = ParagraphStyle('BoldStyle', parent=normal_style, fontName='Helvetica-Bold')
    bullet_style = ParagraphStyle('BulletStyle', parent=normal_style, leftIndent=15, bulletIndent=5)
    center_style = ParagraphStyle('CenterStyle', parent=normal_style, alignment=TA_CENTER)
    
    story = []

    # ---------------------------------------------------------
    # PAGE 1: HEADER & EXECUTIVE SNAPSHOT
    # ---------------------------------------------------------
    
    # Header Table
    header_data = [
        [Paragraph("<b>AAROGYA</b><br/>Healthcare Operations Analytics Report", title_style),
         Paragraph(f"<b>Generated:</b> {now.strftime('%d %b %Y, %I:%M %p')}<br/><b>Data Version:</b> {report.data_version[:8]}", subtitle_style)]
    ]
    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # Meta Table
    meta_data = [
        [Paragraph(f"<b>Health Centre:</b> {hospital_name}", normal_style),
         Paragraph(f"<b>Reporting Period:</b> {report.period_start.strftime('%d %b %Y')} to {report.period_end.strftime('%d %b %Y')}", normal_style)]
    ]
    meta_table = Table(meta_data, colWidths=[3.5*inch, 3.5*inch])
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Health Score
    health_score = metrics.get('health_score', 0)
    score_color = "#16a34a" if health_score >= 80 else "#ea580c" if health_score >= 50 else "#dc2626"
    story.append(Paragraph(f"<font color='{score_color}'>OVERALL HEALTH SCORE: {health_score} / 100</font>", ParagraphStyle('Score', parent=h1_style, alignment=TA_CENTER, fontSize=16)))
    story.append(Spacer(1, 15))
    
    # KPI Grid
    pat = metrics.get('patients', {})
    bed = metrics.get('beds', {})
    doc_m = metrics.get('doctors', {})
    inv = metrics.get('inventory', {})
    
    kpi_data = [
        [Paragraph("<b>PATIENTS</b>", center_style), Paragraph("<b>BEDS</b>", center_style), Paragraph("<b>DOCTORS</b>", center_style), Paragraph("<b>INVENTORY</b>", center_style)],
        [
            Paragraph(f"<b>{pat.get('total_period', 0)}</b> Total<br/>{pat.get('admitted', 0)} Admitted<br/>{pat.get('discharged', 0)} Discharged", center_style),
            Paragraph(f"<b>{bed.get('occupied', 0)}</b> Occupied<br/>{bed.get('available', 0)} Available<br/>{bed.get('occupancy_pct', 0)}% Occ Rate", center_style),
            Paragraph(f"<b>{doc_m.get('present_today', 0)}</b> Present<br/>{doc_m.get('total', 0)} Total<br/>{doc_m.get('attendance_today_pct', 0)}% Att Rate", center_style),
            Paragraph(f"<b>{inv.get('total', 0)}</b> Total Items<br/>{inv.get('low_stock', 0)} Low Stock<br/>{inv.get('out_of_stock', 0)} Critical", center_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[1.8*inch]*4)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), brand_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BACKGROUND', (0,1), (-1,1), light_gray),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 20))
    
    # AI Executive Summary
    story.append(Paragraph("AI EXECUTIVE SUMMARY", h1_style))
    story.append(Paragraph(report.executive_summary or "No executive summary available.", normal_style))
    
    insights = safe_json_loads(report.key_insights)
    if insights:
        story.append(Paragraph("KEY INSIGHTS", h2_style))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", bullet_style))
            
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # PAGE 2: PATIENT FOOTFALL
    # ---------------------------------------------------------
    story.append(Paragraph("PATIENT FOOTFALL", h1_style))
    
    pat_trend = pat.get('trend', [])
    if pat_trend:
        try:
            dates = [datetime.strptime(t['full_date'], "%Y-%m-%d") for t in pat_trend]
            totals = [t.get('patients', 0) for t in pat_trend]
            
            fig, ax = plt.subplots(figsize=(7, 3))
            ax.plot(dates, totals, marker='o', color='#3b82f6', linewidth=2, label='Total Footfall')
            
            ax.set_title('Patient Volume Trend')
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.legend()
            plt.xticks(rotation=45)
            story.append(create_chart_image(fig))
        except Exception as e:
            story.append(Paragraph(f"<i>Could not render chart: {str(e)}</i>", normal_style))
    else:
        story.append(Paragraph("<i>No patient trend data available for this period.</i>", normal_style))

    story.append(Spacer(1, 15))
    
    # Patient Breakdown Pie
    if pat.get('total_period', 0) > 0 or pat.get('admitted', 0) > 0 or pat.get('discharged', 0) > 0:
        fig, ax = plt.subplots(figsize=(4, 3))
        labels = ['Admitted', 'Outpatient', 'Discharged']
        sizes = [pat.get('admitted', 0), pat.get('outpatient', 0), pat.get('discharged', 0)]
        colors_pie = ['#3b82f6', '#10b981', '#64748b']
        
        # Filter out 0s
        labels = [l for l, s in zip(labels, sizes) if s > 0]
        colors_pie = [c for c, s in zip(colors_pie, sizes) if s > 0]
        sizes = [s for s in sizes if s > 0]
        
        if sizes:
            ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title("Patient Flow Outcomes")
            story.append(create_chart_image(fig, width=3.5*inch, height=2.5*inch))
            
    story.append(PageBreak())

    # ---------------------------------------------------------
    # PAGE 3: BED MANAGEMENT
    # ---------------------------------------------------------
    story.append(Paragraph("BED MANAGEMENT", h1_style))
    
    # Bed status breakdown (no trend available, show snapshot)
    story.append(Paragraph(f"Total Beds: <b>{bed.get('total', 0)}</b> | Occupied: <b>{bed.get('occupied', 0)}</b> | Available: <b>{bed.get('available', 0)}</b> | Maintenance: <b>{bed.get('maintenance', 0)}</b> | Occupancy: <b>{bed.get('occupancy_pct', 0)}%</b>", normal_style))
    
    if bed.get('total', 0) > 0:
        try:
            fig, ax = plt.subplots(figsize=(5, 3))
            labels = ['Occupied', 'Available', 'Maintenance']
            sizes = [bed.get('occupied', 0), bed.get('available', 0), bed.get('maintenance', 0)]
            chart_colors = ['#8b5cf6', '#10b981', '#f59e0b']
            labels = [l for l, s in zip(labels, sizes) if s > 0]
            chart_colors = [c for c, s in zip(chart_colors, sizes) if s > 0]
            sizes = [s for s in sizes if s > 0]
            if sizes:
                ax.pie(sizes, labels=labels, colors=chart_colors, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                ax.set_title('Bed Status Breakdown')
                story.append(create_chart_image(fig, width=4*inch, height=3*inch))
        except Exception as e:
            pass
        
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # PAGE 4: DOCTOR ATTENDANCE & INVENTORY
    # ---------------------------------------------------------
    story.append(Paragraph("DOCTOR & STAFF ATTENDANCE", h1_style))
    
    doc_trend = doc_m.get('trend', [])
    if doc_trend:
        try:
            dates = [datetime.strptime(t['full_date'], "%Y-%m-%d") for t in doc_trend]
            present = [t['present'] for t in doc_trend]
            
            fig, ax = plt.subplots(figsize=(7, 3))
            ax.bar(dates, present, color='#0ea5e9')
            ax.set_title('Daily Doctor Attendance')
            ax.grid(axis='y', linestyle='--', alpha=0.6)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            plt.xticks(rotation=45)
            story.append(create_chart_image(fig))
        except Exception as e:
            pass
    else:
        story.append(Paragraph("<i>No attendance trend data available for this period.</i>", normal_style))

    story.append(Spacer(1, 20))
    
    story.append(Paragraph("MEDICINE & INVENTORY", h1_style))
    critical_items = inv.get('critical_items', [])
    if critical_items:
        story.append(Paragraph("Critical Inventory Items", h2_style))
        inv_data = [["Medicine Name", "Current Stock", "Threshold", "Status"]]
        for item in critical_items:
            qty = item.get('quantity', 0)
            status = "OUT OF STOCK" if qty == 0 else "LOW STOCK"
            inv_data.append([item.get('name', 'Unknown'), str(qty), str(item.get('threshold', 0)), status])
            
        inv_table = Table(inv_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        inv_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ef4444")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('PADDING', (0,0), (-1,-1), 6),
            ('TEXTCOLOR', (3,1), (3,-1), colors.HexColor("#ef4444"))
        ]))
        story.append(inv_table)
    else:
        story.append(Paragraph("<i>No critical inventory items during this reporting period.</i>", normal_style))

    story.append(PageBreak())

    # ---------------------------------------------------------
    # PAGE 5: CROSS-DOMAIN INSIGHTS & RISKS
    # ---------------------------------------------------------
    story.append(Paragraph("RISK ANALYSIS", h1_style))
    
    risks = safe_json_loads(report.risk_analysis)
    if risks:
        for r in risks:
            if isinstance(r, dict):
                sev = r.get("severity", "UNKNOWN").upper()
                bg_color = "#fee2e2" if sev == "HIGH" else "#fef3c7" if sev == "MEDIUM" else "#f1f5f9"
                title_color = "#991b1b" if sev == "HIGH" else "#92400e" if sev == "MEDIUM" else "#334155"
                
                content = f"<b>{sev} RISK: {r.get('category', 'Category')}</b><br/><br/>{r.get('description', 'N/A')}"
                if 'evidence' in r:
                    content += f"<br/><br/><b>Evidence:</b> {r['evidence']}"
                if 'action' in r:
                    content += f"<br/><br/><b>Action:</b> {r['action']}"
                    
                t = Table([[Paragraph(content, normal_style)]], colWidths=[7.2*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor(title_color)),
                    ('PADDING', (0,0), (-1,-1), 12),
                ]))
                story.append(KeepTogether([t, Spacer(1, 10)]))
    else:
        story.append(Paragraph("No significant risks identified.", normal_style))
        
    story.append(Spacer(1, 20))
    story.append(Paragraph("PRIORITY RECOMMENDATIONS", h1_style))
    recs = safe_json_loads(report.recommendations)
    if recs:
        for i, rec in enumerate(recs, 1):
            if isinstance(rec, dict):
                text = f"<b>{i}. {rec.get('issue', 'Recommendation')}</b><br/>{rec.get('action', '')}"
            else:
                text = f"<b>{i}.</b> {rec}"
            story.append(Paragraph(text, normal_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No priority recommendations.", normal_style))

    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>End of Operations Report</b><br/>Generated securely by Aarogya Intelligence.<br/>All timestamps are in IST.", ParagraphStyle('Footer', parent=subtitle_style, alignment=TA_CENTER)))

    doc.build(story)
    
    # Upload to Supabase
    sb = _get_supabase_client()
    if sb:
        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()
                
            file_path_in_bucket = f"{filename}"
            sb.storage.from_("reports").upload(
                file=file_bytes,
                path=file_path_in_bucket,
                file_options={"content-type": "application/pdf"}
            )
            public_url = sb.storage.from_("reports").get_public_url(file_path_in_bucket)
            print(f"PDF uploaded to Supabase: {public_url}")
            return public_url
        except Exception as e:
            print(f"Failed to upload to Supabase, falling back to local: {e}")
            return f"/static/reports/{filename}"
    else:
        print("Supabase client not available, using local path")
    
    return f"/static/reports/{filename}"
