"""Pydantic schemas for API requests/responses"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AgencyCreate(BaseModel):
    """Schema for creating a new agency"""
    name: str
    year: int


class AgencyResponse(BaseModel):
    """Schema for agency response"""
    id: int
    name: str
    year: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    """Schema for creating a new report"""
    agency_id: int


class ReportResponse(BaseModel):
    """Schema for report response"""
    id: int
    agency_id: int
    status: str
    created_at: datetime
    flagged_items_count: int
    payroll_tb_variance: Optional[float] = None
    payroll_hours_variance: Optional[float] = None

    class Config:
        from_attributes = True


class FlaggedItemResponse(BaseModel):
    """Schema for flagged item response"""
    id: int
    item_type: str
    original_value: str
    suggested_tag: str
    confidence: float
    reviewed: bool
    approved: bool
    user_corrected_tag: Optional[str] = None
    sheet_name: Optional[str] = None
    row_number: Optional[int] = None

    class Config:
        from_attributes = True


class FlaggedItemUpdate(BaseModel):
    """Schema for updating flagged item"""
    approved: bool
    user_corrected_tag: Optional[str] = None


class ReconciliationResponse(BaseModel):
    """Schema for reconciliation dashboard data"""
    payroll_tb_variance: float
    payroll_tb_status: str  # green, yellow, red
    payroll_hours_variance: float
    payroll_hours_status: str
    flagged_items: List[FlaggedItemResponse]
    checks_passed: bool
    warnings: List[str]
