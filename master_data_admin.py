#!/usr/bin/env python3
"""
Master Data Admin Interface - Streamlit page for CRUD operations on master data
"""

import streamlit as st
import requests
import pandas as pd
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# Configuration
def get_backend_url():
    """Get backend URL based on environment"""
    if os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
        return "http://boq-backend:5000"
    else:
        return "http://localhost:5000"

BACKEND_URL = get_backend_url()

# Processor types configuration
PROCESSOR_TYPES = {
    'interior': {
        'name': 'Interior (งานตกแต่งภายใน)',
        'icon': '🏠',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'total_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    },
    'electrical': {
        'name': 'Electrical (งานไฟฟ้า)',
        'icon': '⚡',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    },
    'ac': {
        'name': 'Air Conditioning (งานแอร์)',
        'icon': '❄️',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    },
    'fp': {
        'name': 'Fire Protection (งานดับเพลิง)',
        'icon': '🔥',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    }
}

class MasterDataAPI:
    """API client for master data CRUD operations"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
    
    def list_items(self, processor_type: str) -> Dict[str, Any]:
        """List all items for a processor type"""
        try:
            response = requests.get(f"{self.base_url}/api/master-data/list/{processor_type}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_item(self, processor_type: str, item_id: str) -> Dict[str, Any]:
        """Get a specific item"""
        try:
            response = requests.get(f"{self.base_url}/api/master-data/get/{processor_type}/{item_id}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_item(self, processor_type: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        try:
            response = requests.post(f"{self.base_url}/api/master-data/create/{processor_type}", json=item_data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_item(self, processor_type: str, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item"""
        try:
            response = requests.put(f"{self.base_url}/api/master-data/update/{processor_type}/{item_id}", json=item_data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_item(self, processor_type: str, item_id: str) -> Dict[str, Any]:
        """Delete an item"""
        try:
            response = requests.delete(f"{self.base_url}/api/master-data/delete/{processor_type}/{item_id}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def bulk_import(self, processor_type: str, file_path: str) -> Dict[str, Any]:
        """Bulk import items from Excel file"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.base_url}/api/master-data/bulk-import/{processor_type}", files=files)
                return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_data(self, processor_type: str) -> Dict[str, Any]:
        """Export master data to Excel"""
        try:
            response = requests.get(f"{self.base_url}/api/master-data/export/{processor_type}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}

def check_backend_connection():
    """Check if backend server is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/config/inquiry", timeout=2)
        return response.status_code == 200
    except:
        return False

def display_item_list(api: MasterDataAPI, processor_type: str, config: Dict[str, Any]):
    """Display list of items with actions"""
    st.subheader(f"📋 รายการข้อมูลหลัก - {config['name']}")
    
    # Load data
    response = api.list_items(processor_type)
    
    if not response.get('success', False):
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {response.get('error', 'Unknown error')}")
        return
    
    items = response.get('items', [])
    
    if not items:
        st.info("ไม่มีข้อมูลในระบบ กรุณาเพิ่มข้อมูลใหม่")
        return
    
    # Display count
    st.write(f"**จำนวนรายการทั้งหมด:** {len(items)} รายการ")
    
    # Convert to DataFrame for display
    df = pd.DataFrame(items)
    
    # Show only relevant columns
    display_columns = config['columns']
    if 'internal_id' in df.columns:
        df_display = df[['internal_id'] + [col for col in display_columns if col in df.columns]].copy()
    else:
        df_display = df[[col for col in display_columns if col in df.columns]].copy()
    
    # Format cost columns
    cost_columns = ['material_unit_cost', 'labor_unit_cost', 'total_unit_cost']
    for col in cost_columns:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and x != '' else '0.00')
    
    # Display table with selection
    selected_rows = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ เพิ่มรายการใหม่", type="primary"):
            st.session_state[f'show_create_{processor_type}'] = True
            st.rerun()
    
    with col2:
        if st.button("✏️ แก้ไข") and selected_rows['selection']['rows']:
            selected_idx = selected_rows['selection']['rows'][0]
            selected_item = items[selected_idx]
            st.session_state[f'edit_item_{processor_type}'] = selected_item
            st.session_state[f'show_edit_{processor_type}'] = True
            st.rerun()
    
    with col3:
        if st.button("🗑️ ลบ", type="secondary") and selected_rows['selection']['rows']:
            selected_idx = selected_rows['selection']['rows'][0]
            selected_item = items[selected_idx]
            st.session_state[f'delete_item_{processor_type}'] = selected_item
            st.session_state[f'show_delete_confirm_{processor_type}'] = True
            st.rerun()
    
    with col4:
        if st.button("📤 ส่งออก Excel"):
            export_response = api.export_data(processor_type)
            if export_response.get('success', False):
                st.success(f"ส่งออกข้อมูลเรียบร้อยแล้ว: {export_response['filename']}")
                st.write(f"[ดาวน์โหลดไฟล์]({export_response['download_url']})")
            else:
                st.error(f"ส่งออกข้อมูลไม่สำเร็จ: {export_response.get('error', 'Unknown error')}")

def show_create_form(api: MasterDataAPI, processor_type: str, config: Dict[str, Any]):
    """Show create item form"""
    st.subheader(f"➕ เพิ่มรายการใหม่ - {config['name']}")
    
    with st.form(f"create_form_{processor_type}"):
        form_data = {}
        
        # Create input fields based on processor type
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['code'] = st.text_input("รหัสรายการ", key=f"create_code_{processor_type}")
            form_data['name'] = st.text_input("ชื่อรายการ *", key=f"create_name_{processor_type}")
            form_data['unit'] = st.text_input("หน่วย", key=f"create_unit_{processor_type}")
        
        with col2:
            form_data['material_unit_cost'] = st.number_input(
                "ต้นทุนวัสดุต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=0.0,
                step=0.01,
                key=f"create_mat_cost_{processor_type}"
            )
            form_data['labor_unit_cost'] = st.number_input(
                "ต้นทุนแรงงานต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=0.0,
                step=0.01,
                key=f"create_lab_cost_{processor_type}"
            )
        
        # Show total unit cost for interior type
        if processor_type == 'interior':
            total_cost = form_data['material_unit_cost'] + form_data['labor_unit_cost']
            st.info(f"ต้นทุนรวมต่อหน่วย: {total_cost:,.2f} บาท")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 บันทึก", type="primary")
        
        with col2:
            if st.form_submit_button("❌ ยกเลิก"):
                st.session_state[f'show_create_{processor_type}'] = False
                st.rerun()
        
        if submitted:
            # Validate required fields
            if not form_data['name'].strip():
                st.error("กรุณากรอกชื่อรายการ")
            else:
                # Create item
                response = api.create_item(processor_type, form_data)
                
                if response.get('success', False):
                    st.success("เพิ่มรายการเรียบร้อยแล้ว")
                    st.session_state[f'show_create_{processor_type}'] = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"เพิ่มรายการไม่สำเร็จ: {response.get('error', 'Unknown error')}")

def show_edit_form(api: MasterDataAPI, processor_type: str, config: Dict[str, Any], item: Dict[str, Any]):
    """Show edit item form"""
    st.subheader(f"✏️ แก้ไขรายการ - {config['name']}")
    
    with st.form(f"edit_form_{processor_type}"):
        form_data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['code'] = st.text_input(
                "รหัสรายการ", 
                value=item.get('code', ''),
                key=f"edit_code_{processor_type}"
            )
            form_data['name'] = st.text_input(
                "ชื่อรายการ *", 
                value=item.get('name', ''),
                key=f"edit_name_{processor_type}"
            )
            form_data['unit'] = st.text_input(
                "หน่วย", 
                value=item.get('unit', ''),
                key=f"edit_unit_{processor_type}"
            )
        
        with col2:
            form_data['material_unit_cost'] = st.number_input(
                "ต้นทุนวัสดุต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=float(item.get('material_unit_cost', 0)),
                step=0.01,
                key=f"edit_mat_cost_{processor_type}"
            )
            form_data['labor_unit_cost'] = st.number_input(
                "ต้นทุนแรงงานต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=float(item.get('labor_unit_cost', 0)),
                step=0.01,
                key=f"edit_lab_cost_{processor_type}"
            )
        
        # Show total unit cost for interior type
        if processor_type == 'interior':
            total_cost = form_data['material_unit_cost'] + form_data['labor_unit_cost']
            st.info(f"ต้นทุนรวมต่อหน่วย: {total_cost:,.2f} บาท")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 บันทึกการแก้ไข", type="primary")
        
        with col2:
            if st.form_submit_button("❌ ยกเลิก"):
                st.session_state[f'show_edit_{processor_type}'] = False
                if f'edit_item_{processor_type}' in st.session_state:
                    del st.session_state[f'edit_item_{processor_type}']
                st.rerun()
        
        if submitted:
            # Validate required fields
            if not form_data['name'].strip():
                st.error("กรุณากรอกชื่อรายการ")
            else:
                # Update item
                response = api.update_item(processor_type, item['internal_id'], form_data)
                
                if response.get('success', False):
                    st.success("แก้ไขรายการเรียบร้อยแล้ว")
                    st.session_state[f'show_edit_{processor_type}'] = False
                    if f'edit_item_{processor_type}' in st.session_state:
                        del st.session_state[f'edit_item_{processor_type}']
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"แก้ไขรายการไม่สำเร็จ: {response.get('error', 'Unknown error')}")

