#!/usr/bin/env python3
"""
Base sheet processor class that defines the interface for all sheet processors.
This provides common functionality and structure for specific sheet implementations.
"""

import fuzzywuzzy
import pandas as pd
import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import uuid
import re
from fuzzywuzzy import fuzz

class BaseSheetProcessor(ABC):
    """Abstract base class for sheet processors"""
    
    def __init__(self, db_path: str, markup_rates: Dict[int, float]):
        self.db_path = db_path
        self.markup_rates = markup_rates
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @property
    @abstractmethod
    def sheet_pattern(self) -> str:
        """Pattern to match sheet names (e.g., 'int' for interior sheets)"""
        pass
    
    @property
    @abstractmethod
    def header_row(self) -> int:
        """0-based index of the header row"""
        pass
    
    @property
    @abstractmethod
    def column_mapping(self) -> Dict[str, int]:
        """Mapping of column names to their 1-based Excel column numbers"""
        pass
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Database table name for this sheet type"""
        pass
    
    def matches_sheet(self, sheet_name: str) -> bool:
        """Check if this processor handles the given sheet name"""
        return self.sheet_pattern.lower() in sheet_name.lower()
    
    def create_table(self, conn: sqlite3.Connection) -> None:
        """Create the database table for this sheet type"""
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                internal_id TEXT PRIMARY KEY, 
                code TEXT, 
                name TEXT NOT NULL,
                material_cost REAL DEFAULT 0, 
                labor_cost REAL DEFAULT 0, 
                total_cost REAL DEFAULT 0,
                unit TEXT
            )
        ''')
        conn.commit()
    
    def process_master_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process master data sheet and return cleaned DataFrame"""
        if df.empty:
            return pd.DataFrame()
        
        result_data = []
        processed_items = {}
        
        for idx, row in df.iterrows():
            try:
                item_data = self._extract_item_data(row)
                if not item_data:
                    continue
                
                # Handle duplicates
                item_key = f"{item_data['code']}|{item_data['name']}"
                if item_key in processed_items:
                    self._handle_duplicate_item(processed_items[item_key], item_data)
                    continue
                
                processed_items[item_key] = item_data
                result_data.append(item_data)
                
            except Exception as e:
                self.logger.error(f"Error processing row {idx}: {e}")
                continue
        
        if not result_data:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(result_data)
        self.logger.info(f"Processed {len(result_df)} items from {self.table_name}")
        return result_df
    
    def _extract_item_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Extract item data from a row using column mapping"""
        try:
            # Get values from fixed positions
            code_idx = self.column_mapping['code'] - 1  # Convert to 0-based
            name_idx = self.column_mapping['name'] - 1
            material_idx = self.column_mapping['material_cost'] - 1
            labor_idx = self.column_mapping['labor_cost'] - 1
            unit_idx = self.column_mapping.get('unit', 0) - 1 if 'unit' in self.column_mapping else None
            
            # Extract values safely
            row_values = row.values
            if len(row_values) <= max(code_idx, name_idx, material_idx, labor_idx):
                return None
            
            code = str(row_values[code_idx]) if code_idx < len(row_values) else ''
            name = str(row_values[name_idx]) if name_idx < len(row_values) else ''
            
            # Clean item name
            name = self._clean_item_name(name, code)
            if not name:
                return None
            
            # Convert cost values
            material_cost = self._safe_float_conversion(row_values[material_idx] if material_idx < len(row_values) else 0)
            labor_cost = self._safe_float_conversion(row_values[labor_idx] if labor_idx < len(row_values) else 0)
            unit = str(row_values[unit_idx]) if unit_idx is not None and unit_idx < len(row_values) else ''
            
            # Skip empty or total rows
            if self._is_skip_row(name):
                return None
            
            return {
                'internal_id': f"item_{uuid.uuid4().hex[:8]}",
                'code': code,
                'name': name,
                'material_cost': material_cost,
                'labor_cost': labor_cost,
                'total_cost': material_cost + labor_cost,
                'unit': unit
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting item data: {e}")
            return None
    
    def _clean_item_name(self, name: str, code: str) -> str:
        """Clean and improve item names, especially for '-' values"""
        if not name or pd.isna(name) or name.strip() in ['-', '', 'nan', 'none']:
            if code and code.strip() and code.strip() not in ['-', 'nan', 'none']:
                return f"Item {code.strip()}"
            else:
                return f"Item_{uuid.uuid4().hex[:6]}"
        
        cleaned = name.strip()
        if cleaned == '-':
            return f"Unnamed item {uuid.uuid4().hex[:6]}"
        
        return cleaned
    
    def _safe_float_conversion(self, value: Any) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if pd.notna(value) else 0
        except (ValueError, TypeError):
            return 0
    
    def _is_skip_row(self, name: str) -> bool:
        """Check if row should be skipped"""
        return any(keyword in name.lower() for keyword in ['total', 'รวม', 'sum', 'subtotal'])
    
    def _handle_duplicate_item(self, existing_item: Dict[str, Any], new_item: Dict[str, Any]) -> None:
        """Handle duplicate items by updating costs if new item has better data"""
        self.logger.warning(f"Duplicate item: Code='{new_item['code']}', Name='{new_item['name']}'")
        
        # Update if new item has costs and existing doesn't
        if (new_item['material_cost'] > 0 or new_item['labor_cost'] > 0) and \
           (existing_item['material_cost'] == 0 and existing_item['labor_cost'] == 0):
            existing_item.update({
                'material_cost': new_item['material_cost'],
                'labor_cost': new_item['labor_cost'],
                'total_cost': new_item['total_cost']
            })
            self.logger.info(f"Updated costs for duplicate: Material={new_item['material_cost']}, Labor={new_item['labor_cost']}")
    
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
                        f"INSERT INTO {self.table_name} (internal_id, code, name, material_cost, labor_cost, total_cost, unit) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            row['internal_id'],
                            row['code'],
                            row['name'],
                            row['material_cost'],
                            row['labor_cost'],
                            row['total_cost'],
                            row.get('unit', '')
                        )
                    )
                except sqlite3.IntegrityError as e:
                    self.logger.error(f"Database integrity error: {e}")
                    continue
            
            conn.commit()
            self.logger.info(f"Synchronized {len(df)} items to {self.table_name}")
    
    def find_best_match(self, name: str, code: str) -> Optional[Dict[str, Any]]:
        """Find best matching item from database using fuzzy matching"""
        if not name or pd.isna(name):
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            all_items = conn.execute(f"SELECT * FROM {self.table_name}").fetchall()
        
        if not all_items:
            return None
        
        sanitized_search = str(name).lower().strip()
        sanitized_code = str(code).lower().strip() if code and not pd.isna(code) else ""
        
        best_match = None
        best_similarity = 0
        
        # Special handling for hyphen-only names
        is_hyphen_only = sanitized_search == '-'
        
        # Try exact match with code + name first
        if sanitized_code:
            for item_row in all_items:
                item_dict = dict(item_row)
                item_code = str(item_dict['code']).lower().strip()
                item_name = str(item_dict['name']).lower().strip()
                
                # Exact match
                if item_code == sanitized_code and item_name == sanitized_search:
                    return {'item': item_dict, 'similarity': 100}
                
                # Special handling for hyphen-only names
                if is_hyphen_only and item_code == sanitized_code:
                    return {'item': item_dict, 'similarity': 95}
                
                # Code match with name similarity boost
                if item_code == sanitized_code:
                    name_similarity = fuzzywuzzy.ratio(sanitized_search, item_name)
                    adjusted_similarity = min(100, name_similarity + 25)
                    
                    if adjusted_similarity > best_similarity:
                        best_similarity = adjusted_similarity
                        best_match = {'item': item_dict, 'similarity': adjusted_similarity}
        
        # Fuzzy matching on name
        for item_row in all_items:
            item_dict = dict(item_row)
            sanitized_candidate = str(item_dict['name']).lower().strip()
            similarity = fuzzywuzzy.ratio(sanitized_search, sanitized_candidate)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {'item': item_dict, 'similarity': similarity}
        
        return best_match
    
    def process_boq_sheet(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process a BOQ sheet and return processed matches"""
        processed_items = []
        total_rows = len(df)
        matched_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Extract name and code
                name_col = self.column_mapping['name'] - 1
                code_col = self.column_mapping['code'] - 1
                
                if name_col >= len(row):
                    continue
                
                name = str(row.iloc[name_col]).strip()
                code = str(row.iloc[code_col]).strip() if code_col < len(row) else ""
                
                # Skip empty or header rows
                if self._should_skip_boq_row(name):
                    continue
                
                # Find match
                match = self.find_best_match(name, code)
                
                if match and match['similarity'] >= 50:
                    processed_items.append({
                        'original_row_index': idx,
                        'row_code': code,
                        'row_name': name,
                        'match': match
                    })
                    matched_count += 1
                    self.logger.info(f"Match: '{name[:40]}...' -> {match['similarity']:.0f}% similarity")
                    
            except Exception as e:
                self.logger.error(f"Error processing BOQ row {idx}: {e}")
                continue
        
        self.logger.info(f"Sheet {self.table_name}: {matched_count}/{total_rows} items matched")
        return processed_items
    
    def _should_skip_boq_row(self, name: str) -> bool:
        """Check if BOQ row should be skipped"""
        clean_name = name.strip()
        
        if (not clean_name or 
            clean_name.lower() in ['nan', 'none', ''] or 
            any(keyword in clean_name.lower() for keyword in ['total', 'รวม', 'system', 'ระบบ'])):
            return True
        
        return False
    

    def process_final_sheet(self, worksheet, data_worksheet, sheet_info: Dict[str, Any], markup_options: List[int]) -> Dict[str, Any]:
      """
      Process final sheet by applying costs to matched items and writing section totals.
      Uses pre-calculated matches and sections from sheet_info.
      """
      items_processed = 0
      items_failed = 0

      try:
          # Get stored data from session
          processed_matches = sheet_info.get('processed_matches', {})
          sections = sheet_info.get('sections', {})

          self.logger.info(f"Processing final sheet with {len(processed_matches)} matches and {len(sections)} sections")

          # Process individual item costs
          for row_index, match_data in processed_matches.items():
              try:
                  # Get quantity from the worksheet
                  quantity_col = self.column_mapping.get('quantity', 4)  # Default to column D
                  quantity = self._get_cell_value(data_worksheet, row_index + self.header_row + 2, quantity_col)
                  quantity = self._safe_float_conversion(quantity) or 1.0

                  # Calculate costs using the match
                  master_item = match_data['item']
                  calculated_costs = self.calculate_item_costs(master_item, quantity)

                  # Write costs to worksheet
                  self._write_item_costs(worksheet, row_index + self.header_row + 2, calculated_costs)
                  items_processed += 1

              except Exception as e:
                  self.logger.error(f"Failed to process item at row {row_index}: {e}")
                  items_failed += 1

          # Calculate and write section totals using structure from session
          if sections:
              # Calculate totals from the now-filled worksheet
              sections_with_totals = self.calculate_section_totals(worksheet, sections)
              start_markup_col = max(self.column_mapping.values()) + 2  # Start after main columns
              self.write_section_totals(worksheet, sections_with_totals, markup_options, start_markup_col)

          self.logger.info(f"Final sheet processing complete: {items_processed} processed, {items_failed} failed")

      except Exception as e:
          self.logger.error(f"Error in process_final_sheet: {e}")
          items_failed += items_processed  # Mark all as failed
          items_processed = 0

      return {
          'items_processed': items_processed,
          'items_failed': items_failed,
          'sections_written': len(sections)
      }

    def _get_cell_value(self, worksheet, row: int, col: int):
        """Safely get cell value from worksheet"""
        try:
            return worksheet.cell(row=row, column=col).value
        except:
            return None

    def _write_item_costs(self, worksheet, row: int, calculated_costs: Dict[str, float]) -> None:
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
    
    @abstractmethod
    def calculate_item_costs(self, master_item: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """Calculate costs for an item. Each sheet type may have different calculation logic."""
        pass
    
    @abstractmethod
    def find_section_boundaries(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """Find section boundaries and total rows for this sheet type"""
        pass
    
    @abstractmethod
    def find_section_structure(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """Find section structure (boundaries only, no cost calculation)"""
        pass
    
    def calculate_section_totals(self, worksheet, section_structure: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate section totals from filled worksheet using pre-determined structure"""
        for section_id, section_data in section_structure.items():
            if 'start_row' in section_data and 'end_row' in section_data:
                # Calculate totals using the existing range-based calculation
                totals = self._calculate_section_totals_from_range(
                    worksheet, section_data['start_row'], section_data['end_row']
                )
                # Update section data with calculated totals
                section_data.update(totals)
        return section_structure
    
    def _calculate_section_totals_from_range(self, worksheet, start_row: int, end_row: int) -> Dict[str, float]:
        """Base implementation for calculating section totals from range - to be overridden by subclasses"""
        return {
            'material_unit_sum': 0.0,
            'labor_unit_sum': 0.0,
            'total_unit_sum': 0.0,
            'total_sum': 0.0,
            'item_count': 0
        }
    
    @abstractmethod
    def write_markup_costs(self, worksheet, row: int, base_cost: float, markup_options: List[int], start_col: int) -> None:
        """Write markup costs to worksheet"""
        pass

