#!/usr/bin/env python3
"""
Interior sheet processor - handles interior construction sheets.
These sheets typically have a simpler structure with material and labor costs.
"""

from typing import Dict, Any, List, Tuple
import re
from base_sheet_processor import BaseSheetProcessor

class InteriorSheetProcessor(BaseSheetProcessor):
    """Processor for Interior (INT) sheets"""
    
    @property
    def sheet_pattern(self) -> str:
        return 'int'
    
    @property
    def header_row(self) -> int:
        return 9  # 0-based, row 10 in Excel
    
    @property
    def column_mapping(self) -> Dict[str, int]:
        return {
            'code': 2,          # Column B
            'name': 3,          # Column C
            'quantity': 4,      # Column D
            'unit': 5,          # Column E
            'material_unit_cost': 6, # Column F
            'labor_unit_cost': 7,    # Column G
            'total_unit_cost': 8,    # Column H
            "total_cost": 9 #Column I

        }
    
    @property
    def table_name(self) -> str:
        return 'interior_items'
    
    def calculate_item_costs(self, master_item: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """
        Calculate costs for interior items.
        Interior logic: Material cost * quantity + Labor cost (not multiplied)
        """
        mat_cost = float(master_item.get('material_cost', 0))
        lab_cost = float(master_item.get('labor_cost', 0))
        

        material_unit_total = mat_cost 
        labor_unit_total = lab_cost   
        total_unit_cost = material_unit_total + labor_unit_total
        total_cost = total_unit_cost * quantity
        
        return {
            'material_unit_cost': mat_cost,
            'labor_unit_cost': lab_cost,
            'material_unit_total': material_unit_total,
            'labor_unit_total': labor_unit_total,
            'total_unit_cost': total_unit_cost,
            'total_cost': total_cost
        }
    
    def find_section_boundaries(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """
        Find section boundaries for interior sheets and calculate totals using range-based approach.
        Interior sheets often have simple 'Total' rows marking sections.
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
            
            # Look for 'Total' in code column
            if code_text.lower() == 'total':
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
                    'material_unit_sum': section_totals['material_unit_sum'],
                    'labor_unit_sum': section_totals['labor_unit_sum'],
                    'total_unit_sum': section_totals['total_unit_sum'],
                    'total_sum': section_totals['total_sum'],
                    'item_count': section_totals['item_count']
                }
                
                self.logger.info(f"Found interior section '{section_id}' (rows {section_start_row}-{row_idx-1}) "
                               f"with {section_totals['item_count']} items, total cost: {section_totals['total_cost']}")
        
        # If no sections found, create a default main section
        if not sections:
            sections['MAIN_SECTION'] = {
                'total_row': None,
                'start_row': 1,
                'end_row': max_row,
                'material_unit_sum': 0,
                'labor_unit_sum': 0,
                'total_unit_sum': 0,
                'total_sum': 0,
                'item_count': 0
            }
        
        return sections
    
    def _find_section_info(self, worksheet, total_row: int, section_name_from_total: str) -> Tuple[str, int]:
        """
        Find the section ID and start row for a total row using two methods:
        1. Search upward for code that matches the section name from total row
        2. Find previous total row, section header = previous_total + 1
        
        Returns: (section_id, section_start_row)
        """
        code_col = self.column_mapping['code']
        
        # METHOD 1: Search upward for matching code
        # Total row has: Code="Total", Name="งานป้าย"
        # Look for: Code="งานป้าย" (section header)
        if section_name_from_total:
            for i in range(total_row - 1, max(1, total_row - 50), -1):
                code_cell = worksheet.cell(row=i, column=code_col).value
                code_text = str(code_cell).strip() if code_cell else ""
                
                if code_text == section_name_from_total:
                    return section_name_from_total, i + 1  # (section_id, start_row after header)
        
        # METHOD 2: Find previous total, section header = previous_total + 1
        for i in range(total_row - 1, max(1, total_row - 100), -1):
            check_code_cell = worksheet.cell(row=i, column=code_col).value
            check_code_text = str(check_code_cell).strip() if check_code_cell else ""
            
            # Found another total row
            if check_code_text.lower() == 'total':
                section_header_row = i + 1
                code_cell = worksheet.cell(row=section_header_row, column=code_col).value
                section_code = str(code_cell).strip() if code_cell else ""
                if section_code:
                    return section_code, section_header_row + 1  # (section_id, start_row after header)
        
        # FALLBACK: Use the name from total row and estimate start
        fallback_start = max(1, total_row - 20)
        return section_name_from_total or f"FALLBACK{total_row}", fallback_start
    
    def _calculate_section_totals_from_range(self, worksheet, start_row: int, end_row: int) -> Dict[str, float]:
        """
        Calculate section totals by iterating through the range and summing up all item costs.
        This is more reliable than accumulation-based approach.
        """
        material_unit_cost_sum = 0.0
        labor_unit_cost_sum = 0.0
        total_unit_cost_sum = 0.0
        total_cost_sum = 0.0
        item_count = 0
        
        # Get column positions
        mat_unit_col = self.column_mapping['material_unit_cost']
        lab_unit_col = self.column_mapping['labor_unit_cost']
        total_unit_col = self.column_mapping['total_unit_cost']
        total_col = self.column_mapping['total_cost']
        code_col = self.column_mapping['code']
        
        self.logger.debug(f"Calculating totals for range {start_row}-{end_row}")
        
        # Sum up all items in the section range
        for row in range(start_row, end_row + 1):
            # Skip if this looks like a header or empty row
            code_cell = worksheet.cell(row=row, column=code_col).value
            code_text = str(code_cell).strip() if code_cell else ""
            
            # Skip section headers and empty rows
            if not code_text or code_text.lower() in ['total', '']:
                continue
            
            # Get costs from each row
            mat_unit_cell = worksheet.cell(row=row, column=mat_unit_col).value
            lab_unit_cell = worksheet.cell(row=row, column=lab_unit_col).value
            total_unit_cell = worksheet.cell(row=row, column=total_unit_col).value
            total_cell = worksheet.cell(row=row, column=total_col).value

            
            # Convert to float safely
            mat_unit_cost = self._safe_float(mat_unit_cell)
            lab_unit_cost = self._safe_float(lab_unit_cell)
            total_unit_cost = self._safe_float(total_unit_cell)
            total_cost = self._safe_float(total_cell)
            
            # Only add if this row has actual costs (not header or empty rows)
            if mat_unit_cost > 0 or lab_unit_cost > 0 or total_unit_cost > 0 or total_cost > 0:
                material_unit_cost_sum += mat_unit_cost
                labor_unit_cost_sum += lab_unit_cost
                total_unit_cost_sum += total_unit_cost
                total_cost_sum += total_cost
                item_count += 1
                
                self.logger.debug(f"Row {row} ({code_text}): Mat unit={mat_unit_cost}, Lab uit={lab_unit_cost}, Total unit={total_unit_cost}, Total={total_cost}")
        
        return {
            'material_unit_sum': material_unit_cost_sum,
            'labor_unit_sum': labor_unit_cost_sum,
            'total_unit_sum': total_unit_cost_sum,
            'total_sum': total_cost_sum,
            'item_count': item_count
        }
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if value is None or value == '' or value == '-':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def write_section_totals(self, worksheet, sections: Dict[str, Dict[str, Any]], 
                           markup_options: List[int], start_markup_col: int) -> None:
        """
        Write pre-calculated section totals to worksheet.
        Totals are already calculated in find_section_boundaries using range-based approach.
        """
        for section_id, section_data in sections.items():
            total_row = section_data.get('total_row')
            if not total_row:
                continue
            
            self.logger.info(f"Writing pre-calculated totals for '{section_id}' at row {total_row}")
            
            # Get pre-calculated sums
            material_unit_sum = section_data['material_unit_sum']
            labor_unit_sum = section_data['labor_unit_sum']
            total_unit_sum = section_data['total_unit_sum']
            total_sum = section_data["total_sum"]
            item_count = section_data['item_count']

             
            self.logger.info(f"Section '{section_id}': {item_count} items, "
                           f"Material unit={material_unit_sum}, Labor unit={labor_unit_sum}, Total unit={total_unit_sum}, Total sum={total_sum}")
            
            # Write basic totals
            mat_unit_col = self.column_mapping['material_unit_cost']
            lab_unit_col = self.column_mapping['labor_unit_cost']
            total_unit_col = self.column_mapping['total_unit_cost']
            total_col = self.column_mapping['total_cost']
            
            try:
                worksheet.cell(row=total_row, column=mat_unit_col).value = material_unit_sum
                worksheet.cell(row=total_row, column=lab_unit_col).value = labor_unit_sum
                worksheet.cell(row=total_row, column=total_unit_col).value = total_unit_sum
                worksheet.cell(row=total_row, column=total_col).value = total_sum
                
                # Write markup totals
                self.write_markup_costs(worksheet, total_row, total_sum, 
                                      markup_options, start_markup_col)
                
                self.logger.info(f"Section '{section_id}' totals written successfully")
                
            except Exception as e:
                self.logger.error(f"Error writing section totals for '{section_id}': {e}")
    
    def write_markup_costs(self, worksheet, row: int, base_cost: float, markup_options: List[int], start_col: int) -> None:
        """Write markup costs for interior items"""
        for i, markup_percent in enumerate(markup_options):
            markup_rate = self.markup_rates.get(markup_percent, 1.0)
            markup_cost = round(base_cost * (1 + markup_rate), 2)
            col_num = start_col + i
            
            try:
                worksheet.cell(row=row, column=col_num).value = markup_cost
                self.logger.debug(f"Wrote markup {markup_percent}% = {markup_cost} to ({row}, {col_num})")
            except Exception as e:
                self.logger.error(f"Error writing markup to ({row}, {col_num}): {e}")
    
    
    
    def add_sample_data(self) -> None:
        """Add sample data for interior items"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table already has data
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.logger.info(f"Table {self.table_name} already has {count} items")
                return
            
            # Add sample interior items
            sample_items = [
                ('INT001', 'Painting - Interior Wall', 150, 100, 'SQM'),
                ('INT002', 'Tile Installation - Floor', 300, 200, 'SQM'),
                ('INT003', 'Ceiling Installation - Gypsum', 250, 150, 'SQM'),
                ('INT004', 'Door Installation - Wooden', 800, 400, 'EA'),
                ('INT005', 'Window Installation - Aluminum', 600, 300, 'EA'),
                ('INT006', 'Flooring - Laminate', 400, 100, 'SQM'),
                ('INT007', 'Cabinet Installation - Kitchen', 1200, 800, 'EA'),
                ('INT008', 'Partition - Drywall', 200, 120, 'SQM'),
                ('INT009', 'Molding - Decorative', 80, 40, 'LM'),
                ('INT010', 'Lighting Fixture - Ceiling', 350, 150, 'EA')
            ]
            
            for i, (code, name, material_cost, labor_cost, unit) in enumerate(sample_items):
                item_id = f"int_sample_{i+1}"
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
                cursor.execute(f"UPDATE {self.table_name} SET material_cost = 300, labor_cost = 200, total_cost = 500")
                conn.commit()
                
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE material_cost > 0")
                updated = cursor.fetchone()[0]
                self.logger.info(f"Added sample costs to {updated} items in {self.table_name}")