def show_delete_confirmation(api: MasterDataAPI, processor_type: str, config: Dict[str, Any], item: Dict[str, Any]):
    """Show delete confirmation dialog"""
    st.subheader(f"🗑️ ยืนยันการลบรายการ")
    
    st.warning(f"คุณต้องการลบรายการนี้หรือไม่?")
    st.write(f"**รหัส:** {item.get('code', 'ไม่มี')}")
    st.write(f"**ชื่อ:** {item.get('name', '')}")
    st.write(f"**ต้นทุนวัสดุ:** {item.get('material_unit_cost', 0):,.2f} บาท")
    st.write(f"**ต้นทุนแรงงาน:** {item.get('labor_unit_cost', 0):,.2f} บาท")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ ยืนยันการลบ", type="primary"):
            response = api.delete_item(processor_type, item['internal_id'])
            
            if response.get('success', False):
                st.success("ลบรายการเรียบร้อยแล้ว")
                st.session_state[f'show_delete_confirm_{processor_type}'] = False
                if f'delete_item_{processor_type}' in st.session_state:
                    del st.session_state[f'delete_item_{processor_type}']
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"ลบรายการไม่สำเร็จ: {response.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("❌ ยกเลิก"):
            st.session_state[f'show_delete_confirm_{processor_type}'] = False
            if f'delete_item_{processor_type}' in st.session_state:
                del st.session_state[f'delete_item_{processor_type}']
            st.rerun()

