# Template Analysis: Anchor and Nemo Core Schedules Template 2024

## Overview
- **File**: Anchor and Nemo Core Schedules Template -2024 - Audit Adjustments.xlsm
- **Total Sheets**: 34
- **Type**: Excel Macro-Enabled Workbook (.xlsm)

## All Sheets (34 total)

1. Detail Data 5 Tagging
2. County allocation
3. HHA-CDPAP
4. TB
5. TB Tagging
6. Payroll Reports Input
7. hide this
8. Schedule 3b
9. Schedule 3c
10. Schedule 4b
11. Schedule 4c
12. schedule 5b
13. schedule 5c
14. Schedule 8b
15. Schedule 8c
16. Detail Data 10
17. Sch 10B
18. Sch 10C
19. Schedule 11b
20. Schedule 11c
21. Schedule 12b
22. Schedule 12c
23. Schedule 17
24. Schedule 18
25. Schedule 19
26. Schedule 17 b
27. schedule 17 c
28. Schedule 18 b
29. Schedule 18 c
30. Schedule 19 b
31. Schedule 19 c
32. G.10
33. Private Pay Pivot
34. Check

---

## KEY INPUT SHEETS STRUCTURE

### 1. **Payroll Reports Input** Sheet

**Structure:**
- Headers start at Row 5
- Data starts at Row 6
- 52 columns total (A through AZ)

**Key Columns (first 14):**
- **Column A**: ??? (appears to be category)
- **Column B**: OTHER/Department marker
- **Column C**: G&A or other category
- **Column D**: Blank or sub-category
- **Column E**: **Tag** (Paycode allocation - "Premium Pay", "Other Wages", "Base Wages for Hours Worked")
- **Column F**: **Code** (Earning code - "Bonus", "Meal", "Misc Pay", "Regular")
- **Column G**: **Hours**
- **Column H**: ??? (multiplier?)
- **Column I**: **Amount** (dollar amount)
- **Column J**: ???
- **Column K**: Tax category description
- **Column L**: **Taxes** (tax code - "FUTA", "MED-R", "NY-MTA1", "NYCLA", "NYSUI", "SS-R")
- **Column M**: **Amount** (tax amount)
- **Column N**: ???

**Summary Totals (visible):**
- Column O: "Total Hours" = 11,891,178.1
- Column Q: "Total wages" = $244,677,337.91
- Column S: "Total Taxes" = $24,623,303.83

**Sample Data Pattern:**
```
Tag: "Base Wages for Hours Worked"
Code: "Regular"
Hours: 628.11
Amount: $122,366.77

Tax: "FICA Taxes"
Code: "SS-R"
Amount: $2,290.89
```

---

### 2. **TB** (Trial Balance) Sheet

**Structure:**
- Title: "Anchor and Nemo Trial Balance"
- Date range: "January 1, 2024 - December 31, 2024"
- 7 columns

**Columns:**
- **Column A**: Account name
- **Column B**: Debit amounts
- **Column C**: Credit amounts
- **Column D**: ??? (calculated balance?)
- **Column E**: "Revenue" header
- **Column F**: Revenue amount (324,121,606.52)
- **Column G**: "for Sch 19"

**Sample Rows:**
- Cross River Bank: Debit $3,135,190.24

---

### 3. **TB Tagging** Sheet

**Structure:**
- Complex allocation sheet with WR&R calculations
- 22 columns (A through V)

**Key Visible Data:**
- **WR&R** calculations visible in columns F-J
- **WR&R** = $6,008,678.19
- **Direct Care**: 88.60% allocation (0.885982)
- **Program Admin**: 11.40% allocation (0.114018)
- **Non-allowable**: 0%

**Row 5+ Headers:**
- Column A: "Account:"
- Column B: "Balance:"
- Column C: "Schedule 3 Allocation Columns"
- Column D: "Schedule 4 Allocation Rows"
- Column E: "Schedule 4 Allocation Columns"
- Column F+: Program type allocations (RN, PDN, etc.)

**Sample Account Row:**
- Account: "GROSS WAGES"
- Balance: $244,627,921.69
- Allocation: "Payroll Allocation"

