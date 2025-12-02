"""Visit data processor - Schedule 5"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
try:
    from config import settings
except ImportError:
    from backend.config_simple import settings

try:
    from backend.sop_loader import SOPLoader
except ImportError:
    from sop_loader import SOPLoader


class VisitProcessor:
    """Process visit/schedule 5 data from HHAeXchange or other platforms"""

    def __init__(self, file_path: str, db_session):
        self.file_path = Path(file_path)
        self.db = db_session
        self.data = None
        self.tagged_data = None
        self.flagged_items = []
        self.questions = []  # Questions for clarification

        # Load SOP dynamically from data/sops directory
        sop_loader = SOPLoader()
        visit_sop = sop_loader.load_visit_sop()

        # Load patterns from SOP (will use defaults if SOP file doesn't exist)
        self.pmpm_codes = visit_sop.get('pmpm_codes', [
            '2443', '2444', '2445',
            '8400', '8401', '8402',
            'T1022:UA', 'T1022:UB', 'T1022:UC'
        ])

        self.live_in_keywords = visit_sop.get('live_in_keywords', ['live-in', 'live in', 'livein'])

        self.program_patterns = visit_sop.get('program_patterns', {
            'HHA': ['hha', 'home health aide', 'aide', 'personal care', 'homemaker',
                   'home care', 'attendant', 'caregiver'],
            'CDPAP': ['cdpap', 'consumer directed', 'consumer-directed', 'cd-pap',
                     'personal assistant', 'pa services'],
            'Nursing': ['rn', 'lpn', 'nurse', 'nursing', 'registered nurse',
                       'licensed practical', 'skilled nursing', 'sn visit'],
            'NHTD': ['nhtd', 'nursing home transition'],
            'TBI': ['tbi', 'traumatic brain injury'],
            'Therapy': ['pt', 'ot', 'st', 'physical therapy', 'occupational therapy',
                       'speech therapy', 'therapist'],
        })

        self.billing_code_patterns = visit_sop.get('billing_code_patterns', {
            'G': 'HHA',
            'S': 'CDPAP',
            'T': 'Therapy',
            '992': 'Nursing'
        })

        self.confidence_threshold = visit_sop.get('confidence_threshold', settings.CONFIDENCE_THRESHOLD)

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
        """Load visit data file - automatically finds sheet with matching headers"""
        if self.file_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']:
            # Expected headers (any of these variations)
            expected_headers = [
                'billing_code', 'code', 'service_code',
                'description', 'service',
                'visits', 'visit_count', 'unique_visits',
                'hours', 'billed_hours', 'unique_hours',
                'patients', 'unique_patients'
            ]

            # Try to find the right sheet by checking headers
            try:
                import openpyxl
                wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)

                matching_sheet = None
                for sheet_name in wb.sheetnames:
                    try:
                        # Read first few rows to check headers
                        df_test = pd.read_excel(self.file_path, sheet_name=sheet_name, engine='openpyxl', nrows=5)

                        # Check if any expected headers are in the columns
                        columns_lower = [str(col).strip().lower() for col in df_test.columns]
                        matches = sum(1 for header in expected_headers if any(header in col for col in columns_lower))

                        # If we find at least 3 matching headers, this is probably the right sheet
                        if matches >= 3:
                            matching_sheet = sheet_name
                            break
                    except Exception:
                        continue

                wb.close()

                # If we found a matching sheet, use it
                if matching_sheet:
                    df = pd.read_excel(self.file_path, sheet_name=matching_sheet, engine='openpyxl')
                else:
                    # Fall back to first sheet if no match found
                    df = pd.read_excel(self.file_path, engine='openpyxl')

            except Exception as e:
                # If any error, just read the first sheet
                df = pd.read_excel(self.file_path, engine='openpyxl')
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
            # Try multiple column possibilities for description
            description = ''
            for col in ['Service Description', 'Description', 'Service', 'Service_Description',
                       'Service Type', 'ServiceDescription', 'Service_Type']:
                if col in row and pd.notna(row[col]):
                    description = str(row[col])
                    break

            # Try multiple column possibilities for billing code
            billing_code = ''
            for col in ['Billing Code', 'Code', 'Service Code', 'Billing_Code',
                       'BillingCode', 'Service_Code']:
                if col in row and pd.notna(row[col]):
                    billing_code = str(row[col])
                    break

            # Determine program type
            program_type, confidence = self._tag_program_type(description, billing_code)

            df.at[idx, 'Program_Type'] = program_type
            df.at[idx, 'Confidence'] = confidence

            # Determine service category
            if description and any(keyword in description.lower() for keyword in self.live_in_keywords):
                df.at[idx, 'Service_Category'] = 'Live-In'
            elif program_type == 'Nursing':
                df.at[idx, 'Service_Category'] = 'Nursing Visit'
            else:
                df.at[idx, 'Service_Category'] = 'Standard Visit'

            # Flag if confidence is low
            if confidence < self.confidence_threshold:
                self.flagged_items.append({
                    'original_value': description if description else billing_code,
                    'suggested_tag': program_type,
                    'confidence': confidence,
                    'row_number': idx + 2
                })

        return df

    def _tag_program_type(self, description: str, billing_code: str) -> tuple:
        """Tag program type based on description and code"""
        # If we have description, try to match it
        if description and description.lower() not in ['nan', 'none', '']:
            description_lower = description.lower().strip()

            # Check each program pattern
            for program, patterns in self.program_patterns.items():
                for pattern in patterns:
                    if pattern in description_lower:
                        return program, 1.0

        # If we have billing code, try to match it
        if billing_code and billing_code.lower() not in ['nan', 'none', '']:
            billing_code_str = str(billing_code).strip().upper()

            # Check billing code patterns dynamically from SOP
            for code_prefix, program_type in self.billing_code_patterns.items():
                if billing_code_str.startswith(code_prefix):
                    return program_type, 0.85

            # Check for specific PMPM codes
            if any(code in billing_code for code in ['2443', '2444', '2445', '8400', '8401', '8402']):
                return 'HHA', 0.9

            # Check for nursing codes
            if any(code in billing_code_str for code in ['9920', '9921', '9922', '9923', '9924', '9925']):
                return 'Nursing', 0.9

        # If we have either description or code, but no match, it's still uncertain
        if description or billing_code:
            return 'Unknown', 0.6

        # If we have neither, it's very uncertain
        return 'Unknown', 0.3

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
