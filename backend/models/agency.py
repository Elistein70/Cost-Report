"""Database models for agencies and reports"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Agency(Base):
    """Agency entity"""
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reports = relationship("Report", back_populates="agency")

    def __repr__(self):
        return f"<Agency {self.name} - {self.year}>"


class Report(Base):
    """Cost Report entity"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    status = Column(String, default="draft")  # draft, processing, review, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Processing metadata
    payroll_file = Column(String)
    trial_balance_file = Column(String)
    visit_file = Column(String)
    additional_files = Column(Text)  # JSON string of additional files

    # Reconciliation metrics
    payroll_tb_variance = Column(Float)
    payroll_hours_variance = Column(Float)
    flagged_items_count = Column(Integer, default=0)

    # Output files
    final_excel_path = Column(String)
    final_pdf_path = Column(String)
    reconciliation_pdf_path = Column(String)

    # Relationships
    agency = relationship("Agency", back_populates="reports")
    flagged_items = relationship("FlaggedItem", back_populates="report")

    def __repr__(self):
        return f"<Report {self.id} - {self.status}>"


class FlaggedItem(Base):
    """Items flagged for user review (confidence < 92%)"""
    __tablename__ = "flagged_items"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)

    # Item details
    item_type = Column(String)  # payroll, trial_balance, visit
    original_value = Column(String)
    suggested_tag = Column(String)
    confidence = Column(Float)

    # User action
    reviewed = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    user_corrected_tag = Column(String)

    # Context
    sheet_name = Column(String)
    row_number = Column(Integer)
    additional_context = Column(Text)  # JSON

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="flagged_items")

    def __repr__(self):
        return f"<FlaggedItem {self.item_type} - {self.confidence:.2%}>"
