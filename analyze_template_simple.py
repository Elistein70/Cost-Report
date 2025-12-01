"""Analyze the uploaded DOH template structure - simplified version"""
import pandas as pd
from pathlib import Path

template_path = "/home/user/Cost-Report/data/templates/Anchor and Nemo Core Schedules Template -2024 - Audit Adjustments.xlsm"

print("=" * 80)
print("TEMPLATE ANALYSIS - Anchor and Nemo Core Schedules Template 2024")
print("=" * 80)

# Get all sheet names
xl_file = pd.ExcelFile(template_path, engine='openpyxl')
sheet_names = xl_file.sheet_names

print(f"\nTotal Sheets: {len(sheet_names)}\n")
print("ALL SHEET NAMES:")
for i, name in enumerate(sheet_names, 1):
    print(f"  {i:2d}. {name}")

# Analyze key input sheets
key_sheets = [
    "Payroll Reports Input",
    "TB",
    "TB Tagging",
    "Detail Data 5",
    "Detail Data 5 Tagging",
    "Schedule 6",
    "Schedule 10",
    "Schedule 11",
    "Schedule 14"
]

print("\n" + "=" * 80)
print("KEY INPUT SHEETS STRUCTURE:")
print("=" * 80)

for sheet_name in key_sheets:
    if sheet_name in sheet_names:
        try:
            # Read first few rows
            df = pd.read_excel(template_path, sheet_name=sheet_name, nrows=5, engine='openpyxl')

            print(f"\n📋 {sheet_name}")
            print(f"   Columns ({len(df.columns)}):")

            for i, col in enumerate(df.columns, 1):
                col_letter = chr(64 + i) if i <= 26 else f"A{chr(64 + i - 26)}"
                print(f"      {col_letter}: {col}")

            print(f"\n   Sample Data (first 2 rows):")
            print(df.head(2).to_string(index=False))
            print()

        except Exception as e:
            print(f"\n📋 {sheet_name}")
            print(f"   ⚠️  Could not read: {str(e)[:100]}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
