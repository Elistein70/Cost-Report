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
import os
from io import BytesIO

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from processors.payroll_processor import PayrollProcessor
from processors.trial_balance_processor import TrialBalanceProcessor
from processors.visit_processor import VisitProcessor

# Import OpenAI for AI reasoning
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="ClearDOH - DOH Cost Report Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# AI reasoning function
def ai_reason_tag(item_description: str, item_type: str, possible_tags: list) -> tuple:
    """Use AI to reason about uncertain tags"""
    if not OPENAI_AVAILABLE:
        return "AI reasoning unavailable", "Install openai package", 0.5

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "No API key", "Set OPENAI_API_KEY in Streamlit secrets", 0.5

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""You are a DOH cost report expert. Analyze this {item_type} and determine the most appropriate tag.

Item: {item_description}

Possible tags: {', '.join(possible_tags)}

Consider:
1. Industry standards for home care accounting
2. DOH reporting requirements
3. Common patterns in cost reports

Provide your reasoning and recommended tag in this format:
REASONING: [your step-by-step reasoning]
TAG: [recommended tag from the list]
CONFIDENCE: [0.0-1.0]"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a DOH cost report expert specialized in home care accounting and reporting requirements."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )

        response_text = response.choices[0].message.content

        # Parse response
        reasoning = ""
        tag = ""
        confidence = 0.8

        for line in response_text.split('\n'):
            if line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()
            elif line.startswith('TAG:'):
                tag = line.replace('TAG:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                except:
                    confidence = 0.8

        return tag, reasoning, confidence

    except Exception as e:
        return "AI Error", str(e), 0.5

# DEFINE PROCESS FUNCTION FIRST (before it's called in UI)
def process_files():
    """Process all uploaded files following SOP"""

    with st.spinner("🔄 Processing files... This may take a few minutes..."):
        try:
            # Create temporary directory for processing
            temp_dir = Path(tempfile.mkdtemp())

            # Combine multiple files for each category
            st.info("📥 Combining uploaded files...")

            # Combine Visit Data files
            visit_dfs = []
            for visit_file in st.session_state.visit_files:
                visit_path = temp_dir / f"visit_{visit_file.name}"
                with open(visit_path, 'wb') as f:
                    f.write(visit_file.read())

                # Read and combine
                try:
                    if visit_file.name.endswith('.csv'):
                        df = pd.read_csv(visit_path)
                    else:
                        df = pd.read_excel(visit_path, engine='openpyxl')
                    visit_dfs.append(df)
                except Exception as e:
                    st.error(f"Error reading visit file {visit_file.name}: {str(e)}")
                    raise

            combined_visit_path = temp_dir / "combined_visits.xlsx"
            combined_visits = pd.concat(visit_dfs, ignore_index=True) if visit_dfs else pd.DataFrame()
            combined_visits.to_excel(combined_visit_path, index=False)

            # Combine Trial Balance files
            tb_dfs = []
            for tb_file in st.session_state.tb_files:
                tb_path = temp_dir / f"tb_{tb_file.name}"
                with open(tb_path, 'wb') as f:
                    f.write(tb_file.read())

                try:
                    if tb_file.name.endswith('.csv'):
                        df = pd.read_csv(tb_path)
                    else:
                        df = pd.read_excel(tb_path, engine='openpyxl')
                    tb_dfs.append(df)
                except Exception as e:
                    st.error(f"Error reading TB file {tb_file.name}: {str(e)}")
                    raise

            combined_tb_path = temp_dir / "combined_tb.xlsx"
            combined_tb = pd.concat(tb_dfs, ignore_index=True) if tb_dfs else pd.DataFrame()
            combined_tb.to_excel(combined_tb_path, index=False)

            # Combine Payroll files
            payroll_dfs = []
            for payroll_file in st.session_state.payroll_files:
                payroll_path = temp_dir / f"payroll_{payroll_file.name}"
                with open(payroll_path, 'wb') as f:
                    f.write(payroll_file.read())

                # Process based on file type
                processor = PayrollProcessor(str(payroll_path), None)
                if payroll_file.name.endswith('.pdf'):
                    df = processor._extract_from_pdf()
                else:
                    df = processor._extract_from_csv()

                if df is not None and not df.empty:
                    payroll_dfs.append(df)

            combined_payroll_path = temp_dir / "combined_payroll.xlsx"
            combined_payroll = pd.concat(payroll_dfs, ignore_index=True) if payroll_dfs else pd.DataFrame()
            combined_payroll.to_excel(combined_payroll_path, index=False)

            # Process each combined file
            st.info("📊 Processing payroll data...")
            payroll_processor = PayrollProcessor(str(combined_payroll_path), None)
            payroll_processor.process()

            st.info("💼 Processing trial balance...")
            tb_processor = TrialBalanceProcessor(str(combined_tb_path), None)
            tb_processor.process()

            st.info("📋 Processing visit data...")
            visit_processor = VisitProcessor(str(combined_visit_path), None)
            visit_processor.process()

            # Use AI reasoning for uncertain tags
            st.info("🤖 Using AI to reason about uncertain items...")
            ai_tagged_items = []

            # Process payroll uncertain items
            for item in payroll_processor.flagged_items:
                if item['confidence'] < 0.92:
                    possible_tags = list(payroll_processor.paycode_tags.values())
                    ai_tag, reasoning, ai_confidence = ai_reason_tag(
                        item['original_value'],
                        "payroll code",
                        possible_tags
                    )
                    ai_tagged_items.append({
                        'type': 'Payroll',
                        'original_value': item['original_value'],
                        'fuzzy_tag': item['suggested_tag'],
                        'fuzzy_confidence': item['confidence'],
                        'ai_tag': ai_tag,
                        'ai_reasoning': reasoning,
                        'ai_confidence': ai_confidence,
                        'row_number': item['row_number'],
                        'approved': None
                    })

            # Store processors and AI items in session state
            st.session_state.payroll_processor = payroll_processor
            st.session_state.tb_processor = tb_processor
            st.session_state.visit_processor = visit_processor
            st.session_state.ai_tagged_items = ai_tagged_items
            st.session_state.processing_complete = True

            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            st.success("✅ Processing complete!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            st.exception(e)

def generate_output_files():
    """Generate copy-paste ready Excel files"""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Generate Payroll output
    payroll_data = st.session_state.payroll_processor.tagged_data
    if payroll_data is not None and not payroll_data.empty:
        # Apply approved AI tags
        for item in st.session_state.ai_tagged_items:
            if item['type'] == 'Payroll' and item['approved']:
                row_idx = item['row_number'] - 6  # Adjust for row offset
                if row_idx < len(payroll_data):
                    payroll_data.at[row_idx, 'Tag'] = item['ai_tag']

        payroll_output = payroll_data[['Tag', 'Code', 'Hours', 'Amount', 'Tax_Category', 'Tax_Code', 'Tax_Amount']]
        payroll_path = output_dir / f"Payroll_Tagged_{datetime.now().strftime('%Y%m%d')}.xlsx"
        payroll_output.to_excel(payroll_path, index=False)
        st.session_state.payroll_output_path = str(payroll_path)

    # Generate TB output
    tb_data = st.session_state.tb_processor.tagged_data
    if tb_data is not None and not tb_data.empty:
        tb_path = output_dir / f"TB_Tagged_{datetime.now().strftime('%Y%m%d')}.xlsx"
        tb_data.to_excel(tb_path, index=False)
        st.session_state.tb_output_path = str(tb_path)

    # Generate Visit output
    visit_data = st.session_state.visit_processor.tagged_data
    if visit_data is not None and not visit_data.empty:
        visit_path = output_dir / f"Visit_Tagged_{datetime.now().strftime('%Y%m%d')}.xlsx"
        visit_data.to_excel(visit_path, index=False)
        st.session_state.visit_output_path = str(visit_path)

    st.session_state.outputs_generated = True

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
if 'visit_files' not in st.session_state:
    st.session_state.visit_files = []
if 'tb_files' not in st.session_state:
    st.session_state.tb_files = []
if 'payroll_files' not in st.session_state:
    st.session_state.payroll_files = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'ai_tagged_items' not in st.session_state:
    st.session_state.ai_tagged_items = []
if 'outputs_generated' not in st.session_state:
    st.session_state.outputs_generated = False
if 'payroll_output_path' not in st.session_state:
    st.session_state.payroll_output_path = None
if 'tb_output_path' not in st.session_state:
    st.session_state.tb_output_path = None
if 'visit_output_path' not in st.session_state:
    st.session_state.visit_output_path = None

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
    st.info("💡 You can upload multiple files for each category - they will be automatically combined")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 1️⃣ Visit Data (Schedule 5)")
        visit_files = st.file_uploader(
            "Upload visit data files",
            type=['xlsx', 'xls', 'csv'],
            key="visit_uploader",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if visit_files:
            st.session_state.visit_files = visit_files
            for f in visit_files:
                st.success(f"✅ {f.name}")

    with col2:
        st.markdown("#### 2️⃣ Trial Balance")
        tb_files = st.file_uploader(
            "Upload trial balance files",
            type=['xlsx', 'xls', 'csv'],
            key="tb_uploader",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if tb_files:
            st.session_state.tb_files = tb_files
            for f in tb_files:
                st.success(f"✅ {f.name}")

    with col3:
        st.markdown("#### 3️⃣ Payroll Reports")
        payroll_files = st.file_uploader(
            "Upload payroll files",
            type=['xlsx', 'xls', 'csv', 'pdf'],
            key="payroll_uploader",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if payroll_files:
            st.session_state.payroll_files = payroll_files
            for f in payroll_files:
                st.success(f"✅ {f.name}")

    # Process Button
    st.markdown("---")

    files_ready = (len(st.session_state.visit_files) > 0 and
                   len(st.session_state.tb_files) > 0 and
                   len(st.session_state.payroll_files) > 0)

    if files_ready:
        if st.button("🚀 Process Files with AI", type="primary", use_container_width=True):
            process_files()
    else:
        st.info("👆 Please upload at least one file for each category to continue")
        st.button("🚀 Process Files with AI", type="primary", use_container_width=True, disabled=True)

# Step 3: AI Review Workflow
if st.session_state.processing_complete and not st.session_state.outputs_generated:
    st.markdown("### 🤖 AI Tagging Review")

    if len(st.session_state.ai_tagged_items) == 0:
        st.success("✅ All items were tagged with high confidence! No review needed.")
        if st.button("Generate Final Output Files", type="primary", use_container_width=True):
            generate_output_files()
            st.rerun()
    else:
        st.markdown("""
        <div class="warning-box">
            <p><strong>⚠️ The following items had uncertain tags and AI was used to reason about them.</strong></p>
            <p>Please review and approve/reject each AI suggestion below.</p>
        </div>
        """, unsafe_allow_html=True)

        # Display each AI-tagged item for review
        for idx, item in enumerate(st.session_state.ai_tagged_items):
            with st.expander(f"📋 Item {idx+1}: {item['original_value']}", expanded=(idx < 3)):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Original Value:** `{item['original_value']}`")
                    st.markdown(f"**Type:** {item['type']}")
                    st.markdown(f"**Row:** {item['row_number']}")

                    st.markdown("---")

                    # Fuzzy match suggestion
                    st.markdown("**🔍 Fuzzy Match Suggestion:**")
                    st.markdown(f"Tag: `{item['fuzzy_tag']}`")
                    st.markdown(f"Confidence: {item['fuzzy_confidence']:.1%}")

                    st.markdown("---")

                    # AI suggestion
                    st.markdown("**🤖 AI Reasoning:**")
                    st.info(item['ai_reasoning'])
                    st.markdown(f"**AI Recommended Tag:** `{item['ai_tag']}`")
                    st.markdown(f"**AI Confidence:** {item['ai_confidence']:.1%}")

                with col2:
                    st.markdown("**Decision:**")

                    # Approval buttons
                    if st.button(f"✅ Approve AI Tag", key=f"approve_{idx}"):
                        st.session_state.ai_tagged_items[idx]['approved'] = True
                        st.success("Approved!")
                        st.rerun()

                    if st.button(f"❌ Use Fuzzy Tag", key=f"reject_{idx}"):
                        # Use fuzzy tag instead
                        st.session_state.ai_tagged_items[idx]['ai_tag'] = item['fuzzy_tag']
                        st.session_state.ai_tagged_items[idx]['approved'] = True
                        st.success("Using fuzzy match!")
                        st.rerun()

                    # Show current status
                    if item['approved'] is True:
                        st.success("✅ Approved")
                    elif item['approved'] is False:
                        st.error("❌ Rejected")

        st.markdown("---")

        # Check if all items are reviewed
        all_reviewed = all(item['approved'] is not None for item in st.session_state.ai_tagged_items)

        if all_reviewed:
            st.success("✅ All items reviewed!")
            if st.button("📊 Generate Final Output Files", type="primary", use_container_width=True):
                generate_output_files()
                st.rerun()
        else:
            remaining = sum(1 for item in st.session_state.ai_tagged_items if item['approved'] is None)
            st.info(f"👆 Please review {remaining} remaining items before generating output")

# Step 4: Download Outputs
if st.session_state.outputs_generated:
    st.markdown("### 📥 Download Tagged Data Files")

    st.markdown("""
    <div class="success-box">
        <p><strong>✅ All files have been processed and tagged!</strong></p>
        <p>Download the files below and copy-paste the data into your template.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    # Payroll output
    with col1:
        if st.session_state.payroll_output_path and Path(st.session_state.payroll_output_path).exists():
            with open(st.session_state.payroll_output_path, 'rb') as f:
                payroll_data = f.read()

            st.download_button(
                label="📊 Download Payroll Data",
                data=payroll_data,
                file_name=f"Payroll_Tagged_{st.session_state.agency_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.info("Copy columns E-M to 'Payroll Reports Input' sheet starting at row 6")

    # TB output
    with col2:
        if st.session_state.tb_output_path and Path(st.session_state.tb_output_path).exists():
            with open(st.session_state.tb_output_path, 'rb') as f:
                tb_data = f.read()

            st.download_button(
                label="💼 Download TB Data",
                data=tb_data,
                file_name=f"TB_Tagged_{st.session_state.agency_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.info("Copy to 'TB Tagging' sheet")

    # Visit output
    with col3:
        if st.session_state.visit_output_path and Path(st.session_state.visit_output_path).exists():
            with open(st.session_state.visit_output_path, 'rb') as f:
                visit_data = f.read()

            st.download_button(
                label="📋 Download Visit Data",
                data=visit_data,
                file_name=f"Visit_Tagged_{st.session_state.agency_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.info("Copy to 'Detail Data 5 Tagging' sheet")

    st.markdown("---")

    # Summary statistics
    st.markdown("### 📈 Processing Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        if hasattr(st.session_state, 'payroll_processor'):
            payroll_count = len(st.session_state.payroll_processor.tagged_data) if st.session_state.payroll_processor.tagged_data is not None else 0
            st.metric("Payroll Records", payroll_count)

    with col2:
        if hasattr(st.session_state, 'tb_processor'):
            tb_count = len(st.session_state.tb_processor.tagged_data) if st.session_state.tb_processor.tagged_data is not None else 0
            st.metric("TB Entries", tb_count)

    with col3:
        if hasattr(st.session_state, 'visit_processor'):
            visit_count = len(st.session_state.visit_processor.tagged_data) if st.session_state.visit_processor.tagged_data is not None else 0
            st.metric("Visit Records", visit_count)

    # Start over button
    st.markdown("---")
    if st.button("🔄 Process New Report"):
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
