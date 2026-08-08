from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("health_centres.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False) # Medicine/Equipment/Consumable
    quantity = Column(Integer, default=0)
    unit = Column(String, nullable=False)
    price = Column(Integer, default=0)
    min_threshold = Column(Integer, default=0)
    expiry_date = Column(Date, nullable=True)
    batch_number = Column(String, nullable=True)
    status = Column(String, default="Normal") # Normal/Low Stock/Expired

    # Relationships
    hospital = relationship("HealthCentre", back_populates="inventory_items")
    logs = relationship("InventoryLog", back_populates="item", cascade="all, delete-orphan")


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    change_type = Column(String, nullable=False) # RESTOCK/DISPENSE/EXPIRED
    change_amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    performed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    item = relationship("InventoryItem", back_populates="logs")
