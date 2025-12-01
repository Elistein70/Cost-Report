# Data Directory

This directory contains reference data and templates for ClearDOH.

## Structure

### `/templates`
Place your "Core Schedules Template – 2024.xlsx" here.

The app will use this as the base template for generating final reports.

### `/guides`
Place your allocation guide Excel files here:
- Payroll Allocation Guide.xlsx
- Trial Balance Allocation Guide.xlsx

These will be loaded by processors for more accurate auto-tagging.

### `/samples`
Sample anonymized data files for testing:
- Sample payroll PDFs/CSVs
- Sample trial balance files
- Sample visit exports

## Adding Your Template

1. Get your "Core Schedules Template – 2024.xlsx" file
2. Copy it to `/templates/Core_Schedules_Template_2024.xlsx`
3. Restart the backend server

The app will now use your actual template with all formulas and pivots intact.

## Adding Allocation Guides

The processors currently use simplified built-in dictionaries.

To use your full allocation guides:

1. Place Excel files in `/guides`
2. Update processors to load from Excel:

```python
# In payroll_processor.py
import pandas as pd
guide_df = pd.read_excel('data/guides/Payroll_Allocation_Guide.xlsx')
self.earning_code_map = dict(zip(guide_df['Pattern'], guide_df['Allocation']))
```

This will significantly improve auto-tagging accuracy.
