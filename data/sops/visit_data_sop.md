# Visit Data (Schedule 5) Processing SOP

## Overview
Process visit data exports from HHAeXchange or other platforms to tag service types and apply DOH rules.

## Input Files
- Excel files with visit/service data
- Must contain: Service Description, Billing Code, Visit Count, Hours

## Processing Steps

### 1. Load Data
- Find sheet with matching headers (service, code, visits, hours)
- Read all rows

### 2. Clean Data (SOP 3.1 Rules)

**Rule 1: PMPM Codes**
Delete Unique Patient/Visit/Hours columns for these codes:
- 2443, 2444, 2445
- 8400, 8401, 8402
- T1022:UA, T1022:UB, T1022:UC

**Rule 2: Live-In Hours**
For services containing "live-in", "live in", or "livein":
- Billed Hours = Visit Count × 13

**Rule 3: Nursing Validation**
For nursing services (RN/LPN):
- Billed Hours should ≈ Visit Count
- Flag if variance > 10%

### 3. Tag Service Types

Tag each service based on description or billing code:

**HHA**: home health aide, aide, personal care, homemaker, attendant, caregiver
**CDPAP**: cdpap, consumer directed, personal assistant
**Nursing**: RN, LPN, nurse, skilled nursing
**NHTD**: nhtd, nursing home transition
**TBI**: tbi, traumatic brain injury
**Therapy**: PT, OT, ST, physical therapy, occupational therapy, speech therapy

**Billing Code Patterns**:
- G codes → HHA
- S codes → CDPAP
- T codes → Therapy
- 99201-99205 → Nursing

### 4. Output Format

**Columns**:
- All original columns
- Program_Type (HHA/CDPAP/Nursing/etc.)
- Service_Category (Live-In/Nursing Visit/Standard Visit)
- Confidence (0.0-1.0)

**Instructions**: Copy to "Detail Data 5 Tagging" sheet in template

## Confidence Thresholds
- 1.0 = Perfect match from description
- 0.85-0.9 = Billing code match
- 0.6 = Has data but no match
- 0.3 = Missing data
- < 0.92 = Flag for review

## Questions to Flag
- Unrecognized service descriptions
- Unusual visit count/hours ratios
- Services with no code or description