def show_bulk_import(api: MasterDataAPI, processor_type: str, config: Dict[str, Any]):
    """Show bulk import interface"""
    st.subheader(f"📤 นำเข้าข้อมูลจาก Excel - {config['name']}")
    
    st.write("**รูปแบบไฟล์ Excel ที่ต้องการ:**")
    
    # Show expected columns
    expected_columns = config['editable_columns']
    column_descriptions = {
        'code': 'รหัสรายการ (ไม่บังคับ)',
        'name': 'ชื่อรายการ (บังคับ)',
        'material_unit_cost': 'ต้นทุนวัสดุต่อหน่วย (บาท)',
        'labor_unit_cost': 'ต้นทุนแรงงานต่อหน่วย (บาท)',
        'unit': 'หน่วย (เช่น ตร.ม., เมตร, ชิ้น)'
    }
    
    columns_df = pd.DataFrame({
        'คอลัมน์': expected_columns,
        'คำอธิบาย': [column_descriptions.get(col, col) for col in expected_columns]
    })
    
    st.dataframe(columns_df, use_container_width=True, hide_index=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "เลือกไฟล์ Excel สำหรับนำเข้าข้อมูล",
        type=['xlsx', 'xls'],
        help="ไฟล์ Excel ต้องมีหัวคอลัมน์ในแถวแรก"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = f"temp_import_{processor_type}_{int(time.time())}.xlsx"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Preview data
        try:
            preview_df = pd.read_excel(temp_path, nrows=5)
            st.write("**ตัวอย่างข้อมูล (5 แถวแรก):**")
            st.dataframe(preview_df, use_container_width=True)
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("🚀 เริ่มนำเข้าข้อมูล", type="primary"):
                    with st.spinner("กำลังนำเข้าข้อมูล..."):
                        response = api.bulk_import(processor_type, temp_path)
                    
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    if response.get('success', False):
                        st.success(f"นำเข้าข้อมูลเรียบร้อยแล้ว: {response.get('imported_count', 0)} รายการ")
                        
                        if response.get('errors'):
                            st.warning("มีข้อผิดพลาดบางรายการ:")
                            for error in response['errors'][:10]:  # Show first 10 errors
                                st.write(f"• {error}")
                        
                        # Refresh the page
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"นำเข้าข้อมูลไม่สำเร็จ: {response.get('error', 'Unknown error')}")
                        
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ได้: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

