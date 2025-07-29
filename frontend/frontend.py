#!/usr/bin/env python3
"""
Streamlit Frontend for BOQ Processor with Download Links
Works perfectly in Docker containers - no folder opening issues!
"""

import streamlit as st
import requests
import json
import os
import platform
from pathlib import Path
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration - Docker network aware
def get_backend_url():
    """Get backend URL based on environment"""
    if os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
        return "http://boq-backend:5000"  # Docker container name
    else:
        return "http://localhost:5000"   # Local development

BACKEND_URL = get_backend_url()
# Use new storage structure
if os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
    OUTPUT_FOLDER = Path("/app/storage/output")  # Docker path
else:
    OUTPUT_FOLDER = Path("../storage/output")    # Local development path

# Language Configuration (keeping your existing languages dict)
LANGUAGES = {
    'th': {
        'name': '🇹🇭 ไทย',
        'title': '📊 ระบบประมาณราคา BOQ',
        'subtitle': 'ระบบคำนวณต้นทุนและมาร์คอัปอัตโนมัติ',
        'backend_connected': '🟢 เชื่อมต่อแบ็กเอนด์สำเร็จ',
        'backend_error': '🔴 **แบ็กเอนด์ไม่ทำงาน**',
        'backend_instruction': '''กรุณาเริ่มเซิร์ฟเวอร์แบ็กเอนด์ก่อน: `python main.py`''',
        'settings': '⚙️ ตั้งค่า',
        'settings_tooltip': 'ตั้งค่าระบบประมวลผล',
        'step1_title': '📁 ขั้นตอนที่ 1: อัปโหลดไฟล์ BOQ',
        'file_upload': 'เลือกไฟล์ Excel (.xlsx)',
        'file_upload_help': 'อัปโหลดไฟล์ BOQ Excel เพื่อประมวลผล',
        'file_uploaded': '✅ อัปโหลดไฟล์: **{}**',
        'process_boq': '🔄 ประมวลผล BOQ',
        'processing': 'กำลังประมวลผลไฟล์ BOQ...',
        'process_success': '🎉 ประมวลผล BOQ สำเร็จ!',
        'process_failed': '❌ ประมวลผลล้มเหลว: {}',
        'summary_title': '📈 สรุปการประมวลผล',
        'step2_title': '📋 ขั้นตอนที่ 2: สร้าง BOQ สุดท้าย',
        'step2_desc': 'สร้าง BOQ สุดท้ายพร้อมต้นทุนที่คำนวณแล้วและคอลัมน์มาร์คอัป',
        'generate_final': '📊 สร้าง BOQ สุดท้าย',
        'generating': 'กำลังสร้าง BOQ สุดท้าย...',
        'generate_success': '✅ สร้าง BOQ สุดท้ายแล้ว: **{}**',
        'generate_failed': '❌ สร้างล้มเหลว: {}',
        'items_processed': '📊 ประมวลผล {} รายการ, ล้มเหลว {} รายการ',
        'step3_title': '💰 ขั้นตอนที่ 3: ใส่มาร์คอัป (ตัวเลือก)',
        'markup_desc': 'เลือกเปอร์เซ็นต์มาร์คอัปที่จะใส่ในต้นทุนทั้งหมด:',
        'markup_multiplier': 'ตัวคูณมาร์คอัป: **{:.2f}x**',
        'apply_markup': '💵 ใส่มาร์คอัป {}%',
        'applying_markup': 'กำลังใส่มาร์คอัป {}%...',
        'markup_success': '✅ ใส่มาร์คอัป {}% แล้ว: **{}**',
        'markup_failed': '❌ การใส่มาร์คอัปล้มเหลว: {}',
        'markup_applied': '📈 ใส่มาร์คอัปใน {} รายการ, ล้มเหลว {} รายการ',
        'session_mgmt': '**การจัดการเซสชัน:** ล้างหน่วยความจำเพื่อลบไฟล์ชั่วคราวและข้อมูลการประมวลผล',
        'clear_memory': '🗑️ ล้างหน่วยความจำ',
        'clear_memory_help': 'ล้างข้อมูลเซสชันและไฟล์ชั่วคราว',
        'confirm_cleanup': '⚠️ **ยืนยันการล้างหน่วยความจำ**',
        'cleanup_warning': '''การดำเนินการนี้จะ:
        - ลบเซสชันการประมวลผลปัจจุบัน
        - ลบไฟล์ชั่วคราวที่อัปโหลด
        - ล้างข้อมูลการประมวลผลทั้งหมดจากหน่วยความจำ''',
        'yes_clear': '✅ ใช่, ล้าง',
        'no_cancel': '❌ ไม่, ยกเลิก',
        'pure_markup_title': '💵 มาร์คอัป: ใส่มาร์คอัปในไฟล์ BOQ โดยตรง ',
        'pure_markup_desc': 'อัปโหลดไฟล์ BOQ ใดๆ (รวมถึงไฟล์ที่แก้ไขแล้ว) และใส่มาร์คอัปโดยตรง',
        'pure_markup_help': 'มาร์คอัปในไฟล์ที่มีข้อมูลต้นทุนอยู่แล้วได้เลย',
        'pure_markup_upload': 'อัปโหลดไฟล์ BOQ สำหรับใส่มาร์คอัป',
        'apply_pure_markup': '💵 ใส่มาร์คอัป {}%',
        'pure_markup_success': '✅ ใส่มาร์คอัป {}% แล้ว: **{}**',
        'pure_markup_failed': '❌ การใส่มาร์คอัปล้มเหลว: {}',
        'memory_cleared': '🧹 ล้างหน่วยความจำสำเร็จ!',
        'clear_failed': 'ล้างหน่วยความจำล้มเหลว: {}',
        'footer': 'ระบบประมาณราคา BOQ v2.0 | Streamlit Frontend',
        'back_main': '🔙 กลับหน้าหลัก',
        'recent_files': '📥 ไฟล์ล่าสุด:',
        'download': '⬇️ ดาวน์โหลด',
        'no_files_found': 'ไม่พบไฟล์ในโฟลเดอร์ผลลัพธ์',
        'files_saved_to': '📁 ไฟล์ถูกบันทึกที่: {}',
        'total_items': 'รายการทั้งหมด',
        'matched_items': 'รายการที่จับคู่ได้',
        'match_rate': 'อัตราการจับคู่',
        'sheets_processed': 'ชีตที่ประมวลผล'
    },
    'en': {
        'name': '🇺🇸 English',
        'title': '📊 BOQ Processor',
        'subtitle': 'Automated Bill of Quantities cost calculation and markup application',
        'backend_connected': '🟢 Backend Connected',
        'backend_error': '🔴 **Backend Server Not Running**',
        'backend_instruction': '''Please start the backend server first: `python main.py`''',
        'settings': '⚙️ Settings',
        'settings_tooltip': 'Configure processor settings',
        'step1_title': '📁 Step 1: Upload BOQ File',
        'file_upload': 'Choose an Excel file (.xlsx)',
        'file_upload_help': 'Upload your BOQ Excel file for processing',
        'file_uploaded': '✅ File uploaded: **{}**',
        'process_boq': '🔄 Process BOQ',
        'processing': 'Processing BOQ file...',
        'process_success': '🎉 BOQ processed successfully!',
        'process_failed': '❌ Processing failed: {}',
        'summary_title': '📈 Processing Summary',
        'step2_title': '📋 Step 2: Generate Final BOQ',
        'step2_desc': 'Generate the final BOQ with calculated costs and markup columns.',
        'generate_final': '📊 Generate Final BOQ',
        'generating': 'Generating final BOQ...',
        'generate_success': '✅ Final BOQ generated: **{}**',
        'generate_failed': '❌ Generation failed: {}',
        'items_processed': '📊 Processed {} items, {} failed',
        'step3_title': '💰 Step 3: Apply Markup (Optional)',
        'markup_desc': 'Select markup percentage to apply to all costs:',
        'markup_multiplier': 'Markup multiplier: **{:.2f}x**',
        'apply_markup': '💵 Apply {}% Markup',
        'applying_markup': 'Applying {}% markup...',
        'markup_success': '✅ {}% markup applied: **{}**',
        'markup_failed': '❌ Markup application failed: {}',
        'markup_applied': '📈 Applied markup to {} items, {} failed',
        'session_mgmt': '**Session Management:** Clear memory to remove temporary files and processing data.',
        'clear_memory': '🗑️ Clear Memory',
        'clear_memory_help': 'Clear session data and temporary files',
        'confirm_cleanup': '⚠️ **Confirm Memory Cleanup**',
        'cleanup_warning': '''This will:
        - Delete the current processing session
        - Remove uploaded temporary files
        - Clear all processing data from memory''',
        'yes_clear': '✅ Yes, Clear',
        'no_cancel': '❌ No, Cancel',
        'pure_markup_title': '💵 Pure Markup: Apply Markup to Any BOQ File',
        'pure_markup_desc': 'Upload any BOQ file (including manually edited ones) and apply markup directly',
        'pure_markup_help': 'This feature requires no session - just markup files that already have cost data',
        'pure_markup_upload': 'Upload BOQ file for markup application',
        'apply_pure_markup': '💵 Apply {}% Markup',
        'pure_markup_success': '✅ {}% markup applied: **{}**',
        'pure_markup_failed': '❌ Pure markup application failed: {}',
        'memory_cleared': '🧹 Memory cleared successfully!',
        'clear_failed': 'Failed to clear memory: {}',
        'footer': 'BOQ Processor v2.0 | Streamlit Frontend',
        'back_main': '🔙 Back to Main',
        'recent_files': '📥 Recent Files:',
        'download': '⬇️ Download',
        'no_files_found': 'No files found in output folder',
        'files_saved_to': '📁 Files saved to: {}',
        'total_items': 'Total Items',
        'matched_items': 'Matched Items',
        'match_rate': 'Match Rate',
        'sheets_processed': 'Sheets Processed'
    }
}

