# ClearDOH - NY DOH Home Care Cost Report Automation

## What This App Does

ClearDOH takes 4 raw data files from NY home care agencies and automatically generates a complete, audit-ready DOH Cost Report in minutes instead of 30-50 hours of manual work.

## Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL or SQLite

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

## User Flow

1. **Create Agency** - Enter agency name + year
2. **Upload Files** (drag & drop):
   - Payroll Register (PDF/CSV)
   - Trial Balance (Excel/CSV)
   - Visit Data - Schedule 5 (Excel/CSV)
   - Optional: Additional schedules
3. **Review** - Check 0-20 flagged items (auto-tagged with <92% confidence)
4. **Generate** - Download complete Cost Report Excel file + PDF

## File Structure

```
Cost-Report/
├── backend/              # Python FastAPI server
│   ├── main.py          # API endpoints
│   ├── models/          # Database models
│   ├── processors/      # File parsing engines
│   ├── tagging/         # Auto-tagging logic
│   └── generators/      # Excel report generator
├── frontend/            # React/Next.js app
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # App pages
│   │   └── utils/       # Helper functions
└── data/               # Sample files & templates
    ├── templates/      # Core Schedules Template
    └── guides/         # Allocation guides
```

## Tech Stack

- **Backend**: Python FastAPI, Pandas, OpenPyXL, pdfplumber
- **Frontend**: React, Next.js, TailwindCSS
- **Database**: PostgreSQL (or SQLite for development)
- **Storage**: Local filesystem (AWS S3 ready)
- **Auth**: Coming in V2

## Development Status

✅ V1 Core Features:
- File upload & parsing (Payroll, TB, Visits)
- Auto-tagging engine with fuzzy matching
- Excel report generation
- Reconciliation dashboard
- Basic UI for review & approval

🚧 Coming in V2:
- User authentication
- Multi-tenant support
- Payment processing
- Advanced analytics
- Cloud deployment

## Support

Questions? Check the `/docs` folder for detailed SOPs and guides.