# Page configuration - this must be at the module level, not inside main()
# Add protection to prevent multiple calls
import streamlit as st

if 'admin_page_config_set' not in st.session_state:
    st.set_page_config(
        page_title="📊 BOQ Master Data Admin",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.session_state.admin_page_config_set = True

# Check backend connection first
if not check_backend_connection():
    st.error("🔴 **แบ็กเอนด์ไม่ทำงาน**")
    st.markdown("กรุณาเริ่มเซิร์ฟเวอร์แบ็กเอนด์ก่อน: `python backend/main.py`")
    st.stop()

# Header
st.title("📊 BOQ Master Data Admin")
st.markdown("*ระบบจัดการข้อมูลหลักสำหรับการประมาณราคา BOQ*")
st.success("🟢 เชื่อมต่อแบ็กเอนด์สำเร็จ")

# Initialize API client
api = MasterDataAPI()

# Sidebar - Processor type selection
st.sidebar.header("เลือกประเภทข้อมูล")

processor_options = []
for proc_type, config in PROCESSOR_TYPES.items():
    processor_options.append(f"{config['icon']} {config['name']}")

selected_processor_display = st.sidebar.selectbox(
    "ประเภทข้อมูลหลัก:",
    processor_options,
    index=0
)

# Get actual processor type from display name
selected_processor = None
for proc_type, config in PROCESSOR_TYPES.items():
    if f"{config['icon']} {config['name']}" == selected_processor_display:
        selected_processor = proc_type
        break

if not selected_processor:
    st.error("ไม่พบประเภทข้อมูลที่เลือก")
    st.stop()

config = PROCESSOR_TYPES[selected_processor]

# Sidebar - Actions
st.sidebar.header("การดำเนินการ")

if st.sidebar.button("📋 ดูรายการทั้งหมด"):
    # Clear all form states
    for key in list(st.session_state.keys()):
        if key.startswith(f'show_') and selected_processor in key:
            del st.session_state[key]
    st.rerun()

if st.sidebar.button("➕ เพิ่มรายการใหม่"):
    st.session_state[f'show_create_{selected_processor}'] = True
    st.rerun()

if st.sidebar.button("📤 นำเข้าจาก Excel"):
    st.session_state[f'show_bulk_import_{selected_processor}'] = True
    st.rerun()

# Main content area
st.markdown("---")

# Show different views based on session state
if st.session_state.get(f'show_create_{selected_processor}', False):
    show_create_form(api, selected_processor, config)
    
elif st.session_state.get(f'show_edit_{selected_processor}', False):
    item = st.session_state.get(f'edit_item_{selected_processor}')
    if item:
        show_edit_form(api, selected_processor, config, item)
    else:
        st.error("ไม่พบข้อมูลรายการที่จะแก้ไข")
        st.session_state[f'show_edit_{selected_processor}'] = False
        
elif st.session_state.get(f'show_delete_confirm_{selected_processor}', False):
    item = st.session_state.get(f'delete_item_{selected_processor}')
    if item:
        show_delete_confirmation(api, selected_processor, config, item)
    else:
        st.error("ไม่พบข้อมูลรายการที่จะลบ")
        st.session_state[f'show_delete_confirm_{selected_processor}'] = False
        
elif st.session_state.get(f'show_bulk_import_{selected_processor}', False):
    show_bulk_import(api, selected_processor, config)
    
    if st.button("🔙 กลับไปดูรายการ"):
        st.session_state[f'show_bulk_import_{selected_processor}'] = False
        st.rerun()
        
else:
    # Default view - show item list
    display_item_list(api, selected_processor, config)

# Sidebar - Statistics
st.sidebar.markdown("---")
st.sidebar.header("สถิติข้อมูล")

try:
    for proc_type, proc_config in PROCESSOR_TYPES.items():
        response = api.list_items(proc_type)
        if response.get('success', False):
            count = response.get('count', 0)
            st.sidebar.metric(
                label=f"{proc_config['icon']} {proc_config['name'].split('(')[0].strip()}",
                value=f"{count} รายการ"
            )
except:
    st.sidebar.write("ไม่สามารถโหลดสถิติได้")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>BOQ Master Data Admin v2.0 | Streamlit Admin Interface</div>",
    unsafe_allow_html=True
)#!/usr/bin/env python3
"""
Master Data Admin Interface - Streamlit page for CRUD operations on master data
"""

