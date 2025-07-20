#!/usr/bin/env python3
"""
Base Pydantic models for BOQ processor shared across all sheet types.
These models provide type safety and structure for common data operations.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID


class ColumnMapping(BaseModel):
    """Excel column definitions - base mapping for all sheet types"""
    code: int
    name: int
    unit: int
    quantity: int


class ItemData(BaseModel):
    """Core item structure from master data - base for all item types"""
    internal_id: str
    code: str
    name: str
    unit: str


class MatchResult(BaseModel):
    """Fuzzy matching result structure"""
    item: Dict[str, Any]  # The matched master item (will be strongly typed later)
    similarity: float     # Match confidence (0-100)


class ProcessedMatch(BaseModel):
    """BOQ processing result per row"""
    original_row_index: int
    row_code: str
    row_name: str
    match: MatchResult


class SectionStructure(BaseModel):
    """Sheet section boundaries and identification"""
    section_id: str
    start_row: int
    end_row: int
    total_row: Optional[int] = None


class ProcessingSummary(BaseModel):
    """Summary of processing results per sheet"""
    total_items: int
    matched_items: int
    match_rate: float
    sheets_processed: int