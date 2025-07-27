# BOQ Processor - Refactored Architecture

This version of the BOQ processor uses a clean, modular architecture with separate processors for each sheet type, making it easier to debug and maintain.

## 🏗️ Architecture Overview

The application is now organized into specialized processors:

- **Base Sheet Processor**: Abstract base class defining common functionality
- **Interior Sheet Processor**: Handles interior construction sheets (INT)
- **Electrical Sheet Processor**: Handles electrical work sheets (EE)
- **AC Sheet Processor**: Handles air conditioning sheets (AC)
- **Fire Protection Sheet Processor**: Handles fire protection sheets (FP)
- **Summary Sheet Processor**: Aggregates data from all processors
- **Main Orchestrator**: Coordinates all processors and handles Flask routes

## 🚀 Quick Start

### 1. Install dependencies

```bash
poetry install
# OR
pip install -r requirements.txt
```

### 2. Run the processor

```bash
python main.py
```

### 3. Available options

```bash
# Reset database and add sample data
python main.py --reset-db --add-sample-data

# Run on different port with debug mode
python main.py --port 8000 --debug

# Show help
python main.py --help
```

## 📁 File Structure

```
your_project_folder/
├── main.py                          # Main application runner
├── app.py      # Main orchestrator
├── base_sheet_processor.py          # Base class for all processors
├── interior_sheet_processor.py      # Interior (INT) sheet processor
├── electrical_sheet_processor.py    # Electrical (EE) sheet processor
├── ac_sheet_processor.py           # Air Conditioning (AC) sheet processor
├── fp_sheet_processor.py           # Fire Protection (FP) sheet processor
├── summary_sheet_processor.py      # Summary aggregation processor
├── master_data/
│   └── master.xlsx                  # Master data file
├── uploads/                         # Temporary upload folder
├── output/                          # Generated BOQ files
└── app.log               # Application log file
```

## 🔧 API Usage

### Process BOQ File

```bash
# Upload a BOQ file for processing
curl -X POST -F "file=@uploads/Blank BOQ AIS ASP Zeer รังสิต-1.xlsx" http://localhost:5000/api/process-boq
```

### Generate Final BOQ

```bash
# Generate the final BOQ with the session ID returned from the previous call
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "YOUR_SESSION_ID"}' http://localhost:5000/api/generate-final-boq
```

### Download Generated File

```bash
# Download the generated file (filename returned from generate-final-boq)
curl -O http://localhost:5000/api/download/final_boq_TIMESTAMP.xlsx
```

## 📊 Sheet Types and Configurations

### Interior Sheets (INT)
- **Pattern**: "int" in sheet name
- **Header row**: 9 (0-based, row 10 in Excel)
- **Database table**: `interior_items`
- **Column mappings**:
  - code: Column B (2)
  - name: Column C (3)
  - quantity: Column D (4)
  - unit: Column E (5)
  - material_cost: Column F (6)
  - labor_cost: Column G (7)
  - total_cost: Column H (8)

### Electrical Sheets (EE)
- **Pattern**: "ee" in sheet name
- **Header row**: 7 (0-based, row 8 in Excel)
- **Database table**: `ee_items`
- **Column mappings**:
  - code: Column B (2)
  - name: Column C (3)
  - unit: Column F (6)
  - quantity: Column G (7)
  - material_cost: Column H (8)
  - labor_cost: Column J (10)
  - total_cost: Column L (12)

### Air Conditioning Sheets (AC)
- **Pattern**: "ac" in sheet name
- **Header row**: 5 (0-based, row 6 in Excel)
- **Database table**: `ac_items`
- **Column mappings**:
  - code: Column B (2)
  - name: Column C (3)
  - unit: Column F (6)
  - quantity: Column G (7)
  - material_cost: Column H (8)
  - labor_cost: Column J (10)
  - total_cost: Column L (12)

### Fire Protection Sheets (FP)
- **Pattern**: "fp" in sheet name
- **Header row**: 7 (0-based, row 8 in Excel)
- **Database table**: `fp_items`
- **Column mappings**:
  - code: Column B (2)
  - name: Column C (3)
  - unit: Column F (6)
  - quantity: Column G (7)
  - material_cost: Column H (8)
  - labor_cost: Column J (10)
  - total_cost: Column L (12)