import streamlit as st
import requests
import pandas as pd
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# Configuration
def get_backend_url():
    """Get backend URL based on environment"""
    if os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
        return "http://boq-backend:5000"
    else:
        return "http://localhost:5000"

BACKEND_URL = get_backend_url()

# Processor types configuration
PROCESSOR_TYPES = {
    'interior': {
        'name': 'Interior (งานตกแต่งภายใน)',
        'icon': '🏠',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'total_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    },
    'electrical': {
        'name': 'Electrical (งานไฟฟ้า)',
        'icon': '⚡',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    },
    'ac': {
        'name': 'Air Conditioning (งานแอร์)',
        'icon': '❄️',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    },
    'fp': {
        'name': 'Fire Protection (งานดับเพลิง)',
        'icon': '🔥',
        'columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'editable_columns': ['code', 'name', 'material_unit_cost', 'labor_unit_cost', 'unit'],
        'required_columns': ['name']
    }
}

class MasterDataAPI:
    """API client for master data CRUD operations"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
    
    def list_items(self, processor_type: str) -> Dict[str, Any]:
        """List all items for a processor type"""
        try:
            response = requests.get(f"{self.base_url}/api/master-data/list/{processor_type}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_item(self, processor_type: str, item_id: str) -> Dict[str, Any]:
        """Get a specific item"""
        try:
            response = requests.get(f"{self.base_url}/api/master-data/get/{processor_type}/{item_id}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_item(self, processor_type: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        try:
            response = requests.post(f"{self.base_url}/api/master-data/create/{processor_type}", json=item_data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_item(self, processor_type: str, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item"""
        try:
            response = requests.put(f"{self.base_url}/api/master-data/update/{processor_type}/{item_id}", json=item_data)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_item(self, processor_type: str, item_id: str) -> Dict[str, Any]:
        """Delete an item"""
        try:
            response = requests.delete(f"{self.base_url}/api/master-data/delete/{processor_type}/{item_id}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def bulk_import(self, processor_type: str, file_path: str) -> Dict[str, Any]:
        """Bulk import items from Excel file"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.base_url}/api/master-data/bulk-import/{processor_type}", files=files)
                return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_data(self, processor_type: str) -> Dict[str, Any]:
        """Export master data to Excel"""
        try:
            response = requests.get(f"{self.base_url}/api/master-data/export/{processor_type}")
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}

def check_backend_connection():
    """Check if backend server is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/config/inquiry", timeout=2)
        return response.status_code == 200
    except:
        return False

def display_item_list(api: MasterDataAPI, processor_type: str, config: Dict[str, Any]):
    """Display list of items with actions"""
    st.subheader(f"📋 รายการข้อมูลหลัก - {config['name']}")
    
    # Load data
    response = api.list_items(processor_type)
    
    if not response.get('success', False):
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {response.get('error', 'Unknown error')}")
        return
    
    items = response.get('items', [])
    
    if not items:
        st.info("ไม่มีข้อมูลในระบบ กรุณาเพิ่มข้อมูลใหม่")
        return
    
    # Display count
    st.write(f"**จำนวนรายการทั้งหมด:** {len(items)} รายการ")
    
    # Convert to DataFrame for display
    df = pd.DataFrame(items)
    
    # Show only relevant columns
    display_columns = config['columns']
    if 'internal_id' in df.columns:
        df_display = df[['internal_id'] + [col for col in display_columns if col in df.columns]].copy()
    else:
        df_display = df[[col for col in display_columns if col in df.columns]].copy()
    
    # Format cost columns
    cost_columns = ['material_unit_cost', 'labor_unit_cost', 'total_unit_cost']
    for col in cost_columns:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and x != '' else '0.00')
    
    # Display table with selection
    selected_rows = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ เพิ่มรายการใหม่", type="primary"):
            st.session_state[f'show_create_{processor_type}'] = True
            st.rerun()
    
    with col2:
        if st.button("✏️ แก้ไข") and selected_rows['selection']['rows']:
            selected_idx = selected_rows['selection']['rows'][0]
            selected_item = items[selected_idx]
            st.session_state[f'edit_item_{processor_type}'] = selected_item
            st.session_state[f'show_edit_{processor_type}'] = True
            st.rerun()
    
    with col3:
        if st.button("🗑️ ลบ", type="secondary") and selected_rows['selection']['rows']:
            selected_idx = selected_rows['selection']['rows'][0]
            selected_item = items[selected_idx]
            st.session_state[f'delete_item_{processor_type}'] = selected_item
            st.session_state[f'show_delete_confirm_{processor_type}'] = True
            st.rerun()
    
    with col4:
        if st.button("📤 ส่งออก Excel"):
            export_response = api.export_data(processor_type)
            if export_response.get('success', False):
                st.success(f"ส่งออกข้อมูลเรียบร้อยแล้ว: {export_response['filename']}")
                st.write(f"[ดาวน์โหลดไฟล์]({export_response['download_url']})")
            else:
                st.error(f"ส่งออกข้อมูลไม่สำเร็จ: {export_response.get('error', 'Unknown error')}")

def show_create_form(api: MasterDataAPI, processor_type: str, config: Dict[str, Any]):
    """Show create item form"""
    st.subheader(f"➕ เพิ่มรายการใหม่ - {config['name']}")
    
    with st.form(f"create_form_{processor_type}"):
        form_data = {}
        
        # Create input fields based on processor type
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['code'] = st.text_input("รหัสรายการ", key=f"create_code_{processor_type}")
            form_data['name'] = st.text_input("ชื่อรายการ *", key=f"create_name_{processor_type}")
            form_data['unit'] = st.text_input("หน่วย", key=f"create_unit_{processor_type}")
        
        with col2:
            form_data['material_unit_cost'] = st.number_input(
                "ต้นทุนวัสดุต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=0.0,
                step=0.01,
                key=f"create_mat_cost_{processor_type}"
            )
            form_data['labor_unit_cost'] = st.number_input(
                "ต้นทุนแรงงานต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=0.0,
                step=0.01,
                key=f"create_lab_cost_{processor_type}"
            )
        
        # Show total unit cost for interior type
        if processor_type == 'interior':
            total_cost = form_data['material_unit_cost'] + form_data['labor_unit_cost']
            st.info(f"ต้นทุนรวมต่อหน่วย: {total_cost:,.2f} บาท")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 บันทึก", type="primary")
        
        with col2:
            if st.form_submit_button("❌ ยกเลิก"):
                st.session_state[f'show_create_{processor_type}'] = False
                st.rerun()
        
        if submitted:
            # Validate required fields
            if not form_data['name'].strip():
                st.error("กรุณากรอกชื่อรายการ")
            else:
                # Create item
                response = api.create_item(processor_type, form_data)
                
                if response.get('success', False):
                    st.success("เพิ่มรายการเรียบร้อยแล้ว")
                    st.session_state[f'show_create_{processor_type}'] = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"เพิ่มรายการไม่สำเร็จ: {response.get('error', 'Unknown error')}")

