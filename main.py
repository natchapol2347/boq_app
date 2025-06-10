# BOQ Cost Automation Backend - Final Python Flask Implementation
# Using SQLite for persistent data storage and correctly processing multi-line items.

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import os
import uuid
from datetime import datetime
import re
from werkzeug.utils import secure_filename
from collections import defaultdict
from pathlib import Path
import sqlite3
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)


class BOQProcessor:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.data_dir = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor'
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_path = self.data_dir / 'master_data.db'
        
        self.master_data_folder = 'master_data'
        os.makedirs(self.master_data_folder, exist_ok=True)

        self._init_db()
        self._sync_default_master_excel()
       
        self.processing_sessions = {}
        self.upload_folder = 'uploads'
        self.output_folder = 'output'
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        self.markup_rates = {1: 1.00, 2: 1.30, 3: 1.50, 4: 0.50, 5: 0.30}
        
        self.setup_routes()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS master_items (
                    internal_id TEXT PRIMARY KEY,
                    code TEXT,
                    name TEXT NOT NULL UNIQUE,
                    material_cost REAL DEFAULT 0,
                    labor_cost REAL DEFAULT 0,
                    total_cost REAL DEFAULT 0
                )
            ''')
            conn.commit()
            logging.info(f"Database initialized at {self.db_path}")

    def _sync_default_master_excel(self):
        default_excel_path = os.path.join(self.master_data_folder, 'master.xlsx')
        logging.info(f"Checking for default master data file at: {default_excel_path}")
        if os.path.exists(default_excel_path):
            try:
                logging.info("Found master.xlsx. Synchronizing with the database...")
                result = self.load_master_data(default_excel_path)
                if result['success']:
                    logging.info("Database successfully synchronized with master.xlsx.")
                else:
                    logging.error(f"Error synchronizing with master.xlsx: {result['error']}")
            except Exception as e:
                logging.error(f"An unexpected error occurred during synchronization: {e}")
        else:
            logging.info("master.xlsx not found. The application will use the existing database.")

    def store_processing_session(self, session_id, results, original_boq):
        self.processing_sessions[session_id] = {
            'results': results, 'original_boq': original_boq,
            'created_at': datetime.now(), 'expires_at': datetime.now() + pd.Timedelta(hours=2)
        }
    
    def sanitize_item_name(self, name):
        if pd.isna(name) or not str(name).strip(): return ""
        name = str(name).lower().strip()
        name = re.sub(r'[^\w\sก-๙]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def detect_column_mapping(self, df):
        mapping = {}
        assigned_maps = set()
        patterns = {
            'name': ['name', 'รายการ', 'ชื่อรายการ', 'รายละเอียด', 'item', 'description', 'งาน', 'work', 'รายการงาน', 'ประเภทงาน'],
            'code': ['code', 'รหัส', 'รหัสรายการ', 'item_code', 'รหัสงาน'],
            'material_cost': ['material', 'วัสดุ', 'ค่าวัสดุ', 'material_cost', 'mat_cost', 'ราคาวัสดุ', 'cost_material'],
            'labor_cost': ['labor', 'labour', 'แรงงาน', 'ค่าแรงงาน', 'labor_cost', 'labour_cost', 'ค่าจ้าง', 'แรง', 'งาน'],
            'quantity': ['quantity', 'จำนวน', 'qty', 'amount', 'ปริมาณ'],
            'unit': ['unit', 'หน่วย', 'หน่วยนับ', 'units'],
            'total_cost': ['total', 'รวม', 'รวมเป็นเงิน', 'total_cost', 'ราคารวม', 'ยรวม']
        }
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for map_name, map_patterns in patterns.items():
                if map_name not in assigned_maps:
                    if any(p in col_lower for p in map_patterns):
                        mapping[col] = map_name
                        assigned_maps.add(map_name)
                        break
        return mapping

    def find_header_row(self, raw_df):
        header_indicators = ['ลำดับ', 'code', 'รายการ', 'จำนวน', 'หน่วย', 'ค่าวัสดุ', 'แรงงาน']
        for i in range(min(15, len(raw_df))):
            row = raw_df.iloc[i].astype(str).str.lower()
            matches = sum(1 for indicator in header_indicators if any(indicator in cell for cell in row if pd.notna(cell)))
            if matches >= 3: return i
        return None

    # THIS IS THE CRITICAL FUNCTION THAT WAS MISSING
    def process_grouped_items(self, df):
        if df.empty or 'code' not in df.columns or 'name' not in df.columns:
            return df
        
        processed_rows = []
        for _, row in df.iterrows():
            code = str(row.get('code', '')).strip()
            name = str(row.get('name', '')).strip()
            
            if not name or name == 'nan': continue
            
            has_code = code and code != 'nan'
            
            if has_code:
                processed_rows.append(row.copy())
            elif processed_rows:
                last_item = processed_rows[-1]
                main_name = str(last_item.get('name', '')).strip()
                combined_name = f"{main_name} - {name}"
                last_item['name'] = combined_name
                
                for cost_col in ['material_cost', 'labor_cost']:
                    if cost_col in row and pd.notna(row[cost_col]) and row[cost_col] > 0:
                        last_item[cost_col] += row[cost_col]

        if not processed_rows: return pd.DataFrame()
        return pd.DataFrame(processed_rows)

    def clean_master_data(self, df):
            # Step 1: Ensure all required columns exist.
            required_cols = ['code', 'name', 'material_cost', 'labor_cost', 'quantity', 'unit']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = 0 if 'cost' in col or 'quantity' in col else ''
            
            # --- FIX: Convert numeric columns to numbers BEFORE grouping. ---
            # This is the crucial change to prevent the TypeError.
            numeric_cols = ['material_cost', 'labor_cost', 'quantity']
            for col in numeric_cols:
                if col in df.columns:
                    # First, clean the string value, then convert to a number.
                    # Using fillna(0) handles any blank cells gracefully.
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '').str.strip(), 
                        errors='coerce'
                    ).fillna(0)
            
            # Step 2: Now that data types are correct, process the multi-line grouped items.
            df = self.process_grouped_items(df)

            # Step 3: Clean up names and filter out non-data rows.
            if 'name' in df.columns:
                df['name'] = df['name'].astype(str).str.strip()
                df = df[df['name'].str.len() > 2]
                df = df[df['name'] != 'nan']
            
            # Step 4: Calculate final values and add internal ID.
            df['total_cost'] = df.get('material_cost', 0) + df.get('labor_cost', 0)
            df['internal_id'] = [f"item_{uuid.uuid4().hex[:8]}" for _ in range(len(df))]
            return df

    def load_master_data(self, file_path):
        try:
            excel_file = pd.ExcelFile(file_path)
            # This logic now correctly processes all sheets from the master file
            all_master_dfs = []
            for sheet_name in excel_file.sheet_names:
                # Skip summary sheets
                if "sum" in sheet_name.lower(): continue
                raw_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                header_row = self.find_header_row(raw_df)
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row) if header_row is not None else pd.read_excel(file_path, sheet_name=sheet_name)
                columns_mapping = self.detect_column_mapping(df)
                df = df.rename(columns=columns_mapping)
                all_master_dfs.append(self.clean_master_data(df))
            
            combined_df = pd.concat(all_master_dfs, ignore_index=True)
            combined_df.drop_duplicates(subset=['name'], keep='last', inplace=True)
            
            db_columns = ['internal_id', 'code', 'name', 'material_cost', 'labor_cost', 'total_cost']
            columns_to_keep = [col for col in db_columns if col in combined_df.columns]
            df_to_insert = combined_df[columns_to_keep]

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for row in df_to_insert.itertuples(index=False):
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO master_items (internal_id, code, name, material_cost, labor_cost, total_cost)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (row.internal_id, row.code, row.name, row.material_cost, row.labor_cost, row.total_cost)
                    )
                conn.commit()
            return {'success': True, 'message': f'Successfully synchronized {len(df_to_insert)} items.'}
        except Exception as e:
            logging.error(f"Error loading master data from {file_path}: {e}")
            return {'success': False, 'error': str(e)}

    def find_best_match(self, item_name):
        if not item_name: return None
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_items")
            all_items = cursor.fetchall()
        if not all_items: return None
        sanitized_search = self.sanitize_item_name(item_name)
        best_match = None
        best_similarity = 0
        for item_row in all_items:
            item_dict = dict(item_row)
            similarity = fuzz.ratio(sanitized_search, self.sanitize_item_name(item_dict['name'])) / 100.0
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {'item': item_dict, 'similarity': similarity}
        return best_match
    
    def process_boq(self, boq_data):
        results = {'matched': [], 'needs_confirmation': [], 'new_items': [], 'zero_value_items': []}
        for _, row in boq_data.iterrows():
            item_name = str(row.get('name', '')).strip()
            quantity = pd.to_numeric(row.get('quantity', 0), errors='coerce')
            if pd.isna(quantity): quantity = 0
            if not item_name or item_name == 'nan': continue

            if quantity == 0:
                results['zero_value_items'].append({'original_name': item_name, 'quantity': 0, 'reason': 'Item has zero quantity.'})
                continue
            
            match = self.find_best_match(item_name)
            if match and match['similarity'] >= 0.8:
                results['matched'].append({
                    'original_name': item_name, 'matched_item': match['item'], 'similarity': match['similarity'],
                    'quantity': quantity, 'unit_cost': match['item']['total_cost'],
                    'total_cost': match['item']['total_cost'] * quantity,
                    'material_cost': match['item']['material_cost'] * quantity,
                    'labor_cost': match['item']['labor_cost'] * quantity
                })
            elif match and match['similarity'] >= 0.5:
                results['needs_confirmation'].append({
                    'original_name': item_name, 'suggested_match': match['item'],
                    'similarity': match['similarity'], 'quantity': quantity
                })
            else:
                results['new_items'].append({
                    'internal_id': f"new_{uuid.uuid4().hex[:8]}", 'name': item_name, 'code': '', 
                    'material_cost': 0, 'labor_cost': 0, 'total_cost': 0,
                    'quantity': quantity, 'needs_pricing': True
                })
        return results

    def generate_final_boq(self, processed_data, markup_options=None):
        if markup_options is None: markup_options = [1, 2, 3, 4, 5]
        final_boq = []
        for item in processed_data.get('matched', []):
            row = {
                'item_name': item['original_name'], 'matched_name': item['matched_item']['name'],
                'code': item['matched_item'].get('code', ''), 'quantity': item['quantity'],
                'unit_material_cost': item['matched_item']['material_cost'],
                'unit_labor_cost': item['matched_item']['labor_cost'],
                'unit_total_cost': item['matched_item']['total_cost'],
                'total_material_cost': item['material_cost'],
                'total_labor_cost': item['labor_cost'],
                'total_cost': item['total_cost']
            }
            for option in markup_options:
                rate = self.markup_rates.get(option, 1.0)
                markup_unit_price = item['matched_item']['total_cost'] * (1 + rate)
                row[f'markup_{option}_unit'] = round(markup_unit_price, 2)
                row[f'markup_{option}_total'] = round(markup_unit_price * item['quantity'], 2)
            final_boq.append(row)
        return final_boq

    def setup_routes(self):
        @self.app.route('/api/load-master-data', methods=['POST'])
        def load_master_data_route():
            if 'file' not in request.files: return jsonify({'success': False, 'error': 'No file uploaded'})
            file = request.files['file']
            filepath = os.path.join(self.upload_folder, secure_filename(file.filename))
            file.save(filepath)
            result = self.load_master_data(filepath)
            os.remove(filepath)
            return jsonify(result)
        
        @self.app.route('/api/process-boq', methods=['POST'])
        def process_boq_route():
            if 'file' not in request.files: return jsonify({'success': False, 'error': 'No file uploaded'})
            file = request.files['file']
            filepath = os.path.join(self.upload_folder, secure_filename(file.filename))
            file.save(filepath)
            try:
                excel_file = pd.ExcelFile(filepath)
                all_boq_dfs = []
                sheets_to_process = [s for s in excel_file.sheet_names if "sum" not in s.lower()]
                for sheet_name in sheets_to_process:
                    raw_df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                    header_row = self.find_header_row(raw_df)
                    sheet_df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row) if header_row is not None else pd.read_excel(filepath, sheet_name=sheet_name)
                    columns_mapping = self.detect_column_mapping(sheet_df)
                    sheet_df = sheet_df.rename(columns=columns_mapping)
                    all_boq_dfs.append(self.clean_master_data(sheet_df))

                combined_boq_df = pd.concat(all_boq_dfs, ignore_index=True)
                results = self.process_boq(combined_boq_df)
                session_id = str(uuid.uuid4())
                self.store_processing_session(session_id, results, combined_boq_df)
                results['session_id'] = session_id
                os.remove(filepath)
                return jsonify({'success': True, 'data': results})
            except Exception as e:
                logging.error(f"Error processing BOQ file: {e}")
                if os.path.exists(filepath): os.remove(filepath)
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/confirm-matches', methods=['POST'])
        def confirm_matches_route():
            data = request.get_json()
            session_id = data.get('session_id')
            if not session_id or session_id not in self.processing_sessions:
                return jsonify({'success': False, 'error': 'Invalid or expired session'})
            session_data = self.processing_sessions[session_id]
            results = session_data['results']
            confirmations = data.get('confirmations', [])
            
            items_to_move = []
            for conf in confirmations:
                item_index = conf.get('item_index')
                if item_index is None or item_index >= len(results['needs_confirmation']): continue
                
                item_to_process = results['needs_confirmation'][item_index]
                item_to_process['confirmed'] = conf.get('confirmed', False)
                items_to_move.append(item_to_process)

            # Process confirmed/rejected items
            for item in items_to_move:
                if item['confirmed']:
                    matched_item = item['suggested_match']
                    results['matched'].append({
                        'original_name': item['original_name'], 'matched_item': matched_item,
                        'similarity': item['similarity'], 'quantity': item['quantity'],
                        'unit_cost': matched_item['total_cost'], 'total_cost': matched_item['total_cost'] * item['quantity'],
                        'material_cost': matched_item['material_cost'] * item['quantity'],
                        'labor_cost': matched_item['labor_cost'] * item['quantity']
                    })
                else:
                    new_item = {
                        'internal_id': f"new_{uuid.uuid4().hex[:8]}", 'name': item['original_name'], 'code': '',
                        'material_cost': 0, 'labor_cost': 0, 'total_cost': 0,
                        'quantity': item['quantity'], 'needs_pricing': True
                    }
                    results['new_items'].append(new_item)
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("INSERT OR IGNORE INTO master_items (internal_id, name) VALUES (?, ?)", (new_item['internal_id'], new_item['name']))
            
            # Rebuild the needs_confirmation list
            results['needs_confirmation'] = [item for item in results['needs_confirmation'] if item not in items_to_move]
            return jsonify({'success': True, 'updated_results': results})
        
        @self.app.route('/api/generate-final-boq', methods=['POST'])
        def generate_final_boq_route():
            data = request.get_json()
            session_id = data.get('session_id')
            processed_data = self.processing_sessions[session_id]['results'] if session_id and session_id in self.processing_sessions else data.get('processed_data', {})
            try:
                final_boq = self.generate_final_boq(processed_data, data.get('markup_options'))
                df = pd.DataFrame(final_boq)
                filename = f"final_boq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filepath = os.path.join(self.output_folder, filename)
                df.to_excel(filepath, index=False, engine='openpyxl')
                if session_id and session_id in self.processing_sessions:
                    del self.processing_sessions[session_id]
                return jsonify({'success': True, 'filename': filename, 'download_url': f'/api/download/{filename}'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/download/<filename>')
        def download_file(filename):
            filepath = os.path.join(self.output_folder, filename)
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            return jsonify({'error': 'File not found'}), 404

    def run(self, host='localhost', port=5000, debug=True):
        logging.info(f"BOQ Processing Server starting on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    processor = BOQProcessor()
    processor.run()