#!/usr/bin/env python3
"""
Fire Protection sheet processor - handles fire protection system sheets.
These sheets have specific safety-related patterns and calculation methods.
"""

from typing import Dict, Any, List
import re
from base_sheet_processor import BaseSheetProcessor

class FPSheetProcessor(BaseSheetProcessor):
    """Processor for Fire Protection (FP) sheets"""
    
    @property
    def sheet_pattern(self) -> str:
        return 'fp'
    
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
        return 'fp_items'
    
    def calculate_item_costs(self, master_item: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """
        Calculate costs for fire protection items.
        FP logic: Both material and labor costs are multiplied by quantity
        """
        mat_cost = float(master_item.get('material_cost', 0))
        lab_cost = float(master_item.get('labor_cost', 0))
        
        # FP calculation: both material and labor * quantity
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
    
    def find_section_boundaries(self, worksheet, max_row: int) -> Dict[str, Dict[str, Any]]:
        """
        Find section boundaries for fire protection sheets.
        FP sheets often have sections like 'FIRE ALARM', 'SPRINKLER', 'EXTINGUISHER', etc.
        """
        sections = {}
        name_col = self.column_mapping['name']
        code_col = self.column_mapping['code']
        
        # Common fire protection section headers
        fp_sections = [
            'FIRE ALARM', 'SPRINKLER', 'EXTINGUISHER', 'FIRE PUMP', 
            'FIRE HOSE', 'FIRE CABINET', 'SMOKE DETECTOR', 'FIRE PROTECTION'
        ]
        
        current_section = None
        
        # Scan for section headers and total rows
        for row_idx in range(1, max_row + 1):
            code_cell = worksheet.cell(row=row_idx, column=code_col).value
            name_cell = worksheet.cell(row=row_idx, column=name_col).value
            
            code_text = str(code_cell).strip() if code_cell else ""
            name_text = str(name_cell).strip() if name_cell else ""
            
            # Check for section headers
            if self._is_fp_section_header(name_text, fp_sections):
                current_section = name_text
                sections[current_section] = {
                    'start_row': row_idx,
                    'total_row': None,
                    'material_total': 0,
                    'labor_total': 0,
                    'total_cost': 0,
                    'item_rows': []
                }
                self.logger.info(f"Found FP section '{current_section}' at row {row_idx}")
            
            # Check for total rows
            elif self._is_fp_total_row(code_text, name_text):
                section_id = self._identify_fp_section(code_text, name_text, current_section)
                
                if section_id not in sections:
                    sections[section_id] = {
                        'start_row': None,
                        'total_row': row_idx,
                        'material_total': 0,
                        'labor_total': 0,
                        'total_cost': 0,
                        'item_rows': []
                    }
                else:
                    sections[section_id]['total_row'] = row_idx
                
                self.logger.info(f"Found FP total row for '{section_id}' at row {row_idx}")
        
        # If no sections found, create a default main section
        if not sections:
            sections['MAIN_FP'] = {
                'start_row': None,
                'total_row': None,
                'material_total': 0,
                'labor_total': 0,
                'total_cost': 0,
                'item_rows': []
            }
        
        return sections
    
    def _is_fp_section_header(self, text: str, section_keywords: List[str]) -> bool:
        """Check if text is a fire protection section header"""
        if not text or len(text) < 3:
            return False
        
        text_upper = text.upper()
        
        # Check for exact matches or partial matches with FP keywords
        for keyword in section_keywords:
            if keyword in text_upper:
                return True
        
        # Check for fire-related terms
        fire_terms = ['FIRE', 'SMOKE', 'ALARM', 'SPRINKLER', 'EXTINGUISHER']
        for term in fire_terms:
            if term in text_upper:
                return True
        
        # Check if it's all caps (likely a header)
        if text.isupper() and len(text) > 5:
            return True
        
        return False
    
    def _is_fp_total_row(self, code_text: str, name_text: str) -> bool:
        """Check if row is a fire protection total row"""
        combined_text = f"{code_text} {name_text}".lower()
        
        # Look for total indicators
        total_indicators = ['total', 'รวม', 'รวมรายการ', 'subtotal', 'sum']
        
        for indicator in total_indicators:
            if indicator in combined_text:
                return True
        
        return False
    
    def _identify_fp_section(self, code_text: str, name_text: str, current_section: str) -> str:
        """Identify which section a total row belongs to"""
        combined_text = f"{code_text} {name_text}".lower()
        
        # Try to extract section name from total text
        if 'total' in combined_text:
            # Look for patterns like "Total FIRE ALARM" or "FIRE ALARM Total"
            for section_name in ['fire alarm', 'sprinkler', 'extinguisher', 'fire pump', 'fire hose']:
                if section_name in combined_text:
                    return section_name.upper().replace(' ', '_')
        
        # If we can't identify the section, use current section or default
        if current_section:
            return current_section.upper().replace(' ', '_')
        
        return 'MAIN_FP'
    
    def write_markup_costs(self, worksheet, row: int, base_cost: float, markup_options: List[int], start_col: int) -> None:
        """Write markup costs for fire protection items"""
        for i, markup_percent in enumerate(markup_options):
            markup_rate = self.markup_rates.get(markup_percent, 1.0)
            markup_cost = round(base_cost * (1 + markup_rate), 2)
            col_num = start_col + i
            
            try:
                worksheet.cell(row=row, column=col_num).value = markup_cost
                self.logger.debug(f"Wrote FP markup {markup_percent}% = {markup_cost} to ({row}, {col_num})")
            except Exception as e:
                self.logger.error(f"Error writing FP markup to ({row}, {col_num}): {e}")
    
    def assign_item_to_section(self, item_row: int, sections: Dict[str, Dict[str, Any]]) -> str:
        """Assign a fire protection item to the appropriate section"""
        # Find the section that contains this item
        best_section = None
        
        for section_id, section_data in sections.items():
            start_row = section_data.get('start_row')
            total_row = section_data.get('total_row')
            
            # Item belongs to section if it's between start and total rows
            if start_row and total_row:
                if start_row < item_row < total_row:
                    best_section = section_id
                    break
            elif start_row and item_row > start_row:
                # No total row defined, but item is after start
                best_section = section_id
            elif total_row and item_row < total_row:
                # No start row defined, but item is before total
                best_section = section_id
        
        # If no section found, use main FP section
        if not best_section:
            if 'MAIN_FP' not in sections:
                sections['MAIN_FP'] = {
                    'start_row': None,
                    'total_row': None,
                    'material_total': 0,
                    'labor_total': 0,
                    'total_cost': 0,
                    'item_rows': []
                }
            best_section = 'MAIN_FP'
        
        return best_section
    
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
        
        self.logger.debug(f"Updated FP section '{section_id}' totals: "
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
            
            self.logger.info(f"Writing FP section totals for '{section_id}' at row {total_row}")
            
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
                
                self.logger.info(f"FP section '{section_id}' totals written successfully")
                
            except Exception as e:
                self.logger.error(f"Error writing FP section totals for '{section_id}': {e}")
    
    def _should_skip_boq_row(self, name: str) -> bool:
        """Check if BOQ row should be skipped - FP specific"""
        clean_name = name.strip()
        
        # Base skip conditions
        if super()._should_skip_boq_row(name):
            return True
        
        # FP-specific skip conditions
        fp_skip_keywords = ['fire protection system', 'fp system', 'fire safety']
        
        if any(keyword in clean_name.lower() for keyword in fp_skip_keywords):
            return True
        
        return False
    
    def add_sample_data(self) -> None:
        """Add sample data for fire protection items"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table already has data
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.logger.info(f"Table {self.table_name} already has {count} items")
                return
            
            # Add sample fire protection items
            sample_items = [
                ('FP001', 'Smoke Detector - Photoelectric', 800, 200, 'EA'),
                ('FP002', 'Fire Extinguisher - 10lb ABC', 1200, 100, 'EA'),
                ('FP003', 'Fire Alarm Panel - 8 Zone', 5000, 1000, 'EA'),
                ('FP004', 'Sprinkler Head - Standard', 300, 150, 'EA'),
                ('FP005', 'Fire Hose - 50ft', 1500, 200, 'EA'),
                ('FP006', 'Fire Cabinet - Steel', 2000, 400, 'EA'),
                ('FP007', 'Fire Pump - 500 GPM', 15000, 3000, 'EA'),
                ('FP008', 'Heat Detector - Fixed Temp', 600, 150, 'EA'),
                ('FP009', 'Manual Pull Station', 400, 100, 'EA'),
                ('FP010', 'Fire Pipe - 4 inch', 200, 100, 'M')
            ]
            
            for i, (code, name, material_cost, labor_cost, unit) in enumerate(sample_items):
                item_id = f"fp_sample_{i+1}"
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
                cursor.execute(f"UPDATE {self.table_name} SET material_cost = 600, labor_cost = 200, total_cost = 800")
                conn.commit()
                
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE material_cost > 0")
                updated = cursor.fetchone()[0]
                self.logger.info(f"Added sample costs to {updated} items in {self.table_name}")