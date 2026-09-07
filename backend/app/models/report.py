from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("health_centres.id"), nullable=False, index=True)
    
    # Period Metadata
    period_type = Column(String, nullable=False, default='This Week')
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Hashing for staleness checks
    data_version = Column(String, nullable=False)
    
    # Generation Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Structured AI Content
    executive_summary = Column(Text, nullable=True)
    risk_analysis = Column(Text, nullable=True)     # stored as JSON string
    recommendations = Column(Text, nullable=True)   # stored as JSON string
    key_insights = Column(Text, nullable=True)      # stored as JSON string
    
    # Aggregate Metrics
    health_score = Column(Float, nullable=True)
    pdf_url = Column(String, nullable=True)