### Default Sheets
- **Used when**: No other pattern matches
- **Header row**: 8 (0-based, row 9 in Excel)
- **Database table**: `default_items`
- **Column mappings**:
  - code: Column B (2)
  - name: Column C (3)
  - quantity: Column D (4)
  - unit: Column E (5)
  - material_cost: Column F (6)
  - labor_cost: Column G (7)
  - total_cost: Column H (8)

## 🎯 Development Approach

This refactored version follows a **step-by-step improvement approach**:

### Phase 1: Refactoring ✅
- Clean, organized code structure
- Separate processors for each sheet type
- Same behavior as original (no logic changes)
- Easier debugging and maintenance

### Phase 2: Testing & Debugging 🔄
- Use clean structure to identify issues
- Debug individual processors
- Compare with original behavior
- Document actual problems

### Phase 3: Logic Improvements 📋
- Apply targeted fixes to specific processors
- Improve cost calculation logic
- Enhance fuzzy matching
- Fix section detection

## 🔍 Debugging Features

### Enhanced Logging
- Detailed logging for each processor
- Separate log files for different components
- Debug mode for verbose output

### Database Inspection
```bash
# Check database contents
python -c "
import sqlite3
conn = sqlite3.connect('~/AppData/Roaming/App/master_data.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print('Tables:', [row[0] for row in cursor.fetchall()])
"
```

### Individual Processor Testing
Each processor can be tested individually:
```python
from interior_sheet_processor import InteriorSheetProcessor
processor = InteriorSheetProcessor(db_path, markup_rates)
# Test specific functionality
```

## 🛠️ Troubleshooting

### Issue: No costs showing up in final BOQ

1. **Reset database and add sample data**:
   ```bash
   python main.py --reset-db --add-sample-data
   ```

2. **Check database has cost data**:
   ```bash
   python -c "
   import sqlite3
   conn = sqlite3.connect('~/AppData/Roaming/App/master_data.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM interior_items WHERE material_cost > 0')
   print('Items with costs:', cursor.fetchone()[0])
   "
   ```

3. **Run in debug mode**:
   ```bash
   python main.py --debug
   ```

### Issue: Import errors

Make sure all processor files are in the same directory:
```bash
ls -la *.py | grep processor
```

You should see:
- `base_sheet_processor.py`
- `interior_sheet_processor.py`
- `electrical_sheet_processor.py`
- `ac_sheet_processor.py`
- `fp_sheet_processor.py`
- `summary_sheet_processor.py`
- `app.py`

### Issue: Processing errors

1. **Check log file**: `app.log`
2. **Run with debug flag**: `python main.py --debug`
3. **Validate master data**: Ensure `master_data/master.xlsx` exists

## 🔧 Configuration

### Markup Rates
Default markup rates can be modified in `app.py`:
```python
self.markup_rates = {100: 1.00, 130: 1.30, 150: 1.50, 50: 0.50, 30: 0.30}
```

### Database Location
Default database location: `~/AppData/Roaming/App/master_data.db`

### File Paths
- **Master data**: `master_data/master.xlsx`
- **Uploads**: `uploads/` (temporary)
- **Output**: `output/` (generated files)
- **Logs**: `app.log`

## 📝 Next Steps

1. **Test the refactored version** with your existing BOQ files
2. **Compare behavior** with the original processor
3. **Identify specific issues** using the clean structure
4. **Apply targeted fixes** to individual processors
5. **Enhance functionality** incrementally

## 🤝 Contributing

When modifying the code:
1. **Follow the processor pattern** - each sheet type has its own processor
2. **Update the base class** for common functionality
3. **Test individual processors** before integration
4. **Maintain backward compatibility** with existing APIs
5. **Document changes** in this README

## 📚 Additional Resources

- **Original Logic**: Reference `hard_coded_boq_fixed.py` for original implementation
- **Business Logic**: See `CLAUDE.md` for detailed business requirements
- **Development Guide**: Follow the step-by-step approach outlined above