"""Payroll file processor - handles PDF and CSV payroll files"""
import pandas as pd
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any
from rapidfuzz import fuzz
from config import settings


class PayrollProcessor:
    """Process payroll register files (PDF or CSV)"""

    def __init__(self, file_path: str, db_session):
        self.file_path = Path(file_path)
        self.db = db_session
        self.data = None
        self.tagged_data = None
        self.flagged_items = []

        # Master payroll allocation guide (simplified - you'll load from Excel)
        self.earning_code_map = {
            "Regular Pay": "Base Wages for Hours Worked",
            "Regular": "Base Wages for Hours Worked",
            "Overtime": "Overtime Wages",
            "OT Pay": "Overtime Wages",
            "Holiday Pay": "Holiday Pay",
            "Sick Pay": "Sick Time",
            "Vacation": "Vacation Time",
            "PTO": "PTO",
            "Bonus": "Bonus",
            "Per Diem": "Per Diem",
        }

        self.tax_code_map = {
            "SS-R": "FICA Taxes",
            "FICA": "FICA Taxes",
            "Medicare": "FICA Taxes",
            "FUTA": "FUTA Tax",
            "SUI": "SUI Tax",
            "Workers Comp": "Workers Comp",
            "WC": "Workers Comp",
        }

        # Department hierarchy map
        self.department_map = {
            "HHA": ("Home Health Aide", "HHA", "Direct Care"),
            "CDPAP": ("CDPAP", "CDPAP", "Direct Care"),
            "Nursing": ("Nursing", "RN/LPN", "Direct Care"),
            "Admin": ("Administration", "Admin", "G&A"),
            "Office": ("Administration", "Admin", "G&A"),
        }

    def process(self) -> List[Dict[str, Any]]:
        """Main processing method"""
        # Step 1: Extract data from file
        if self.file_path.suffix.lower() == '.pdf':
            self.data = self._extract_from_pdf()
        else:
            self.data = self._extract_from_csv()

        # Step 2: Auto-tag the data
        self.tagged_data = self._auto_tag()

        # Step 3: Return flagged items
        return self.flagged_items

    def _extract_from_pdf(self) -> pd.DataFrame:
        """Extract payroll data from PDF"""
        rows = []
        current_department = None

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                # Parse line by line
                for line in text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # Detect department headers (customize based on your PDFs)
                    if "Department:" in line or line.endswith("Department"):
                        current_department = line.replace("Department:", "").strip()
                        continue

                    # Parse payroll lines (customize column detection)
                    # This is simplified - you'll need to adapt to your specific PDF format
                    parts = line.split()
                    if len(parts) >= 4 and current_department:
                        try:
                            # Example: Earning Code, Hours, Amount, Tax Code, Tax Amount
                            rows.append({
                                'Department Name': current_department,
                                'Earning Code': ' '.join(parts[:-3]),
                                'Hours': float(parts[-3]),
                                'Amount': float(parts[-2].replace('$', '').replace(',', '')),
                                'ER Tax Code': parts[-1] if len(parts) > 4 else '',
                                'ER Tax Amount': 0.0
                            })
                        except (ValueError, IndexError):
                            continue

        return pd.DataFrame(rows)

    def _extract_from_csv(self) -> pd.DataFrame:
        """Extract payroll data from CSV/Excel"""
        if self.file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(self.file_path)
        else:
            df = pd.read_csv(self.file_path)

        # Standardize column names
        column_mapping = {
            'dept': 'Department Name',
            'department': 'Department Name',
            'earning': 'Earning Code',
            'paycode': 'Earning Code',
            'hrs': 'Hours',
            'hours': 'Hours',
            'amount': 'Amount',
            'gross': 'Amount',
            'tax_code': 'ER Tax Code',
            'tax': 'ER Tax Code',
            'tax_amount': 'ER Tax Amount',
        }

        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns=column_mapping)

        return df

    def _auto_tag(self) -> pd.DataFrame:
        """Auto-tag payroll data with allocation codes"""
        if self.data is None or self.data.empty:
            return pd.DataFrame()

        df = self.data.copy()

        # Add tagging columns
        df['Department_L1'] = ''
        df['Department_L2'] = ''
        df['Department_L3'] = ''
        df['Paycode_Allocation'] = ''
        df['Tax_Allocation'] = ''
        df['Confidence_Paycode'] = 0.0
        df['Confidence_Tax'] = 0.0

        for idx, row in df.iterrows():
            # Tag department hierarchy
            dept_tag, confidence = self._tag_department(row['Department Name'])
            df.at[idx, 'Department_L1'] = dept_tag[0]
            df.at[idx, 'Department_L2'] = dept_tag[1]
            df.at[idx, 'Department_L3'] = dept_tag[2]

            # Tag earning code
            paycode_tag, paycode_confidence = self._tag_earning_code(
                row.get('Earning Code', '')
            )
            df.at[idx, 'Paycode_Allocation'] = paycode_tag
            df.at[idx, 'Confidence_Paycode'] = paycode_confidence

            # Flag if confidence is low
            if paycode_confidence < settings.CONFIDENCE_THRESHOLD:
                self.flagged_items.append({
                    'original_value': row.get('Earning Code', ''),
                    'suggested_tag': paycode_tag,
                    'confidence': paycode_confidence,
                    'row_number': idx + 2  # +2 for header row in Excel
                })

            # Tag tax code
            if pd.notna(row.get('ER Tax Code')):
                tax_tag, tax_confidence = self._tag_tax_code(row['ER Tax Code'])
                df.at[idx, 'Tax_Allocation'] = tax_tag
                df.at[idx, 'Confidence_Tax'] = tax_confidence

                if tax_confidence < settings.CONFIDENCE_THRESHOLD:
                    self.flagged_items.append({
                        'original_value': row['ER Tax Code'],
                        'suggested_tag': tax_tag,
                        'confidence': tax_confidence,
                        'row_number': idx + 2
                    })

        return df

    def _tag_department(self, dept_name: str) -> tuple:
        """Tag department with fuzzy matching"""
        if not dept_name:
            return ('Unknown', 'Unknown', 'Unknown'), 0.5

        dept_name_clean = dept_name.strip().upper()

        # Exact match first
        for key, value in self.department_map.items():
            if key.upper() in dept_name_clean:
                return value, 1.0

        # Fuzzy match
        best_match = None
        best_score = 0
        for key, value in self.department_map.items():
            score = fuzz.ratio(dept_name_clean, key.upper()) / 100
            if score > best_score:
                best_score = score
                best_match = value

        if best_match and best_score > 0.7:
            return best_match, best_score

        return ('Unknown', 'Unknown', 'Unknown'), 0.5

    def _tag_earning_code(self, earning_code: str) -> tuple:
        """Tag earning code with fuzzy matching"""
        if not earning_code:
            return 'Unknown', 0.5

        earning_clean = earning_code.strip()

        # Exact match
        if earning_clean in self.earning_code_map:
            return self.earning_code_map[earning_clean], 1.0

        # Fuzzy match
        best_match = None
        best_score = 0
        for key, value in self.earning_code_map.items():
            score = fuzz.ratio(earning_clean.lower(), key.lower()) / 100
            if score > best_score:
                best_score = score
                best_match = value

        if best_match and best_score > 0.7:
            return best_match, best_score

        return 'Unknown', 0.5

    def _tag_tax_code(self, tax_code: str) -> tuple:
        """Tag tax code with fuzzy matching"""
        if not tax_code:
            return 'Unknown', 0.5

        tax_clean = tax_code.strip()

        # Exact match
        if tax_clean in self.tax_code_map:
            return self.tax_code_map[tax_clean], 1.0

        # Fuzzy match
        best_match = None
        best_score = 0
        for key, value in self.tax_code_map.items():
            score = fuzz.ratio(tax_clean.lower(), key.lower()) / 100
            if score > best_score:
                best_score = score
                best_match = value

        if best_match and best_score > 0.7:
            return best_match, best_score

        return 'Unknown', 0.5

    def save_to_excel(self, output_path: str):
        """Save tagged data to Excel file"""
        if self.tagged_data is not None:
            self.tagged_data.to_excel(output_path, sheet_name='Payroll Reports Input', index=False)