def show_edit_form(api: MasterDataAPI, processor_type: str, config: Dict[str, Any], item: Dict[str, Any]):
    """Show edit item form"""
    st.subheader(f"✏️ แก้ไขรายการ - {config['name']}")
    
    with st.form(f"edit_form_{processor_type}"):
        form_data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['code'] = st.text_input(
                "รหัสรายการ", 
                value=item.get('code', ''),
                key=f"edit_code_{processor_type}"
            )
            form_data['name'] = st.text_input(
                "ชื่อรายการ *", 
                value=item.get('name', ''),
                key=f"edit_name_{processor_type}"
            )
            form_data['unit'] = st.text_input(
                "หน่วย", 
                value=item.get('unit', ''),
                key=f"edit_unit_{processor_type}"
            )
        
        with col2:
            form_data['material_unit_cost'] = st.number_input(
                "ต้นทุนวัสดุต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=float(item.get('material_unit_cost', 0)),
                step=0.01,
                key=f"edit_mat_cost_{processor_type}"
            )
            form_data['labor_unit_cost'] = st.number_input(
                "ต้นทุนแรงงานต่อหน่วย (บาท)", 
                min_value=0.0, 
                value=float(item.get('labor_unit_cost', 0)),
                step=0.01,
                key=f"edit_lab_cost_{processor_type}"
            )
        
        # Show total unit cost for interior type
        if processor_type == 'interior':
            total_cost = form_data['material_unit_cost'] + form_data['labor_unit_cost']
            st.info(f"ต้นทุนรวมต่อหน่วย: {total_cost:,.2f} บาท")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 บันทึกการแก้ไข", type="primary")
        
        with col2:
            if st.form_submit_button("❌ ยกเลิก"):
                st.session_state[f'show_edit_{processor_type}'] = False
                if f'edit_item_{processor_type}' in st.session_state:
                    del st.session_state[f'edit_item_{processor_type}']
                st.rerun()
        
        if submitted:
            # Validate required fields
            if not form_data['name'].strip():
                st.error("กรุณากรอกชื่อรายการ")
            else:
                # Update item
                response = api.update_item(processor_type, item['internal_id'], form_data)
                
                if response.get('success', False):
                    st.success("แก้ไขรายการเรียบร้อยแล้ว")
                    st.session_state[f'show_edit_{processor_type}'] = False
                    if f'edit_item_{processor_type}' in st.session_state:
                        del st.session_state[f'edit_item_{processor_type}']
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"แก้ไขรายการไม่สำเร็จ: {response.get('error', 'Unknown error')}")

