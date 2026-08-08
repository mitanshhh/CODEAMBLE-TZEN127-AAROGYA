from sqlalchemy.orm import Session
from app.models.health_centre import HealthCentre
from app.models.inventory import InventoryItem
from app.models.attendance import DailyQRSession, AttendanceRecord, Doctor
from app.models.bed import Bed
from datetime import date

def calculate_health_score(db: Session, hospital_id: int) -> float:
    score = 100.0
    
    # 1. Bed Availability (30% weight) Target 70-85%
    total_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id).count()
    occupied_beds = db.query(Bed).filter(Bed.hospital_id == hospital_id, Bed.status == "Occupied").count()
    if total_beds > 0:
        occupancy_rate = occupied_beds / total_beds
        if occupancy_rate > 0.85:
            score -= (occupancy_rate - 0.85) * 100 * 0.3
        elif occupancy_rate < 0.70:
            score -= (0.70 - occupancy_rate) * 100 * 0.3
    else:
        score -= 30 # Penalty for no beds
        
    # 2. Inventory Stock Health (30% weight)
    total_items = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id).count()
    low_stock = db.query(InventoryItem).filter(InventoryItem.hospital_id == hospital_id, InventoryItem.status == "Low Stock").count()
    if total_items > 0:
        low_stock_ratio = low_stock / total_items
        score -= (low_stock_ratio * 100 * 0.3)
        
    # 3. Staff Attendance Rate (25% weight)
    today = date.today()
    session = db.query(DailyQRSession).filter(DailyQRSession.hospital_id == hospital_id, DailyQRSession.date == today).first()
    total_doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).count()
    
    if session and total_doctors > 0:
        present = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).count()
        absence_rate = (total_doctors - present) / total_doctors
        score -= (absence_rate * 100 * 0.25)
    else:
        score -= 25 # Penalty for missing QR session or no doctors
        
    # 4. Patient Flow & Throughput (15% weight) - Simplified for MVP
    
    return max(0.0, min(100.0, score))
