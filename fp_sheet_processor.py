#!/usr/bin/env python3
"""
Fire Protection sheet processor - handles fire protection system sheets.
Updated to match new abstract methods and range-based approach.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import uuid
import sqlite3

from base_sheet_processor import BaseSheetProcessor
from models.config_models import SystemProcessorConfig

class FPSheetProcessor(BaseSheetProcessor):
    """Processor for Fire Protection (FP) sheets"""
    
    def __init__(self, db_path: str, markup_rates: Dict[int, float], config: Optional[SystemProcessorConfig] = None):
        super().__init__(db_path, markup_rates, config)
        # Use default values if no config provided
        if config is None:
            from models.config_models import ProcessorConfigs
            default_configs = ProcessorConfigs.get_default_config()
            self.config = default_configs.fp
    
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
            'total_row_col': self.config.column_mapping.total_row_col,
            'unit': self.config.column_mapping.unit,
            'quantity': self.config.column_mapping.quantity,
            'material_unit_cost': self.config.column_mapping.material_unit_cost,
            'material_cost': self.config.column_mapping.material_cost,
            'labor_unit_cost': self.config.column_mapping.labor_unit_cost,
            'labor_cost': self.config.column_mapping.labor_cost,
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
                        f"INSERT INTO {self.table_name} (internal_id, code, name, material_unit_cost, labor_unit_cost, unit) "
                        f"VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            row['internal_id'],
                            row['code'],
                            row['name'],
                            row['material_unit_cost'],
                            row['labor_unit_cost'],
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
            material_unit_idx = self.column_mapping['material_unit_cost'] - 1
            material_idx = self.column_mapping['material_cost'] - 1
            labor_unit_idx = self.column_mapping['labor_unit_cost'] - 1
            labor_idx = self.column_mapping['labor_cost'] - 1
            unit_idx = (self.column_mapping['unit'] - 1) if 'unit' in self.column_mapping else None
            
            # Extract values safely
            row_values = row.values
            if len(row_values) <= max(code_idx, name_idx, material_unit_idx, labor_unit_idx):
                return None
            
            # Extract values exactly as they appear in Excel (no cleaning)
            code = str(row_values[code_idx]) if code_idx < len(row_values) and pd.notna(row_values[code_idx]) else ''
            name = str(row_values[name_idx]) if name_idx < len(row_values) and pd.notna(row_values[name_idx]) else ''
            
            # Skip total/summary rows and completely empty rows (but don't modify data)
            if(self._is_skip_row(code) or (not name.strip() and not code.strip())):
                return None
            
            # Convert cost values only
            material_unit_cost = self._safe_float_conversion(row_values[material_unit_idx] if material_unit_idx < len(row_values) else 0)
            material_cost = self._safe_float_conversion(row_values[material_idx] if material_idx < len(row_values) else 0)
            labor_unit_cost = self._safe_float_conversion(row_values[labor_unit_idx] if labor_unit_idx < len(row_values) else 0)
            labor_cost = self._safe_float_conversion(row_values[labor_idx] if labor_idx < len(row_values) else 0)
            unit = str(row_values[unit_idx]) if unit_idx is not None and unit_idx < len(row_values) and pd.notna(row_values[unit_idx]) else ''
            
            return {
                'internal_id': f"item_{uuid.uuid4().hex[:8]}",
                'code': code,
                'name': name,
                'material_unit_cost': material_unit_cost,
                'material_cost': material_cost,
                'labor_unit_cost': labor_unit_cost,
                'labor_cost': labor_cost,
                'total_cost': material_cost + labor_cost,
                'unit': unit
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting item data: {e}")
            return None
    def handle_duplicate_item(self, existing_item: Dict[str, Any], new_item: Dict[str, Any]) -> None:
        """Handle duplicate items by updating costs if new item has better data"""
        self.logger.warning(f"Duplicate item: Code='{new_item['code']}', Name='{new_item['name']}'")
        
        # Update if new item has costs and existing doesn't
        if (new_item['material_unit_cost'] > 0 or new_item['labor_unit_cost'] > 0 or new_item['material_cost'] > 0 or new_item['labor_cost']) and \
           (existing_item['material_unit_cost'] == 0 and existing_item['labor_unit_cost'] == 0 and existing_item['material_cost'] == 0 and existing_item['labor_cost'] == 0):
            existing_item.update({
                'material_unit_cost': new_item['material_unit_cost'],
                'material_cost': new_item['material_cost'],
                'labor_unit_cost': new_item['labor_unit_cost'],
                'labor_cost': new_item['labor_cost'],
                'total_cost': new_item['total_cost']
            })
            self.logger.debug(f"Updated costs for duplicate: Material unit={new_item['material_unit_cost']}, Material={new_item['material_cost']}, Labor unit={new_item['labor_unit_cost']}, Labor ={new_item['labor_cost']}")
    
    def write_item_costs(self, worksheet, row: int, calculated_costs: Dict[str, float]) -> None:
        """Write calculated costs to worksheet row"""
        try:
            # Map cost types to column positions
            cost_mapping = {
                'material_unit_cost': self.column_mapping.get('material_unit_cost'),
                'material_cost': self.column_mapping.get('material_cost'),
                'labor_unit_cost': self.column_mapping.get('labor_unit_cost'),
                'labor_cost': self.column_mapping.get('labor_cost'),
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
                'material_cost': "ต้องตรวจสอบ",
                'labor_unit_cost': "ต้องตรวจสอบ",
                'labor_cost': "ต้องตรวจสอบ",
                'total_cost': "ต้องตรวจสอบ",
            }

        mat_unit_cost = float(master_item.get('material_unit_cost', 0))
        lab_unit_cost = float(master_item.get('labor_unit_cost', 0))
        mat_cost = mat_unit_cost * quantity
        lab_cost = lab_unit_cost * quantity
          
        total_cost =  mat_cost + lab_cost
        
        return {
            'material_unit_cost': mat_unit_cost,
            'material_cost': mat_cost,
            'labor_unit_cost': lab_unit_cost,
            'labor_cost': lab_cost,
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
        total_row_col = self.column_mapping['total_row_col']
        
        self.logger.debug(f"Scanning electrical sheet for sections in column {total_row_col} (max_row={max_row})")
        
        # Scan for total rows
        for row_idx in range(1, max_row + 1):
            total_cell = worksheet.cell(row=row_idx, column= total_row_col).value
            name_cell = worksheet.cell(row=row_idx, column=name_col).value
            
            total_text = str(total_cell).strip() if total_cell else ""
            name_text = str(name_cell).strip() if name_cell else ""
            
            # Debug every row that has content in total_row_col
            if total_text:
                self.logger.debug(f"Row {row_idx} column {total_row_col}: '{total_text}' (checking for รวมรายการ)")
            
            # Look for 'Total' in code column
            if 'รวมรายการ' in total_text.lower() or total_text.lower() == 'รวม':
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
        Find the section ID and start row for a total row using method 2 only:
        Find previous total row, section header = previous_total + 1
        
        Returns: (section_id, section_start_row)
        """
        total_row_col = self.column_mapping['total_row_col']
        
        # METHOD 2: Find previous total, section header = previous_total + 1
        for i in range(total_row - 1, max(1, total_row - 100), -1):
            check_code_cell = worksheet.cell(row=i, column=total_row_col).value
            check_code_text = str(check_code_cell).strip() if check_code_cell else ""
            
            # Found another total row using same pattern as find_section_structure
            if 'รวมรายการ' in check_code_text.lower() or check_code_text.lower() == 'รวม':
                section_header_row = i + 1
                code_cell = worksheet.cell(row=section_header_row, column=total_row_col).value
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
        material_cost_sum = 0.0
        labor_unit_cost_sum = 0.0
        labor_cost_sum = 0.0
        total_cost_sum = 0.0
        item_count = 0
        
        # Get column positions
        mat_unit_col = self.column_mapping['material_unit_cost']
        mat_col = self.column_mapping['material_cost']
        lab_unit_col = self.column_mapping['labor_unit_cost']
        lab_col = self.column_mapping['labor_cost']
        total_col = self.column_mapping['total_cost']
        total_row_col = self.column_mapping['total_row_col']
        
        self.logger.debug(f"Calculating totals for range {start_row}-{end_row}")
        
        # Sum up all items in the section range
        for row in range(start_row, end_row + 1):
            # Skip if this looks like a header or empty row
            total_row_cell = worksheet.cell(row=row, column=total_row_col).value
            total_row_text = str(total_row_cell).strip() if total_row_cell else ""
            
            # Skip only actual total rows, not empty code cells - use same pattern as find_section_structure
            if 'รวมรายการ' in total_row_text.lower() or total_row_text.lower() == 'รวม':
                continue
            
            # Get costs from each row
            mat_unit_cell = worksheet.cell(row=row, column=mat_unit_col).value
            mat_cell = worksheet.cell(row=row, column=mat_col).value
            lab_unit_cell = worksheet.cell(row=row, column=lab_unit_col).value
            lab_cell = worksheet.cell(row=row, column=lab_col).value
            total_cell = worksheet.cell(row=row, column=total_col).value

            
            # Convert to float safely
            mat_unit_cost = self._safe_float(mat_unit_cell)
            mat_cost = self._safe_float(mat_cell)
            lab_unit_cost = self._safe_float(lab_unit_cell)
            lab_cost = self._safe_float(lab_cell)
            total_cost = self._safe_float(total_cell)
            
            # Only add if this row has actual costs (not header or empty rows)
            if mat_unit_cost > 0 or lab_unit_cost > 0 or mat_cost > 0 or lab_cost > 0 or total_cost > 0:
                material_unit_cost_sum += mat_unit_cost
                material_cost_sum += mat_cost
                labor_unit_cost_sum += lab_unit_cost
                labor_cost_sum += lab_cost                
                total_cost_sum += total_cost
                item_count += 1
                
                self.logger.debug(f"Row {row} ({total_row_text}): Mat unit={mat_unit_cost}, Lab unit={lab_unit_cost}, Mat={mat_cost}, Lab={lab_cost}, Total={total_cost}")
        
        return {
            'material_unit_sum': material_unit_cost_sum,
            'material_sum': material_cost_sum,
            'labor_unit_sum': labor_unit_cost_sum,
            'labor_sum': labor_cost_sum,
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
        self.logger.debug(f"write_section_totals called with {len(sections)} sections: {list(sections.keys())}")
        
        for section_id, section_data in sections.items():
            total_row = section_data.get('total_row')
            if not total_row:
                continue
            
            self.logger.debug(f"Writing pre-calculated totals for '{section_id}' at row {total_row}")
            self.logger.debug(f"Section data keys: {list(section_data.keys())}")
            
            # Get pre-calculated sums
            material_unit_sum = section_data.get('material_unit_sum', 0)
            material_sum = section_data.get('material_sum', 0)
            labor_unit_sum = section_data.get('labor_unit_sum', 0)
            labor_sum = section_data.get('labor_sum', 0)
            total_sum = section_data.get('total_sum', 0)
            item_count = section_data.get('item_count', 0)

             
            self.logger.debug(f"Section '{section_id}': {item_count} items, "
                           f"Material unit={material_unit_sum}, Labor unit={labor_unit_sum}, Material={material_sum}, Labor={labor_sum}, Total sum={total_sum}")
            
            # Write basic totals
            mat_unit_col = self.column_mapping['material_unit_cost']
            mat_col = self.column_mapping['material_cost']
            lab_unit_col = self.column_mapping['labor_unit_cost']
            lab_col = self.column_mapping['labor_cost']
            total_col = self.column_mapping['total_cost']
            
            try:
                self.logger.debug(f"Writing to cells: mat_unit=({total_row},{mat_unit_col}), mat=({total_row},{mat_col}), lab_unit=({total_row},{lab_unit_col}), lab=({total_row},{lab_col}), total=({total_row},{total_col})")
                
                worksheet.cell(row=total_row, column=mat_unit_col).value = material_unit_sum
                worksheet.cell(row=total_row, column=mat_col).value = material_sum
                worksheet.cell(row=total_row, column=lab_unit_col).value = labor_unit_sum
                worksheet.cell(row=total_row, column=lab_col).value = labor_sum
                worksheet.cell(row=total_row, column=total_col).value = total_sum
                
                self.logger.debug(f"Cell values written: mat_unit={material_unit_sum}, mat={material_sum}, lab_unit={labor_unit_sum}, lab={labor_sum}, total={total_sum}")
                
                # Write markup totals
                self.write_markup_costs(worksheet, total_row, total_sum, 
                                      markup_options, start_markup_col)
                
                self.logger.debug(f"Section '{section_id}' totals written successfully")
                
            except Exception as e:
                self.logger.error(f"Error writing section totals for '{section_id}': {e}")
                import traceback
                self.logger.error(traceback.format_exc())
    
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
    
    
    
    