def show_delete_confirmation(api: MasterDataAPI, processor_type: str, config: Dict[str, Any], item: Dict[str, Any]):
    """Show delete confirmation dialog"""
    st.subheader(f"🗑️ ยืนยันการลบรายการ")
    
    st.warning(f"คุณต้องการลบรายการนี้หรือไม่?")
    st.write(f"**รหัส:** {item.get('code', 'ไม่มี')}")
    st.write(f"**ชื่อ:** {item.get('name', '')}")
    st.write(f"**ต้นทุนวัสดุ:** {item.get('material_unit_cost', 0):,.2f} บาท")
    st.write(f"**ต้นทุนแรงงาน:** {item.get('labor_unit_cost', 0):,.2f} บาท")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ ยืนยันการลบ", type="primary"):
            response = api.delete_item(processor_type, item['internal_id'])
            
            if response.get('success', False):
                st.success("ลบรายการเรียบร้อยแล้ว")
                st.session_state[f'show_delete_confirm_{processor_type}'] = False
                if f'delete_item_{processor_type}' in st.session_state:
                    del st.session_state[f'delete_item_{processor_type}']
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"ลบรายการไม่สำเร็จ: {response.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("❌ ยกเลิก"):
            st.session_state[f'show_delete_confirm_{processor_type}'] = False
            if f'delete_item_{processor_type}' in st.session_state:
                del st.session_state[f'delete_item_{processor_type}']
            st.rerun()

def show_bulk_import(api: MasterDataAPI, processor_type: str, config: Dict[str, Any]):
    """Show bulk import interface"""
    st.subheader(f"📤 นำเข้าข้อมูลจาก Excel - {config['name']}")
    
    st.write("**รูปแบบไฟล์ Excel ที่ต้องการ:**")
    
    # Show expected columns
    expected_columns = config['editable_columns']
    column_descriptions = {
        'code': 'รหัสรายการ (ไม่บังคับ)',
        'name': 'ชื่อรายการ (บังคับ)',
        'material_unit_cost': 'ต้นทุนวัสดุต่อหน่วย (บาท)',
        'labor_unit_cost': 'ต้นทุนแรงงานต่อหน่วย (บาท)',
        'unit': 'หน่วย (เช่น ตร.ม., เมตร, ชิ้น)'
    }
    
    columns_df = pd.DataFrame({
        'คอลัมน์': expected_columns,
        'คำอธิบาย': [column_descriptions.get(col, col) for col in expected_columns]
    })
    
    st.dataframe(columns_df, use_container_width=True, hide_index=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "เลือกไฟล์ Excel สำหรับนำเข้าข้อมูล",
        type=['xlsx', 'xls'],
        help="ไฟล์ Excel ต้องมีหัวคอลัมน์ในแถวแรก"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = f"temp_import_{processor_type}_{int(time.time())}.xlsx"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Preview data
        try:
            preview_df = pd.read_excel(temp_path, nrows=5)
            st.write("**ตัวอย่างข้อมูล (5 แถวแรก):**")
            st.dataframe(preview_df, use_container_width=True)
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("🚀 เริ่มนำเข้าข้อมูล", type="primary"):
                    with st.spinner("กำลังนำเข้าข้อมูล..."):
                        response = api.bulk_import(processor_type, temp_path)
                    
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    if response.get('success', False):
                        st.success(f"นำเข้าข้อมูลเรียบร้อยแล้ว: {response.get('imported_count', 0)} รายการ")
                        
                        if response.get('errors'):
                            st.warning("มีข้อผิดพลาดบางรายการ:")
                            for error in response['errors'][:10]:  # Show first 10 errors
                                st.write(f"• {error}")
                        
                        # Refresh the page
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"นำเข้าข้อมูลไม่สำเร็จ: {response.get('error', 'Unknown error')}")
                        
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ได้: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

