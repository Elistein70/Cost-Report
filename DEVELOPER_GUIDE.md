# ClearDOH - Developer Guide

## Architecture Overview

ClearDOH is a full-stack application with three main components:

### 1. Backend (Python FastAPI)
- **Location**: `/backend`
- **Purpose**: File processing, auto-tagging, Excel generation
- **Key Technologies**: FastAPI, Pandas, OpenPyXL, pdfplumber, rapidfuzz
- **Database**: SQLite (development), PostgreSQL (production)

### 2. Frontend (React/Next.js)
- **Location**: `/frontend`
- **Purpose**: User interface for file upload and review
- **Key Technologies**: Next.js, React, TypeScript, TailwindCSS
- **API Communication**: Axios

### 3. Processing Engine
- **Payroll Processor**: Extracts and tags payroll data from PDF/CSV
- **Trial Balance Processor**: Parses and categorizes GL/TB data
- **Visit Processor**: Cleans and tags Schedule 5 visit data
- **Excel Generator**: Assembles final DOH Cost Report

## Project Structure

```
Cost-Report/
├── backend/
│   ├── main.py              # FastAPI app & endpoints
│   ├── config.py            # App configuration
│   ├── database.py          # Database setup
│   ├── schemas.py           # Pydantic models
│   ├── models/              # SQLAlchemy models
│   │   └── agency.py
│   ├── processors/          # File processing engines
│   │   ├── payroll_processor.py
│   │   ├── trial_balance_processor.py
│   │   └── visit_processor.py
│   ├── generators/          # Report generators
│   │   └── excel_generator.py
│   ├── uploads/             # Uploaded files (gitignored)
│   ├── output/              # Generated reports (gitignored)
│   └── templates/           # Excel templates
│
├── frontend/
│   ├── src/
│   │   ├── pages/           # Next.js pages
│   │   │   ├── index.tsx    # Home page
│   │   │   └── report/[id].tsx  # Report workflow page
│   │   ├── components/      # Reusable components (future)
│   │   └── styles/          # Global styles
│   └── public/              # Static assets
│
└── data/                    # Reference data & guides
    ├── templates/           # Core Schedules Template
    └── guides/              # Allocation guides (Excel)
```

## Key Workflows

### File Upload & Processing

1. User creates agency + report
2. User uploads 3-4 files via drag-and-drop
3. Backend stores files in `/uploads`
4. User clicks "Start Processing"
5. Backend runs processors in background:
   - Parse files → Extract data → Auto-tag → Flag low-confidence items
6. Report status changes to "review"
7. Frontend polls for completion

### Auto-Tagging Engine

Uses **fuzzy string matching** (rapidfuzz) to tag:
- Payroll earning codes → "Base Wages", "Overtime", etc.
- Payroll tax codes → "FICA", "FUTA", etc.
- Department names → Program hierarchy
- TB expense descriptions → Program/Category/Router
- Visit service codes → HHA, CDPAP, Nursing, etc.

**Confidence Scoring:**
- Exact match: 1.0 (100%)
- Fuzzy match: 0.7-0.99
- No match: 0.5 (flagged)
- Threshold: 0.92 (configurable)

Items below threshold are flagged for user review.

### Excel Generation

1. Load template or create basic structure
2. Fill data into specific sheets:
   - Payroll Reports Input
   - TB & TB Tagging
   - Detail Data 5 Tagging
3. Apply user corrections from flagged items
4. Apply formatting (colors, fonts)
5. Save as agency-named file
6. (Future: Refresh pivots/formulas with xlwings)

## API Endpoints

### Agencies
- `POST /api/agencies` - Create agency
- `GET /api/agencies` - List agencies
- `GET /api/agencies/{id}` - Get agency

### Reports
- `POST /api/reports` - Create report for agency
- `GET /api/reports/{id}` - Get report details
- `POST /api/reports/{id}/upload/payroll` - Upload payroll file
- `POST /api/reports/{id}/upload/trial-balance` - Upload TB file
- `POST /api/reports/{id}/upload/visits` - Upload visit file
- `POST /api/reports/{id}/process` - Start processing
- `GET /api/reports/{id}/flagged-items` - Get flagged items
- `POST /api/reports/{id}/generate` - Generate final report
- `GET /api/reports/{id}/download/excel` - Download Excel file

### Flagged Items
- `PUT /api/flagged-items/{id}` - Approve or correct item

## Database Schema

### Agency
- id, name, year, created_at, updated_at

### Report
- id, agency_id, status, file paths, variance metrics, output paths

### FlaggedItem
- id, report_id, item_type, original_value, suggested_tag, confidence
- reviewed, approved, user_corrected_tag
- sheet_name, row_number, context

## Extending the App

### Add a New Processor

1. Create `/backend/processors/my_processor.py`
2. Implement `process()` method
3. Return flagged items list
4. Add endpoint in `main.py`
5. Integrate into report generation

### Add a New Schedule

1. Update processors to handle new data
2. Add sheet to Excel template
3. Update `excel_generator.py` to fill sheet
4. Add tagging rules if needed

### Improve Auto-Tagging

1. Edit master guide dictionaries in processors
2. Load from Excel files in `/data/guides`
3. Train on prior-year agency data (future: ML model)
4. Adjust confidence threshold in config

### Add Authentication

1. Backend: Add JWT auth middleware
2. Frontend: Add login page
3. Database: Add User model
4. Associate reports with users

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
1. Use sample files in `/data/samples`
2. Verify output matches expected template
3. Check reconciliation variances

## Deployment

### Option 1: Docker
```bash
docker-compose up
```

### Option 2: Traditional Hosting
- Backend: Deploy to Heroku, Railway, or AWS EC2
- Frontend: Deploy to Vercel, Netlify
- Database: PostgreSQL on RDS or Heroku
- Storage: AWS S3 for file uploads

### Environment Variables
See `.env.example` for required variables.

## Performance Optimization

- Use Celery for background processing (vs. current background_tasks)
- Cache master tagging guides in Redis
- Optimize pandas operations for large files
- Add progress tracking for long-running processes

## Future Enhancements

- [ ] PDF generation for final report
- [ ] Reconciliation dashboard with charts
- [ ] Multi-tenant support
- [ ] Prior-year data import for better auto-tagging
- [ ] ML model for tagging (vs. fuzzy matching)
- [ ] Schedule 6, 10, 14, 15/16, 20 processors
- [ ] Automated testing suite
- [ ] Cloud deployment scripts

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## Support

Questions? Contact the development team or check the main README.
