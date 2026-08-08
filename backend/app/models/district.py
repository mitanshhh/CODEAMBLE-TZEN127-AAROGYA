from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class ResourceRequest(Base):
    __tablename__ = "resource_requests"

    id = Column(Integer, primary_key=True, index=True)
    requesting_phc_id = Column(Integer, ForeignKey("health_centres.id"), nullable=False, index=True)
    target_district = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False) # Medicine/Equipment/Staff/Beds
    quantity = Column(Integer, nullable=False)
    urgency = Column(String, nullable=False) # LOW/MEDIUM/HIGH/CRITICAL
    status = Column(String, default="PENDING", index=True) # PENDING/APPROVED/REJECTED/FULFILLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
