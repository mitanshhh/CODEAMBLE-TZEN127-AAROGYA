"""Backfill patient_code for all existing patients that don't have one."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine
from sqlalchemy import text

def backfill():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id FROM patients WHERE patient_code IS NULL")).fetchall()
        count = 0
        for row in rows:
            patient_id = row[0]
            code = f"PT-{str(patient_id).zfill(4)}"
            conn.execute(text("UPDATE patients SET patient_code = :code WHERE id = :pid"), {"code": code, "pid": patient_id})
            count += 1
        conn.commit()
        print(f"Backfilled {count} patients with patient_code.")
        
        # Print first 10 to verify
        result = conn.execute(text("SELECT id, patient_code, name FROM patients ORDER BY id LIMIT 10")).fetchall()
        for r in result:
            print(f"  ID={r[0]}  patient_code={r[1]}  name={r[2]}")

if __name__ == "__main__":
    backfill()