def main():
    """Main Streamlit application for master data admin"""
    
    # Page configuration
    st.set_page_config(
        page_title="📊 BOQ Master Data Admin",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check backend connection first
    if not check_backend_connection():
        st.error("🔴 **แบ็กเอนด์ไม่ทำงาน**")
        st.markdown("กรุณาเริ่มเซิร์ฟเวอร์แบ็กเอนด์ก่อน: `python backend/main.py`")
        st.stop()
    
    # Header
    st.title("📊 BOQ Master Data Admin")
    st.markdown("*ระบบจัดการข้อมูลหลักสำหรับการประมาณราคา BOQ*")
    st.success("🟢 เชื่อมต่อแบ็กเอนด์สำเร็จ")
    
    # Initialize API client
    api = MasterDataAPI()
    
    # Sidebar - Processor type selection
    st.sidebar.header("เลือกประเภทข้อมูล")
    
    processor_options = []
    for proc_type, config in PROCESSOR_TYPES.items():
        processor_options.append(f"{config['icon']} {config['name']}")
    
    selected_processor_display = st.sidebar.selectbox(
        "ประเภทข้อมูลหลัก:",
        processor_options,
        index=0
    )
    
    # Get actual processor type from display name
    selected_processor = None
    for proc_type, config in PROCESSOR_TYPES.items():
        if f"{config['icon']} {config['name']}" == selected_processor_display:
            selected_processor = proc_type
            break
    
    if not selected_processor:
        st.error("ไม่พบประเภทข้อมูลที่เลือก")
        st.stop()
    
    config = PROCESSOR_TYPES[selected_processor]
    
    # Sidebar - Actions
    st.sidebar.header("การดำเนินการ")
    
    if st.sidebar.button("📋 ดูรายการทั้งหมด"):
        # Clear all form states
        for key in list(st.session_state.keys()):
            if key.startswith(f'show_') and selected_processor in key:
                del st.session_state[key]
        st.rerun()
    
    if st.sidebar.button("➕ เพิ่มรายการใหม่"):
        st.session_state[f'show_create_{selected_processor}'] = True
        st.rerun()
    
    if st.sidebar.button("📤 นำเข้าจาก Excel"):
        st.session_state[f'show_bulk_import_{selected_processor}'] = True
        st.rerun()
    
    # Main content area
    st.markdown("---")
    
    # Show different views based on session state
    if st.session_state.get(f'show_create_{selected_processor}', False):
        show_create_form(api, selected_processor, config)
        
    elif st.session_state.get(f'show_edit_{selected_processor}', False):
        item = st.session_state.get(f'edit_item_{selected_processor}')
        if item:
            show_edit_form(api, selected_processor, config, item)
        else:
            st.error("ไม่พบข้อมูลรายการที่จะแก้ไข")
            st.session_state[f'show_edit_{selected_processor}'] = False
            
    elif st.session_state.get(f'show_delete_confirm_{selected_processor}', False):
        item = st.session_state.get(f'delete_item_{selected_processor}')
        if item:
            show_delete_confirmation(api, selected_processor, config, item)
        else:
            st.error("ไม่พบข้อมูลรายการที่จะลบ")
            st.session_state[f'show_delete_confirm_{selected_processor}'] = False
            
    elif st.session_state.get(f'show_bulk_import_{selected_processor}', False):
        show_bulk_import(api, selected_processor, config)
        
        if st.button("🔙 กลับไปดูรายการ"):
            st.session_state[f'show_bulk_import_{selected_processor}'] = False
            st.rerun()
            
    else:
        # Default view - show item list
        display_item_list(api, selected_processor, config)
    
    # Sidebar - Statistics
    st.sidebar.markdown("---")
    st.sidebar.header("สถิติข้อมูล")
    
    try:
        for proc_type, proc_config in PROCESSOR_TYPES.items():
            response = api.list_items(proc_type)
            if response.get('success', False):
                count = response.get('count', 0)
                st.sidebar.metric(
                    label=f"{proc_config['icon']} {proc_config['name'].split('(')[0].strip()}",
                    value=f"{count} รายการ"
                )
    except:
        st.sidebar.write("ไม่สามารถโหลดสถิติได้")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>BOQ Master Data Admin v2.0 | Streamlit Admin Interface</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()