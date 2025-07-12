#!/usr/bin/env python3
"""
Summary sheet processor - handles summary sheets that aggregate data from other sheets.
These sheets typically contain totals and overview information.
"""

from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

class SummarySheetProcessor:
    """Processor for Summary sheets that aggregate data from other processors"""
    
    def __init__(self, db_path: str, markup_rates: Dict[int, float]):
        self.db_path = db_path
        self.markup_rates = markup_rates
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Summary sheets typically contain aggregated data
        self.summary_patterns = ['sum', 'summary', 'total', 'overview', 'รวม']
    
    def matches_sheet(self, sheet_name: str) -> bool:
        """Check if this processor handles summary sheets"""
        sheet_name_lower = sheet_name.lower()
        return any(pattern in sheet_name_lower for pattern in self.summary_patterns)
    
    def process_summary_sheet(self, sheet_processors: List, processed_sheets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process summary sheet by aggregating data from other sheets.
        This creates a summary of all processed sheets.
        """
        summary_data = {
            'total_items': 0,
            'total_matched': 0,
            'total_material_cost': 0.0,
            'total_labor_cost': 0.0,
            'total_cost': 0.0,
            'sheet_breakdown': {},
            'markup_totals': {}
        }
        
        # Aggregate data from all processed sheets
        for sheet_name, sheet_data in processed_sheets.items():
            if 'processed_matches' not in sheet_data:
                continue
            
            sheet_summary = self._calculate_sheet_summary(sheet_data)
            summary_data['sheet_breakdown'][sheet_name] = sheet_summary
            
            # Add to overall totals
            summary_data['total_items'] += sheet_data.get('total_rows', 0)
            summary_data['total_matched'] += sheet_data.get('matched_count', 0)
            summary_data['total_material_cost'] += sheet_summary['material_cost']
            summary_data['total_labor_cost'] += sheet_summary['labor_cost']
            summary_data['total_cost'] += sheet_summary['total_cost']
        
        # Calculate markup totals
        for markup_percent in self.markup_rates.keys():
            markup_rate = self.markup_rates[markup_percent]
            markup_total = summary_data['total_cost'] * (1 + markup_rate)
            summary_data['markup_totals'][markup_percent] = markup_total
        
        self.logger.info(f"Summary calculated: {summary_data['total_matched']} items matched, "
                        f"Total cost: {summary_data['total_cost']:.2f}")
        
        return summary_data
    
    def _calculate_sheet_summary(self, sheet_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate summary for a single sheet"""
        summary = {
            'material_cost': 0.0,
            'labor_cost': 0.0,
            'total_cost': 0.0,
            'item_count': 0
        }
        
        processed_matches = sheet_data.get('processed_matches', {})
        
        for match_data in processed_matches.values():
            if 'item' in match_data:
                item = match_data['item']
                summary['material_cost'] += float(item.get('material_cost', 0))
                summary['labor_cost'] += float(item.get('labor_cost', 0))
                summary['total_cost'] += float(item.get('total_cost', 0))
                summary['item_count'] += 1
        
        return summary
    
    def write_summary_to_worksheet(self, worksheet, summary_data: Dict[str, Any], 
                                 markup_options: List[int]) -> None:
        """Write summary data to a summary worksheet"""
        try:
            # Clear existing content
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.value = None
            
            # Write headers
            worksheet.cell(row=1, column=1).value = "BOQ Summary Report"
            worksheet.cell(row=2, column=1).value = f"Generated: {self._get_current_timestamp()}"
            
            # Write overall totals
            row_offset = 4
            worksheet.cell(row=row_offset, column=1).value = "Overall Totals"
            worksheet.cell(row=row_offset + 1, column=1).value = "Total Items:"
            worksheet.cell(row=row_offset + 1, column=2).value = summary_data['total_items']
            worksheet.cell(row=row_offset + 2, column=1).value = "Matched Items:"
            worksheet.cell(row=row_offset + 2, column=2).value = summary_data['total_matched']
            worksheet.cell(row=row_offset + 3, column=1).value = "Material Cost:"
            worksheet.cell(row=row_offset + 3, column=2).value = summary_data['total_material_cost']
            worksheet.cell(row=row_offset + 4, column=1).value = "Labor Cost:"
            worksheet.cell(row=row_offset + 4, column=2).value = summary_data['total_labor_cost']
            worksheet.cell(row=row_offset + 5, column=1).value = "Total Cost:"
            worksheet.cell(row=row_offset + 5, column=2).value = summary_data['total_cost']
            
            # Write markup totals
            row_offset += 7
            worksheet.cell(row=row_offset, column=1).value = "Markup Options"
            for i, markup_percent in enumerate(markup_options):
                markup_total = summary_data['markup_totals'].get(markup_percent, 0)
                worksheet.cell(row=row_offset + 1 + i, column=1).value = f"Markup {markup_percent}%:"
                worksheet.cell(row=row_offset + 1 + i, column=2).value = markup_total
            
            # Write sheet breakdown
            row_offset += len(markup_options) + 3
            worksheet.cell(row=row_offset, column=1).value = "Sheet Breakdown"
            worksheet.cell(row=row_offset + 1, column=1).value = "Sheet Name"
            worksheet.cell(row=row_offset + 1, column=2).value = "Items"
            worksheet.cell(row=row_offset + 1, column=3).value = "Material Cost"
            worksheet.cell(row=row_offset + 1, column=4).value = "Labor Cost"
            worksheet.cell(row=row_offset + 1, column=5).value = "Total Cost"
            
            row_idx = row_offset + 2
            for sheet_name, sheet_summary in summary_data['sheet_breakdown'].items():
                worksheet.cell(row=row_idx, column=1).value = sheet_name
                worksheet.cell(row=row_idx, column=2).value = sheet_summary['item_count']
                worksheet.cell(row=row_idx, column=3).value = sheet_summary['material_cost']
                worksheet.cell(row=row_idx, column=4).value = sheet_summary['labor_cost']
                worksheet.cell(row=row_idx, column=5).value = sheet_summary['total_cost']
                row_idx += 1
            
            self.logger.info("Summary written to worksheet successfully")
            
        except Exception as e:
            self.logger.error(f"Error writing summary to worksheet: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for reporting"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def create_summary_report(self, summary_data: Dict[str, Any], 
                            output_path: Optional[str] = None) -> str:
        """Create a text-based summary report"""
        report_lines = [
            "BOQ Processing Summary Report",
            "=" * 50,
            f"Generated: {self._get_current_timestamp()}",
            "",
            "OVERALL TOTALS:",
            f"  Total Items: {summary_data['total_items']}",
            f"  Matched Items: {summary_data['total_matched']}",
            f"  Match Rate: {(summary_data['total_matched'] / summary_data['total_items'] * 100):.1f}%" if summary_data['total_items'] > 0 else "  Match Rate: 0%",
            f"  Material Cost: {summary_data['total_material_cost']:,.2f}",
            f"  Labor Cost: {summary_data['total_labor_cost']:,.2f}",
            f"  Total Cost: {summary_data['total_cost']:,.2f}",
            "",
            "MARKUP OPTIONS:",
        ]
        
        for markup_percent, markup_total in summary_data['markup_totals'].items():
            report_lines.append(f"  {markup_percent}% Markup: {markup_total:,.2f}")
        
        report_lines.extend([
            "",
            "SHEET BREAKDOWN:",
            "-" * 80,
            f"{'Sheet Name':<30} {'Items':<8} {'Material':<12} {'Labor':<12} {'Total':<12}",
            "-" * 80,
        ])
        
        for sheet_name, sheet_summary in summary_data['sheet_breakdown'].items():
            report_lines.append(
                f"{sheet_name:<30} {sheet_summary['item_count']:<8} "
                f"{sheet_summary['material_cost']:<12,.2f} {sheet_summary['labor_cost']:<12,.2f} "
                f"{sheet_summary['total_cost']:<12,.2f}"
            )
        
        report_content = "\n".join(report_lines)
        
        # Save to file if path provided
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.logger.info(f"Summary report saved to {output_path}")
            except Exception as e:
                self.logger.error(f"Error saving summary report: {e}")
        
        return report_content
    
    def validate_summary_data(self, summary_data: Dict[str, Any]) -> bool:
        """Validate that summary data is consistent"""
        try:
            # Check that sheet totals add up to overall totals
            calculated_material = sum(sheet['material_cost'] for sheet in summary_data['sheet_breakdown'].values())
            calculated_labor = sum(sheet['labor_cost'] for sheet in summary_data['sheet_breakdown'].values())
            calculated_total = sum(sheet['total_cost'] for sheet in summary_data['sheet_breakdown'].values())
            
            tolerance = 0.01  # Allow small rounding differences
            
            if abs(calculated_material - summary_data['total_material_cost']) > tolerance:
                self.logger.warning(f"Material cost mismatch: calculated={calculated_material}, reported={summary_data['total_material_cost']}")
                return False
            
            if abs(calculated_labor - summary_data['total_labor_cost']) > tolerance:
                self.logger.warning(f"Labor cost mismatch: calculated={calculated_labor}, reported={summary_data['total_labor_cost']}")
                return False
            
            if abs(calculated_total - summary_data['total_cost']) > tolerance:
                self.logger.warning(f"Total cost mismatch: calculated={calculated_total}, reported={summary_data['total_cost']}")
                return False
            
            self.logger.info("Summary data validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating summary data: {e}")
            return False
    
    def export_summary_to_json(self, summary_data: Dict[str, Any], output_path: str) -> bool:
        """Export summary data to JSON format"""
        try:
            import json
            
            # Create a JSON-serializable version of the data
            json_data = {
                'timestamp': self._get_current_timestamp(),
                'summary': summary_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary exported to JSON: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting summary to JSON: {e}")
            return False