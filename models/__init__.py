#!/usr/bin/env python3
"""
BOQ Processor Pydantic Models Package

This package provides type-safe data models for the BOQ processor application.

Models are organized by domain:
- base_models: Shared models across all sheet types
- interior_models: Interior sheet specific models  
- system_models: System sheets (AC, EE, FP) models
- api_models: API request/response models
"""

# Base models - shared across all processors
from .base_models import (
    ColumnMapping,
    ItemData,
    MatchResult,
    ProcessedMatch,
    SectionStructure,
    ProcessingSummary
)

# Interior sheet models
from .interior_models import (
    InteriorColumnMapping,
    InteriorItemData,
    InteriorCostCalculation,
    InteriorSectionTotals
)

# System sheet models (AC, EE, FP)
from .system_models import (
    SystemColumnMapping,
    SystemItemData,
    SystemCostCalculation,
    SystemSectionTotals,
    ACItemData,
    EEItemData,
    FPItemData
)

# API models
from .api_models import (
    ProcessBOQResponse,
    GenerateBOQRequest,
    GenerateBOQResponse,
    ApplyMarkupRequest,
    ApplyMarkupResponse,
    CleanupSessionRequest,
    CleanupSessionResponse,
    SessionSheetInfo
)

__all__ = [
    # Base models
    "ColumnMapping",
    "ItemData", 
    "MatchResult",
    "ProcessedMatch",
    "SectionStructure",
    "ProcessingSummary",
    
    # Interior models
    "InteriorColumnMapping",
    "InteriorItemData",
    "InteriorCostCalculation", 
    "InteriorSectionTotals",
    
    # System models
    "SystemColumnMapping",
    "SystemItemData",
    "SystemCostCalculation",
    "SystemSectionTotals", 
    "ACItemData",
    "EEItemData",
    "FPItemData",
    
    # API models
    "ProcessBOQResponse",
    "GenerateBOQRequest",
    "GenerateBOQResponse",
    "ApplyMarkupRequest",
    "ApplyMarkupResponse",
    "CleanupSessionRequest", 
    "CleanupSessionResponse",
    "SessionSheetInfo"
]