def get_text(key: str) -> str:
    """Get text in current language"""
    lang = st.session_state.get('language', 'th')
    return LANGUAGES[lang].get(key, key)

def check_backend_connection():
    """Check if backend server is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/config/inquiry", timeout=2)
        return response.status_code == 200
    except:
        return False

class BOQProcessorAPI:
    """API client for BOQ Processor backend"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
    
    def process_boq(self, file_path: str) -> Dict[str, Any]:
        """Upload and process BOQ file"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.base_url}/api/process-boq", files=files)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_final_boq(self, session_id: str, markup_options: list = None) -> Dict[str, Any]:
        """Generate final BOQ with calculated costs"""
        if markup_options is None:
            markup_options = [30, 50, 100, 130, 150]
        
        data = {
            'session_id': session_id,
            'markup_options': markup_options
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/generate-final-boq", json=data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def apply_markup(self, session_id: str, markup_percent: float) -> Dict[str, Any]:
        """Apply markup percentage to all values"""
        data = {
            'session_id': session_id,
            'markup_percent': markup_percent
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/apply-markup", json=data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def pure_markup(self, file_path: str, markup_percent: float) -> Dict[str, Any]:
        """Apply markup to any BOQ file without session dependency"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'markup_percent': str(markup_percent)}
                response = requests.post(f"{self.base_url}/api/pure-markup", files=files, data=data)
                return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """Cleanup session data and files"""
        data = {'session_id': session_id}
        
        try:
            response = requests.post(f"{self.base_url}/api/cleanup-session", json=data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        """Get current processor configurations"""
        try:
            response = requests.get(f"{self.base_url}/api/config/inquiry")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_file(self, filename: str):
        """Download file from backend and return content"""
        try:
            response = requests.get(f"{self.base_url}/api/download/{filename}", timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            # Don't show error to user, just return None
            return None

def show_download_links(folder_path: Path, latest_filename: str = None):
    """Show download link for the latest generated file only"""
    try:
        st.write("---")
        st.subheader(get_text('recent_files'))
        
        # Show only the latest file if provided
        if latest_filename:
            show_single_download_link(latest_filename, folder_path / latest_filename if folder_path.exists() else None, is_latest=True)
        else:
            st.info("No file to download")
        
        # Show folder location for reference
        st.write("")
        st.info(get_text('files_saved_to').format(folder_path))
        
    except Exception as e:
        st.error(f"Error accessing files: {e}")
        # Fallback: show at least the latest file if we have it
        if latest_filename:
            show_single_download_link(latest_filename, folder_path / latest_filename if folder_path.exists() else None, is_latest=True)

def show_single_download_link(filename: str, file_path: Path = None, is_latest: bool = False):
    """Show a single download link - Save button only, no section collapse"""
    try:
        # Create columns for file info and download button
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Show file info
            if file_path and file_path.exists():
                file_size = file_path.stat().st_size / 1024 / 1024  # MB
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                st.write(f"📄 {filename}")
                st.caption(f"Size: {file_size:.1f} MB | Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.write(f"📄 {filename}")
                if is_latest:
                    st.caption("✨ Just generated")
                else:
                    st.caption("API only")
        
        with col2:
            # Only Save button - always try to provide download
            if file_path and file_path.exists():
                # File exists locally - use Streamlit download
                try:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="💾 Save",
                            data=f.read(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_{filename}_{int(time.time())}",  # Unique key to prevent conflicts
                            help="Download file"
                        )
                except Exception as e:
                    st.caption("Download error")
            else:
                # File doesn't exist locally - try API download and provide as Streamlit download
                try:
                    api = BOQProcessorAPI()
                    file_content = api.download_file(filename)
                    if file_content:
                        st.download_button(
                            label="💾 Save",
                            data=file_content,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"api_download_{filename}_{int(time.time())}",  # Unique key
                            help="Download via API"
                        )
                    else:
                        st.caption("Unavailable")
                except Exception as e:
                    st.caption("Download failed")
                
    except Exception as e:
        st.error(f"Error showing download link: {e}")

def show_processing_summary(summary: Dict[str, Any]):
    """Display processing summary in a nice format"""
    if not summary:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(get_text('total_items'), summary.get('total_items', 0))
    with col2:
        st.metric(get_text('matched_items'), summary.get('matched_items', 0))
    with col3:
        st.metric(get_text('match_rate'), f"{summary.get('match_rate', 0):.1f}%")
    with col4:
        st.metric(get_text('sheets_processed'), summary.get('sheets_processed', 0))
        

def show_cleanup_confirmation(session_id: str):
    """Show cleanup confirmation dialog"""
    if st.button(get_text('clear_memory'), type="secondary", help=get_text('clear_memory_help')):
        # Create a confirmation dialog using session state
        if 'show_cleanup_confirm' not in st.session_state:
            st.session_state.show_cleanup_confirm = True
        else:
            st.session_state.show_cleanup_confirm = not st.session_state.show_cleanup_confirm
    
    # Show confirmation dialog
    if st.session_state.get('show_cleanup_confirm', False):
        st.warning(get_text('confirm_cleanup'))
        st.write(get_text('cleanup_warning'))
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button(get_text('yes_clear'), type="primary"):
                api = BOQProcessorAPI()
                cleanup_response = api.cleanup_session(session_id)
                
                if cleanup_response.get('success', False):
                    st.success(get_text('memory_cleared'))
                    # Clear session state
                    for key in ['session_id', 'processing_summary', 'show_cleanup_confirm']:
                        if key in st.session_state:
                            del st.session_state[key]
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(get_text('clear_failed').format(cleanup_response.get('error', 'Unknown error')))
        
        with col2:
            if st.button(get_text('no_cancel')):
                st.session_state.show_cleanup_confirm = False
                st.rerun()

def main():
    """Main Streamlit application"""
    
    # Initialize language if not set (default to Thai)
    if 'language' not in st.session_state:
        st.session_state.language = 'th'
    
    # Page configuration
    st.set_page_config(
        page_title=get_text('title'),
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Check backend connection first
    if not check_backend_connection():
        st.error(get_text('backend_error'))
        st.markdown(get_text('backend_instruction'))
        st.stop()
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 50px;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with language selection
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title(get_text('title'))
        st.markdown(f"*{get_text('subtitle')}*")
        st.success(get_text('backend_connected'))
    
    with col2:
        # Language selector
        current_lang = st.session_state.get('language', 'th')
        lang_options = [LANGUAGES['th']['name'], LANGUAGES['en']['name']]
        selected_lang_name = st.selectbox(
            "🌐",
            lang_options,
            index=0 if current_lang == 'th' else 1,
            label_visibility="collapsed"
        )
        
        # Update language if changed
        new_lang = 'th' if selected_lang_name == LANGUAGES['th']['name'] else 'en'
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()
    
    with col3:
        if st.button(get_text('settings'), help=get_text('settings_tooltip')):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)
            st.rerun()
    
    # Show settings panel if toggled
    if st.session_state.get('show_settings', False):
        st.markdown("---")
        st.header("⚙️ " + get_text('settings'))
        
        with st.expander("🔧 Processor Configuration", expanded=True):
            try:
                response = requests.get(f"{BACKEND_URL}/api/config/inquiry")
                if response.status_code == 200:
                    config_data = response.json()
                    
                    if config_data.get('success'):
                        configs = config_data.get('configs', {})
                        if configs:
                            processor_names = ['interior', 'ac', 'electrical', 'fp']
                            available_processors = [name for name in processor_names if name in configs]
                            
                            # Show editable processor configurations
                            for proc_name in available_processors:
                                proc_config = configs[proc_name]
                                column_mapping = proc_config.get('column_mapping', {})
                                
                                with st.expander(f"🔧 {proc_name.title()} Processor", expanded=False):
                                    # Create form for this processor
                                    with st.form(f"config_form_{proc_name}"):
                                        # Basic settings
                                        st.write("**Basic Settings**")
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            new_header_row = st.number_input(
                                                "Header Row:",
                                                min_value=0,
                                                max_value=100,
                                                value=proc_config.get('header_row', 0),
                                                key=f"header_{proc_name}"
                                            )
                                        
                                        with col2:
                                            new_sheet_pattern = st.text_input(
                                                "Sheet Pattern:",
                                                value=proc_config.get('sheet_pattern', ''),
                                                key=f"pattern_{proc_name}",
                                                help="Pattern to match sheet names"
                                            )
                                        
                                        # Column mapping settings
                                        st.write("**Column Mapping** (Column numbers, 1-based)")
                                        
                                        # Common columns for all processors
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            new_code_col = st.number_input(
                                                "Code Column:",
                                                min_value=1,
                                                max_value=50,
                                                value=column_mapping.get('code', 2),
                                                key=f"code_{proc_name}"
                                            )
                                        with col2:
                                            new_name_col = st.number_input(
                                                "Name Column:",
                                                min_value=1,
                                                max_value=50,
                                                value=column_mapping.get('name', 3),
                                                key=f"name_{proc_name}"
                                            )
                                        with col3:
                                            new_unit_col = st.number_input(
                                                "Unit Column:",
                                                min_value=1,
                                                max_value=50,
                                                value=column_mapping.get('unit', 5),
                                                key=f"unit_{proc_name}"
                                            )
                                        with col4:
                                            new_quantity_col = st.number_input(
                                                "Quantity Column:",
                                                min_value=1,
                                                max_value=50,
                                                value=column_mapping.get('quantity', 4),
                                                key=f"quantity_{proc_name}"
                                            )
                                        
                                        # Processor-specific columns
                                        if proc_name == 'interior':
                                            st.write("**Interior-Specific Columns**")
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                new_mat_unit_cost = st.number_input(
                                                    "Material Unit Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('material_unit_cost', 6),
                                                    key=f"mat_unit_{proc_name}"
                                                )
                                            with col2:
                                                new_labor_unit_cost = st.number_input(
                                                    "Labor Unit Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('labor_unit_cost', 7),
                                                    key=f"labor_unit_{proc_name}"
                                                )
                                            with col3:
                                                new_total_unit_cost = st.number_input(
                                                    "Total Unit Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('total_unit_cost', 8),
                                                    key=f"total_unit_{proc_name}"
                                                )
                                            with col4:
                                                new_total_cost = st.number_input(
                                                    "Total Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('total_cost', 9),
                                                    key=f"total_{proc_name}"
                                                )
                                        else:
                                            # System processors (AC, EE, FP)
                                            st.write("**System-Specific Columns**")
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                new_total_row_col = st.number_input(
                                                    "Total Row Marker:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('total_row_col', 3),
                                                    key=f"total_row_{proc_name}"
                                                )
                                            with col2:
                                                new_mat_unit_cost = st.number_input(
                                                    "Material Unit Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('material_unit_cost', 8),
                                                    key=f"mat_unit_{proc_name}"
                                                )
                                            with col3:
                                                new_mat_cost = st.number_input(
                                                    "Material Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('material_cost', 9),
                                                    key=f"mat_cost_{proc_name}"
                                                )
                                            
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                new_labor_unit_cost = st.number_input(
                                                    "Labor Unit Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('labor_unit_cost', 10),
                                                    key=f"labor_unit_{proc_name}"
                                                )
                                            with col2:
                                                new_labor_cost = st.number_input(
                                                    "Labor Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('labor_cost', 11),
                                                    key=f"labor_cost_{proc_name}"
                                                )
                                            with col3:
                                                new_total_cost = st.number_input(
                                                    "Total Cost:",
                                                    min_value=1,
                                                    max_value=50,
                                                    value=column_mapping.get('total_cost', 12),
                                                    key=f"total_{proc_name}"
                                                )
                                        
                                        # Submit button
                                        submitted = st.form_submit_button(f"💾 Update {proc_name.title()} Configuration", type="primary")
                                        
                                        if submitted:
                                            # Build column mapping based on processor type
                                            if proc_name == 'interior':
                                                new_column_mapping = {
                                                    'code': new_code_col,
                                                    'name': new_name_col,
                                                    'unit': new_unit_col,
                                                    'quantity': new_quantity_col,
                                                    'material_unit_cost': new_mat_unit_cost,
                                                    'labor_unit_cost': new_labor_unit_cost,
                                                    'total_unit_cost': new_total_unit_cost,
                                                    'total_cost': new_total_cost
                                                }
                                            else:
                                                new_column_mapping = {
                                                    'code': new_code_col,
                                                    'name': new_name_col,
                                                    'unit': new_unit_col,
                                                    'quantity': new_quantity_col,
                                                    'total_row_col': new_total_row_col,
                                                    'material_unit_cost': new_mat_unit_cost,
                                                    'material_cost': new_mat_cost,
                                                    'labor_unit_cost': new_labor_unit_cost,
                                                    'labor_cost': new_labor_cost,
                                                    'total_cost': new_total_cost
                                                }
                                            
                                            # Update configuration via API
                                            update_data = {
                                                'processor_name': proc_name,
                                                'header_row': new_header_row,
                                                'column_mapping': new_column_mapping
                                            }
                                            
                                            try:
                                                update_response = requests.post(
                                                    f"{BACKEND_URL}/api/config/update",
                                                    json=update_data
                                                )
                                                
                                                if update_response.status_code == 200:
                                                    result = update_response.json()
                                                    if result.get('success'):
                                                        st.success(f"✅ {proc_name.title()} processor configuration updated successfully!")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"❌ Update failed: {result.get('error', 'Unknown error')}")
                                                else:
                                                    st.error(f"❌ HTTP error: {update_response.status_code}")
                                            
                                            except Exception as e:
                                                st.error(f"❌ Update error: {str(e)}")
                                
                                st.markdown("---")
                        else:
                            st.warning("No processor configurations found")
                    else:
                        st.error("Failed to load configuration data")
                else:
                    st.error(f"Backend connection failed (HTTP {response.status_code})")
                    
            except Exception as e:
                st.error(f"Cannot connect to backend: {str(e)}")
            
            # Close settings button
            if st.button("✖️ Close Settings"):
                st.session_state.show_settings = False
                st.rerun()
        
        st.markdown("---")
    
    # Initialize API client
    api = BOQProcessorAPI()
    
    # Main application layout
    st.markdown("---")
    
    # Step 1: File Upload
    st.header(get_text('step1_title'))
    
    uploaded_file = st.file_uploader(
        get_text('file_upload'),
        type=['xlsx'],
        help=get_text('file_upload_help')
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = Path("temp_uploads")
        temp_path.mkdir(exist_ok=True)
        
        file_path = temp_path / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(get_text('file_uploaded').format(uploaded_file.name))
        
        with col2:
            if st.button(get_text('process_boq'), type="primary"):
                with st.spinner(get_text('processing')):
                    response = api.process_boq(str(file_path))
                
                if response.get('success', False):
                    st.session_state.session_id = response['session_id']
                    st.session_state.processing_summary = response['summary']
                    st.success(get_text('process_success'))
                else:
                    st.error(get_text('process_failed').format(response.get('error', 'Unknown error')))
    
    # Show processing summary if available
    if 'processing_summary' in st.session_state:
        st.markdown("---")
        st.header(get_text('summary_title'))
        show_processing_summary(st.session_state.processing_summary)
        
        # Step 2: Generate Final BOQ
        st.markdown("---")
        st.header(get_text('step2_title'))
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(get_text('step2_desc'))
        
        with col2:
            if st.button(get_text('generate_final'), type="primary"):
                with st.spinner(get_text('generating')):
                    response = api.generate_final_boq(st.session_state.session_id)
                
                if response.get('success', False):
                    st.success(get_text('generate_success').format(response['filename']))
                    
                    # Show download links instead of opening folder
                    show_download_links(OUTPUT_FOLDER, response['filename'])
                    
                    # Show generation summary
                    st.info(get_text('items_processed').format(response['items_processed'], response['items_failed']))
                else:
                    st.error(get_text('generate_failed').format(response.get('error', 'Unknown error')))
        
        # Step 3: Apply Markup
        st.markdown("---")
        st.header(get_text('step3_title'))
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            markup_percent = st.slider(
                get_text('markup_desc'),
                min_value=0,
                max_value=200,
                value=30,
                step=5,
                help="This will multiply all cost values by (1 + markup%/100)" if st.session_state.language == 'en' else "การดำเนินการนี้จะคูณค่าต้นทุนทั้งหมดด้วย (1 + markup%/100)"
            )
            st.write(get_text('markup_multiplier').format(1 + markup_percent/100))
        
        with col2:
            if st.button(get_text('apply_markup').format(markup_percent), type="primary"):
                with st.spinner(get_text('applying_markup').format(markup_percent)):
                    response = api.apply_markup(st.session_state.session_id, markup_percent)
                
                if response.get('success', False):
                    st.success(get_text('markup_success').format(markup_percent, response['filename']))
                    
                    # Show download links for markup file
                    show_download_links(OUTPUT_FOLDER, response['filename'])
                    
                    # Show application summary
                    st.info(get_text('markup_applied').format(response['items_processed'], response['items_failed']))
                else:
                    st.error(get_text('markup_failed').format(response.get('error', 'Unknown error')))
        
        # Cleanup section
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(get_text('session_mgmt'))
        
        with col2:
            show_cleanup_confirmation(st.session_state.session_id)
    
    # Pure Markup Section - Independent of main workflow
    st.markdown("---")
    st.header(get_text('pure_markup_title'))
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(get_text('pure_markup_desc'))
        st.info(get_text('pure_markup_help'))
    
    with col2:
        st.write("")  # Spacing
    
    # Pure markup file upload
    pure_markup_file = st.file_uploader(
        get_text('pure_markup_upload'),
        type=['xlsx'],
        key="pure_markup_uploader"
    )
    
    if pure_markup_file is not None:
        # Save the file temporarily
        temp_path = Path("temp_uploads")
        temp_path.mkdir(exist_ok=True)
        
        pure_file_path = temp_path / pure_markup_file.name
        with open(pure_file_path, "wb") as f:
            f.write(pure_markup_file.getbuffer())
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(get_text('file_uploaded').format(pure_markup_file.name))
            
            # Markup percentage slider
            pure_markup_percent = st.slider(
                get_text('markup_desc'),
                min_value=0,
                max_value=200,
                value=30,
                step=5,
                key="pure_markup_slider",
                help="This will multiply all cost values by (1 + markup%/100)" if st.session_state.language == 'en' else "การดำเนินการนี้จะคูณค่าต้นทุนทั้งหมดด้วย (1 + markup%/100)"
            )
            st.write(get_text('markup_multiplier').format(1 + pure_markup_percent/100))
        
        with col2:
            st.write("")  # Spacing
            if st.button(get_text('apply_pure_markup').format(pure_markup_percent), type="primary", key="pure_markup_apply"):
                with st.spinner(get_text('applying_markup').format(pure_markup_percent)):
                    response = api.pure_markup(str(pure_file_path), pure_markup_percent)
                
                if response.get('success', False):
                    st.success(get_text('pure_markup_success').format(pure_markup_percent, response['filename']))
                    
                    # Show download links for pure markup file
                    show_download_links(OUTPUT_FOLDER, response['filename'])
                    
                    # Show application summary
                    st.info(get_text('markup_applied').format(response['items_processed'], response['items_failed']))
                else:
                    st.error(get_text('pure_markup_failed').format(response.get('error', 'Unknown error')))

    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666;'>{get_text('footer')}</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()