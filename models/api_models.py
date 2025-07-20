#!/usr/bin/env python3
"""
Pydantic models for API requests and responses.
These models provide type safety for all API endpoints.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .base_models import ProcessedMatch, SectionStructure


class ProcessBOQResponse(BaseModel):
    """Response model for /api/process-boq endpoint"""
    success: bool
    session_id: str
    summary: Dict[str, Any]  # Will use ProcessingSummary later


class GenerateBOQRequest(BaseModel):
    """Request model for /api/generate-final-boq endpoint"""
    session_id: str
    markup_options: List[int] = [30, 50, 100, 130, 150]


class GenerateBOQResponse(BaseModel):
    """Response model for /api/generate-final-boq endpoint"""
    success: bool
    filename: str
    download_url: str
    items_processed: int
    items_failed: int
    processing_summary: Dict[str, Any]


class ApplyMarkupRequest(BaseModel):
    """Request model for /api/apply-markup endpoint"""
    session_id: str
    markup_percent: float


class ApplyMarkupResponse(BaseModel):
    """Response model for /api/apply-markup endpoint"""
    success: bool
    filename: str
    download_url: str
    markup_percent: float
    items_processed: int
    items_failed: int
    processing_summary: Dict[str, Any]


class CleanupSessionRequest(BaseModel):
    """Request model for /api/cleanup-session endpoint"""
    session_id: str


class CleanupSessionResponse(BaseModel):
    """Response model for /api/cleanup-session endpoint"""
    success: bool
    session_cleaned: bool
    files_deleted: int
    deleted_files: List[str]
    errors: List[str]


class SessionSheetInfo(BaseModel):
    """Sheet data stored in processing sessions"""
    processor_type: str
    header_row: int
    processed_matches: Dict[int, Dict[str, Any]]  # Row index -> match data
    row_details: Dict[int, Dict[str, str]]        # Row index -> {code, name}
    sections: Dict[str, Dict[str, Any]]           # Section data
    total_rows: int
    matched_count: int