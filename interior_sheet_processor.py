#!/usr/bin/env python3
"""
Interior sheet processor - handles interior construction sheets.
These sheets typically have a simpler structure with material and labor costs.
"""

from typing import Dict, Any, List
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
            'material_cost': 6, # Column F
            'labor_cost': 7,    # Column G
            'total_cost': 8     # Column H
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
        
        # Interior calculation: material * quantity + labor (fixed)
        material_total = mat_cost * quantity
        labor_total = lab_cost  # Labor is NOT multiplied by quantity
        total_cost = material_total + labor_total
        
        return {
            'material_unit_cost': mat_cost,
            'labor_unit_cost': lab_cost,
            'material_total': material_total,
            'labor_total': labor_total,
            'total_cost': total_cost
        }
    
    def find_section_boundaries(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """
        Find section boundaries for interior sheets.
        Interior sheets often have simple 'Total' rows marking sections.
        """
        sections = {}
        name_col = self.column_mapping['name']
        code_col = self.column_mapping['code']
        
        # Scan for total rows
        for row_idx in range(1, max_row + 1):
            # Check both code and name columns for 'Total'
            code_cell = worksheet.cell(row=row_idx, column=code_col).value
            name_cell = worksheet.cell(row=row_idx, column=name_col).value
            
            code_text = str(code_cell).strip() if code_cell else ""
            name_text = str(name_cell).strip() if name_cell else ""
            
            # Look for 'Total' in either column
            is_total_row = False
            section_id = None
            
            if code_text.lower() == 'total':
                is_total_row = True
                section_id = self._find_section_title_for_total(worksheet, row_idx, name_col)
            elif name_text.lower() == 'total':
                is_total_row = True
                section_id = self._find_section_title_for_total(worksheet, row_idx, name_col)
            
            if is_total_row:
                if not section_id:
                    section_id = f"SECTION_{row_idx}"
                
                sections[section_id] = {
                    'total_row': row_idx,
                    'material_total': 0,
                    'labor_total': 0,
                    'total_cost': 0,
                    'item_rows': []
                }
                
                self.logger.info(f"Found interior total row for section '{section_id}' at row {row_idx}")
        
        # If no sections found, create a default main section
        if not sections:
            sections['MAIN_SECTION'] = {
                'total_row': None,
                'material_total': 0,
                'labor_total': 0,
                'total_cost': 0,
                'item_rows': []
            }
        
        return sections
    
    def _find_section_title_for_total(self, worksheet, total_row: int, name_col: int) -> str:
        """Find the section title for a total row by looking upward"""
        # Look for a section header above the total row
        for i in range(total_row - 1, max(1, total_row - 20), -1):
            cell_value = worksheet.cell(row=i, column=name_col).value
            if not cell_value:
                continue
            
            cell_text = str(cell_value).strip()
            
            # Skip if it's another total row
            if 'total' in cell_text.lower() or 'รวม' in cell_text.lower():
                continue
            
            # Check if this looks like a section header
            if self._is_section_header(cell_text, worksheet, i):
                return cell_text
        
        return f"SECTION_{total_row}"
    
    def _is_section_header(self, text: str, worksheet, row: int) -> bool:
        """Determine if a text looks like a section header"""
        # Section headers are typically:
        # - All caps or title case
        # - Don't contain hyphens (items usually do)
        # - Don't have numeric values in other columns
        
        if len(text) < 3:
            return False
        
        if '-' in text and not text.isupper():
            return False
        
        # Check if row has numeric values (items usually do, headers don't)
        has_numbers = False
        for col in range(1, worksheet.max_column + 1):
            try:
                val = worksheet.cell(row=row, column=col).value
                if isinstance(val, (int, float)) and val > 0:
                    has_numbers = True
                    break
            except:
                pass
        
        # Headers typically don't have numbers
        return not has_numbers
    
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
    
    def assign_item_to_section(self, item_row: int, sections: Dict[str, Dict[str, Any]]) -> str:
        """Assign an item to the appropriate section"""
        # For interior sheets, find the next total row below this item
        closest_section = None
        closest_total_row = float('inf')
        
        for section_id, section_data in sections.items():
            total_row = section_data.get('total_row')
            if total_row and item_row < total_row < closest_total_row:
                closest_total_row = total_row
                closest_section = section_id
        
        # If no section found, use main section
        if not closest_section:
            if 'MAIN_SECTION' not in sections:
                sections['MAIN_SECTION'] = {
                    'total_row': None,
                    'material_total': 0,
                    'labor_total': 0,
                    'total_cost': 0,
                    'item_rows': []
                }
            closest_section = 'MAIN_SECTION'
        
        return closest_section
    
    def update_section_totals(self, sections: Dict[str, Dict[str, Any]], 
                            section_id: str, costs: Dict[str, float], item_row: int) -> None:
        """Update section totals with item costs"""
        if section_id not in sections:
            return
        
        section = sections[section_id]
        section['material_total'] += costs['material_total']
        section['labor_total'] += costs['labor_total']
        section['total_cost'] += costs['total_cost']
        section['item_rows'].append(item_row)
        
        self.logger.debug(f"Updated section '{section_id}' totals: "
                         f"Material={section['material_total']}, "
                         f"Labor={section['labor_total']}, "
                         f"Total={section['total_cost']}")
    
    def write_section_totals(self, worksheet, sections: Dict[str, Dict[str, Any]], 
                           markup_options: List[int], start_markup_col: int) -> None:
        """Write section totals to worksheet"""
        for section_id, section_data in sections.items():
            total_row = section_data.get('total_row')
            if not total_row:
                continue
            
            self.logger.info(f"Writing section totals for '{section_id}' at row {total_row}")
            
            # Write basic totals
            mat_col = self.column_mapping['material_cost']
            lab_col = self.column_mapping['labor_cost']
            total_col = self.column_mapping['total_cost']
            
            try:
                worksheet.cell(row=total_row, column=mat_col).value = section_data['material_total']
                worksheet.cell(row=total_row, column=lab_col).value = section_data['labor_total']
                worksheet.cell(row=total_row, column=total_col).value = section_data['total_cost']
                
                # Write markup totals
                self.write_markup_costs(worksheet, total_row, section_data['total_cost'], 
                                      markup_options, start_markup_col)
                
                self.logger.info(f"Section '{section_id}' totals written successfully")
                
            except Exception as e:
                self.logger.error(f"Error writing section totals for '{section_id}': {e}")
    
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