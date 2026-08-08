from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("health_centres.id"), nullable=False, index=True)
    month_year = Column(String, nullable=False, index=True)
    health_score = Column(Float, nullable=True)
    ai_insights_json = Column(Text, nullable=True)
    pdf_url = Column(String, nullable=True) # Stored internally, accessed via secure endpoint
    created_at = Column(DateTime(timezone=True), server_default=func.now())
