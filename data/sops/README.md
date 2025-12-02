# ClearDOH Standard Operating Procedures (SOPs)

This directory contains all SOPs that guide the data processing logic.

## Directory Structure

```
data/sops/
├── README.md (this file)
├── visit_data_sop.md          # Visit Data processing rules
├── payroll_sop.md             # Payroll processing rules
├── trial_balance_sop.md       # Trial Balance processing rules
├── allocation_guides/         # Master allocation dictionaries
│   ├── payroll_codes.xlsx     # Payroll code mappings
│   ├── expense_categories.xlsx # TB expense categories
│   └── service_types.xlsx     # Visit service type mappings
└── output_formats/            # Expected output formats
    ├── payroll_output.md      # Payroll output spec
    ├── tb_output.md           # TB output spec
    └── visit_output.md        # Visit output spec
```

## How SOPs Are Used

The code automatically reads SOPs from this directory:
- **Markdown files** (.md) - For processing steps and rules
- **Excel files** (.xlsx) - For allocation guides and mappings

## How to Update

When you update an SOP:
1. Save the updated file in the appropriate location
2. The processors will automatically reload the mappings
3. For structural changes, code updates may be needed

## File Format Guidelines

### Processing SOPs (Markdown)
- Use numbered steps
- Include specific rules and thresholds
- Document exceptions
- Example output format

### Allocation Guides (Excel)
- Column 1: Original Value (code/description from source data)
- Column 2: Tag/Category (what it should be tagged as)
- Column 3: Notes (optional - why this mapping exists)

## Questions?

If the app encounters items not in the SOPs, they will be:
1. Flagged with low confidence
2. Sent to AI for reasoning (if enabled)
3. Presented for your review
