#!/usr/bin/env python3
"""
Pydantic models for the BOQ Processing system.
This file contains all data models used throughout the application,
replacing the fragile dict-based approach with proper type safety and validation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class SheetType(str, Enum):
    """Enum for different sheet types"""
    INTERIOR = "interior"
    ELECTRICAL = "electrical"
    AC = "ac"
    FIRE_PROTECTION = "fp"
    UNKNOWN = "unknown"


class ItemData(BaseModel):
    """Model for individual items from master data or BOQ"""
    internal_id: str = Field(..., description="Unique internal identifier")
    code: str = Field("", description="Item code (can be empty)")
    name: str = Field(..., description="Item name")
    material_unit_cost: float = Field(0.0, ge=0, description="Material cost per unit")
    labor_unit_cost: float = Field(0.0, ge=0, description="Labor cost per unit")
    total_unit_cost: float = Field(0.0, ge=0, description="Total cost per unit")
    unit: str = Field("", description="Unit of measurement")

    @field_validator("total_unit_cost")
    def calculate_total_unit_cost(cls, v, info):
        if v == 0.0:
            material = info.data.get("material_unit_cost", 0.0)
            labor = info.data.get("labor_unit_cost", 0.0)
            return material + labor
        return v


class MatchResult(BaseModel):
    """Model for fuzzy matching results"""
    item: ItemData = Field(..., description="The matched item")
    similarity: float = Field(..., ge=0, le=100, description="Similarity score (0-100)")
    match_type: str = Field("fuzzy", description="Type of match (exact, code_match, fuzzy, etc.)")

    @field_validator("similarity")
    def validate_similarity(cls, v):
        return max(0.0, min(100.0, v))


class ProcessedMatch(BaseModel):
    """Model for processed BOQ matches with additional context"""
    original_row_index: int = Field(..., ge=0, description="Original row index in BOQ")
    row_code: str = Field("", description="Code from BOQ row")
    row_name: str = Field(..., description="Name from BOQ row")
    match: MatchResult = Field(..., description="The match result")
    quantity: Optional[float] = Field(None, ge=0, description="Quantity from BOQ")
    calculated_costs: Optional[Dict[str, Union[float, str]]] = Field(None, description="Calculated costs")


class SectionTotals(BaseModel):
    """Model for section totals calculation results"""
    material_unit_sum: float = Field(0.0, ge=0, description="Sum of material unit costs")
    labor_unit_sum: float = Field(0.0, ge=0, description="Sum of labor unit costs")
    total_unit_sum: float = Field(0.0, ge=0, description="Sum of total unit costs")
    total_sum: float = Field(0.0, ge=0, description="Sum of total costs")
    item_count: int = Field(0, ge=0, description="Number of items in section")


class SectionData(BaseModel):
    """Model for section information and boundaries"""
    section_id: str = Field(..., description="Unique section identifier")
    total_row: Optional[int] = Field(None, description="Row number of section total")
    start_row: int = Field(..., ge=1, description="First row of section content")
    end_row: int = Field(..., ge=1, description="Last row of section content")
    material_unit_sum: float = Field(0.0, ge=0, description="Sum of material unit costs")
    labor_unit_sum: float = Field(0.0, ge=0, description="Sum of labor unit costs")
    total_unit_sum: float = Field(0.0, ge=0, description="Sum of total unit costs")
    total_sum: float = Field(0.0, ge=0, description="Sum of total costs")
    item_count: int = Field(0, ge=0, description="Number of items in section")

    @field_validator("end_row")
    def validate_end_after_start(cls, v, info):
        start_row = info.data.get("start_row", 1)
        if v < start_row:
            raise ValueError(f"end_row ({v}) must be >= start_row ({start_row})")
        return v


class InteriorCostCalculation(BaseModel):
    """Model for interior sheet cost calculations"""
    material_unit_cost: Union[float, str] = Field(...)
    labor_unit_cost: Union[float, str] = Field(...)
    material_unit_total: Union[float, str] = Field(...)
    labor_unit_total: Union[float, str] = Field(...)
    total_unit_cost: Union[float, str] = Field(...)
    total_cost: Union[float, str] = Field(...)

    @field_validator("*")
    def validate_cost_values(cls, v, info):
        if info.field_name in [
            "material_unit_cost", "labor_unit_cost",
            "material_unit_total", "labor_unit_total",
            "total_unit_cost", "total_cost"
        ]:
            if isinstance(v, str):
                if v not in ["ต้องตรวจสอบ", ""]:
                    raise ValueError(f"String value must be one of ['ต้องตรวจสอบ', '']")
            elif isinstance(v, (int, float)) and v < 0:
                raise ValueError("Cost values must be non-negative")
        return v


class SystemCostCalculation(BaseModel):
    """Model for system sheet cost calculations (AC, FP, etc.)"""
    material_unit_cost: Union[float, str] = Field(...)
    labor_unit_cost: Union[float, str] = Field(...)
    material_total: Union[float, str] = Field(...)
    labor_total: Union[float, str] = Field(...)
    total_cost: Union[float, str] = Field(...)

    @field_validator("*")
    def validate_cost_values(cls, v, info):
        if info.field_name in [
            "material_unit_cost", "labor_unit_cost",
            "material_total", "labor_total", "total_cost"
        ]:
            if isinstance(v, str):
                if v not in ["ต้องตรวจสอบ", ""]:
                    raise ValueError(f"String value must be one of ['ต้องตรวจสอบ', '']")
            elif isinstance(v, (int, float)) and v < 0:
                raise ValueError("Cost values must be non-negative")
        return v


class SheetProcessingResult(BaseModel):
    """Model for sheet processing results"""
    sheet_name: str = Field(..., description="Name of the processed sheet")
    sheet_type: SheetType = Field(..., description="Type of sheet processed")
    items_processed: int = Field(0, ge=0, description="Number of items processed")
    items_failed: int = Field(0, ge=0, description="Number of items that failed processing")
    total_matches: int = Field(0, ge=0, description="Total number of matches found")
    sections_found: int = Field(0, ge=0, description="Number of sections found")
    sections_written: int = Field(0, ge=0, description="Number of sections written")
    processed_matches: Dict[str, ProcessedMatch] = Field(default_factory=dict, description="Processed matches by row index")
    sections: Dict[str, SectionData] = Field(default_factory=dict, description="Section data by section ID")

    @property
    def success_rate(self) -> float:
        total = self.items_processed + self.items_failed
        return (self.items_processed / total * 100) if total > 0 else 0.0


class DatabaseConfig(BaseModel):
    """Model for database configuration"""
    db_path: str = Field(..., description="Path to the database file")
    table_name: str = Field(..., description="Name of the database table")

    @field_validator("db_path")
    def validate_db_path(cls, v):
        if not v.strip():
            raise ValueError("Database path cannot be empty")
        return v.strip()


class MarkupConfig(BaseModel):
    """Model for markup configuration"""
    markup_rates: Dict[int, float] = Field(default_factory=dict, description="Markup rates by percentage")
    markup_options: List[int] = Field(default_factory=list, description="Available markup options")

    @field_validator("markup_rates")
    def validate_markup_rates(cls, v):
        for percentage, rate in v.items():
            if percentage < 0 or percentage > 100:
                raise ValueError(f"Markup percentage must be between 0 and 100, got {percentage}")
            if rate < 0:
                raise ValueError(f"Markup rate must be non-negative, got {rate}")
        return v


class ProcessorConfig(BaseModel):
    """Model for processor configuration"""
    sheet_pattern: str = Field(..., description="Pattern to match sheet names")
    header_row: int = Field(..., ge=0, description="Header row index (0-based)")
    column_mapping: Dict[str, int] = Field(..., description="Column mapping")
    database_config: DatabaseConfig = Field(..., description="Database configuration")
    markup_config: MarkupConfig = Field(..., description="Markup configuration")

    @field_validator("column_mapping")
    def validate_column_mapping(cls, v):
        required_fields = ['code', 'name']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Column mapping must include '{field}'")
            if v[field] <= 0:
                raise ValueError(f"Column number for '{field}' must be positive")
        return v


class BOQProcessingSession(BaseModel):
    """Model for BOQ processing session data"""
    session_id: str = Field(..., description="Unique session identifier")
    sheet_results: Dict[str, SheetProcessingResult] = Field(default_factory=dict, description="Results by sheet name")
    total_items_processed: int = Field(0, ge=0, description="Total items processed across all sheets")
    total_items_failed: int = Field(0, ge=0, description="Total items failed across all sheets")

    @property
    def overall_success_rate(self) -> float:
        total = self.total_items_processed + self.total_items_failed
        return (self.total_items_processed / total * 100) if total > 0 else 0.0

    def add_sheet_result(self, result: SheetProcessingResult) -> None:
        self.sheet_results[result.sheet_name] = result
        self.total_items_processed += result.items_processed
        self.total_items_failed += result.items_failed


class ValidationError(BaseModel):
    """Model for validation errors"""
    field: str = Field(..., description="Field that failed validation")
    error_message: str = Field(..., description="Error message")
    invalid_value: Any = Field(..., description="The invalid value")


class ProcessingError(BaseModel):
    """Model for processing errors"""
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    row_index: Optional[int] = Field(None, description="Row index where error occurred")
    item_name: Optional[str] = Field(None, description="Item name where error occurred")
    timestamp: Optional[str] = Field(None, description="Timestamp of error")


# BOQ Processor-specific models
class ProcessingSummary(BaseModel):
    """Model for processing summary statistics"""
    total_items: int = Field(0, ge=0, description="Total number of items processed")
    matched_items: int = Field(0, ge=0, description="Number of items matched")
    match_rate: float = Field(0.0, ge=0, le=100, description="Match rate percentage")
    sheets_processed: int = Field(0, ge=0, description="Number of sheets processed")
    
    @field_validator("match_rate")
    def validate_match_rate(cls, v):
        return max(0.0, min(100.0, v))


class RowDetail(BaseModel):
    """Model for BOQ row details"""
    code: str = Field("", description="Item code from BOQ row")
    name: str = Field(..., description="Item name from BOQ row")


class SheetSessionData(BaseModel):
    """Model for sheet-specific session data"""
    processor_type: str = Field(..., description="Type of processor used")
    header_row: int = Field(..., ge=0, description="Header row index")
    processed_matches: Dict[int, MatchResult] = Field(default_factory=dict, description="Processed matches by row index")
    row_details: Dict[int, RowDetail] = Field(default_factory=dict, description="Row details by row index")
    sections: Dict[str, SectionData] = Field(default_factory=dict, description="Section data by section ID")
    total_rows: int = Field(0, ge=0, description="Total number of rows in sheet")
    matched_count: int = Field(0, ge=0, description="Number of matched rows")
    
    @field_validator("matched_count")
    def validate_matched_count(cls, v, info):
        total_rows = info.data.get("total_rows", 0)
        if v > total_rows:
            raise ValueError(f"matched_count ({v}) cannot exceed total_rows ({total_rows})")
        return v


class ProcessingSession(BaseModel):
    """Model for complete processing session"""
    session_id: str = Field(..., description="Unique session identifier")
    sheets: Dict[str, SheetSessionData] = Field(default_factory=dict, description="Sheet data by sheet name")
    original_filepath: str = Field(..., description="Path to original uploaded file")
    created_at: str = Field(..., description="Session creation timestamp")
    
    @field_validator("original_filepath")
    def validate_filepath(cls, v):
        if not v.strip():
            raise ValueError("Original filepath cannot be empty")
        return v.strip()


class APIResponse(BaseModel):
    """Base model for API responses"""
    success: bool = Field(..., description="Whether the operation was successful")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ProcessBOQResponse(APIResponse):
    """Model for process BOQ API response"""
    session_id: Optional[str] = Field(None, description="Session ID for the processing session")
    summary: Optional[ProcessingSummary] = Field(None, description="Processing summary")


class GenerateFinalBOQRequest(BaseModel):
    """Model for generate final BOQ request"""
    session_id: str = Field(..., description="Session ID from previous processing")
    markup_options: List[int] = Field(default=[100, 130, 150, 50, 30], description="Markup options to apply")
    
    @field_validator("markup_options")
    def validate_markup_options(cls, v):
        for option in v:
            if option < 0 or option > 1000:
                raise ValueError(f"Markup option {option} must be between 0 and 1000")
        return v


class GenerateFinalBOQResponse(APIResponse):
    """Model for generate final BOQ API response"""
    filename: Optional[str] = Field(None, description="Generated filename")
    download_url: Optional[str] = Field(None, description="Download URL for the file")
    items_processed: Optional[int] = Field(None, ge=0, description="Number of items processed")
    items_failed: Optional[int] = Field(None, ge=0, description="Number of items that failed")
    processing_summary: Optional[Dict[str, Any]] = Field(None, description="Detailed processing summary")


class ProcessorStats(BaseModel):
    """Model for processor statistics"""
    processor_name: str = Field(..., description="Name of the processor")
    items_in_database: int = Field(0, ge=0, description="Number of items in database")
    items_with_costs: int = Field(0, ge=0, description="Number of items with cost data")
    last_sync: Optional[str] = Field(None, description="Last synchronization timestamp")
