#!/usr/bin/env python3
"""
Refactored BOQ Processor - Main application class that orchestrates all sheet processors.
This is the main entry point that uses the specialized sheet processors.
CLEANED VERSION - Removed redundant/unused code.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import uuid
from datetime import datetime
import logging
from werkzeug.utils import secure_filename
from pathlib import Path
import sqlite3
import shutil
import openpyxl
from typing import Dict, List, Any, Optional

# Import the specialized processors
from interior_sheet_processor import InteriorSheetProcessor
from electrical_sheet_processor import ElectricalSheetProcessor
from ac_sheet_processor import ACSheetProcessor
from fp_sheet_processor import FPSheetProcessor
from summary_sheet_processor import SummarySheetProcessor

logging.basicConfig(level=logging.INFO)

class RefactoredBOQProcessor:
    """Main BOQ processor that orchestrates all sheet-specific processors"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup directories
        self.data_dir = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor'
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_path = str(self.data_dir / 'master_data.db')
        
        # Session management
        self.processing_sessions = {}
        
        # Folder setup
        self.master_data_folder = 'master_data'
        self.upload_folder = 'uploads'
        self.output_folder = 'output'
        for folder in [self.master_data_folder, self.upload_folder, self.output_folder]:
            os.makedirs(folder, exist_ok=True)
        
        # Markup rates
        self.markup_rates = {100: 1.00, 130: 1.30, 150: 1.50, 50: 0.50, 30: 0.30}
        
        # Initialize sheet processors
        self.sheet_processors = [
            InteriorSheetProcessor(self.db_path, self.markup_rates),
            ElectricalSheetProcessor(self.db_path, self.markup_rates),
            ACSheetProcessor(self.db_path, self.markup_rates),
            FPSheetProcessor(self.db_path, self.markup_rates)
        ]
        
        # Summary processor
        self.summary_processor = SummarySheetProcessor(self.db_path, self.markup_rates)
        
        # Initialize database and sync master data
        self._init_database()
        self._sync_master_data()
        
        # Setup Flask routes
        self.setup_routes()
    
    def _init_database(self):
        """Initialize database with all required tables"""
        logging.info(f"Initializing database at {self.db_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            # Create tables for each processor
            for processor in self.sheet_processors:
                processor.create_table(conn)
            
            # Log table creation
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logging.info(f"Database tables created: {tables}")
    
    def _sync_master_data(self):
        """Sync master data from Excel files to database"""
        master_excel_path = os.path.join(self.master_data_folder, 'master.xlsx')
        
        if not os.path.exists(master_excel_path):
            logging.warning(f"Master Excel file not found at {master_excel_path}")
            self._add_sample_data()
            return
        
        logging.info(f"Synchronizing master data from {master_excel_path}")
        
        try:
            excel_file = pd.ExcelFile(master_excel_path)
            sheet_names = excel_file.sheet_names
            logging.info(f"Found {len(sheet_names)} sheets: {sheet_names}")
            
            for sheet_name in sheet_names:
                if self.summary_processor.matches_sheet(sheet_name):
                    logging.info(f"Skipping summary sheet: {sheet_name}")
                    continue
                
                # Find the appropriate processor for this sheet
                processor = self._find_processor_for_sheet(sheet_name)
                if not processor:
                    logging.warning(f"No processor found for sheet: {sheet_name}")
                    continue
                
                logging.info(f"Processing sheet {sheet_name} with {processor.__class__.__name__}")
                
                # Read and process the sheet
                df = pd.read_excel(master_excel_path, sheet_name=sheet_name, header=processor.header_row)
                processed_df = processor.process_master_sheet(df)
                
                if not processed_df.empty:
                    processor.sync_to_database(processed_df)
                else:
                    logging.warning(f"No data processed for sheet: {sheet_name}")
            
            # Ensure all processors have cost data
            for processor in self.sheet_processors:
                processor.ensure_costs_exist()
                
        except Exception as e:
            logging.error(f"Error synchronizing master data: {e}", exc_info=True)
    
    def _find_processor_for_sheet(self, sheet_name: str):
        """Find the appropriate processor for a given sheet name"""
        for processor in self.sheet_processors:
            if processor.matches_sheet(sheet_name):
                return processor
        return None
    
    def _add_sample_data(self):
        """Add sample data to all processors if no master data is available"""
        logging.info("Adding sample data to all processors")
        for processor in self.sheet_processors:
            processor.add_sample_data()
    
    def store_processing_session(self, session_id: str, data: Dict[str, Any]):
        """Store processing session data"""
        self.processing_sessions[session_id] = {
            'data': data,
            'created_at': datetime.now()
        }
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/process-boq', methods=['POST'])
        def process_boq_route():
            """Process uploaded BOQ file"""
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'})
            
            file = request.files['file']
            filepath = os.path.join(self.upload_folder, secure_filename(file.filename))
            file.save(filepath)
            
            try:
                excel_file = pd.ExcelFile(filepath)
                session_data = {'sheets': {}, 'original_filepath': filepath}
                
                # Filter out summary sheets
                sheets_to_process = [
                    s for s in excel_file.sheet_names 
                    if not self.summary_processor.matches_sheet(s)
                ]
                
                total_items = 0
                total_matches = 0
                
                for sheet_name in sheets_to_process:
                    # Find appropriate processor
                    processor = self._find_processor_for_sheet(sheet_name)
                    if not processor:
                        logging.warning(f"No processor found for sheet: {sheet_name}")
                        continue
                    
                    logging.info(f"Processing BOQ sheet: {sheet_name} with {processor.__class__.__name__}")
                    
                    # Read sheet data
                    df = pd.read_excel(filepath, sheet_name=sheet_name, header=processor.header_row)
                    
                    # Process the sheet
                    processed_items = processor.process_boq_sheet(df)
                    
                    # Store sheet data
                    session_data['sheets'][sheet_name] = {
                        'processor_type': processor.__class__.__name__,
                        'header_row': processor.header_row,
                        'processed_matches': {item['original_row_index']: item['match'] for item in processed_items},
                        'row_details': {item['original_row_index']: {'code': item['row_code'], 'name': item['row_name']} for item in processed_items},
                        'total_rows': len(df),
                        'matched_count': len(processed_items)
                    }
                    
                    total_items += len(df)
                    total_matches += len(processed_items)
                
                # Store session
                session_id = str(uuid.uuid4())
                self.store_processing_session(session_id, session_data)
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'summary': {
                        'total_items': total_items,
                        'matched_items': total_matches,
                        'match_rate': (total_matches / total_items * 100) if total_items > 0 else 0
                    }
                })
                
            except Exception as e:
                logging.error(f"Error processing BOQ file: {e}", exc_info=True)
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/generate-final-boq', methods=['POST'])
        def generate_final_boq_route():
            """Generate final BOQ with calculated costs"""
            data = request.get_json()
            session_id = data.get('session_id')
            
            if not session_id or session_id not in self.processing_sessions:
                return jsonify({'success': False, 'error': 'Invalid session'})
            
            session_data = self.processing_sessions[session_id]['data']
            original_filepath = session_data['original_filepath']
            markup_options = data.get('markup_options', [100, 130, 150, 50, 30])
            
            try:
                # Generate output filename
                filename = f"final_boq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                output_filepath = os.path.join(self.output_folder, filename)
                shutil.copy(original_filepath, output_filepath)
                
                # Open workbooks
                workbook = openpyxl.load_workbook(output_filepath)
                data_workbook = openpyxl.load_workbook(original_filepath, data_only=True)
                
                # Process each sheet
                items_processed = 0
                items_failed = 0
                processing_summary = {}
                
                for sheet_name, sheet_info in session_data['sheets'].items():
                    if sheet_name not in workbook.sheetnames:
                        continue
                    
                    # Find the processor for this sheet
                    processor = self._find_processor_for_sheet(sheet_name)
                    if not processor:
                        logging.warning(f"No processor found for sheet: {sheet_name}")
                        continue
                    
                    logging.info(f"Generating costs for sheet: {sheet_name}")
                    
                    # Process the sheet
                    sheet_result = self._process_sheet_costs(
                        workbook[sheet_name], 
                        data_workbook[sheet_name],
                        processor, 
                        sheet_info, 
                        markup_options
                    )
                    
                    items_processed += sheet_result['items_processed']
                    items_failed += sheet_result['items_failed']
                    processing_summary[sheet_name] = sheet_result
                
                # Generate summary data
                summary_data = self.summary_processor.process_summary_sheet(
                    self.sheet_processors, 
                    session_data['sheets']
                )
                
                # Add summary sheet if it doesn't exist
                if 'Summary' not in workbook.sheetnames:
                    summary_sheet = workbook.create_sheet('Summary')
                else:
                    summary_sheet = workbook['Summary']
                
                self.summary_processor.write_summary_to_worksheet(
                    summary_sheet, 
                    summary_data, 
                    markup_options
                )
                
                # Save workbook
                workbook.save(output_filepath)
                workbook.close()
                data_workbook.close()
                
                # Cleanup
                if os.path.exists(original_filepath):
                    os.remove(original_filepath)
                if session_id in self.processing_sessions:
                    del self.processing_sessions[session_id]
                
                logging.info(f"Processing complete: {items_processed} items processed, {items_failed} failed")
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'items_processed': items_processed,
                    'items_failed': items_failed,
                    'summary': summary_data,
                    'sheet_details': processing_summary
                })
                
            except Exception as e:
                logging.error(f"Error generating final BOQ: {e}", exc_info=True)
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/download/<filename>')
        def download_file(filename):
            """Download generated BOQ file"""
            filepath = os.path.join(self.output_folder, filename)
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            return jsonify({'error': 'File not found'}), 404
    
    def _process_sheet_costs(self, worksheet, data_worksheet, processor, sheet_info: Dict[str, Any], markup_options: List[int]) -> Dict[str, Any]:
        """Process costs for a single sheet using its specific processor with range-based approach"""
        try:
            # Find section boundaries (now includes pre-calculated totals)
            sections = processor.find_section_boundaries(worksheet, worksheet.max_row)
            
            # Add markup headers
            header_row_excel = processor.header_row + 1
            start_markup_col = worksheet.max_column + 1
            for i, markup_percent in enumerate(markup_options):
                cell = worksheet.cell(row=header_row_excel, column=start_markup_col + i)
                cell.value = f'Markup {markup_percent}%'
            
            # Process each matched item (write individual item costs)
            items_processed = 0
            items_failed = 0
            
            for original_row_index, match_info in sheet_info['processed_matches'].items():
                if match_info['similarity'] < 50:
                    continue
                
                try:
                    # Calculate target Excel row
                    target_row_excel = header_row_excel + 1 + int(original_row_index)
                    
                    # Get quantity from data worksheet
                    quantity = self._get_quantity_from_worksheet(
                        data_worksheet, 
                        target_row_excel, 
                        processor.column_mapping.get('quantity')
                    )
                    
                    # Calculate costs using processor-specific logic
                    master_item = match_info['item']
                    costs = processor.calculate_item_costs(master_item, quantity)
                    
                    # Write costs to worksheet
                    success = self._write_item_costs(worksheet, target_row_excel, processor, costs)
                    
                    # Write markup costs for individual items
                    processor.write_markup_costs(
                        worksheet, 
                        target_row_excel, 
                        costs['total_cost'], 
                        markup_options, 
                        start_markup_col
                    )
                    
                    if success:
                        items_processed += 1
                    else:
                        items_failed += 1
                        
                except Exception as e:
                    logging.error(f"Error processing item at row {original_row_index}: {e}")
                    items_failed += 1
            
            # Write section totals (now using pre-calculated values from find_section_boundaries)
            processor.write_section_totals(worksheet, sections, markup_options, start_markup_col)
            
            return {
                'items_processed': items_processed,
                'items_failed': items_failed,
                'sections': list(sections.keys()),
                'total_cost': sum(section['total_cost'] for section in sections.values())
            }
            
        except Exception as e:
            logging.error(f"Error processing sheet costs: {e}")
            return {
                'items_processed': 0,
                'items_failed': 0,
                'sections': [],
                'total_cost': 0.0,
                'error': str(e)
            }
    
    def _get_quantity_from_worksheet(self, data_worksheet, row: int, qty_col: Optional[int]) -> float:
        """Get quantity value from worksheet"""
        if not qty_col:
            return 1.0
        
        try:
            qty_cell = data_worksheet.cell(row=row, column=qty_col)
            return float(qty_cell.value or 0)
        except (ValueError, TypeError):
            return 1.0
    
    def _write_item_costs(self, worksheet, row: int, processor, costs: Dict[str, float]) -> bool:
        """Write item costs to worksheet"""
        try:
            success_count = 0
            
            # Write material cost
            mat_col = processor.column_mapping.get('material_cost')
            if mat_col:
                worksheet.cell(row=row, column=mat_col).value = costs['material_unit_cost']
                success_count += 1
            
            # Write labor cost
            lab_col = processor.column_mapping.get('labor_cost')
            if lab_col:
                worksheet.cell(row=row, column=lab_col).value = costs['labor_unit_cost']
                success_count += 1
            
            # Write total cost
            total_col = processor.column_mapping.get('total_cost')
            if total_col:
                worksheet.cell(row=row, column=total_col).value = costs['total_cost']
                success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Error writing costs to row {row}: {e}")
            return False
    
    def run(self, host: str = 'localhost', port: int = 5000, debug: bool = True):
        """Run the Flask application"""
        logging.info(f"Refactored BOQ Processing Server starting on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    processor = RefactoredBOQProcessor()
    processor.run()