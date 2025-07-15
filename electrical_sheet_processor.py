#!/usr/bin/env python3
"""
Electrical sheet processor - handles electrical work sheets.
Updated to match new abstract methods and range-based approach.
"""

from typing import Dict, Any, List, Tuple
import re
from base_sheet_processor import BaseSheetProcessor

class ElectricalSheetProcessor(BaseSheetProcessor):
    """Processor for Electrical (EE) sheets"""
    
    @property
    def sheet_pattern(self) -> str:
        return 'ee'
    
    @property
    def header_row(self) -> int:
        return 7  # 0-based, row 8 in Excel
    
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
        return 'ee_items'
    
    def calculate_item_costs(self, master_item: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """
        Calculate costs for electrical items.
        Electrical logic: Both material and labor costs are multiplied by quantity
        """
        mat_cost = float(master_item.get('material_cost', 0))
        lab_cost = float(master_item.get('labor_cost', 0))
        
        # Electrical calculation: both material and labor * quantity
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
        """Find section structure (boundaries only) for electrical sheets - STUB IMPLEMENTATION"""
        # TODO: Implement proper electrical section structure detection
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
            
            # Look for 'Total' in code column or electrical total patterns
            if (code_text.lower() == 'total' or 
                'รวมรายการ' in name_text or 
                self._is_electrical_total_row(code_text, name_text)):
                
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
                
                self.logger.debug(f"Found electrical section '{section_id}' (rows {section_start_row}-{row_idx-1}) "
                               f"with {section_totals['item_count']} items, total cost: {section_totals['total_cost']}")
        
        # If no sections found, create a default main section
        if not sections:
            sections['MAIN_ELECTRICAL'] = {
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
        """Find the section ID and start row for electrical sheets"""
        code_col = self.column_mapping['code']
        name_col = self.column_mapping['name']
        
        # METHOD 1: Search upward for matching code (electrical sections)
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
                self._is_electrical_total_row(code_text, name_text)):
                section_header_row = i + 1
                code_cell = worksheet.cell(row=section_header_row, column=code_col).value
                section_code = str(code_cell).strip() if code_cell else ""
                if section_code:
                    return section_code, section_header_row + 1
        
        # FALLBACK: Use electrical section naming
        fallback_start = max(1, total_row - 20)
        return section_name_from_total or f"ELECTRICAL_{total_row}", fallback_start
    
    def _is_electrical_total_row(self, code_text: str, name_text: str) -> bool:
        """Check if row is an electrical total row"""
        combined_text = f"{code_text} {name_text}".lower()
        
        # Look for electrical-specific total indicators
        electrical_total_indicators = [
            'รวมรายการที่', 'รวมรายการ', 'total', 'รวม', 'subtotal',
            'electrical total', 'ee total'
        ]
        
        return any(indicator in combined_text for indicator in electrical_total_indicators)
    
    def _calculate_section_totals_from_range(self, worksheet, start_row: int, end_row: int) -> Dict[str, float]:
        """Calculate section totals for electrical items"""
        material_total = 0.0
        labor_total = 0.0
        total_cost = 0.0
        item_count = 0
        
        # Get column positions
        mat_col = self.column_mapping['material_cost']
        lab_col = self.column_mapping['labor_cost']
        total_col = self.column_mapping['total_cost']
        code_col = self.column_mapping['code']
        
        self.logger.debug(f"Calculating electrical totals for range {start_row}-{end_row}")
        
        # Sum up all items in the section range
        for row in range(start_row, end_row + 1):
            # Skip headers and empty rows
            code_cell = worksheet.cell(row=row, column=code_col).value
            code_text = str(code_cell).strip() if code_cell else ""
            
            # Skip section headers, empty rows, and electrical system headers
            if (not code_text or 
                code_text.lower() in ['total', 'electrical', 'ee'] or
                self._is_electrical_section_header(code_text)):
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
    
    def _is_electrical_section_header(self, code_text: str) -> bool:
        """Check if code looks like an electrical section header"""
        electrical_headers = [
            'panelboard', 'conduit', 'conductor', 'lighting', 'receptacle',
            'switch', 'outlet', 'fixture', 'wiring', 'electrical'
        ]
        
        code_lower = code_text.lower()
        return any(header in code_lower for header in electrical_headers)
    
    def write_markup_costs(self, worksheet, row: int, base_cost: float, markup_options: List[int], start_col: int) -> None:
        """Write markup costs for electrical items"""
        for i, markup_percent in enumerate(markup_options):
            markup_rate = self.markup_rates.get(markup_percent, 1.0)
            markup_cost = round(base_cost * (1 + markup_rate), 2)
            col_num = start_col + i
            
            try:
                worksheet.cell(row=row, column=col_num).value = markup_cost
                self.logger.debug(f"Wrote electrical markup {markup_percent}% = {markup_cost} to ({row}, {col_num})")
            except Exception as e:
                self.logger.error(f"Error writing electrical markup to ({row}, {col_num}): {e}")
    
    def add_sample_data(self) -> None:
        """Add sample data for electrical items"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table already has data
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.logger.debug(f"Table {self.table_name} already has {count} items")
                return
            
            # Add sample electrical items
            sample_items = [
                ('EE001', 'Cable Installation - 2.5mm²', 50, 30, 'M'),
                ('EE002', 'Conduit Installation - PVC 20mm', 25, 15, 'M'),
                ('EE003', 'Switch Installation - 1 Gang', 150, 100, 'EA'),
                ('EE004', 'Outlet Installation - 13A', 120, 80, 'EA'),
                ('EE005', 'Junction Box - 4x4', 80, 40, 'EA'),
                ('EE006', 'Panelboard - 12 Way', 2500, 800, 'EA'),
                ('EE007', 'Circuit Breaker - 32A', 300, 50, 'EA'),
                ('EE008', 'Lighting Fixture - LED 18W', 400, 150, 'EA'),
                ('EE009', 'Cable Tray - 300mm', 180, 120, 'M'),
                ('EE010', 'Grounding Rod - 2.4m', 200, 100, 'EA')
            ]
            
            for i, (code, name, material_cost, labor_cost, unit) in enumerate(sample_items):
                item_id = f"ee_sample_{i+1}"
                total_cost = material_cost + labor_cost
                
                cursor.execute(
                    f"INSERT INTO {self.table_name} (internal_id, code, name, material_cost, labor_cost, total_cost, unit) "
                    f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (item_id, code, name, material_cost, labor_cost, total_cost, unit)
                )
            
            conn.commit()
            self.logger.debug(f"Added {len(sample_items)} sample items to {self.table_name}")
    
    def ensure_costs_exist(self) -> None:
        """Ensure table has items with costs"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table has costs
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE material_cost > 0 OR labor_cost > 0")
            count = cursor.fetchone()[0]
            
            if count == 0:
                self.logger.debug(f"No costs found in {self.table_name}, adding sample costs")
                cursor.execute(f"UPDATE {self.table_name} SET material_cost = 200, labor_cost = 150, total_cost = 350")
                conn.commit()
                
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE material_cost > 0")
                updated = cursor.fetchone()[0]
                self.logger.debug(f"Added sample costs to {updated} items in {self.table_name}")