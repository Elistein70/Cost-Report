"""SOP Loader - Dynamically load SOPs from data/sops directory"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class SOPLoader:
    """Load and parse SOPs from data/sops directory"""

    def __init__(self, sops_dir: str = "data/sops"):
        self.sops_dir = Path(sops_dir)
        self.allocation_guides_dir = self.sops_dir / "allocation_guides"
        self.output_formats_dir = self.sops_dir / "output_formats"

    def load_visit_sop(self) -> Dict[str, Any]:
        """Load Visit Data SOP and return parsed rules"""
        sop_path = self.sops_dir / "visit_data_sop.md"

        if not sop_path.exists():
            # Return default patterns if SOP doesn't exist
            return self._get_default_visit_patterns()

        try:
            with open(sop_path, 'r') as f:
                content = f.read()

            # Parse the SOP content
            rules = {
                'pmpm_codes': self._extract_pmpm_codes(content),
                'live_in_keywords': self._extract_live_in_keywords(content),
                'program_patterns': self._extract_program_patterns(content),
                'billing_code_patterns': self._extract_billing_code_patterns(content),
                'confidence_threshold': self._extract_confidence_threshold(content),
            }

            return rules

        except Exception as e:
            print(f"Error loading visit SOP: {e}")
            return self._get_default_visit_patterns()

    def load_payroll_sop(self) -> Dict[str, Any]:
        """Load Payroll SOP and return parsed rules"""
        sop_path = self.sops_dir / "payroll_sop.md"

        if not sop_path.exists():
            return self._get_default_payroll_patterns()

        try:
            with open(sop_path, 'r') as f:
                content = f.read()

            rules = {
                'employee_type_patterns': self._extract_employee_patterns(content),
                'confidence_threshold': self._extract_confidence_threshold(content),
            }

            return rules

        except Exception as e:
            print(f"Error loading payroll SOP: {e}")
            return self._get_default_payroll_patterns()

    def load_trial_balance_sop(self) -> Dict[str, Any]:
        """Load Trial Balance SOP and return parsed rules"""
        sop_path = self.sops_dir / "trial_balance_sop.md"

        if not sop_path.exists():
            return self._get_default_tb_patterns()

        try:
            with open(sop_path, 'r') as f:
                content = f.read()

            rules = {
                'expense_patterns': self._extract_expense_patterns(content),
                'confidence_threshold': self._extract_confidence_threshold(content),
            }

            return rules

        except Exception as e:
            print(f"Error loading trial balance SOP: {e}")
            return self._get_default_tb_patterns()

    def load_allocation_guide(self, guide_name: str) -> Optional[pd.DataFrame]:
        """Load an allocation guide Excel file"""
        guide_path = self.allocation_guides_dir / f"{guide_name}.xlsx"

        if not guide_path.exists():
            return None

        try:
            df = pd.read_excel(guide_path, engine='openpyxl')
            return df
        except Exception as e:
            print(f"Error loading allocation guide {guide_name}: {e}")
            return None

    def _extract_pmpm_codes(self, content: str) -> List[str]:
        """Extract PMPM codes from SOP content"""
        # Look for the PMPM codes section
        match = re.search(r'\*\*Rule 1: PMPM Codes\*\*.*?Delete.*?codes:.*?(?=\*\*|$)', content, re.DOTALL)
        if not match:
            return ['2443', '2444', '2445', '8400', '8401', '8402', 'T1022:UA', 'T1022:UB', 'T1022:UC']

        section = match.group(0)
        # Extract all codes (numbers and T codes)
        codes = re.findall(r'\b\d{4}\b|T\d+:[A-Z]+', section)
        return codes if codes else ['2443', '2444', '2445', '8400', '8401', '8402', 'T1022:UA', 'T1022:UB', 'T1022:UC']

    def _extract_live_in_keywords(self, content: str) -> List[str]:
        """Extract live-in keywords from SOP content"""
        # Look for live-in section
        match = re.search(r'\*\*Rule 2: Live-In Hours\*\*.*?containing\s+"([^"]+)"', content, re.DOTALL)
        if not match:
            return ['live-in', 'live in', 'livein']

        keywords_str = match.group(1)
        keywords = [kw.strip().strip('"').lower() for kw in keywords_str.split(',')]
        return keywords if keywords else ['live-in', 'live in', 'livein']

    def _extract_program_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract program type patterns from SOP content"""
        patterns = {}

        # Look for the Tag Service Types section
        section_match = re.search(r'### 3\. Tag Service Types.*?(?=###|$)', content, re.DOTALL)
        if not section_match:
            return self._get_default_visit_patterns()['program_patterns']

        section = section_match.group(0)

        # Extract each program type and its keywords
        program_lines = re.findall(r'\*\*([A-Z]+)\*\*:\s*([^\n]+)', section)

        for program, keywords_str in program_lines:
            # Split by comma and clean up
            keywords = [kw.strip().lower() for kw in keywords_str.split(',')]
            patterns[program] = keywords

        # If we didn't find any patterns, use defaults
        if not patterns:
            return self._get_default_visit_patterns()['program_patterns']

        return patterns

    def _extract_billing_code_patterns(self, content: str) -> Dict[str, str]:
        """Extract billing code patterns from SOP content"""
        patterns = {}

        # Look for Billing Code Patterns section
        match = re.search(r'\*\*Billing Code Patterns\*\*:.*?(?=###|\*\*[A-Z]|$)', content, re.DOTALL)
        if not match:
            return {
                'G': 'HHA',
                'S': 'CDPAP',
                'T': 'Therapy',
                '992': 'Nursing'
            }

        section = match.group(0)

        # Extract patterns like "G codes → HHA"
        pattern_lines = re.findall(r'-\s*([A-Z0-9]+)\s+codes?\s*→\s*([A-Z]+)', section)

        for code_prefix, program in pattern_lines:
            patterns[code_prefix] = program

        return patterns if patterns else {
            'G': 'HHA',
            'S': 'CDPAP',
            'T': 'Therapy',
            '992': 'Nursing'
        }

    def _extract_employee_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract employee type patterns from payroll SOP"""
        # Similar pattern extraction for payroll
        # This is a placeholder - implement based on actual payroll SOP format
        return {
            'Direct Care': ['aide', 'hha', 'personal care', 'caregiver', 'pa', 'personal assistant'],
            'Nursing': ['rn', 'lpn', 'nurse', 'registered nurse', 'licensed practical'],
            'Therapy': ['pt', 'ot', 'st', 'therapist', 'physical therapist'],
            'Admin': ['admin', 'office', 'manager', 'coordinator', 'supervisor'],
        }

    def _extract_expense_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract expense category patterns from trial balance SOP"""
        # Similar pattern extraction for trial balance
        # This is a placeholder - implement based on actual TB SOP format
        return {
            'Salaries': ['salary', 'wage', 'payroll', 'compensation'],
            'Benefits': ['benefit', 'insurance', 'retirement', '401k', 'health insurance'],
            'Rent': ['rent', 'lease', 'occupancy'],
            'Utilities': ['electric', 'gas', 'water', 'utility', 'phone', 'internet'],
        }

    def _extract_confidence_threshold(self, content: str) -> float:
        """Extract confidence threshold from SOP content"""
        # Look for patterns like "< 0.92" or "92%"
        match = re.search(r'<\s*0\.(\d+)|<\s*(\d+)%|threshold[:\s]+0\.(\d+)|threshold[:\s]+(\d+)%', content, re.IGNORECASE)
        if match:
            groups = match.groups()
            for g in groups:
                if g:
                    threshold = float(f"0.{g}") if len(g) == 2 else float(g) / 100
                    return threshold

        return 0.92  # Default

    def _get_default_visit_patterns(self) -> Dict[str, Any]:
        """Get default visit patterns if SOP file doesn't exist"""
        return {
            'pmpm_codes': ['2443', '2444', '2445', '8400', '8401', '8402', 'T1022:UA', 'T1022:UB', 'T1022:UC'],
            'live_in_keywords': ['live-in', 'live in', 'livein'],
            'program_patterns': {
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
            },
            'billing_code_patterns': {
                'G': 'HHA',
                'S': 'CDPAP',
                'T': 'Therapy',
                '992': 'Nursing'
            },
            'confidence_threshold': 0.92
        }

    def _get_default_payroll_patterns(self) -> Dict[str, Any]:
        """Get default payroll patterns if SOP file doesn't exist"""
        return {
            'employee_type_patterns': {
                'Direct Care': ['aide', 'hha', 'personal care', 'caregiver', 'pa', 'personal assistant'],
                'Nursing': ['rn', 'lpn', 'nurse', 'registered nurse', 'licensed practical'],
                'Therapy': ['pt', 'ot', 'st', 'therapist', 'physical therapist'],
                'Admin': ['admin', 'office', 'manager', 'coordinator', 'supervisor'],
            },
            'confidence_threshold': 0.92
        }

    def _get_default_tb_patterns(self) -> Dict[str, Any]:
        """Get default trial balance patterns if SOP file doesn't exist"""
        return {
            'expense_patterns': {
                'Salaries': ['salary', 'wage', 'payroll', 'compensation'],
                'Benefits': ['benefit', 'insurance', 'retirement', '401k', 'health insurance'],
                'Rent': ['rent', 'lease', 'occupancy'],
                'Utilities': ['electric', 'gas', 'water', 'utility', 'phone', 'internet'],
            },
            'confidence_threshold': 0.92
        }