**Account Categories Visible:**
- GROSS WAGES
- WR&R WAGES
- WAGES AIDES
- WAGES AIDES LHCSA/CDPAP
- WAGES AIDES NHTD/TBI

---

### 4. **Detail Data 5 Tagging** Sheet

**Structure:**
- Clean header row (Row 1)
- 21 columns

**Complete Column List:**
1. **Sr#** - Serial number
2. **County** - County name (Nassau, Kings, etc.)
3. **Contract** - Contract name (Americare, Centers Plan For Healthy Living CDPAP, etc.)
4. **Source Of Admission** - CHHA, MLTC, etc.
5. **Contract Type** - CHHA, CDPAP, etc.
6. **Service Code** - Service code description
7. **Export Code** - Billing code (S9122, T1019:U6, etc.)
8. **Level of Service** - Service level description
9. **HHA/CDPAP** - Program type (HHA, CDPAP, etc.)
10. **Payor Source** - Payer (Other, MC Medicaid CDPAP, etc.)
11. **CHHA** - CHHA designation (CHHA, NaN, etc.)
12. **Patient Count** - Number of patients
13. **Visit Count** - Number of visits
14. **Billed Hours** - Total billed hours
15. **Unique Patient Count** - Unique patients
16. **Unique Visit Count** - Unique visits
17. **Unique Billed Hours** - Unique hours
18. **Nursing override** - Override flag
19. **PDN** - PDN flag
20. **Live-In 13** - Live-in indicator
21. **Admin** - Admin category (NR, R, etc.)

**Sample Data Row 1:**
- Sr#: 1
- County: Nassau
- Contract: Americare
- Source: CHHA
- Type: CHHA
- Service Code: HHA1
- Export Code: S9122
- Level: Subcontractor Services
- HHA/CDPAP: HHA
- Payor: Other
- CHHA: CHHA
- Patients: 3
- Visits: 48
- Hours: 179.25
- Unique Patients: 2
- Unique Visits: 10
- Unique Hours: 34.0

**Sample Data Row 2:**
- County: Kings
- Contract: Centers Plan For Healthy Living CDPAP
- Source: MLTC
- Type: CDPAP
- Service Code: PA Hourly - 5 Boroughs
- Export Code: T1019:U6
- Level: CDPAS: Individual - Basic
- HHA/CDPAP: CDPAP
- Payor: MC Medicaid CDPAP
- Visits: 10
- Hours: 40.00
- Admin: R

---

## Key Observations for App Customization

### Payroll Reports Input:
- **NOT a simple column A-N layout** as originally coded
- Headers are in Row 5
- Data starts Row 6
- Need to map:
  - Column E → Tag/Paycode Allocation
  - Column F → Earning Code
  - Column G → Hours
  - Column I → Amount
  - Column L → Tax Code
  - Column M → Tax Amount

### TB Tagging:
- **Complex allocation structure** with percentages
- WR&R calculations built-in
- Multiple allocation columns for different programs
- Need to preserve existing formulas

### Detail Data 5 Tagging:
- **21 columns** (not simplified version in app)
- Already has proper headers in Row 1
- Includes override columns (Nursing override, PDN, Live-In 13, Admin)
- Need to map all 21 columns correctly

---

## Next Steps for Code Updates

1. **Update `payroll_processor.py`**:
   - Write to columns E, F, G, I, L, M (not A-N)
   - Start writing at Row 6 (Row 5 is headers)
   - Preserve summary formulas in columns O, Q, S

2. **Update `trial_balance_processor.py`**:
   - Understand complex TB Tagging structure
   - Map accounts correctly
   - Preserve WR&R calculations and allocation percentages

3. **Update `visit_processor.py`**:
   - Map all 21 columns from Detail Data 5 Tagging
   - Handle override columns
   - Preserve Admin (NR/R) designations

4. **Update `excel_generator.py`**:
   - Load actual template file
   - Write to correct rows/columns
   - Don't overwrite formulas and pivot tables
   - Preserve all 34 sheets

---

## Template File Location

```
/home/user/Cost-Report/data/templates/Anchor and Nemo Core Schedules Template -2024 - Audit Adjustments.xlsm
```

Ready for integration into ClearDOH app!
