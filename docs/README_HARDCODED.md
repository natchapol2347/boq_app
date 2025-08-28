# BOQ Processor - Database-Driven System 🚀

## 🎯 What Changed?

### ❌ OLD SYSTEM:
- Master data synced from `master.xlsx` 
- Manual Excel file updates required
- Data could become stale
- No real-time updates

### ✅ NEW SYSTEM:
- **100% Database-driven** - no more Excel dependency
- **Full CRUD API** for master data management
- **Real-time updates** through web interface
- **Employee-friendly admin panel**
- **Import/Export capabilities** for bulk operations

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   SQLite DB     │
│   (Streamlit)   │◄──►│   (Flask)        │◄──►│   (master_data) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
│                       │                       │
│ • BOQ Processing      │ • CRUD Operations     │ • interior_items
│ • Admin Interface     │ • File Processing     │ • ee_items  
│ • Data Management     │ • Configuration       │ • ac_items
                        │ • Import/Export       │ • fp_items
```

## 🚀 Quick Start

### 1. Start the Backend
```bash
python backend/main.py
```
This will:
- Initialize empty database with sample data
- Start Flask API server on http://localhost:5000
- No more Excel sync required!

### 2. Use BOQ Processing (Normal Users)
```bash
streamlit run frontend/frontend.py
```
Access at: http://localhost:8501
- Same BOQ processing functionality
- Upload BOQ files, generate costs, apply markup

### 3. Use Admin Interface (Data Managers)
```bash
streamlit run admin_master_data.py
```
Access at: http://localhost:8502 (different port)
- Add/Edit/Delete master data items
- Bulk import from Excel
- Export data to Excel
- Real-time updates

## 📊 Master Data Management

### Available Operations:

#### ✅ Create Items
- Add new items via web form
- All processor types supported (Interior, Electrical, AC, Fire Protection)
- Real-time cost calculations

#### ✏️ Edit Items  
- Update existing items
- Automatic total cost calculation
- Instant database updates

#### 🗑️ Delete Items
- Safe deletion with confirmation
- Immediate removal from system

#### 📤 Bulk Import
- Upload Excel files with master data
- Automatic validation and error reporting
- Support for all processor types

#### 📥 Export Data
- Download current master data as Excel
- Perfect for backups or sharing

## 🎛️ API Endpoints

### Master Data CRUD
```
GET    /api/master-data/list/<processor_type>          # List all items
GET    /api/master-data/get/<processor_type>/<id>      # Get specific item  
POST   /api/master-data/create/<processor_type>        # Create new item
PUT    /api/master-data/update/<processor_type>/<id>   # Update item
DELETE /api/master-data/delete/<processor_type>/<id>   # Delete item
POST   /api/master-data/bulk-import/<processor_type>   # Bulk import Excel
GET    /api/master-data/export/<processor_type>        # Export to Excel
```

### BOQ Processing (Unchanged)
```
POST /api/process-boq           # Process uploaded BOQ
POST /api/generate-final-boq    # Generate final BOQ with costs
POST /api/apply-markup          # Apply markup percentage
POST /api/cleanup-session       # Clean up session data
```

### Configuration
```
GET  /api/config/inquiry        # Get current config
POST /api/config/update         # Update processor config
GET  /api/download/<filename>   # Download generated files
```

## 💾 Database Schema

### Interior Items (interior_items)
```sql
internal_id TEXT PRIMARY KEY
code TEXT                    -- รหัสรายการ
name TEXT NOT NULL          -- ชื่อรายการ  
material_unit_cost REAL     -- ต้นทุนวัสดุ/หน่วย
labor_unit_cost REAL        -- ต้นทุนแรงงาน/หน่วย
total_unit_cost REAL        -- ต้นทุนรวม/หน่วย (auto-calculated)
unit TEXT                   -- หน่วย (ตร.ม., เมตร, ชิ้น)
```

### System Items (ee_items, ac_items, fp_items)
```sql
internal_id TEXT PRIMARY KEY
code TEXT                    -- รหัสรายการ
name TEXT NOT NULL          -- ชื่อรายการ
material_unit_cost REAL     -- ต้นทุนวัสดุ/หน่วย  
labor_unit_cost REAL        -- ต้นทุนแรงงาน/หน่วย
unit TEXT                   -- หน่วย
```

## 🔧 Usage Examples

### For System Administrators

#### 1. Reset Database & Start Fresh
```bash
python backend/main.py --reset-db
```
This creates empty database with sample data.

#### 2. Add New Interior Item via API
```python
import requests

