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
                material_unit_cost REAL DEFAULT 0, 
                labor_unit_cost REAL DEFAULT 0, 
                total_unit_cost REAL DEFAULT 0,
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
        self.logger.debug(f"Processed {len(result_df)} items from {self.table_name}")
        return result_df
    
    def _extract_item_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
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
    
   
    
    def _safe_float_conversion(self, value: Any) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if pd.notna(value) else 0
        except (ValueError, TypeError):
            return 0
    
    def _is_skip_row(self, code: str) -> bool:
        """Check if row should be skipped"""
        return any(keyword in code.lower() for keyword in ['total', 'รวม', 'sum', 'subtotal'])
    
    def _handle_duplicate_item(self, existing_item: Dict[str, Any], new_item: Dict[str, Any]) -> None:
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
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by handling special characters and quotes"""
        if not text:
            return ""
        
        # Convert to string and strip whitespace
        normalized = str(text).strip()
        
        # Normalize different types of quotation marks to standard double quotes
        quote_replacements = {
            '"': '"',  # Left double quotation mark
            '"': '"',  # Right double quotation mark
            ''': "'",  # Left single quotation mark
            ''': "'",  # Right single quotation mark
            '`': "'",  # Backtick to apostrophe
            '´': "'",  # Acute accent to apostrophe
        }
        
        for old_quote, new_quote in quote_replacements.items():
            normalized = normalized.replace(old_quote, new_quote)
        
        # Remove extra whitespace between words
        normalized = ' '.join(normalized.split())
        
        return normalized.lower()

    def find_best_match(self, name: str, code: str) -> Optional[Dict[str, Any]]:
        """Find best matching item from database using comprehensive fuzzy matching"""
        if not name or pd.isna(name):
            return None

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            all_items = conn.execute(f"SELECT * FROM {self.table_name}").fetchall()

        if not all_items:
            self.logger.warning(f"No items found in {self.table_name} database")
            return None

        sanitized_search = self._normalize_text(name)
        sanitized_code = self._normalize_text(code) if code and not pd.isna(code) else ""


        best_match = None
        best_similarity = 0
        match_type = "none"

        # Special handling for hyphen-only names
        is_hyphen_only = sanitized_search == '-'

        # Process all items once with comprehensive matching logic
        for item_row in all_items:
            item_dict = dict(item_row)
            item_code = self._normalize_text(item_dict['code'])
            item_name = self._normalize_text(item_dict['name'])
            
            
            # Calculate name similarity once
            name_similarity = fuzz.ratio(sanitized_search, item_name)

            # Case 1: Exact match (code + name)
            if sanitized_code and item_code == sanitized_code and item_name == sanitized_search:
                self.logger.debug(f"EXACT MATCH: {item_dict['name']}")
                return {'item': item_dict, 'similarity': 100}

            # Case 2: Special handling for hyphen-only names with code match
            if is_hyphen_only and sanitized_code and item_code == sanitized_code:
                self.logger.debug(f"HYPHEN CODE MATCH: {item_dict['name']}")
                return {'item': item_dict, 'similarity': 95}

            # Case 3: Code match with name similarity boost
            if sanitized_code and item_code == sanitized_code:
                adjusted_similarity = min(100, name_similarity + 25)
                self.logger.debug(f"CODE MATCH: {item_code} -> {adjusted_similarity:.0f}% (name: {name_similarity:.0f}%)")

                if adjusted_similarity > best_similarity:
                    best_similarity = adjusted_similarity
                    best_match = {'item': item_dict, 'similarity': adjusted_similarity}
                    match_type = "code_match"

            # Case 4: High name similarity but code mismatch (penalized)
            elif sanitized_code and name_similarity >= 80:
                # Apply penalty for code mismatch but still consider it
                adjusted_similarity = max(50, name_similarity - 15)
                self.logger.debug(f"NAME MATCH WITH CODE MISMATCH: {name_similarity:.0f}% -> {adjusted_similarity:.0f}% (penalty applied)")

                if adjusted_similarity > best_similarity:
                    best_similarity = adjusted_similarity
                    best_match = {'item': item_dict, 'similarity': adjusted_similarity}
                    match_type = "name_match_code_mismatch"
            
            # # Case 5: Pure name matching (fallback for items without codes)
            # elif not sanitized_code and name_similarity > best_similarity:
            #     best_similarity = name_similarity
            #     best_match = {'item': item_dict, 'similarity': name_similarity}
            #     match_type = "name_only"

        # Final debug log
        if best_match:
            self.logger.debug(f"Best match ({match_type}): {best_similarity:.0f}% - {best_match['item']['name'][:50]}...")
        else:
            self.logger.debug("No suitable match found")
        
        return best_match
    #WORK3:make nested dicts pydantic models for easy code maintenance and reading
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
                    self.logger.debug(f"Match: '{name[:40]}...' -> {match['similarity']:.0f}% similarity")
                    
            except Exception as e:
                self.logger.error(f"Error processing BOQ row {idx}: {e}")
                continue
        
        self.logger.debug(f"Sheet {self.table_name}: {matched_count}/{total_rows} items matched")
        return processed_items
    
    def _should_skip_boq_row(self, name: str) -> bool:
        """Check if BOQ row should be skipped"""
        clean_name = name.strip()
        
        if (not clean_name or 
            clean_name.lower() in ['nan', 'none', ''] or 
            any(keyword in clean_name.lower() for keyword in ['total', 'รวม'])):
            return True
        
        return False
    
    #WORK4: have non interior sheet function for calculting columns such as material_total, labor_total (multiplied with qty)
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

          self.logger.debug(f"Processing final sheet with {len(processed_matches)} matches and {len(sections)} sections")

          # Process individual item costs
          for row_index, match_data in processed_matches.items():
              try:
                  # Get quantity from the worksheet
                  quantity_col = self.column_mapping.get('quantity', 4)  # Default to column D
                  quantity = self._get_cell_value(data_worksheet, row_index + self.header_row + 2, quantity_col)
                  quantity = self._safe_float_conversion(quantity) or 1.0

                  # Calculate costs using the match
                  master_item = match_data['item']
                  similarity = match_data['similarity']
                  calculated_costs = self.calculate_item_costs(master_item, quantity, similarity)

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

          self.logger.debug(f"Final sheet processing complete: {items_processed} processed, {items_failed} failed")

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
