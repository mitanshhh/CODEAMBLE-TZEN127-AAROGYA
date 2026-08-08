from sqlalchemy import text
from app.db.database import engine

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE inventory_items ADD COLUMN price INTEGER DEFAULT 0;'))
    conn.commit()
print("Added price column")
