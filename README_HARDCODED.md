# Hard-Coded BOQ Processor (FIXED)

This version of the BOQ processor uses hard-coded column mappings for each sheet type, which solves the issues with the previous dynamic column detection approach.

## Important Fix

The original version had an issue with row index calculation when writing costs to Excel cells. This has been fixed in the current version:

- **Problem**: The row calculation formula subtracted the header row index, which resulted in costs being written to the wrong cells.
- **Solution**: The row calculation formula has been fixed to correctly map pandas DataFrame indices to Excel rows.

## Key Features

- Fixed, sheet-specific column mappings
- Separate database tables for each sheet type (INT, EE, AC, FP)
- Sample cost data to ensure costs are always populated
- Direct matching against sheet-specific master data
- Fixed header row detection based on sheet type

## How to Use

### 1. Install dependencies

```bash
poetry install
# OR
pip install -r requirements.txt
```

### 2. Run the processor

```bash
python run_hard_coded_boq.py
```

Options:
- `--reset-db`: Reset the database before running
- `--port`: Port to run the server on (default: 5000)
- `--host`: Host to run the server on (default: localhost)
- `--debug`: Run in debug mode
- `--add-sample-costs`: Add sample costs to the database

### 3. Process BOQ files

With the server running, you can process BOQ files using the API:

```bash
# Upload a BOQ file for processing
curl -X POST -F "file=@uploads/Blank BOQ AIS ASP Zeer รังสิต-1.xlsx" http://localhost:5000/api/process-boq

# Generate the final BOQ with the session ID returned from the previous call
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "YOUR_SESSION_ID"}' http://localhost:5000/api/generate-final-boq

# Download the generated file
# The filename will be returned from the previous call
curl -O http://localhost:5000/api/download/final_boq_TIMESTAMP.xlsx
```

## Testing

To test the hard-coded processor:

```bash
python test_hard_coded.py
```

This will:
1. Test the database setup with separate tables
2. Verify the sheet type detection and column mappings
3. Test direct item matching against the database

## Sheet Types and Mappings

The processor supports the following sheet types:

### Interior Sheets (INT)
- Pattern: "int" in sheet name
- Header row: 9 (0-based, row 10 in Excel)
- Column mappings:
  - code: Column B
  - name: Column C
  - quantity: Column D
  - unit: Column E
  - material_cost: Column F
  - labor_cost: Column G
  - total_cost: Column H

### Electrical Sheets (EE)
- Pattern: "ee" in sheet name
- Header row: 7 (0-based, row 8 in Excel)
- Column mappings:
  - code: Column B
  - name: Column C
  - unit: Column F
  - quantity: Column G
  - material_cost: Column H
  - labor_cost: Column J
  - total_cost: Column L

### Air Conditioning Sheets (AC)
- Pattern: "ac" in sheet name
- Header row: 5 (0-based, row 6 in Excel)
- Column mappings:
  - code: Column B
  - name: Column C
  - unit: Column F
  - quantity: Column G
  - material_cost: Column H
  - labor_cost: Column J
  - total_cost: Column L

### Fire Protection Sheets (FP)
- Pattern: "fp" in sheet name
- Header row: 7 (0-based, row 8 in Excel)
- Column mappings:
  - code: Column B
  - name: Column C
  - unit: Column F
  - quantity: Column G
  - material_cost: Column H
  - labor_cost: Column J
  - total_cost: Column L

### Default Sheets
- Used when no other pattern matches
- Header row: 8 (0-based, row 9 in Excel)
- Column mappings:
  - code: Column B
  - name: Column C
  - quantity: Column D
  - unit: Column E
  - material_cost: Column F
  - labor_cost: Column G
  - total_cost: Column H

## Troubleshooting

If you encounter issues with costs not showing up in the final BOQ:

1. Reset the database and add sample costs:
   ```bash
   python run_hard_coded_boq.py --reset-db --add-sample-costs
   ```

2. Check the database directly:
   ```bash
   python3 -c "import sqlite3; conn = sqlite3.connect('~/AppData/Roaming/BOQProcessor/master_data.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM interior_items WHERE material_cost > 0'); print(cursor.fetchone()[0])"
   ```

3. Verify the sheet formats by running the test script:
   ```bash
   python test_hard_coded.py
   ```