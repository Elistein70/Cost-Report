"""Get actual column headers from template"""
import pandas as pd

template_path = "/home/user/Cost-Report/data/templates/Anchor and Nemo Core Schedules Template -2024 - Audit Adjustments.xlsm"

print("=" * 80)
print("DETAILED COLUMN HEADER ANALYSIS")
print("=" * 80)

# Check Payroll Reports Input
print("\n📋 PAYROLL REPORTS INPUT - First 15 rows to find headers:")
df = pd.read_excel(template_path, sheet_name="Payroll Reports Input", header=None, nrows=15, engine='openpyxl')
print(df.iloc[:, :14].to_string())

print("\n\n" + "=" * 80)
print("📋 TB TAGGING - First 10 rows:")
df2 = pd.read_excel(template_path, sheet_name="TB Tagging", header=None, nrows=10, engine='openpyxl')
print(df2.iloc[:, :10].to_string())

print("\n\n" + "=" * 80)
print("📋 DETAIL DATA 5 TAGGING - Headers:")
df3 = pd.read_excel(template_path, sheet_name="Detail Data 5 Tagging", header=0, nrows=3, engine='openpyxl')
print("Columns:")
for i, col in enumerate(df3.columns, 1):
    print(f"  {i:2d}. {col}")
