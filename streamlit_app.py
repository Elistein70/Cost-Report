"""
ClearDOH - NY DOH Home Care Cost Report Automation
Streamlit Version for HCCGcostreport.streamlit.app
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from processors.payroll_processor import PayrollProcessor
from processors.trial_balance_processor import TrialBalanceProcessor
from processors.visit_processor import VisitProcessor

# Page configuration
st.set_page_config(
    page_title="ClearDOH - DOH Cost Report Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# DEFINE PROCESS FUNCTION FIRST (before it's called in UI)
def process_files():
    """Process all uploaded files following SOP"""

    with st.spinner("🔄 Processing files... This may take a few minutes..."):
        try:
            all_questions = []

            # Create temporary directory for processing
            temp_dir = Path(tempfile.mkdtemp())

            # Save uploaded files
            visit_path = temp_dir / f"visit_{st.session_state.visit_file.name}"
            tb_path = temp_dir / f"tb_{st.session_state.tb_file.name}"
            payroll_path = temp_dir / f"payroll_{st.session_state.payroll_file.name}"

            with open(visit_path, 'wb') as f:
                f.write(st.session_state.visit_file.read())
            with open(tb_path, 'wb') as f:
                f.write(st.session_state.tb_file.read())
            with open(payroll_path, 'wb') as f:
                f.write(st.session_state.payroll_file.read())

            # Process Payroll
            st.info("📊 Processing payroll data...")
            payroll_processor = PayrollProcessor(str(payroll_path), None)
            payroll_processor.process()
            all_questions.extend(payroll_processor.get_questions())

            # Process Trial Balance
            st.info("💼 Processing trial balance...")
            tb_processor = TrialBalanceProcessor(str(tb_path), None)
            tb_processor.process()
            all_questions.extend(tb_processor.get_questions())

            # Process Visits
            st.info("📋 Processing visit data...")
            visit_processor = VisitProcessor(str(visit_path), None)
            visit_processor.process()
            all_questions.extend(visit_processor.get_questions())

            # Generate final report
            st.info("📝 Generating final report...")

            # Get template path
            template_path = Path(__file__).parent / "data" / "templates" / "Anchor and Nemo Core Schedules Template -2024 - Audit Adjustments.xlsm"

            if not template_path.exists():
                st.error("❌ Template file not found. Please ensure the template is in data/templates/")
                return

            # Output path
            output_dir = Path(__file__).parent / "output"
            output_dir.mkdir(exist_ok=True)

            output_filename = f"{st.session_state.agency_name}_DOH_Cost_Report_{st.session_state.year}_FINAL.xlsm"
            output_path = output_dir / output_filename

            # Copy template
            shutil.copy(template_path, output_path)

            # Write data to template
            payroll_processor.save_to_template(str(template_path), str(output_path))
            tb_processor.save_to_template(str(output_path), str(output_path))
            visit_processor.save_to_template(str(output_path), str(output_path))

            # Update session state
            st.session_state.questions = list(set(all_questions))  # Remove duplicates
            st.session_state.report_path = str(output_path)
            st.session_state.processing_complete = True

            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            st.success("✅ Processing complete!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            st.exception(e)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: #667eea;
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .question-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agency_name' not in st.session_state:
    st.session_state.agency_name = ""
if 'year' not in st.session_state:
    st.session_state.year = datetime.now().year
if 'visit_file' not in st.session_state:
    st.session_state.visit_file = None
if 'tb_file' not in st.session_state:
    st.session_state.tb_file = None
if 'payroll_file' not in st.session_state:
    st.session_state.payroll_file = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'report_path' not in st.session_state:
    st.session_state.report_path = None

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 ClearDOH</h1>
    <p style="font-size: 1.2rem; margin: 0;">NY DOH Home Care Cost Report Automation</p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">Generate audit-ready reports in minutes</p>
</div>
""", unsafe_allow_html=True)

