import sys
import os
import random
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine, SessionLocal
from sqlalchemy.orm import Session
from app.models.health_centre import HealthCentre
from app.models.user import User, UserRole
from app.models.patient import Patient, PatientAuditLog
from app.models.bed import Bed
from app.models.inventory import InventoryItem, InventoryLog
from app.models.attendance import Doctor, DailyQRSession, AttendanceRecord
from app.core.security import get_password_hash

# Mock data sources
CITIES = ["Pune", "Mumbai", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Amravati", "Kolhapur", "Sangli", "Jalgaon", "Latur", "Dhule", "Ahmednagar", "Chandrapur"]
PHC_NAMES = ["Sanjeevani", "Aarogya", "Jivan", "Swasthya", "Navjeevan", "Chetana", "Kalyan", "Sahyadri", "Shraddha", "Anand", "Vatsalya", "Aadhar"]
MEDICINES = ["Paracetamol 500mg", "Amoxicillin 250mg", "Ibuprofen 400mg", "Cetirizine 10mg", "Omeprazole 20mg", "Metformin 500mg", "Amlodipine 5mg", "Azithromycin 500mg", "Pantoprazole 40mg", "Diclofenac 50mg"]
EQUIPMENTS = ["Syringes", "Bandages", "Cotton Rolls", "Surgical Gloves", "Thermometers", "Stethoscopes", "BP Monitors"]
FIRST_NAMES = ["Amit", "Rahul", "Priya", "Sneha", "Vikram", "Suresh", "Ramesh", "Sunita", "Anita", "Geeta", "Mohan", "Raju", "Anjali", "Pooja", "Kiran"]
LAST_NAMES = ["Sharma", "Patil", "Deshmukh", "Joshi", "Kulkarni", "Deshpande", "Pawar", "Jadhav", "Kale", "Bhosale", "More", "Shinde", "Yadav", "Singh"]

def generate_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def seed_db():
    db = SessionLocal()
    try:
        # Create 10 new PHCs
        print("Creating Health Centres...")
        new_phcs = []
        for i in range(10):
            district = random.choice(CITIES)
            phc_name = f"{random.choice(PHC_NAMES)} {random.choice(['PHC', 'CHC'])} {district}"
            hc = HealthCentre(
                name=phc_name,
                type=random.choice(["PHC", "CHC"]),
                district=district,
                state="Maharashtra",
                total_beds=random.randint(10, 50),
                latitude=round(random.uniform(15.0, 22.0), 4),
                longitude=round(random.uniform(72.0, 80.0), 4),
                contact_number=generate_phone(),
                location=f"Near Main Square, {district}"
            )
            hc.available_beds = hc.total_beds
            db.add(hc)
            db.flush()
            new_phcs.append(hc)
            
        print("Creating Users & Doctors...")
        admin_pass = get_password_hash("admin123")
        doc_pass = get_password_hash("doc123")
        
        shared_patients_codes = [f"PT-SHARED-{i}" for i in range(1001, 1006)]
        
        for hc in new_phcs:
            # Users
            mo_user = User(username=f"mo_{hc.id}", email=f"mo{hc.id}@example.com", hashed_password=admin_pass, role=UserRole.MEDICAL_OFFICER, hospital_id=hc.id)
            doc_user = User(username=f"doc_{hc.id}", email=f"doc{hc.id}@example.com", hashed_password=doc_pass, role=UserRole.DOCTOR, hospital_id=hc.id)
            rec_user = User(username=f"rec_{hc.id}", email=f"rec{hc.id}@example.com", hashed_password=admin_pass, role=UserRole.RECEPTIONIST, hospital_id=hc.id)
            pharm_user = User(username=f"pharm_{hc.id}", email=f"pharm{hc.id}@example.com", hashed_password=admin_pass, role=UserRole.PHARMACIST, hospital_id=hc.id)
            
            db.add_all([mo_user, doc_user, rec_user, pharm_user])
            db.flush()
            
            # Doctor Model
            doctor = Doctor(
                hospital_id=hc.id,
                name=f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                specialization=random.choice(["General Physician", "Pediatrician", "Gynecologist", "Orthopedic"]),
                phone=generate_phone(),
                email=doc_user.email,
                shift="Morning",
                user_id=doc_user.id
            )
            db.add(doctor)
            db.flush()
            
            # Attendance
            today = datetime.now().date()
            qr_session = DailyQRSession(hospital_id=hc.id, date=today, qr_token=f"QR-{hc.id}-{today}")
            db.add(qr_session)
            db.flush()
            
            att_record = AttendanceRecord(
                doctor_id=doctor.id,
                session_id=qr_session.id,
                status=random.choice(["PRESENT", "PRESENT", "LATE"]),
                scanned_via="MOBILE_APP"
            )
            db.add(att_record)
            
            # Beds
            beds = []
            for i in range(1, hc.total_beds + 1):
                bed = Bed(
                    hospital_id=hc.id,
                    bed_number=f"B-{i:02d}",
                    ward=random.choice(["General", "ICU", "Emergency"]),
                    bed_type=random.choice(["General", "Oxygen Bed"]),
                    status="Available"
                )
                db.add(bed)
                beds.append(bed)
            db.flush()
            
            # Inventory
            inventory_items = []
            for med in MEDICINES:
                item = InventoryItem(
                    hospital_id=hc.id,
                    name=med,
                    category="Medicine",
                    quantity=random.randint(50, 500),
                    unit="Tablets",
                    price=random.randint(5, 50),
                    min_threshold=50,
                    status="Normal"
                )
                db.add(item)
                inventory_items.append(item)
            for eq in EQUIPMENTS:
                item = InventoryItem(
                    hospital_id=hc.id,
                    name=eq,
                    category="Equipment",
                    quantity=random.randint(10, 100),
                    unit="Pieces",
                    price=random.randint(100, 500),
                    min_threshold=10,
                    status="Normal"
                )
                db.add(item)
                inventory_items.append(item)
            db.flush()
            
            # Patients
            num_patients = random.randint(20, 40)
            for p_idx in range(num_patients):
                # Use shared code sometimes to simulate patient visiting multiple PHCs
                if random.random() < 0.1:
                    pt_code = random.choice(shared_patients_codes)
                else:
                    pt_code = f"PT-{hc.id}-{p_idx:04d}"
                    
                status = random.choice(["Outpatient", "Admitted", "Discharged"])
                patient = Patient(
                    hospital_id=hc.id,
                    patient_code=pt_code,
                    name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    age=random.randint(5, 80),
                    gender=random.choice(["Male", "Female"]),
                    contact=generate_phone(),
                    address=f"{random.choice(CITIES)}, Maharashtra",
                    status=status
                )
                db.add(patient)
                db.flush()
                
                if status == "Admitted":
                    avail_beds = [b for b in beds if b.status == "Available"]
                    if avail_beds:
                        bed = avail_beds[0]
                        bed.status = "Occupied"
                        bed.patient_id = patient.id
                        bed.admitted_at = datetime.now()
                        patient.admitted_at = datetime.now()
                        hc.available_beds -= 1
                        
                # Some inventory logs linked to this patient's code
                if random.random() < 0.3:
                    item = random.choice(inventory_items)
                    dispense_amount = random.randint(1, 10)
                    if item.quantity >= dispense_amount:
                        item.quantity -= dispense_amount
                        log = InventoryLog(
                            inventory_id=item.id,
                            change_type="DISPENSE",
                            change_amount=-dispense_amount,
                            reason=f"Dispensed to Patient {patient.patient_code}",
                            performed_by_user_id=pharm_user.id
                        )
                        db.add(log)
            
            # Initial Restock Logs
            for item in inventory_items:
                log = InventoryLog(
                    inventory_id=item.id,
                    change_type="RESTOCK",
                    change_amount=item.quantity,
                    reason="Initial Stock",
                    performed_by_user_id=mo_user.id
                )
                db.add(log)
                
            hc.total_staff = 4
            
        db.commit()
        print("Mock data seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
