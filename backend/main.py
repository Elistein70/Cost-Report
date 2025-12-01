"""Main FastAPI application"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
from pathlib import Path

from config import settings
from database import get_db, init_db
from models import Agency, Report, FlaggedItem
from schemas import (
    AgencyCreate,
    AgencyResponse,
    ReportCreate,
    ReportResponse,
    FlaggedItemResponse,
    FlaggedItemUpdate,
    ReconciliationResponse,
)
from processors.payroll_processor import PayrollProcessor
from processors.trial_balance_processor import TrialBalanceProcessor
from processors.visit_processor import VisitProcessor
from generators.excel_generator import ExcelGenerator

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/api/agencies", response_model=AgencyResponse)
def create_agency(agency: AgencyCreate, db: Session = Depends(get_db)):
    """Create a new agency"""
    db_agency = Agency(name=agency.name, year=agency.year)
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    return db_agency


@app.get("/api/agencies", response_model=List[AgencyResponse])
def list_agencies(db: Session = Depends(get_db)):
    """List all agencies"""
    return db.query(Agency).all()


@app.get("/api/agencies/{agency_id}", response_model=AgencyResponse)
def get_agency(agency_id: int, db: Session = Depends(get_db)):
    """Get agency by ID"""
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


@app.post("/api/reports", response_model=ReportResponse)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    """Create a new report for an agency"""
    # Verify agency exists
    agency = db.query(Agency).filter(Agency.id == report.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    db_report = Report(agency_id=report.agency_id, status="draft")
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


@app.get("/api/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get report by ID"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.post("/api/reports/{report_id}/upload/payroll")
async def upload_payroll(
    report_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload payroll file"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Save file
    file_path = settings.UPLOAD_DIR / f"report_{report_id}_payroll_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update report
    report.payroll_file = str(file_path)
    db.commit()

    return {"message": "Payroll file uploaded", "filename": file.filename}


@app.post("/api/reports/{report_id}/upload/trial-balance")
async def upload_trial_balance(
    report_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload trial balance file"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Save file
    file_path = settings.UPLOAD_DIR / f"report_{report_id}_tb_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update report
    report.trial_balance_file = str(file_path)
    db.commit()

    return {"message": "Trial balance file uploaded", "filename": file.filename}


@app.post("/api/reports/{report_id}/upload/visits")
async def upload_visits(
    report_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload visit data file"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Save file
    file_path = settings.UPLOAD_DIR / f"report_{report_id}_visits_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update report
    report.visit_file = str(file_path)
    db.commit()

    return {"message": "Visit file uploaded", "filename": file.filename}


async def process_report_background(report_id: int, db: Session):
    """Background task to process all uploaded files"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return

    try:
        report.status = "processing"
        db.commit()

        # Process payroll
        if report.payroll_file:
            processor = PayrollProcessor(report.payroll_file, db)
            flagged_items = processor.process()

            # Create flagged items
            for item in flagged_items:
                db_item = FlaggedItem(
                    report_id=report_id,
                    item_type="payroll",
                    original_value=item["original_value"],
                    suggested_tag=item["suggested_tag"],
                    confidence=item["confidence"],
                    sheet_name="Payroll Reports Input",
                    row_number=item.get("row_number")
                )
                db.add(db_item)

        # Process trial balance
        if report.trial_balance_file:
            processor = TrialBalanceProcessor(report.trial_balance_file, db)
            flagged_items = processor.process()

            for item in flagged_items:
                db_item = FlaggedItem(
                    report_id=report_id,
                    item_type="trial_balance",
                    original_value=item["original_value"],
                    suggested_tag=item["suggested_tag"],
                    confidence=item["confidence"],
                    sheet_name="TB Tagging",
                    row_number=item.get("row_number")
                )
                db.add(db_item)

        # Process visits
        if report.visit_file:
            processor = VisitProcessor(report.visit_file, db)
            flagged_items = processor.process()

            for item in flagged_items:
                db_item = FlaggedItem(
                    report_id=report_id,
                    item_type="visit",
                    original_value=item["original_value"],
                    suggested_tag=item["suggested_tag"],
                    confidence=item["confidence"],
                    sheet_name="Detail Data 5 Tagging",
                    row_number=item.get("row_number")
                )
                db.add(db_item)

        # Update report
        report.status = "review"
        report.flagged_items_count = db.query(FlaggedItem).filter(
            FlaggedItem.report_id == report_id
        ).count()
        db.commit()

    except Exception as e:
        report.status = "error"
        db.commit()
        print(f"Error processing report: {e}")