data = {
    "code": "INT999",
    "name": "กระเบื้องพอร์ซเลน 80x80",
    "material_unit_cost": 650.0,
    "labor_unit_cost": 280.0,
    "unit": "ตร.ม."
}

response = requests.post("http://localhost:5000/api/master-data/create/interior", json=data)
print(response.json())
```

#### 3. Bulk Import from Excel
Upload Excel file with columns:
- `code` (รหัส)
- `name` (ชื่อรายการ)  
- `material_unit_cost` (ต้นทุนวัสดุ)
- `labor_unit_cost` (ต้นทุนแรงงาน)
- `unit` (หน่วย)

### For Employees

1. **Access Admin Panel**: http://localhost:8502
2. **Select Processor Type**: Interior, Electrical, AC, or Fire Protection
3. **Manage Data**: Add, edit, delete items through user-friendly forms
4. **Import/Export**: Use Excel files for bulk operations

## 🔄 Migration from Old System

### Step 1: Export Existing Data (if needed)
If you have existing master.xlsx with important data:
1. Start the old system once to sync data to database
2. Use export feature to backup current data

### Step 2: Switch to New System
1. Update to new codebase
2. Start backend: `python backend/main.py`
3. Access admin interface for data management

### Step 3: Import Your Data (if needed)
1. Use bulk import feature in admin interface
2. Upload your existing Excel files
3. Verify imported data

## 🎯 Benefits

### For Administrators:
✅ **No more manual Excel updates**  
✅ **Real-time data management**  
✅ **Better data consistency**  
✅ **Audit trail capabilities**  
✅ **Multi-user support**  

### For Employees:
✅ **User-friendly web interface**  
✅ **No Excel skills required**  
✅ **Instant updates**  
✅ **Error validation**  
✅ **Bulk operations support**  

### For System:
✅ **Better performance**  
✅ **Data integrity**  
✅ **Scalability**  
✅ **API-first design**  
✅ **Maintainable codebase**  

## 📁 File Structure

```
your_project/
├── backend/
│   ├── main.py              # Updated - no Excel sync
│   └── app.py               # Updated - with CRUD API
├── frontend/
│   └── frontend.py          # Unchanged - BOQ processing
├── master_data_admin.py     # NEW - Admin interface
├── admin_master_data.py     # NEW - Admin launcher  
├── src/
│   ├── processors/          # Unchanged
│   └── config/              # Unchanged
├── models/                  # Unchanged
├── data/
│   └── master_data.db       # Database file
└── storage/
    ├── uploads/             # Temp uploads
    └── output/              # Generated files
```

## 🚨 Important Notes

1. **No master.xlsx Required**: The system no longer reads from Excel files for master data
2. **Database Persistence**: All data is stored in SQLite database
3. **Sample Data**: System starts with sample data for testing
4. **Backup Recommendations**: Regular database backups recommended
5. **Multi-user Access**: Multiple employees can use admin interface simultaneously

## 🔍 Troubleshooting

### Backend won't start?
```bash
# Check Python dependencies
pip install -r requirements.txt

# Reset database if corrupted
python backend/main.py --reset-db
```

### Admin interface shows connection error?
1. Make sure backend is running on http://localhost:5000
2. Check firewall settings
3. Verify no port conflicts

### Data not updating?
1. Check API logs in terminal
2. Verify database write permissions
3. Try refreshing browser

---

## 🎉 Ready to Go!

Your BOQ processor is now fully database-driven with a modern CRUD interface. No more Excel file management headaches! 

**Start with:** `python backend/main.py` and then open the admin interface for data management.

Happy processing! 📊✨