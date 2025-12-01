"""Trial Balance processor"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from rapidfuzz import fuzz
from config import settings


class TrialBalanceProcessor:
    """Process Trial Balance / General Ledger files"""

    def __init__(self, file_path: str, db_session):
        self.file_path = Path(file_path)
        self.db = db_session
        self.data = None
        self.tagged_data = None
        self.flagged_items = []

        # Master TB allocation guide (simplified - load from Excel in production)
        self.expense_allocation_map = {
            # Account description patterns -> (Program, Category, Router)
            "Wages": ("All Programs", "Salaries", "Payroll Router"),
            "Salaries": ("All Programs", "Salaries", "Payroll Router"),
            "Payroll Tax": ("All Programs", "Payroll Taxes", "Payroll Router"),
            "FICA": ("All Programs", "Payroll Taxes", "Payroll Router"),
            "Health Insurance": ("All Programs", "Fringe Benefits", "All Direct Care"),
            "Workers Comp": ("All Programs", "Workers Compensation", "Payroll Router"),
            "Rent": ("All Programs", "Rent", "G&A Allocation"),
            "Utilities": ("All Programs", "Utilities", "G&A Allocation"),
            "Telephone": ("All Programs", "Telephone", "G&A Allocation"),
            "Office Supplies": ("All Programs", "Office Supplies", "G&A Allocation"),
            "Professional Fees": ("All Programs", "Professional Fees", "G&A Allocation"),
            "Insurance": ("All Programs", "Insurance", "G&A Allocation"),
            "Depreciation": ("All Programs", "Depreciation", "G&A Allocation"),
            "Bad Debt": ("All Programs", "Bad Debt", "Revenue Router"),
            "Wage Parity": ("Program Aide", "Wage Parity", "WP Router"),
        }

        # Color codes for payroll allocation lines (matches template)
        self.payroll_line_colors = {
            "Salaries": "LightBlue",
            "Payroll Taxes": "Red",
            "Fringe Benefits": "Orange",
            "Workers Compensation": "Purple",
        }

    def process(self) -> List[Dict[str, Any]]:
        """Main processing method"""
        # Step 1: Load file
        self.data = self._load_file()

        # Step 2: Normalize (handle DR/CR columns)
        self.data = self._normalize_balances()

        # Step 3: Auto-tag
        self.tagged_data = self._auto_tag()

        return self.flagged_items

    def _load_file(self) -> pd.DataFrame:
        """Load TB file (Excel or CSV)"""
        if self.file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(self.file_path)
        else:
            df = pd.read_csv(self.file_path)

        # Standardize column names
        column_mapping = {
            'account': 'Account',
            'account_number': 'Account',
            'acct': 'Account',
            'description': 'Description',
            'account_name': 'Description',
            'debit': 'Debit',
            'dr': 'Debit',
            'credit': 'Credit',
            'cr': 'Credit',
            'balance': 'Balance',
            'amount': 'Balance',
        }

        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns=column_mapping)

        return df

    def _normalize_balances(self) -> pd.DataFrame:
        """Create net balance column if needed"""
        df = self.data.copy()

        if 'Balance' not in df.columns:
            # If DR/CR columns exist, calculate balance
            if 'Debit' in df.columns and 'Credit' in df.columns:
                df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
                df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
                df['Balance'] = df['Debit'] - df['Credit']
            else:
                df['Balance'] = 0

        df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce').fillna(0)
        return df

    def _auto_tag(self) -> pd.DataFrame:
        """Auto-tag TB expenses"""
        df = self.data.copy()

        # Add tagging columns
        df['Program'] = ''
        df['Category'] = ''
        df['Router'] = ''
        df['Color_Code'] = ''
        df['Confidence'] = 0.0

        for idx, row in df.iterrows():
            description = str(row.get('Description', ''))

            # Tag based on description
            tag, confidence = self._tag_expense(description)

            df.at[idx, 'Program'] = tag[0]
            df.at[idx, 'Category'] = tag[1]
            df.at[idx, 'Router'] = tag[2]

            # Color code payroll lines
            if tag[1] in self.payroll_line_colors:
                df.at[idx, 'Color_Code'] = self.payroll_line_colors[tag[1]]

            df.at[idx, 'Confidence'] = confidence

            # Flag low confidence items
            if confidence < settings.CONFIDENCE_THRESHOLD:
                self.flagged_items.append({
                    'original_value': description,
                    'suggested_tag': f"{tag[0]} | {tag[1]} | {tag[2]}",
                    'confidence': confidence,
                    'row_number': idx + 2
                })

        return df

    def _tag_expense(self, description: str) -> tuple:
        """Tag expense line with fuzzy matching"""
        if not description:
            return ('Unknown', 'Unknown', 'Unknown'), 0.5

        description_clean = description.strip()

        # Exact substring match first
        for key, value in self.expense_allocation_map.items():
            if key.lower() in description_clean.lower():
                return value, 1.0

        # Fuzzy match
        best_match = None
        best_score = 0
        for key, value in self.expense_allocation_map.items():
            score = fuzz.partial_ratio(description_clean.lower(), key.lower()) / 100
            if score > best_score:
                best_score = score
                best_match = value

        if best_match and best_score > 0.75:
            return best_match, best_score

        return ('Unknown', 'Unknown', 'Unknown'), 0.5

    def save_to_excel(self, output_path: str):
        """Save tagged data to Excel"""
        if self.tagged_data is not None:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Raw TB
                self.data.to_excel(writer, sheet_name='TB', index=False)
                # Tagged TB
                self.tagged_data.to_excel(writer, sheet_name='TB Tagging', index=False)