@app.post("/api/reports/{report_id}/process")
async def process_report(
    report_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start processing all uploaded files"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.payroll_file or not report.trial_balance_file or not report.visit_file:
        raise HTTPException(
            status_code=400,
            detail="All required files must be uploaded first"
        )

    # Start background processing
    background_tasks.add_task(process_report_background, report_id, db)

    return {"message": "Processing started", "report_id": report_id}


@app.get("/api/reports/{report_id}/flagged-items", response_model=List[FlaggedItemResponse])
def get_flagged_items(report_id: int, db: Session = Depends(get_db)):
    """Get all flagged items for a report"""
    items = db.query(FlaggedItem).filter(FlaggedItem.report_id == report_id).all()
    return items


@app.put("/api/flagged-items/{item_id}")
def update_flagged_item(
    item_id: int,
    update: FlaggedItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a flagged item (approve or correct)"""
    item = db.query(FlaggedItem).filter(FlaggedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Flagged item not found")

    item.reviewed = True
    item.approved = update.approved
    if update.user_corrected_tag:
        item.user_corrected_tag = update.user_corrected_tag

    db.commit()
    return {"message": "Flagged item updated"}


@app.get("/api/reports/{report_id}/reconciliation", response_model=ReconciliationResponse)
def get_reconciliation(report_id: int, db: Session = Depends(get_db)):
    """Get reconciliation dashboard data"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    flagged_items = db.query(FlaggedItem).filter(
        FlaggedItem.report_id == report_id,
        FlaggedItem.reviewed == False
    ).all()

    # Calculate variances (placeholder - will be calculated from actual data)
    payroll_tb_variance = report.payroll_tb_variance or 0.0
    payroll_hours_variance = report.payroll_hours_variance or 0.0

    def get_status(variance: float) -> str:
        if abs(variance) < 0.03:
            return "green"
        elif abs(variance) < 0.05:
            return "yellow"
        return "red"

    return ReconciliationResponse(
        payroll_tb_variance=payroll_tb_variance,
        payroll_tb_status=get_status(payroll_tb_variance),
        payroll_hours_variance=payroll_hours_variance,
        payroll_hours_status=get_status(payroll_hours_variance),
        flagged_items=[FlaggedItemResponse.from_orm(item) for item in flagged_items],
        checks_passed=len(flagged_items) == 0,
        warnings=[]
    )


@app.post("/api/reports/{report_id}/generate")
async def generate_final_report(report_id: int, db: Session = Depends(get_db)):
    """Generate final Excel and PDF reports"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check all items are reviewed
    unreviewed = db.query(FlaggedItem).filter(
        FlaggedItem.report_id == report_id,
        FlaggedItem.reviewed == False
    ).count()

    if unreviewed > 0:
        raise HTTPException(
            status_code=400,
            detail=f"{unreviewed} items still need review"
        )

    try:
        # Generate Excel report
        generator = ExcelGenerator(report, db)
        excel_path = generator.generate()

        report.final_excel_path = excel_path
        report.status = "completed"
        db.commit()

        return {
            "message": "Report generated successfully",
            "excel_path": excel_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/api/reports/{report_id}/download/excel")
async def download_excel(report_id: int, db: Session = Depends(get_db)):
    """Download final Excel report"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.final_excel_path:
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report.final_excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{report.agency.name}_DOH_Cost_Report_{report.agency.year}_FINAL.xlsx"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
