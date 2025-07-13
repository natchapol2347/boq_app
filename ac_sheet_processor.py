#!/usr/bin/env python3
"""
Air Conditioning sheet processor - handles AC system sheets.
Updated to match new abstract methods and range-based approach.
"""

from typing import Dict, Any, List, Tuple
import re
from base_sheet_processor import BaseSheetProcessor

class ACSheetProcessor(BaseSheetProcessor):
    """Processor for Air Conditioning (AC) sheets"""
    
    @property
    def sheet_pattern(self) -> str:
        return 'ac'
    
    @property
    def header_row(self) -> int:
        return 5  # 0-based, row 6 in Excel
    
    @property
    def column_mapping(self) -> Dict[str, int]:
        return {
            'code': 2,          # Column B
            'name': 3,          # Column C
            'unit': 6,          # Column F
            'quantity': 7,      # Column G
            'material_cost': 8, # Column H
            'labor_cost': 10,   # Column J
            'total_cost': 12    # Column L
        }
    
    @property
    def table_name(self) -> str:
        return 'ac_items'
    
    def calculate_item_costs(self, master_item: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """
        Calculate costs for AC items.
        AC logic: Both material and labor costs are multiplied by quantity
        """
        mat_cost = float(master_item.get('material_cost', 0))
        lab_cost = float(master_item.get('labor_cost', 0))
        
        # AC calculation: both material and labor * quantity
        material_total = mat_cost * quantity
        labor_total = lab_cost * quantity
        total_cost = material_total + labor_total
        
        return {
            'material_unit_cost': mat_cost,
            'labor_unit_cost': lab_cost,
            'material_total': material_total,
            'labor_total': labor_total,
            'total_cost': total_cost
        }
    
    def find_section_structure(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """Find section structure (boundaries only) for AC sheets - STUB IMPLEMENTATION"""
        # TODO: Implement proper AC section structure detection
        # For now, return a single main section to avoid errors
        return {
            'MAIN_SECTION': {
                'total_row': None,
                'start_row': 1,
                'end_row': max_row,
                'section_id': 'MAIN_SECTION'
            }
        }
    
    def find_section_boundaries(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """
        DEPRECATED: Use find_section_structure() instead. Kept for backward compatibility.
        """
        sections = {}
        name_col = self.column_mapping['name']
        code_col = self.column_mapping['code']
        
        # Scan for total rows
        for row_idx in range(1, max_row + 1):
            code_cell = worksheet.cell(row=row_idx, column=code_col).value
            name_cell = worksheet.cell(row=row_idx, column=name_col).value
            
            code_text = str(code_cell).strip() if code_cell else ""
            name_text = str(name_cell).strip() if name_cell else ""
            
            # Look for AC total patterns
            if (code_text.lower() == 'total' or 
                self._is_ac_total_row(code_text, name_text)):
                
                # Get section info (ID and start row)
                section_id, section_start_row = self._find_section_info(worksheet, row_idx, name_text)
                
                # Calculate section totals using range-based approach
                section_totals = self._calculate_section_totals_from_range(
                    worksheet, section_start_row, row_idx - 1
                )
                
                sections[section_id] = {
                    'total_row': row_idx,
                    'start_row': section_start_row,
                    'end_row': row_idx - 1,
                    'material_total': section_totals['material_total'],
                    'labor_total': section_totals['labor_total'],
                    'total_cost': section_totals['total_cost'],
                    'item_count': section_totals['item_count']
                }
                
                self.logger.info(f"Found AC section '{section_id}' (rows {section_start_row}-{row_idx-1}) "
                               f"with {section_totals['item_count']} items, total cost: {section_totals['total_cost']}")
        
        # If no sections found, create a default main section
        if not sections:
            sections['MAIN_AC'] = {
                'total_row': None,
                'start_row': 1,
                'end_row': max_row,
                'material_total': 0,
                'labor_total': 0,
                'total_cost': 0,
                'item_count': 0
            }
        
        return sections
    
    def _find_section_info(self, worksheet, total_row: int, section_name_from_total: str) -> Tuple[str, int]:
        """Find the section ID and start row for AC sheets"""
        code_col = self.column_mapping['code']
        name_col = self.column_mapping['name']
        
        # METHOD 1: Search upward for matching code
        if section_name_from_total:
            for i in range(total_row - 1, max(1, total_row - 50), -1):
                code_cell = worksheet.cell(row=i, column=code_col).value
                code_text = str(code_cell).strip() if code_cell else ""
                
                if code_text == section_name_from_total:
                    return section_name_from_total, i + 1
        
        # METHOD 2: Find previous total, section header = previous_total + 1
        for i in range(total_row - 1, max(1, total_row - 100), -1):
            code_cell = worksheet.cell(row=i, column=code_col).value
            name_cell = worksheet.cell(row=i, column=name_col).value
            
            code_text = str(code_cell).strip() if code_cell else ""
            name_text = str(name_cell).strip() if name_cell else ""
            
            # Found another total row
            if (code_text.lower() == 'total' or 
                self._is_ac_total_row(code_text, name_text)):
                section_header_row = i + 1
                code_cell = worksheet.cell(row=section_header_row, column=code_col).value
                section_code = str(code_cell).strip() if code_cell else ""
                if section_code:
                    return section_code, section_header_row + 1
        
        # FALLBACK: Use AC section naming
        fallback_start = max(1, total_row - 20)
        return section_name_from_total or f"AC_{total_row}", fallback_start
    
    def _is_ac_total_row(self, code_text: str, name_text: str) -> bool:
        """Check if row is an AC total row"""
        combined_text = f"{code_text} {name_text}".lower()
        
        # Look for AC-specific total indicators
        ac_total_indicators = [
            'รวมรายการ', 'total', 'รวม', 'subtotal', 'sum',
            'ac total', 'air conditioning total'
        ]
        
        return any(indicator in combined_text for indicator in ac_total_indicators)
    
    def _calculate_section_totals_from_range(self, worksheet, start_row: int, end_row: int) -> Dict[str, float]:
        """Calculate section totals for AC items"""
        material_total = 0.0
        labor_total = 0.0
        total_cost = 0.0
        item_count = 0
        
        # Get column positions
        mat_col = self.column_mapping['material_cost']
        lab_col = self.column_mapping['labor_cost']
        total_col = self.column_mapping['total_cost']
        code_col = self.column_mapping['code']
        
        self.logger.debug(f"Calculating AC totals for range {start_row}-{end_row}")
        
        # Sum up all items in the section range
        for row in range(start_row, end_row + 1):
            # Skip headers and empty rows
            code_cell = worksheet.cell(row=row, column=code_col).value
            code_text = str(code_cell).strip() if code_cell else ""
            
            # Skip section headers, empty rows, and AC system headers
            if (not code_text or 
                code_text.lower() in ['total', 'ac', 'air conditioning'] or
                self._is_ac_section_header(code_text)):
                continue
            
            # Get costs from each row
            mat_cell = worksheet.cell(row=row, column=mat_col).value
            lab_cell = worksheet.cell(row=row, column=lab_col).value
            total_cell = worksheet.cell(row=row, column=total_col).value
            
            # Convert to float safely
            mat_cost = self._safe_float(mat_cell)
            lab_cost = self._safe_float(lab_cell)
            row_total = self._safe_float(total_cell)
            
            # Only add if this row has actual costs
            if mat_cost > 0 or lab_cost > 0 or row_total > 0:
                material_total += mat_cost
                labor_total += lab_cost
                total_cost += row_total
                item_count += 1
                
                self.logger.debug(f"Row {row} ({code_text}): Mat={mat_cost}, Lab={lab_cost}, Total={row_total}")
        
        return {
            'material_total': material_total,
            'labor_total': labor_total,
            'total_cost': total_cost,
            'item_count': item_count
        }
    
    def _is_ac_section_header(self, code_text: str) -> bool:
        """Check if code looks like an AC section header"""
        ac_headers = [
            'ac', 'air conditioning', 'hvac', 'cooling', 'split unit',
            'ducting', 'diffuser', 'thermostat', 'refrigerant'
        ]
        
        code_lower = code_text.lower()
        return any(header in code_lower for header in ac_headers)
    
    def write_markup_costs(self, worksheet, row: int, base_cost: float, markup_options: List[int], start_col: int) -> None:
        """Write markup costs for AC items"""
        for i, markup_percent in enumerate(markup_options):
            markup_rate = self.markup_rates.get(markup_percent, 1.0)
            markup_cost = round(base_cost * (1 + markup_rate), 2)
            col_num = start_col + i
            
            try:
                worksheet.cell(row=row, column=col_num).value = markup_cost
                self.logger.debug(f"Wrote AC markup {markup_percent}% = {markup_cost} to ({row}, {col_num})")
            except Exception as e:
                self.logger.error(f"Error writing AC markup to ({row}, {col_num}): {e}")
    
    def add_sample_data(self) -> None:
        """Add sample data for AC items"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table already has data
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.logger.info(f"Table {self.table_name} already has {count} items")
                return
            
            # Add sample AC items
            sample_items = [
                ('AC001', 'Split Unit - 18,000 BTU', 15000, 3000, 'EA'),
                ('AC002', 'Ducting - Flexible 6 inch', 120, 80, 'M'),
                ('AC003', 'Diffuser - 4 Way 600x600', 800, 200, 'EA'),
                ('AC004', 'Thermostat - Digital', 1200, 300, 'EA'),
                ('AC005', 'Refrigerant Piping - 1/2 inch', 200, 100, 'M'),
                ('AC006', 'Insulation - Pipe Wrap', 50, 30, 'M'),
                ('AC007', 'Condensate Drain - PVC', 80, 40, 'M'),
                ('AC008', 'Air Filter - Washable', 300, 50, 'EA'),
                ('AC009', 'Remote Control - AC Unit', 500, 0, 'EA'),
                ('AC010', 'Installation Kit - Wall Mount', 800, 400, 'EA')
            ]
            
            for i, (code, name, material_cost, labor_cost, unit) in enumerate(sample_items):
                item_id = f"ac_sample_{i+1}"
                total_cost = material_cost + labor_cost
                
                cursor.execute(
                    f"INSERT INTO {self.table_name} (internal_id, code, name, material_cost, labor_cost, total_cost, unit) "
                    f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (item_id, code, name, material_cost, labor_cost, total_cost, unit)
                )
            
            conn.commit()
            self.logger.info(f"Added {len(sample_items)} sample items to {self.table_name}")
    
    def ensure_costs_exist(self) -> None:
        """Ensure table has items with costs"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table has costs
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE material_cost > 0 OR labor_cost > 0")
            count = cursor.fetchone()[0]
            
            if count == 0:
                self.logger.info(f"No costs found in {self.table_name}, adding sample costs")
                cursor.execute(f"UPDATE {self.table_name} SET material_cost = 800, labor_cost = 400, total_cost = 1200")
                conn.commit()
                
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE material_cost > 0")
                updated = cursor.fetchone()[0]
                self.logger.info(f"Added sample costs to {updated} items in {self.table_name}")