# Step 1: Agency Information
if not st.session_state.agency_name:
    st.markdown("### 📋 Step 1: Agency Information")

    col1, col2 = st.columns([2, 1])
    with col1:
        agency_name = st.text_input(
            "Agency Name",
            placeholder="e.g., Anchor and Nemo",
            key="agency_input"
        )
    with col2:
        year = st.number_input(
            "Report Year",
            min_value=2020,
            max_value=2030,
            value=datetime.now().year,
            key="year_input"
        )

    if st.button("Continue →", type="primary"):
        if agency_name:
            st.session_state.agency_name = agency_name
            st.session_state.year = year
            st.rerun()
        else:
            st.error("Please enter an agency name")

    st.stop()

# Display agency info
st.markdown(f"""
<div style="background: #e7f3ff; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
    <h3 style="margin: 0; color: #004085;">Agency: {st.session_state.agency_name} | Year: {st.session_state.year}</h3>
</div>
""", unsafe_allow_html=True)

# Step 2: File Uploads
if not st.session_state.processing_complete:
    st.markdown("### 📤 Step 2: Upload Required Files")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 1️⃣ Visit Data (Schedule 5)")
        visit_file = st.file_uploader(
            "Upload visit data",
            type=['xlsx', 'xls', 'csv'],
            key="visit_uploader",
            label_visibility="collapsed"
        )
        if visit_file:
            st.session_state.visit_file = visit_file
            st.success(f"✅ {visit_file.name}")

    with col2:
        st.markdown("#### 2️⃣ Trial Balance")
        tb_file = st.file_uploader(
            "Upload trial balance",
            type=['xlsx', 'xls', 'csv'],
            key="tb_uploader",
            label_visibility="collapsed"
        )
        if tb_file:
            st.session_state.tb_file = tb_file
            st.success(f"✅ {tb_file.name}")

    with col3:
        st.markdown("#### 3️⃣ Payroll Reports")
        payroll_file = st.file_uploader(
            "Upload payroll",
            type=['xlsx', 'xls', 'csv', 'pdf'],
            key="payroll_uploader",
            label_visibility="collapsed"
        )
        if payroll_file:
            st.session_state.payroll_file = payroll_file
            st.success(f"✅ {payroll_file.name}")

    # Process Button
    st.markdown("---")

    files_ready = (st.session_state.visit_file and
                   st.session_state.tb_file and
                   st.session_state.payroll_file)

    if files_ready:
        if st.button("🚀 Process & Generate Report", type="primary", use_container_width=True):
            process_files()
    else:
        st.info("👆 Please upload all 3 required files to continue")
        st.button("🚀 Process & Generate Report", type="primary", use_container_width=True, disabled=True)

# Step 3: Results
if st.session_state.processing_complete:
    st.markdown("### ✅ Processing Complete!")

    # Show questions if any
    if st.session_state.questions:
        st.markdown("### ❓ Questions for Clarification")
        st.markdown("""
        <div class="warning-box">
            <p><strong>The following items need clarification:</strong></p>
        </div>
        """, unsafe_allow_html=True)

        for i, question in enumerate(st.session_state.questions, 1):
            st.markdown(f"""
            <div class="question-box">
                <strong>{i}.</strong> {question}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

    # Download section
    if st.session_state.report_path and Path(st.session_state.report_path).exists():
        st.markdown("### 📥 Download Your Report")

        with open(st.session_state.report_path, 'rb') as f:
            report_data = f.read()

        filename = f"{st.session_state.agency_name}_DOH_Cost_Report_{st.session_state.year}_FINAL.xlsm"

        st.download_button(
            label="📥 Download Excel Report",
            data=report_data,
            file_name=filename,
            mime="application/vnd.ms-excel.sheet.macroEnabled.12",
            type="primary",
            use_container_width=True
        )

        st.markdown("""
        <div class="success-box">
            <p><strong>✅ Report generated successfully!</strong></p>
            <p>Your complete DOH Cost Report is ready for download.</p>
        </div>
        """, unsafe_allow_html=True)

    # Start over button
    st.markdown("---")
    if st.button("🔄 Start New Report"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.9rem; padding: 2rem 0 1rem 0;">
    <p>Following SOP procedures • Questions compiled for unclear items • Memory updated for next time</p>
    <p style="margin-top: 0.5rem;">ClearDOH v1.0 | Home Care Consulting Group</p>
</div>
""", unsafe_allow_html=True)
