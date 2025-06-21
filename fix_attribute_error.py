"""
Quick fix for the attribute error: 'BOQProcessor' object has no attribute 'find_header_row'
"""

import os

def fix_attribute_error():
    """Fix the attribute error by ensuring find_header_row is properly defined as a method of BOQProcessor"""
    
    # First check if main_final.py exists
    if os.path.exists("main_final.py"):
        input_file = "main_final.py"
        output_file = "main_fixed_final.py"
    else:
        input_file = "main.py"
        output_file = "main_fixed.py"
    
    print(f"Fixing attribute error in {input_file}...")
    
    with open(input_file, "r") as f:
        content = f.read()
    
    # Check if find_header_row is already a method
    if "def find_header_row(self, raw_df):" in content:
        print("Method already exists but might be defined incorrectly")
        
        # Just in case it's defined but not as a method, find and replace
        old_method = "def find_header_row(self, raw_df):"
        old_method_end = "return None"
        
        # Find the complete method
        start_pos = content.find(old_method)
        end_pos = content.find(old_method_end, start_pos) + len(old_method_end)
        
        # Extract the method code
        method_code = content[start_pos:end_pos]
        
        # Make sure it's indented correctly (4 spaces)
        if not method_code.startswith("    def"):
            fixed_method = "    " + method_code.replace("\n", "\n    ")
            content = content.replace(method_code, fixed_method)
            print("Fixed method indentation")
    else:
        # Method doesn't exist, add it
        print("Method not found, adding it")
        
        # Create the method
        header_method = """    def find_header_row(self, raw_df):
        \"\"\"Find the row containing column headers\"\"\"
        header_indicators = ['ลำดับ', 'code', 'รายการ', 'จำนวน', 'หน่วย']
        
        for i in range(min(15, len(raw_df))):
            row = raw_df.iloc[i].astype(str).str.lower()
            matches = sum(1 for indicator in header_indicators 
                         if any(indicator in cell for cell in row if pd.notna(cell)))
            if matches >= 3:
                return i
        return None"""
        
        # Find a good place to insert it (after _prepare_dataframe_for_master method)
        insert_marker = "def load_data_from_excel_to_db(self, file_path):"
        insert_pos = content.find(insert_marker)
        
        if insert_pos != -1:
            content = content[:insert_pos] + header_method + "\n\n    " + content[insert_pos:]
            print("Added find_header_row method")
        else:
            print("Could not find a good place to insert the method")
            return False
    
    # Also check for any call to self.find_header_row and make sure it exists
    if "header_row = self.find_header_row(raw_df)" in content:
        print("Method is called correctly as self.find_header_row")
    else:
        # Look for incorrect calls like find_header_row(raw_df) without self
        content = content.replace("header_row = find_header_row(raw_df)", 
                                "header_row = self.find_header_row(raw_df)")
        print("Fixed incorrect method calls")
    
    # Make sure pandas is imported
    if "import pandas as pd" not in content:
        content = "import pandas as pd\n" + content
        print("Added pandas import")
    
    # Save the fixed file
    with open(output_file, "w") as f:
        f.write(content)
    
    print(f"Fixed file saved as {output_file}")
    return True

if __name__ == "__main__":
    fix_attribute_error()