from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("health_centres.id"), nullable=False, index=True)
    bed_number = Column(String, nullable=False, index=True)
    ward = Column(String, nullable=False) # General/ICU/Emergency
    bed_type = Column(String, default="General") # General/ICU/Oxygen Bed/Ventilator Bed/Pediatric
    status = Column(String, default="Available", index=True) # Available/Occupied/Maintenance
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, unique=True)
    admitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    hospital = relationship("HealthCentre", back_populates="beds")
    patient = relationship("Patient", back_populates="bed")
