#!/usr/bin/env python3
"""
Streamlit Frontend for BOQ Processor
A lightweight web interface for the BOQ processing backend application.

Usage:
1. First, start your backend server:
   python main.py

2. Then, in a separate terminal, start this frontend:
   streamlit run streamlit_frontend.py

This keeps your backend and frontend completely separate for better architecture.
"""

import streamlit as st
import requests
import json
import os
import subprocess
import platform
from pathlib import Path
import time
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "http://localhost:5000"
OUTPUT_FOLDER = Path("output")

# Language Configuration
LANGUAGES = {
    'th': {
        'name': '🇹🇭 ไทย',
        'title': '📊 ระบบประมาณราคา BOQ',
        'subtitle': 'ระบบคำนวณต้นทุนและมาร์คอัปอัตโนมัติ',
        'backend_connected': '🟢 เชื่อมต่อแบ็กเอนด์สำเร็จ',
        'backend_error': '🔴 **แบ็กเอนด์ไม่ทำงาน**',
        'backend_instruction': '''
        กรุณาเริ่มเซิร์ฟเวอร์แบ็กเอนด์ก่อน:
        
        ```bash
        python main.py
        ```
        
        แล้วรีเฟรชหน้านี้
        ''',
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
        'open_folder': '📁 เปิดโฟลเดอร์ผลลัพธ์',
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
        'memory_cleared': '🧹 ล้างหน่วยความจำสำเร็จ!',
        'clear_failed': 'ล้างหน่วยความจำล้มเหลว: {}',
        'footer': 'ระบบประมาณราคา BOQ v2.0 | Streamlit Frontend',
        'back_main': '🔙 กลับหน้าหลัก',
        'folder_opened': 'เปิดโฟลเดอร์: {}',
        'folder_error': 'เปิดโฟลเดอร์ล้มเหลว: {}',
        'folder_not_exist': 'ไม่พบโฟลเดอร์: {}',
        'loading_config': 'กำลังโหลดการตั้งค่าปัจจุบัน...',
        'config_load_failed': 'โหลดการตั้งค่าล้มเหลว: {}',
        'config_title': '⚙️ การตั้งค่าระบบประมวลผล',
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
        'backend_instruction': '''
        Please start the backend server first:
        
        ```bash
        python main.py
        ```
        
        Then refresh this page.
        ''',
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
        'open_folder': '📁 Open Output Folder',
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
        'memory_cleared': '🧹 Memory cleared successfully!',
        'clear_failed': 'Failed to clear memory: {}',
        'footer': 'BOQ Processor v2.0 | Streamlit Frontend',
        'back_main': '🔙 Back to Main',
        'folder_opened': 'Opened folder: {}',
        'folder_error': 'Failed to open folder: {}',
        'folder_not_exist': 'Folder does not exist: {}',
        'loading_config': 'Loading current configuration...',
        'config_load_failed': 'Failed to load configuration: {}',
        'config_title': '⚙️ Processor Configuration Settings',
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

# Check if backend is running
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
    
    def update_config(self, processor_name: str, header_row: Optional[int] = None, 
                     column_mapping: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Update processor configuration"""
        data = {'processor_name': processor_name}
        
        if header_row is not None:
            data['header_row'] = header_row
        if column_mapping is not None:
            data['column_mapping'] = column_mapping
        
        try:
            response = requests.post(f"{self.base_url}/api/config/update", json=data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}


def open_folder(folder_path: Path):
    """Open folder in system file explorer"""
    try:
        folder_path = folder_path.resolve()
        if not folder_path.exists():
            st.error(get_text('folder_not_exist').format(folder_path))
            return
        
        system = platform.system()
        if system == "Windows":
            os.startfile(folder_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])
            
        st.success(get_text('folder_opened').format(folder_path))
    except Exception as e:
        st.error(get_text('folder_error').format(e))


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


def show_settings_page():
    """Display the settings configuration page"""
    st.header(get_text('config_title'))
    
    # Initialize API client
    api = BOQProcessorAPI()
    
    # Get current configuration
    with st.spinner(get_text('loading_config')):
        config_response = api.get_config()
    
    if not config_response.get('success', False):
        st.error(get_text('config_load_failed').format(config_response.get('error', 'Unknown error')))
        return
    
    configs = config_response.get('configs', {})
    
    # Create tabs for different processor types
    processor_types = ['interior', 'electrical', 'ac', 'fp']
    tab_labels = {
        'th': ['ตกแต่งภายใน (INT)', 'ไฟฟ้า (EE)', 'แอร์ (AC)', 'ดับเพลิง (FP)'],
        'en': ['Interior (INT)', 'Electrical (EE)', 'AC System', 'Fire Protection (FP)']
    }
    
    current_lang = st.session_state.get('language', 'th')
    tabs = st.tabs(tab_labels[current_lang])
    
    for i, processor_type in enumerate(processor_types):
        with tabs[i]:
            processor_config = configs.get(processor_type, {})
            
            if not processor_config:
                st.warning(f"No configuration found for {processor_type} processor")
                continue
            
            st.subheader(f"{processor_type.upper()} Processor Settings")
            
            # Display current settings
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Current Settings:**" if current_lang == 'en' else "**การตั้งค่าปัจจุบัน:**")
                st.write(f"- Sheet Pattern: `{processor_config.get('sheet_pattern', 'N/A')}`")
                st.write(f"- Header Row: `{processor_config.get('header_row', 'N/A')}`")
                st.write(f"- Table Name: `{processor_config.get('table_name', 'N/A')}`")
            
            with col2:
                st.write("**Column Mapping:**" if current_lang == 'en' else "**การแมปคอลัมน์:**")
                column_mapping = processor_config.get('column_mapping', {})
                for key, value in column_mapping.items():
                    thai_labels = {
                        'code': 'รหัส',
                        'name': 'ชื่อ',
                        'unit': 'หน่วย',
                        'quantity': 'จำนวน',
                        'material_unit_cost': 'ต้นทุนวัสดุต่อหน่วย',
                        'labor_unit_cost': 'ต้นทุนแรงงานต่อหน่วย',
                        'total_unit_cost': 'ต้นทุนรวมต่อหน่วย',
                        'total_cost': 'ต้นทุนรวม',
                        'total_row_col': 'คอลัมน์แถวรวม',
                        'material_cost': 'ต้นทุนวัสดุ',
                        'labor_cost': 'ต้นทุนแรงงาน'
                    }
                    label = thai_labels.get(key, key) if current_lang == 'th' else key
                    st.write(f"- {label}: Column {value}")
            
            # Update form
            with st.form(f"update_{processor_type}_config"):
                st.write("**Update Configuration:**" if current_lang == 'en' else "**อัปเดตการตั้งค่า:**")
                
                # Header row input
                header_label = "Header Row (0-based)" if current_lang == 'en' else "แถวหัวตาราง (เริ่มต้นที่ 0)"
                new_header_row = st.number_input(
                    header_label,
                    min_value=0,
                    max_value=100,
                    value=processor_config.get('header_row', 0),
                    key=f"{processor_type}_header_row"
                )
                
                # Column mapping inputs
                mapping_title = "**Column Mapping:**" if current_lang == 'en' else "**การแมปคอลัมน์:**"
                st.write(mapping_title)
                col_map_cols = st.columns(2)
                
                new_column_mapping = {}
                
                # Get current column mapping for default values
                current_mapping = processor_config.get('column_mapping', {})
                
                # Common columns for all processors
                with col_map_cols[0]:
                    code_label = "Code Column" if current_lang == 'en' else "คอลัมน์รหัส"
                    name_label = "Name Column" if current_lang == 'en' else "คอลัมน์ชื่อ"
                    unit_label = "Unit Column" if current_lang == 'en' else "คอลัมน์หน่วย"
                    qty_label = "Quantity Column" if current_lang == 'en' else "คอลัมน์จำนวน"
                    
                    new_column_mapping['code'] = st.number_input(
                        code_label, min_value=1, max_value=100,
                        value=current_mapping.get('code', 2),
                        key=f"{processor_type}_code_col"
                    )
                    new_column_mapping['name'] = st.number_input(
                        name_label, min_value=1, max_value=100,
                        value=current_mapping.get('name', 3),
                        key=f"{processor_type}_name_col"
                    )
                    new_column_mapping['unit'] = st.number_input(
                        unit_label, min_value=1, max_value=100,
                        value=current_mapping.get('unit', 5),
                        key=f"{processor_type}_unit_col"
                    )
                    new_column_mapping['quantity'] = st.number_input(
                        qty_label, min_value=1, max_value=100,
                        value=current_mapping.get('quantity', 4),
                        key=f"{processor_type}_quantity_col"
                    )
                
                with col_map_cols[1]:
                    # Processor-specific columns
                    if processor_type == 'interior':
                        mat_unit_label = "Material Unit Cost" if current_lang == 'en' else "ต้นทุนวัสดุต่อหน่วย"
                        lab_unit_label = "Labor Unit Cost" if current_lang == 'en' else "ต้นทุนแรงงานต่อหน่วย"
                        total_unit_label = "Total Unit Cost" if current_lang == 'en' else "ต้นทุนรวมต่อหน่วย"
                        total_cost_label = "Total Cost" if current_lang == 'en' else "ต้นทุนรวม"
                        
                        new_column_mapping['material_unit_cost'] = st.number_input(
                            mat_unit_label, min_value=1, max_value=100,
                            value=current_mapping.get('material_unit_cost', 6),
                            key=f"{processor_type}_mat_unit_col"
                        )
                        new_column_mapping['labor_unit_cost'] = st.number_input(
                            lab_unit_label, min_value=1, max_value=100,
                            value=current_mapping.get('labor_unit_cost', 7),
                            key=f"{processor_type}_lab_unit_col"
                        )
                        new_column_mapping['total_unit_cost'] = st.number_input(
                            total_unit_label, min_value=1, max_value=100,
                            value=current_mapping.get('total_unit_cost', 8),
                            key=f"{processor_type}_total_unit_col"
                        )
                        new_column_mapping['total_cost'] = st.number_input(
                            total_cost_label, min_value=1, max_value=100,
                            value=current_mapping.get('total_cost', 9),
                            key=f"{processor_type}_total_col"
                        )
                    else:
                        # System processors (AC, EE, FP)
                        total_row_label = "Total Row Marker Column" if current_lang == 'en' else "คอลัมน์แถวรวม"
                        mat_unit_label = "Material Unit Cost" if current_lang == 'en' else "ต้นทุนวัสดุต่อหน่วย"
                        mat_cost_label = "Material Cost" if current_lang == 'en' else "ต้นทุนวัสดุ"
                        lab_unit_label = "Labor Unit Cost" if current_lang == 'en' else "ต้นทุนแรงงานต่อหน่วย"
                        lab_cost_label = "Labor Cost" if current_lang == 'en' else "ต้นทุนแรงงาน"
                        total_cost_label = "Total Cost" if current_lang == 'en' else "ต้นทุนรวม"
                        
                        new_column_mapping['total_row_col'] = st.number_input(
                            total_row_label, min_value=1, max_value=100,
                            value=current_mapping.get('total_row_col', 3),
                            key=f"{processor_type}_total_row_col"
                        )
                        new_column_mapping['material_unit_cost'] = st.number_input(
                            mat_unit_label, min_value=1, max_value=100,
                            value=current_mapping.get('material_unit_cost', 8),
                            key=f"{processor_type}_mat_unit_col"
                        )
                        new_column_mapping['material_cost'] = st.number_input(
                            mat_cost_label, min_value=1, max_value=100,
                            value=current_mapping.get('material_cost', 9),
                            key=f"{processor_type}_mat_col"
                        )
                        new_column_mapping['labor_unit_cost'] = st.number_input(
                            lab_unit_label, min_value=1, max_value=100,
                            value=current_mapping.get('labor_unit_cost', 10),
                            key=f"{processor_type}_lab_unit_col"
                        )
                        new_column_mapping['labor_cost'] = st.number_input(
                            lab_cost_label, min_value=1, max_value=100,
                            value=current_mapping.get('labor_cost', 11),
                            key=f"{processor_type}_lab_col"
                        )
                        new_column_mapping['total_cost'] = st.number_input(
                            total_cost_label, min_value=1, max_value=100,
                            value=current_mapping.get('total_cost', 12),
                            key=f"{processor_type}_total_col"
                        )
                
                # Submit button
                update_btn_text = f"Update {processor_type.upper()} Configuration" if current_lang == 'en' else f"อัปเดตการตั้งค่า {processor_type.upper()}"
                if st.form_submit_button(update_btn_text):
                    with st.spinner("Updating configuration..." if current_lang == 'en' else "กำลังอัปเดตการตั้งค่า..."):
                        update_response = api.update_config(
                            processor_name=processor_type,
                            header_row=new_header_row,
                            column_mapping=new_column_mapping
                        )
                    
                    if update_response.get('success', False):
                        success_msg = f"✅ {processor_type.upper()} configuration updated successfully!" if current_lang == 'en' else f"✅ อัปเดตการตั้งค่า {processor_type.upper()} สำเร็จ!"
                        st.success(success_msg)
                        st.rerun()  # Refresh the page to show updated values
                    else:
                        error_msg = f"❌ Failed to update configuration: {update_response.get('error', 'Unknown error')}" if current_lang == 'en' else f"❌ อัปเดตการตั้งค่าล้มเหลว: {update_response.get('error', 'ข้อผิดพลาดที่ไม่ทราบสาเหตุ')}"
                        st.error(error_msg, f"- Table Name: `{processor_config.get('table_name', 'N/A')}`")
            
            with col2:
                st.write("**Column Mapping:**")
                column_mapping = processor_config.get('column_mapping', {})
                for key, value in column_mapping.items():
                    st.write(f"- {key}: Column {value}")
            
            # Update form
            with st.form(f"update_{processor_type}_config"):
                st.write("**Update Configuration:**")
                
                # Header row input
                new_header_row = st.number_input(
                    "Header Row (0-based)",
                    min_value=0,
                    max_value=100,
                    value=processor_config.get('header_row', 0),
                    key=f"{processor_type}_header_row"
                )
                
                # Column mapping inputs
                st.write("**Column Mapping:**")
                col_map_cols = st.columns(2)
                
                new_column_mapping = {}
                
                # Get current column mapping for default values
                current_mapping = processor_config.get('column_mapping', {})
                
                # Common columns for all processors
                with col_map_cols[0]:
                    new_column_mapping['code'] = st.number_input(
                        "Code Column", min_value=1, max_value=100,
                        value=current_mapping.get('code', 2),
                        key=f"{processor_type}_code_col"
                    )
                    new_column_mapping['name'] = st.number_input(
                        "Name Column", min_value=1, max_value=100,
                        value=current_mapping.get('name', 3),
                        key=f"{processor_type}_name_col"
                    )
                    new_column_mapping['unit'] = st.number_input(
                        "Unit Column", min_value=1, max_value=100,
                        value=current_mapping.get('unit', 5),
                        key=f"{processor_type}_unit_col"
                    )
                    new_column_mapping['quantity'] = st.number_input(
                        "Quantity Column", min_value=1, max_value=100,
                        value=current_mapping.get('quantity', 4),
                        key=f"{processor_type}_quantity_col"
                    )
                
                with col_map_cols[1]:
                    # Processor-specific columns
                    if processor_type == 'interior':
                        new_column_mapping['material_unit_cost'] = st.number_input(
                            "Material Unit Cost", min_value=1, max_value=100,
                            value=current_mapping.get('material_unit_cost', 6),
                            key=f"{processor_type}_mat_unit_col"
                        )
                        new_column_mapping['labor_unit_cost'] = st.number_input(
                            "Labor Unit Cost", min_value=1, max_value=100,
                            value=current_mapping.get('labor_unit_cost', 7),
                            key=f"{processor_type}_lab_unit_col"
                        )
                        new_column_mapping['total_unit_cost'] = st.number_input(
                            "Total Unit Cost", min_value=1, max_value=100,
                            value=current_mapping.get('total_unit_cost', 8),
                            key=f"{processor_type}_total_unit_col"
                        )
                        new_column_mapping['total_cost'] = st.number_input(
                            "Total Cost", min_value=1, max_value=100,
                            value=current_mapping.get('total_cost', 9),
                            key=f"{processor_type}_total_col"
                        )
                    else:
                        # System processors (AC, EE, FP)
                        new_column_mapping['total_row_col'] = st.number_input(
                            "Total Row Marker Column", min_value=1, max_value=100,
                            value=current_mapping.get('total_row_col', 3),
                            key=f"{processor_type}_total_row_col"
                        )
                        new_column_mapping['material_unit_cost'] = st.number_input(
                            "Material Unit Cost", min_value=1, max_value=100,
                            value=current_mapping.get('material_unit_cost', 8),
                            key=f"{processor_type}_mat_unit_col"
                        )
                        new_column_mapping['material_cost'] = st.number_input(
                            "Material Cost", min_value=1, max_value=100,
                            value=current_mapping.get('material_cost', 9),
                            key=f"{processor_type}_mat_col"
                        )
                        new_column_mapping['labor_unit_cost'] = st.number_input(
                            "Labor Unit Cost", min_value=1, max_value=100,
                            value=current_mapping.get('labor_unit_cost', 10),
                            key=f"{processor_type}_lab_unit_col"
                        )
                        new_column_mapping['labor_cost'] = st.number_input(
                            "Labor Cost", min_value=1, max_value=100,
                            value=current_mapping.get('labor_cost', 11),
                            key=f"{processor_type}_lab_col"
                        )
                        new_column_mapping['total_cost'] = st.number_input(
                            "Total Cost", min_value=1, max_value=100,
                            value=current_mapping.get('total_cost', 12),
                            key=f"{processor_type}_total_col"
                        )
                
                # Submit button
                if st.form_submit_button(f"Update {processor_type.upper()} Configuration"):
                    with st.spinner("Updating configuration..."):
                        update_response = api.update_config(
                            processor_name=processor_type,
                            header_row=new_header_row,
                            column_mapping=new_column_mapping
                        )
                    
                    if update_response.get('success', False):
                        st.success(f"✅ {processor_type.upper()} configuration updated successfully!")
                        st.rerun()  # Refresh the page to show updated values
                    else:
                        st.error(f"❌ Failed to update configuration: {update_response.get('error', 'Unknown error')}")


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
    
    # Show settings page if requested
    if st.session_state.get('show_settings', False):
        show_settings_page()
        
        if st.button(get_text('back_main')):
            st.session_state.show_settings = False
            st.rerun()
        return
    
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
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(get_text('step2_desc'))
        
        with col2:
            if st.button(get_text('generate_final'), type="primary"):
                with st.spinner(get_text('generating')):
                    response = api.generate_final_boq(st.session_state.session_id)
                
                if response.get('success', False):
                    st.success(get_text('generate_success').format(response['filename']))
                    
                    # Auto-open output folder
                    open_folder(OUTPUT_FOLDER)
                    
                    # Show generation summary
                    st.info(get_text('items_processed').format(response['items_processed'], response['items_failed']))
                else:
                    st.error(get_text('generate_failed').format(response.get('error', 'Unknown error')))
        
        with col3:
            if st.button(get_text('open_folder')):
                open_folder(OUTPUT_FOLDER)
        
        # Step 3: Apply Markup
        st.markdown("---")
        st.header(get_text('step3_title'))
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
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
                    
                    # Auto-open output folder
                    open_folder(OUTPUT_FOLDER)
                    
                    # Show application summary
                    st.info(get_text('markup_applied').format(response['items_processed'], response['items_failed']))
                else:
                    st.error(get_text('markup_failed').format(response.get('error', 'Unknown error')))
        
        with col3:
            if st.button(get_text('open_folder') + " ", key="markup_open"):
                open_folder(OUTPUT_FOLDER)
        
        # Cleanup section
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(get_text('session_mgmt'))
        
        with col2:
            show_cleanup_confirmation(st.session_state.session_id)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666;'>{get_text('footer')}</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()