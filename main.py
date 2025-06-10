# BOQ Cost Automation Backend - Complete Python Flask Implementation
# Enhanced for Thai BOQ processing with Excel-only storage

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz, process
import os
import uuid
from datetime import datetime
import re
import json
from werkzeug.utils import secure_filename
from collections import defaultdict

class BOQProcessor:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Data storage - all in memory/Excel
        self.master_data = pd.DataFrame()
        self.inverted_index = defaultdict(set)
        self.master_data_file = None  # Track current master data file
        
        # Configuration
        self.upload_folder = 'uploads'
        self.output_folder = 'output'
        self.master_data_folder = 'master_data'
        
        # Create directories
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.master_data_folder, exist_ok=True)
        
        # Setup routes
        self.setup_routes()
        
        # Markup rates
        self.markup_rates = {
            1: 1.00,  # 100%
            2: 1.30,  # 130%
            3: 1.50,  # 150%
            4: 0.50,  # 50%
            5: 0.30   # 30%
        }

    def save_master_data(self, filename=None):
        """Save current master data to Excel file"""
        if filename is None:
            filename = f"master_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = os.path.join(self.master_data_folder, filename)
        self.master_data.to_excel(filepath, index=False)
        self.master_data_file = filepath
        return filepath

    def load_existing_master_data(self, filepath):
        """Load existing master data file"""
        try:
            self.master_data = pd.read_excel(filepath)
            self.master_data_file = filepath
            self.create_inverted_index()
            return True
        except Exception as e:
            print(f"Error loading existing master data: {e}")
            return False

    def sanitize_item_name(self, name):
        """Clean and normalize item names for better matching"""
        if pd.isna(name) or not str(name).strip():
            return ""
        
        name = str(name).lower().strip()
        # Remove special characters but keep Thai characters
        name = re.sub(r'[^\w\sก-๙]', ' ', name)
        # Multiple spaces to single space
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def create_inverted_index(self):
        """Create inverted index for fast text search"""
        self.inverted_index.clear()
        
        if self.master_data.empty:
            return
            
        for idx, row in self.master_data.iterrows():
            sanitized_name = self.sanitize_item_name(row['name'])
            words = sanitized_name.split()
            
            for word in words:
                if len(word) > 2:  # Skip very short words
                    self.inverted_index[word].add(idx)

    def detect_column_mapping(self, df):
        """Auto-detect column mappings based on content and headers - Enhanced for Thai BOQ"""
        mapping = {}
        
        # Enhanced patterns for Thai BOQ files
        name_patterns = [
            'name', 'รายการ', 'ชื่อรายการ', 'รายละเอียด', 'item', 'description',
            'งาน', 'work', 'รายการงาน', 'ประเภทงาน'
        ]
        code_patterns = [
            'code', 'รหัส', 'รหัสรายการ', 'item_code', 'รหัสงาน'
        ]
        material_patterns = [
            'material', 'วัสดุ', 'ค่าวัสดุ', 'material_cost', 'mat_cost',
            'ราคาวัสดุ', 'cost_material'
        ]
        labor_patterns = [
            'labor', 'labour', 'แรงงาน', 'ค่าแรงงาน', 'labor_cost', 'labour_cost',
            'ค่าจ้าง', 'แรง', 'งาน'
        ]
        quantity_patterns = [
            'quantity', 'จำนวน', 'qty', 'amount', 'ปริมาณ'
        ]
        unit_patterns = [
            'unit', 'หน่วย', 'หน่วยนับ', 'units'
        ]
        total_patterns = [
            'total', 'รวม', 'รวมเป็นเงิน', 'total_cost', 'ราคารวม', 'ยรวม'
        ]
        
        # Check each column header
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Check for name column (highest priority for column 2 in Thai BOQ)
            if any(pattern in col_lower for pattern in name_patterns):
                mapping[col] = 'name'
            # Check for code column  
            elif any(pattern in col_lower for pattern in code_patterns):
                mapping[col] = 'code'
            # Check for material cost
            elif any(pattern in col_lower for pattern in material_patterns):
                mapping[col] = 'material_cost'
            # Check for labor cost
            elif any(pattern in col_lower for pattern in labor_patterns):
                mapping[col] = 'labor_cost'
            # Check for quantity
            elif any(pattern in col_lower for pattern in quantity_patterns):
                mapping[col] = 'quantity'
            # Check for unit
            elif any(pattern in col_lower for pattern in unit_patterns):
                mapping[col] = 'unit'
            # Check for total
            elif any(pattern in col_lower for pattern in total_patterns):
                mapping[col] = 'total_cost'
        
        # Special handling for Thai BOQ structure where data might be in specific columns
        # If we have minimal mapping, try positional mapping based on Thai BOQ standard
        if len(mapping) < 3:
            cols = list(df.columns)
            if len(cols) >= 8:  # Standard Thai BOQ has 8+ columns
                # Standard positions: ลำดับ(0), CODE(1), รายการ(2), จำนวน(3), หน่วย(4), ค่าวัสดุ(5), แรงงาน(6), รวม(7)
                positional_mapping = {
                    cols[1]: 'code',        # Column 1: CODE
                    cols[2]: 'name',        # Column 2: รายการ (most important)
                    cols[3]: 'quantity',    # Column 3: จำนวน
                    cols[4]: 'unit',        # Column 4: หน่วย
                    cols[5]: 'material_cost', # Column 5: ค่าวัสดุ
                    cols[6]: 'labor_cost',   # Column 6: แรงงาน
                    cols[7]: 'total_cost'    # Column 7: รวม
                }
                
                # Merge with existing mapping, giving priority to header-based detection
                for col, mapped_name in positional_mapping.items():
                    if col not in mapping:
                        mapping[col] = mapped_name
        
        return mapping

    def find_header_row(self, raw_df):
        """Find the row that contains column headers in Thai BOQ files"""
        # Look for common Thai BOQ header patterns
        header_indicators = ['ลำดับ', 'code', 'รายการ', 'จำนวน', 'หน่วย', 'ค่าวัสดุ', 'แรงงาน']
        
        for i in range(min(15, len(raw_df))):  # Check first 15 rows
            row = raw_df.iloc[i].astype(str).str.lower()
            matches = sum(1 for indicator in header_indicators 
                         if any(indicator in cell for cell in row if pd.notna(cell)))
            
            if matches >= 3:  # If we find at least 3 header indicators
                return i
        
        return None

    def clean_master_data(self, df):
        """Clean and process master data - Enhanced to handle grouped items"""
        # Ensure required columns exist
        required_cols = ['code', 'name', 'material_cost', 'labor_cost', 'quantity', 'unit']
        for col in required_cols:
            if col not in df.columns:
                if 'cost' in col:
                    df[col] = 0
                else:
                    df[col] = ''
        
        # Process grouped items (consecutive rows without code)
        df = self.process_grouped_items(df)
        
        # Clean name column
        if 'name' in df.columns:
            df['name'] = df['name'].astype(str).str.strip()
            # Remove rows with empty or invalid names
            df = df[df['name'].str.len() > 2]
            df = df[df['name'] != 'nan']
            df = df[~df['name'].str.contains('total|รวม|sum', case=False, na=False)]
        
        # Clean numeric columns
        numeric_cols = ['material_cost', 'labor_cost', 'quantity']
        for col in numeric_cols:
            if col in df.columns:
                # Remove commas and spaces, convert to numeric
                df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate total cost
        df['total_cost'] = df.get('material_cost', 0) + df.get('labor_cost', 0)
        
        # Add internal ID
        df['internal_id'] = [f"item_{uuid.uuid4().hex[:8]}" for _ in range(len(df))]
        
        return df

    def process_grouped_items(self, df):
        """Process consecutive rows without code as grouped items"""
        if df.empty or 'code' not in df.columns or 'name' not in df.columns:
            return df
        
        processed_rows = []
        current_main_item = None
        
        for idx, row in df.iterrows():
            code = str(row.get('code', '')).strip()
            name = str(row.get('name', '')).strip()
            
            # Skip completely empty rows
            if not name or name == 'nan':
                continue
            
            # Check if this row has a code (main item) or not (sub-item)
            has_code = code and code != 'nan' and len(code) > 0
            
            if has_code:
                # This is a main item
                current_main_item = row.copy()
                current_main_item['sub_items'] = []  # Track sub-items
                processed_rows.append(current_main_item)
                
            else:
                # This is a sub-item (no code)
                if current_main_item is not None:
                    # Combine sub-item description with main item
                    main_name = str(current_main_item['name']).strip()
                    sub_name = name.strip()
                    
                    # Combine names intelligently
                    if sub_name.startswith('-'):
                        # Already formatted as sub-item
                        combined_name = f"{main_name} {sub_name}"
                    else:
                        # Add as sub-item
                        combined_name = f"{main_name} - {sub_name}"
                    
                    # Update the main item's name
                    current_main_item['name'] = combined_name
                    current_main_item['sub_items'].append(sub_name)
                    
                    # If sub-item has costs, add them to main item
                    for cost_col in ['material_cost', 'labor_cost']:
                        if cost_col in row and pd.notna(row[cost_col]):
                            sub_cost = pd.to_numeric(str(row[cost_col]).replace(',', '').replace(' ', ''), errors='coerce')
                            if not pd.isna(sub_cost) and sub_cost > 0:
                                main_cost = pd.to_numeric(str(current_main_item[cost_col]).replace(',', '').replace(' ', ''), errors='coerce')
                                if pd.isna(main_cost):
                                    main_cost = 0
                                current_main_item[cost_col] = main_cost + sub_cost
                else:
                    # No current main item, treat as standalone
                    standalone_item = row.copy()
                    standalone_item['code'] = ''  # No code for standalone
                    processed_rows.append(standalone_item)
        
        # Convert back to DataFrame
        if processed_rows:
            result_df = pd.DataFrame(processed_rows)
            # Remove the temporary sub_items column
            if 'sub_items' in result_df.columns:
                result_df = result_df.drop('sub_items', axis=1)
            return result_df
        else:
            return df

    def load_master_data(self, file_path):
        """Load master data from Excel file - Enhanced for Thai BOQ"""
        try:
            # Handle multi-sheet Excel files
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                excel_file = pd.ExcelFile(file_path)
                
                # For Thai BOQ files, try to find the sheet with most data
                best_sheet = None
                max_rows = 0
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        temp_df = pd.read_excel(file_path, sheet_name=sheet_name)
                        if len(temp_df) > max_rows:
                            max_rows = len(temp_df)
                            best_sheet = sheet_name
                    except:
                        continue
                
                if not best_sheet:
                    best_sheet = excel_file.sheet_names[0]
                
                # Read the sheet without header first to analyze structure
                raw_df = pd.read_excel(file_path, sheet_name=best_sheet, header=None)
                
                # For Thai BOQ, find where the actual data starts
                header_row = self.find_header_row(raw_df)
                
                if header_row is not None:
                    # Read again with proper header
                    df = pd.read_excel(file_path, sheet_name=best_sheet, header=header_row)
                else:
                    # Fallback to reading normally
                    df = pd.read_excel(file_path, sheet_name=best_sheet)
                
                # Auto-detect columns
                columns_mapping = self.detect_column_mapping(df)
                
                # Rename columns to standard names
                df = df.rename(columns=columns_mapping)
                
                # Clean the data
                df = self.clean_master_data(df)
                
                # Store the processed data
                self.master_data = df.reset_index(drop=True)
                self.create_inverted_index()
                
                return {
                    'success': True,
                    'message': f'Successfully loaded {len(self.master_data)} items from sheet "{best_sheet}"',
                    'sheet_used': best_sheet,
                    'columns_detected': columns_mapping,
                    'sample_data': self.master_data.head(3).to_dict('records') if not self.master_data.empty else []
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Failed to load master data: {str(e)}'}

    def find_candidate_matches(self, search_name):
        """Find candidate matches using inverted index"""
        sanitized_search = self.sanitize_item_name(search_name)
        search_words = sanitized_search.split()
        
        candidates = defaultdict(int)
        
        for word in search_words:
            if word in self.inverted_index:
                for idx in self.inverted_index[word]:
                    candidates[idx] += 1
        
        # Sort by word match count
        return sorted(candidates.keys(), key=lambda x: candidates[x], reverse=True)

    def find_best_match(self, item_name):
        """Find best match for an item name using fuzzy matching"""
        if not item_name or self.master_data.empty:
            return None
            
        sanitized_search = self.sanitize_item_name(item_name)
        
        # Get candidates from inverted index
        candidates = self.find_candidate_matches(item_name)
        
        # If no candidates from index, check all items (fallback)
        if not candidates:
            candidates = list(range(len(self.master_data)))
        
        best_match = None
        best_similarity = 0
        
        # Check top candidates (performance optimization)
        candidates_to_check = candidates[:min(50, len(candidates))]
        
        for idx in candidates_to_check:
            if idx >= len(self.master_data):
                continue
                
            candidate_name = self.master_data.iloc[idx]['name']
            sanitized_candidate = self.sanitize_item_name(candidate_name)
            
            # Use multiple similarity methods for better accuracy
            ratio1 = fuzz.ratio(sanitized_search, sanitized_candidate) / 100.0
            ratio2 = fuzz.partial_ratio(sanitized_search, sanitized_candidate) / 100.0
            ratio3 = fuzz.token_sort_ratio(sanitized_search, sanitized_candidate) / 100.0
            
            # Take the maximum similarity
            similarity = max(ratio1, ratio2, ratio3)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'item': self.master_data.iloc[idx].to_dict(),
                    'similarity': similarity,
                    'index': idx
                }
        
        return best_match

    def process_boq(self, boq_data):
        """Process BOQ data and match items"""
        results = {
            'matched': [],
            'needs_confirmation': [],
            'new_items': [],
            'summary': {}
        }
        
        for idx, row in boq_data.iterrows():
            item_name = str(row.get('name', '')).strip()
            quantity = pd.to_numeric(row.get('quantity', 0), errors='coerce')
            if pd.isna(quantity):
                quantity = 0
                
            if not item_name or item_name == 'nan':
                continue
            
            match = self.find_best_match(item_name)
            
            if match and match['similarity'] >= 0.8:
                # High confidence match
                matched_item = match['item']
                results['matched'].append({
                    'original_name': item_name,
                    'matched_item': matched_item,
                    'similarity': match['similarity'],
                    'quantity': quantity,
                    'unit_cost': matched_item['total_cost'],
                    'total_cost': matched_item['total_cost'] * quantity,
                    'material_cost': matched_item['material_cost'] * quantity,
                    'labor_cost': matched_item['labor_cost'] * quantity
                })
                
            elif match and match['similarity'] >= 0.5:
                # Needs confirmation
                results['needs_confirmation'].append({
                    'original_n ame': item_name,
                    'suggested_match': match['item'],
                    'similarity': match['similarity'],
                    'quantity': quantity,
                    'match_index': match['index']
                })
                
            else:
                # Create new item
                new_item = {
                    'internal_id': f"new_{uuid.uuid4().hex[:8]}",
                    'name': item_name,
                    'code': '',
                    'material_cost': 0,
                    'labor_cost': 0,
                    'total_cost': 0,
                    'quantity': quantity,
                    'needs_pricing': True
                }
                results['new_items'].append(new_item)
        
        # Generate summary
        results['summary'] = {
            'total_items': len(boq_data),
            'matched_count': len(results['matched']),
            'confirmation_needed': len(results['needs_confirmation']),
            'new_items_count': len(results['new_items']),
            'match_rate': len(results['matched']) / len(boq_data) * 100 if len(boq_data) > 0 else 0
        }
        
        return results

    def apply_markup(self, cost, markup_option):
        """Apply markup to cost"""
        rate = self.markup_rates.get(markup_option, 1.0)
        return cost * (1 + rate)

    def generate_final_boq(self, processed_data, markup_options=None):
        """Generate final BOQ with costs and markup pricing"""
        if markup_options is None:
            markup_options = [1, 2, 3, 4, 5]
        
        final_boq = []
        
        # Process matched items
        for item in processed_data.get('matched', []):
            row = {
                'item_name': item['original_name'],
                'matched_name': item['matched_item']['name'],
                'code': item['matched_item'].get('code', ''),
                'quantity': item['quantity'],
                'unit_material_cost': item['matched_item']['material_cost'],
                'unit_labor_cost': item['matched_item']['labor_cost'],
                'unit_total_cost': item['matched_item']['total_cost'],
                'total_material_cost': item['material_cost'],
                'total_labor_cost': item['labor_cost'],
                'total_cost': item['total_cost']
            }
            
            # Add markup columns
            for option in markup_options:
                markup_unit_price = self.apply_markup(item['matched_item']['total_cost'], option)
                markup_total_price = markup_unit_price * item['quantity']
                
                row[f'markup_{option}_unit'] = round(markup_unit_price, 2)
                row[f'markup_{option}_total'] = round(markup_total_price, 2)
            
            final_boq.append(row)
        
        return final_boq

    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health():
            return jsonify({'status': 'OK', 'timestamp': datetime.now().isoformat()})
        
        @self.app.route('/api/load-master-data', methods=['POST'])
        def load_master_data():
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'})
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'})
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)
            
            # Load master data
            result = self.load_master_data(filepath)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify(result)
        
        @self.app.route('/api/process-boq', methods=['POST'])
        def process_boq():
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'})
            
            if self.master_data.empty:
                return jsonify({'success': False, 'error': 'Master data not loaded'})
            
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)
            
            try:
                # Read BOQ file - same format as master data
                excel_file = pd.ExcelFile(filepath)
                
                # For BOQ processing, also find the best sheet
                best_sheet = None
                max_rows = 0
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        temp_df = pd.read_excel(filepath, sheet_name=sheet_name)
                        if len(temp_df) > max_rows:
                            max_rows = len(temp_df)
                            best_sheet = sheet_name
                    except:
                        continue
                
                if not best_sheet:
                    best_sheet = 0
                
                # Read the sheet without header first
                raw_df = pd.read_excel(filepath, sheet_name=best_sheet, header=None)
                header_row = self.find_header_row(raw_df)
                
                if header_row is not None:
                    boq_df = pd.read_excel(filepath, sheet_name=best_sheet, header=header_row)
                else:
                    boq_df = pd.read_excel(filepath, sheet_name=best_sheet)
                
                # Auto-detect columns
                columns_mapping = self.detect_column_mapping(boq_df)
                boq_df = boq_df.rename(columns=columns_mapping)
                
                # Clean BOQ data
                boq_df = self.clean_master_data(boq_df)
                
                # Process BOQ
                results = self.process_boq(boq_df)
                
                # Clean up
                os.remove(filepath)
                
                return jsonify({'success': True, 'data': results})
                
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/confirm-match', methods=['POST'])
        def confirm_match():
            data = request.get_json()
            original_name = data.get('original_name')
            match_index = data.get('match_index')
            confirm = data.get('confirm', False)
            
            if confirm and match_index is not None:
                # User confirmed the match
                matched_item = self.master_data.iloc[match_index].to_dict()
                return jsonify({'success': True, 'confirmed_match': matched_item})
            else:
                # User rejected - create new item entry
                new_item = {
                    'internal_id': f"new_{uuid.uuid4().hex[:8]}",
                    'name': original_name,
                    'code': '',
                    'material_cost': 0,
                    'labor_cost': 0,
                    'total_cost': 0,
                    'needs_pricing': True
                }
                
                # Add to master data for future use
                new_row = pd.DataFrame([{
                    'internal_id': f"new_{uuid.uuid4().hex[:8]}",
                    'name': original_name,
                    'code': '',
                    'material_cost': 0,
                    'labor_cost': 0,
                    'total_cost': 0
                }])
                self.master_data = pd.concat([self.master_data, new_row], ignore_index=True)
                self.create_inverted_index()
                
                # Save updated master data
                self.save_master_data()
                
                return jsonify({'success': True, 'new_item': new_item, 'master_updated': True})
        
        @self.app.route('/api/generate-final-boq', methods=['POST'])
        def generate_final_boq():
            data = request.get_json()
            processed_data = data.get('processed_data', {})
            markup_options = data.get('markup_options', [1, 2, 3, 4, 5])
            
            try:
                final_boq = self.generate_final_boq(processed_data, markup_options)
                
                # Create Excel file
                df = pd.DataFrame(final_boq)
                filename = f"final_boq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filepath = os.path.join(self.output_folder, filename)
                
                df.to_excel(filepath, index=False, engine='openpyxl')
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'download_url': f'/api/download/{filename}',
                    'data': final_boq[:10],  # First 10 rows for preview
                    'total_rows': len(final_boq)
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/download/<filename>', methods=['GET'])
        def download_file(filename):
            filepath = os.path.join(self.output_folder, filename)
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            else:
                return jsonify({'error': 'File not found'}), 404
        
        @self.app.route('/api/master-data-summary', methods=['GET'])
        def master_data_summary():
            if self.master_data.empty:
                return jsonify({
                    'loaded': False,
                    'message': 'No master data loaded'
                })
            
            summary = {
                'loaded': True,
                'total_items': len(self.master_data),
                'columns': list(self.master_data.columns),
                'sample_data': self.master_data.head(5).to_dict('records'),
                'cost_statistics': {
                    'avg_material_cost': float(self.master_data['material_cost'].mean()),
                    'avg_labor_cost': float(self.master_data['labor_cost'].mean()),
                    'avg_total_cost': float(self.master_data['total_cost'].mean()),
                    'total_value': float(self.master_data['total_cost'].sum())
                },
                'current_file': self.master_data_file
            }
            
            return jsonify(summary)
        
        @self.app.route('/api/save-master-data', methods=['POST'])
        def save_master_data_route():
            """Save current master data to Excel"""
            try:
                data = request.get_json()
                filename = data.get('filename', None)
                filepath = self.save_master_data(filename)
                
                return jsonify({
                    'success': True, 
                    'message': 'Master data saved successfully',
                    'filepath': filepath,
                    'download_url': f'/api/download-master/{os.path.basename(filepath)}'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/download-master/<filename>', methods=['GET'])
        def download_master_data(filename):
            """Download master data file"""
            filepath = os.path.join(self.master_data_folder, filename)
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            else:
                return jsonify({'error': 'Master data file not found'}), 404
        
        @self.app.route('/api/list-master-files', methods=['GET'])
        def list_master_files():
            """List all available master data files"""
            try:
                files = []
                for filename in os.listdir(self.master_data_folder):
                    if filename.endswith(('.xlsx', '.xls')):
                        filepath = os.path.join(self.master_data_folder, filename)
                        stat = os.stat(filepath)
                        files.append({
                            'filename': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'download_url': f'/api/download-master/{filename}'
                        })
                
                return jsonify({'success': True, 'files': files})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/load-existing-master', methods=['POST'])
        def load_existing_master():
            """Load an existing master data file"""
            data = request.get_json()
            filename = data.get('filename')
            
            if not filename:
                return jsonify({'success': False, 'error': 'No filename provided'})
            
            filepath = os.path.join(self.master_data_folder, filename)
            
            if not os.path.exists(filepath):
                return jsonify({'success': False, 'error': 'File not found'})
            
            if self.load_existing_master_data(filepath):
                return jsonify({
                    'success': True, 
                    'message': f'Loaded {len(self.master_data)} items from {filename}',
                    'total_items': len(self.master_data)
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to load master data file'})

    def run(self, host='localhost', port=5000, debug=True):
        """Start the Flask server"""
        print(f"BOQ Processing Server starting on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Usage
if __name__ == '__main__':
    processor = BOQProcessor()
    processor.run()