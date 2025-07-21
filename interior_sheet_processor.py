#!/usr/bin/env python3
"""
Interior sheet processor - handles interior construction sheets.
These sheets typically have a simpler structure with material and labor costs.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import uuid
from base_sheet_processor import BaseSheetProcessor
import sqlite3
from models.config_models import InteriorProcessorConfig


class InteriorSheetProcessor(BaseSheetProcessor):
    """Processor for Interior (INT) sheets"""
    
    def __init__(self, db_path: str, markup_rates: Dict[int, float], config: Optional[InteriorProcessorConfig] = None):
        super().__init__(db_path, markup_rates, config)
        # Use default values if no config provided
        if config is None:
            from models.config_models import ProcessorConfigs
            default_configs = ProcessorConfigs.get_default_config()
            self.config = default_configs.interior
    
    @property
    def sheet_pattern(self) -> str:
        return self.config.sheet_pattern
    
    @property
    def header_row(self) -> int:
        return self.config.header_row
    
    @property
    def column_mapping(self) -> Dict[str, int]:
        # Convert Pydantic model to dict for backward compatibility
        return {
            'code': self.config.column_mapping.code,
            'name': self.config.column_mapping.name,
            'quantity': self.config.column_mapping.quantity,
            'unit': self.config.column_mapping.unit,
            'material_unit_cost': self.config.column_mapping.material_unit_cost,
            'labor_unit_cost': self.config.column_mapping.labor_unit_cost,
            'total_unit_cost': self.config.column_mapping.total_unit_cost,
            'total_cost': self.config.column_mapping.total_cost
        }
    
    @property
    def table_name(self) -> str:
        return self.config.table_name
    
    def create_table(self, conn: sqlite3.Connection) -> None:
        """Create the database table for this sheet type"""
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                internal_id TEXT PRIMARY KEY, 
                code TEXT, 
                name TEXT NOT NULL,
                material_unit_cost REAL DEFAULT 0, 
                labor_unit_cost REAL DEFAULT 0, 
                total_unit_cost REAL DEFAULT 0,
                unit TEXT
            )
        ''')
        conn.commit()

    def sync_to_database(self, df: pd.DataFrame) -> None:
        """Sync processed data to database"""
        if df.empty:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing data
            conn.execute(f"DELETE FROM {self.table_name}")
            
            # Insert new data
            for _, row in df.iterrows():
                try:
                    conn.execute(
                        f"INSERT INTO {self.table_name} (internal_id, code, name, material_unit_cost, labor_unit_cost, total_unit_cost, unit) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            row['internal_id'],
                            row['code'],
                            row['name'],
                            row['material_unit_cost'],
                            row['labor_unit_cost'],
                            row['total_unit_cost'],
                            row.get('unit', '')
                        )
                    )
                except sqlite3.IntegrityError as e:
                    self.logger.error(f"Database integrity error: {e}")
                    continue
            
            conn.commit()
            self.logger.debug(f"Synchronized {len(df)} items to {self.table_name}")

    def extract_item_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Extract item data from a row using column mapping"""
        try:
            # Get values from fixed positions
            code_idx = self.column_mapping['code'] - 1  # Convert to 0-based
            name_idx = self.column_mapping['name'] - 1
            material_idx = self.column_mapping['material_unit_cost'] - 1
            labor_idx = self.column_mapping['labor_unit_cost'] - 1
            unit_idx = (self.column_mapping['unit'] - 1) if 'unit' in self.column_mapping else None
            
            # Extract values safely
            row_values = row.values
            if len(row_values) <= max(code_idx, name_idx, material_idx, labor_idx):
                return None
            
            # Extract values exactly as they appear in Excel (no cleaning)
            code = str(row_values[code_idx]) if code_idx < len(row_values) and pd.notna(row_values[code_idx]) else ''
            name = str(row_values[name_idx]) if name_idx < len(row_values) and pd.notna(row_values[name_idx]) else ''
            
            # Skip total/summary rows and completely empty rows (but don't modify data)
            if(self._is_skip_row(code) or (not name.strip() and not code.strip())):
                return None
            
            # Convert cost values only
            material_cost = self._safe_float_conversion(row_values[material_idx] if material_idx < len(row_values) else 0)
            labor_cost = self._safe_float_conversion(row_values[labor_idx] if labor_idx < len(row_values) else 0)
            unit = str(row_values[unit_idx]) if unit_idx is not None and unit_idx < len(row_values) and pd.notna(row_values[unit_idx]) else ''
            
            return {
                'internal_id': f"item_{uuid.uuid4().hex[:8]}",
                'code': code,
                'name': name,
                'material_unit_cost': material_cost,
                'labor_unit_cost': labor_cost,
                'total_unit_cost': material_cost + labor_cost,
                'unit': unit
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting item data: {e}")
            return None
    def handle_duplicate_item(self, existing_item: Dict[str, Any], new_item: Dict[str, Any]) -> None:
        """Handle duplicate items by updating costs if new item has better data"""
        self.logger.warning(f"Duplicate item: Code='{new_item['code']}', Name='{new_item['name']}'")
        
        # Update if new item has costs and existing doesn't
        if (new_item['material_unit_cost'] > 0 or new_item['labor_unit_cost'] > 0) and \
           (existing_item['material_unit_cost'] == 0 and existing_item['labor_unit_cost'] == 0):
            existing_item.update({
                'material_unit_cost': new_item['material_unit_cost'],
                'labor_unit_cost': new_item['labor_unit_cost'],
                'total_unit_cost': new_item['total_unit_cost']
            })
            self.logger.debug(f"Updated costs for duplicate: Material={new_item['material_unit_cost']}, Labor={new_item['labor_unit_cost']}")
    
    def write_item_costs(self, worksheet, row: int, calculated_costs: Dict[str, float]) -> None:
        """Write calculated costs to worksheet row"""
        try:
            # Map cost types to column positions
            cost_mapping = {
                'material_unit_cost': self.column_mapping.get('material_unit_cost'),
                'labor_unit_cost': self.column_mapping.get('labor_unit_cost'),
                'total_unit_cost': self.column_mapping.get('total_unit_cost'),
                'total_cost': self.column_mapping.get('total_cost')
            }

            # Write each cost to its column
            for cost_type, col_num in cost_mapping.items():
                if col_num and cost_type in calculated_costs:
                    worksheet.cell(row=row, column=col_num).value = calculated_costs[cost_type]

        except Exception as e:
            self.logger.error(f"Error writing costs to row {row}: {e}")
    
    
    def calculate_item_costs(self, master_item: Dict[str, Any], quantity: float, similarity: float = 100) -> Dict[str, float]:
        """
        Calculate costs for interior items.
        Interior logic: Material cost * quantity + Labor cost (not multiplied)
        """
        # If similarity was too low, return "needs checking" values
        if similarity < 50:
            return {
                'material_unit_cost': "ต้องตรวจสอบ",
                'labor_unit_cost': "ต้องตรวจสอบ",
                'total_unit_cost': "ต้องตรวจสอบ",
                'total_cost': "ต้องตรวจสอบ"
            }

        mat_cost = float(master_item.get('material_unit_cost', 0))
        lab_cost = float(master_item.get('labor_unit_cost', 0))
        

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
        DEPRECATED: Use find_section_structure() instead.
        This method is kept for backward compatibility only.
        """
        return self.find_section_structure(worksheet, max_row)
    
    def find_section_structure(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """
        Find section structure (boundaries only, no cost calculation) for interior sheets.
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
                
                sections[section_id] = {
                    'total_row': row_idx,
                    'start_row': section_start_row,
                    'end_row': row_idx - 1,
                    'section_id': section_id
                }
                
                self.logger.debug(f"Found interior section structure '{section_id}' (rows {section_start_row}-{row_idx-1})")
        
        # If no sections found, create a default main section
        if not sections:
            sections['MAIN_SECTION'] = {
                'total_row': None,
                'start_row': 1,
                'end_row': max_row,
                'section_id': 'MAIN_SECTION'
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
        
        # FALLBACK: For first section, start from header row + 1
        # If no previous total found, this is likely the first section
        fallback_start = self.header_row + 1  # Start right after header
        return section_name_from_total or f"FALLBACK{total_row}", fallback_start
    
    def calculate_section_totals_from_range(self, worksheet, start_row: int, end_row: int) -> Dict[str, float]:
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
            
            # Skip only actual total rows, not empty code cells
            if code_text.lower() == 'total':
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
        """
        self.logger.debug(f"write_section_totals called with {len(sections)} sections: {list(sections.keys())}")
        
        for section_id, section_data in sections.items():
            total_row = section_data.get('total_row')
            if not total_row:
                continue
            
            self.logger.debug(f"Writing pre-calculated totals for '{section_id}' at row {total_row}")
            
            # Get pre-calculated sums
            material_unit_sum = section_data['material_unit_sum']
            labor_unit_sum = section_data['labor_unit_sum']
            total_unit_sum = section_data['total_unit_sum']
            total_sum = section_data["total_sum"]
            
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
                
                self.logger.debug(f"Section '{section_id}' totals written successfully")
                
            except Exception as e:
                self.logger.error(f"Error writing section totals for '{section_id}': {e}")
        
        # After all section totals are written, calculate and write grand total
        self.write_grand_total_from_sections(worksheet, sections, markup_options, start_markup_col)
    
    def write_grand_total_from_sections(self, worksheet, sections: Dict[str, Dict[str, Any]], 
                                      markup_options: List[int], start_markup_col: int) -> None:
        """
        Calculate grand total by reading total_cost values from section rows and write to รวมรายการ row.
        """
        try:
            # Sum up total_cost from all section rows
            grand_total_cost = 0
            total_col = self.column_mapping['total_cost']  # Column I
            
            for section_id, section_data in sections.items():
                total_row = section_data.get('total_row')
                if total_row:
                    # Read the total_cost value that we just wrote
                    section_total = worksheet.cell(row=total_row, column=total_col).value or 0
                    grand_total_cost += float(section_total)
                    self.logger.debug(f"Section '{section_id}' total: {section_total}, Grand total so far: {grand_total_cost}")
            
            # Find รวมรายการ row in column L (8)
            search_col = 8  # Column L
            max_row = worksheet.max_row
            
            self.logger.debug(f"Searching for รวมรายการ in column {search_col} (Column L), grand total to write: {grand_total_cost}")
            
            for row_idx in range(1, max_row + 1):
                cell_value = worksheet.cell(row=row_idx, column=search_col).value
                if cell_value and 'รวมรายการ' in str(cell_value):
                    self.logger.debug(f"Found grand total row at {row_idx}: '{cell_value}'")
                    
                    # Write only the grand total to total_cost column (I)
                    worksheet.cell(row=row_idx, column=total_col).value = grand_total_cost
                    
                    # Write markup costs for grand total
                    self.write_markup_costs(worksheet, row_idx, grand_total_cost, markup_options, start_markup_col)
                    
                    self.logger.debug(f"Grand total written: {grand_total_cost} to row {row_idx}, column {total_col}")
                    return
            
            self.logger.debug("No grand total row found with รวมรายการ pattern")
            
        except Exception as e:
            self.logger.error(f"Error writing grand total: {e}")
    
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
    
    
    
    