"""Visit data processor - Schedule 5"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
try:
    from config import settings
except ImportError:
    from backend.config_simple import settings


class VisitProcessor:
    """Process visit/schedule 5 data from HHAeXchange or other platforms"""

    def __init__(self, file_path: str, db_session):
        self.file_path = Path(file_path)
        self.db = db_session
        self.data = None
        self.tagged_data = None
        self.flagged_items = []
        self.questions = []  # Questions for clarification

        # PMPM codes (delete Unique Patient/Visit/Hours per SOP 3.1)
        self.pmpm_codes = [
            '2443', '2444', '2445',
            '8400', '8401', '8402',
            'T1022:UA', 'T1022:UB', 'T1022:UC'
        ]

        # Live-In codes (apply x13 rule)
        self.live_in_keywords = ['live-in', 'live in', 'livein']

        # Program type patterns
        self.program_patterns = {
            'HHA': ['hha', 'home health aide', 'aide'],
            'CDPAP': ['cdpap', 'consumer directed'],
            'Nursing': ['rn', 'lpn', 'nurse', 'nursing'],
            'NHTD': ['nhtd'],
            'TBI': ['tbi'],
        }

    def process(self) -> List[Dict[str, Any]]:
        """Main processing method"""
        # Step 1: Load file
        self.data = self._load_file()

        # Step 2: Clean data per SOP rules
        self.data = self._clean_data()

        # Step 3: Auto-tag program types
        self.tagged_data = self._auto_tag()

        return self.flagged_items

    def _load_file(self) -> pd.DataFrame:
        """Load visit data file - only reads 'Detail Data' tab from Excel"""
        if self.file_path.suffix.lower() in ['.xlsx', '.xls']:
            # Only read from 'Detail Data' sheet
            df = pd.read_excel(self.file_path, sheet_name='Detail Data', engine='openpyxl')
        else:
            df = pd.read_csv(self.file_path)

        # Standardize column names
        column_mapping = {
            'billing_code': 'Billing Code',
            'code': 'Billing Code',
            'service_code': 'Billing Code',
            'description': 'Service Description',
            'service': 'Service Description',
            'unique_patients': 'Unique Patients',
            'patients': 'Unique Patients',
            'unique_visits': 'Unique Visits',
            'visits': 'Visit Count',
            'visit_count': 'Visit Count',
            'unique_hours': 'Unique Hours',
            'billed_hours': 'Billed Hours',
            'hours': 'Billed Hours',
            'county': 'County',
            'payer': 'Payer',
            'payor': 'Payer',
        }

        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns=column_mapping)

        # Ensure required columns exist
        required_cols = ['Billing Code', 'Visit Count', 'Billed Hours']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0

        return df

    def _clean_data(self) -> pd.DataFrame:
        """Apply SOP 3.1 cleaning rules"""
        df = self.data.copy()

        # Rule 1: Delete Unique columns for PMPM codes
        for idx, row in df.iterrows():
            billing_code = str(row.get('Billing Code', ''))
            if any(code in billing_code for code in self.pmpm_codes):
                df.at[idx, 'Unique Patients'] = None
                df.at[idx, 'Unique Visits'] = None
                df.at[idx, 'Unique Hours'] = None

        # Rule 2: Live-In hours = Visit Count × 13
        for idx, row in df.iterrows():
            description = str(row.get('Service Description', '')).lower()
            if any(keyword in description for keyword in self.live_in_keywords):
                visit_count = pd.to_numeric(row.get('Visit Count', 0), errors='coerce')
                if pd.notna(visit_count):
                    df.at[idx, 'Billed Hours'] = visit_count * 13

        # Rule 3: Nursing - Billed Hours should ≈ Visit Count
        # (This is a check, not an auto-correction - flag if variance is high)

        return df

    def _auto_tag(self) -> pd.DataFrame:
        """Auto-tag program types"""
        df = self.data.copy()

        df['Program_Type'] = ''
        df['Service_Category'] = ''
        df['Confidence'] = 0.0

        for idx, row in df.iterrows():
            description = str(row.get('Service Description', ''))
            billing_code = str(row.get('Billing Code', ''))

            # Determine program type
            program_type, confidence = self._tag_program_type(description, billing_code)

            df.at[idx, 'Program_Type'] = program_type
            df.at[idx, 'Confidence'] = confidence

            # Determine service category
            if any(keyword in description.lower() for keyword in self.live_in_keywords):
                df.at[idx, 'Service_Category'] = 'Live-In'
            elif program_type == 'Nursing':
                df.at[idx, 'Service_Category'] = 'Nursing Visit'
            else:
                df.at[idx, 'Service_Category'] = 'Standard Visit'

            # Flag if confidence is low
            if confidence < settings.CONFIDENCE_THRESHOLD:
                self.flagged_items.append({
                    'original_value': description,
                    'suggested_tag': program_type,
                    'confidence': confidence,
                    'row_number': idx + 2
                })

        return df

    def _tag_program_type(self, description: str, billing_code: str) -> tuple:
        """Tag program type based on description and code"""
        if not description:
            return 'Unknown', 0.5

        description_lower = description.lower()

        # Check each program pattern
        for program, patterns in self.program_patterns.items():
            for pattern in patterns:
                if pattern in description_lower:
                    return program, 1.0

        # Check billing code patterns (customize based on your codes)
        if billing_code.startswith('G'):
            return 'HHA', 0.85
        elif billing_code.startswith('S'):
            return 'CDPAP', 0.85

        return 'Unknown', 0.5

    def save_to_template(self, template_path: str, output_path: str):
        """Save tagged data to actual template"""
        from openpyxl import load_workbook

        if self.tagged_data is None:
            return

        wb = load_workbook(output_path, keep_vba=True)

        # Write to Detail Data 5 Tagging sheet
        if 'Detail Data 5 Tagging' in wb.sheetnames:
            ws = wb['Detail Data 5 Tagging']
            # Write tagged visit data
            # Customize based on template 21-column structure

        wb.save(output_path)

    def get_questions(self) -> List[str]:
        """Return list of questions for user clarification"""
        return list(set(self.questions))
