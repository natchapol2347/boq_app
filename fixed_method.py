"""
This file contains the find_header_row method that was missing from BOQProcessor
"""

def find_header_row(raw_df):
    """Find the row containing column headers"""
    header_indicators = ['ลำดับ', 'code', 'รายการ', 'จำนวน', 'หน่วย']
    
    for i in range(min(15, len(raw_df))):
        row = raw_df.iloc[i].astype(str).str.lower()
        matches = sum(1 for indicator in header_indicators 
                     if any(indicator in cell for cell in row if pd.notna(cell)))
        if matches >= 3:
            return i
    return None