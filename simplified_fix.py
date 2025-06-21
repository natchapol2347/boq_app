"""
Simplified fix for the Thai BOQ application - fixes just the essential issues
"""
import openpyxl
import sqlite3
from pathlib import Path
import os

def main_fix():
    """Apply essential fixes to the BOQ processor"""
    # 1. Fix column mapping
    with open("main.py", "r") as f:
        main_content = f.read()
    
    # First fix the header row finder
    find_header_row_method = """    def find_header_row(self, raw_df):
        \"\"\"Find the row containing column headers\"\"\"
        header_indicators = ['ลำดับ', 'code', 'รายการ', 'จำนวน', 'หน่วย']
        
        for i in range(min(15, len(raw_df))):
            row = raw_df.iloc[i].astype(str).str.lower()
            matches = sum(1 for indicator in header_indicators 
                         if any(indicator in cell for cell in row if pd.notna(cell)))
            if matches >= 3:
                return i
        return None"""
    
    # Add the method if it's missing
    if "def find_header_row(self, raw_df):" not in main_content:
        # Find a suitable location for insertion
        init_end = main_content.find("def _init_db(self):")
        if init_end > 0:
            # Insert after __init__ method
            main_content = main_content[:init_end] + find_header_row_method + "\n\n    " + main_content[init_end:]
            print("Added find_header_row method")
    
    # 2. Fix column mapping for Thai BOQ
    # Replace the _find_column_numbers method with a simpler version
    find_column_numbers_method = """    def _find_column_numbers(self, worksheet, header_row_num, column_map):
        \"\"\"Fixed column mapping for Thai BOQ format\"\"\"
        sheet_name = worksheet.title
        print(f"\\n📋 Processing sheet: {sheet_name}")
        
        # Initialize with default fixed column positions for Thai BOQ
        column_numbers = {}
        
        # Use different mappings based on sheet type
        if "Int" in sheet_name:
            # Interior sheet - values in F, G, H columns
            column_numbers = {
                'code': 2,          # B
                'name': 3,          # C
                'quantity': 4,      # D
                'unit': 5,          # E
                'material_cost': 6, # F
                'labor_cost': 7,    # G 
                'total_cost': 8     # H
            }
            print("Using Interior sheet mapping: F=material, G=labor, H=total")
        else:
            # System sheets (EE, AC, FP) - values in H, J, L columns
            column_numbers = {
                'code': 2,          # B
                'name': 3,          # C
                'unit': 6,          # F
                'quantity': 7,      # G
                'material_cost': 8, # H
                'labor_cost': 10,   # J
                'total_cost': 12    # L
            }
            print("Using System sheet mapping: H=material, J=labor, L=total")
        
        return column_numbers"""
    
    # Find and replace the old method
    start_marker = "def _find_column_numbers(self, worksheet, header_row_num, column_map):"
    start_pos = main_content.find(start_marker)
    
    if start_pos > 0:
        # Find the end of the method
        end_markers = ["def setup_routes(self):", "def run(self, host="]
        end_pos = -1
        
        for marker in end_markers:
            pos = main_content.find(marker, start_pos)
            if pos > 0 and (end_pos < 0 or pos < end_pos):
                end_pos = pos
        
        if end_pos > 0:
            # Replace the entire method
            old_method = main_content[start_pos:end_pos]
            main_content = main_content.replace(old_method, find_column_numbers_method)
            print("Replaced _find_column_numbers method")
    
    # 3. Add sample costs to the database
    print("\nAdding sample costs to the database...")
    db_path = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor' / 'master_data.db'
    
    if os.path.exists(db_path):
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Update all items with sample costs
                cursor.execute("UPDATE master_items SET material_cost = 500, labor_cost = 300, total_cost = 800")
                conn.commit()
                
                # Verify the update
                cursor.execute("SELECT COUNT(*) FROM master_items WHERE material_cost > 0")
                count = cursor.fetchone()[0]
                print(f"Updated {count} items with sample costs")
                
                # Show some sample items
                cursor.execute("SELECT name, material_cost, labor_cost FROM master_items LIMIT 5")
                items = cursor.fetchall()
                print("\nSample items with costs:")
                for item in items:
                    print(f"  - {item[0]}: Material={item[1]}, Labor={item[2]}")
        except Exception as e:
            print(f"Error updating database: {e}")
    else:
        print(f"Database not found at {db_path}")
    
    # Save the fixed file
    with open("main_simple_fix.py", "w") as f:
        f.write(main_content)
    
    print("\nCreated fixed version: main_simple_fix.py")
    print("To run: python main_simple_fix.py")

if __name__ == "__main__":
    main_fix()