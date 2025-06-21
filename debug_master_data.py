import pandas as pd
import sqlite3
import os
from pathlib import Path

def analyze_master_data():
    print("Analyzing master data file...")
    
    # File path
    master_file = os.path.join("master_data", "master.xlsx")
    
    if not os.path.exists(master_file):
        print(f"Error: Master file not found at {master_file}")
        return
    
    # Check the file
    print(f"Master file exists at {master_file}")
    
    # Initialize db connection to check if data was loaded
    db_path = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor' / 'master_data.db'
    if os.path.exists(db_path):
        print(f"Database exists at {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='master_items'")
            if cursor.fetchone():
                print("Table 'master_items' exists in database")
                
                # Check item count
                cursor.execute("SELECT COUNT(*) FROM master_items")
                count = cursor.fetchone()[0]
                print(f"Database contains {count} master items")
                
                # Check items with costs
                cursor.execute("SELECT COUNT(*) FROM master_items WHERE material_cost > 0 OR labor_cost > 0")
                items_with_costs = cursor.fetchone()[0]
                print(f"Items with costs: {items_with_costs} ({items_with_costs/count*100 if count > 0 else 0:.1f}%)")
                
                # Sample some items with costs
                cursor.execute("SELECT name, material_cost, labor_cost FROM master_items WHERE material_cost > 0 OR labor_cost > 0 LIMIT 5")
                sample_items = cursor.fetchall()
                
                print("Sample items with costs:")
                for item in sample_items:
                    print(f"  - {item[0][:40]}: Material: {item[1]}, Labor: {item[2]}")
            else:
                print("Table 'master_items' does not exist in database")
            
            conn.close()
            
        except Exception as e:
            print(f"Error accessing database: {e}")
    else:
        print(f"Database not found at {db_path}")
    
    # Read the Excel file
    try:
        excel_file = pd.ExcelFile(master_file)
        print(f"Excel file contains {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n----- Sheet: {sheet_name} -----")
            
            # Try to find header row
            raw_df = pd.read_excel(master_file, sheet_name=sheet_name, header=None, nrows=20)
            
            # Look for header row
            header_row = None
            header_indicators = ['ลำดับ', 'code', 'รายการ', 'จำนวน', 'หน่วย', 'รหัส', 'material', 'labor', 'วัสดุ', 'แรง']
            
            for i in range(min(15, len(raw_df))):
                row = raw_df.iloc[i].astype(str).str.lower()
                matches = sum(1 for indicator in header_indicators 
                             if any(indicator in str(cell).lower() for cell in row if pd.notna(cell)))
                if matches >= 3:
                    header_row = i
                    print(f"Header row found at row {i+1}")
                    print(f"Header content: {raw_df.iloc[i].tolist()}")
                    break
            
            if header_row is None:
                print("No header row found, using first row")
                header_row = 0
            
            # Read with proper header
            df = pd.read_excel(master_file, sheet_name=sheet_name, header=header_row)
            
            print(f"Sheet dimensions: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Column headers: {list(df.columns)}")
            
            # Detect potential cost columns
            cost_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(term in col_str for term in ['cost', 'ราคา', 'ค่า', 'material', 'labor', 'วัสดุ', 'แรง']):
                    cost_columns.append(col)
            
            print(f"Potential cost columns: {cost_columns}")
            
            # Check for non-zero values in cost columns
            if cost_columns:
                for col in cost_columns:
                    try:
                        numeric_col = pd.to_numeric(df[col], errors='coerce')
                        non_zero_count = (numeric_col > 0).sum()
                        print(f"Column '{col}' has {non_zero_count} non-zero values")
                        if non_zero_count > 0:
                            print(f"Sample values: {df[numeric_col > 0][col].head().tolist()}")
                    except Exception as e:
                        print(f"Error analyzing column {col}: {e}")
            
            # Sample some rows
            print("\nSample rows (first 5):")
            sample_rows = df.head(5)
            for i, row in sample_rows.iterrows():
                print(f"Row {i}:")
                for col in row.index:
                    print(f"  {col}: {row[col]}")
                    
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")
    
if __name__ == "__main__":
    analyze_master_data()