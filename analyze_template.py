"""Analyze the uploaded DOH template structure"""
import openpyxl
from pathlib import Path
import json

template_path = Path("/home/user/Cost-Report/data/templates/Anchor and Nemo Core Schedules Template -2024 - Audit Adjustments.xlsm")

# Load workbook
wb = openpyxl.load_workbook(template_path, data_only=False)

analysis = {
    "sheet_names": wb.sheetnames,
    "sheets_detail": {}
}

# Analyze key input sheets
key_sheets = [
    "Payroll Reports Input",
    "TB",
    "TB Tagging",
    "Detail Data 5",
    "Detail Data 5 Tagging"
]

for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]

    # Get first row (headers)
    headers = []
    for cell in ws[1]:
        if cell.value:
            headers.append({
                "column": cell.column_letter,
                "value": str(cell.value)
            })

    analysis["sheets_detail"][sheet_name] = {
        "max_row": ws.max_row,
        "max_col": ws.max_column,
        "headers": headers[:20]  # First 20 columns
    }

# Print analysis
print("=" * 80)
print("TEMPLATE ANALYSIS")
print("=" * 80)
print(f"\nTotal Sheets: {len(analysis['sheet_names'])}\n")

print("ALL SHEET NAMES:")
for i, name in enumerate(analysis['sheet_names'], 1):
    print(f"  {i}. {name}")

print("\n" + "=" * 80)
print("KEY INPUT SHEETS STRUCTURE:")
print("=" * 80)

for sheet_name in key_sheets:
    if sheet_name in analysis['sheets_detail']:
        detail = analysis['sheets_detail'][sheet_name]
        print(f"\n📋 {sheet_name}")
        print(f"   Dimensions: {detail['max_row']} rows × {detail['max_col']} columns")
        print(f"   Headers:")
        for h in detail['headers']:
            print(f"      {h['column']}: {h['value']}")

print("\n" + "=" * 80)
