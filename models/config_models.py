#!/usr/bin/env python3
"""
Pydantic models for BOQ processor configuration system.
These models define the structure for sheet processor configurations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional
from enum import Enum


class ProcessorType(str, Enum):
    """Enum for processor types"""
    INTERIOR = "interior"
    AC = "ac"
    ELECTRICAL = "electrical"
    FP = "fp"


class ColumnMapping(BaseModel):
    """Base column mapping model"""
    code: int = Field(..., gt=0, description="Code column number (1-based)")
    name: int = Field(..., gt=0, description="Name column number (1-based)")
    unit: int = Field(..., gt=0, description="Unit column number (1-based)")
    quantity: int = Field(..., gt=0, description="Quantity column number (1-based)")


class InteriorColumnMapping(ColumnMapping):
    """Interior sheet specific column mapping"""
    material_unit_cost: int = Field(..., gt=0, description="Material unit cost column")
    labor_unit_cost: int = Field(..., gt=0, description="Labor unit cost column")
    total_unit_cost: int = Field(..., gt=0, description="Total unit cost column")
    total_cost: int = Field(..., gt=0, description="Total cost column")


class SystemColumnMapping(ColumnMapping):
    """System sheets (AC, EE, FP) column mapping"""
    total_row_col: int = Field(..., gt=0, description="Total row marker column (รวมรายการ)")
    material_unit_cost: int = Field(..., gt=0, description="Material unit cost column")
    material_cost: int = Field(..., gt=0, description="Material total cost column")
    labor_unit_cost: int = Field(..., gt=0, description="Labor unit cost column") 
    labor_cost: int = Field(..., gt=0, description="Labor total cost column")
    total_cost: int = Field(..., gt=0, description="Total cost column")


class ProcessorConfig(BaseModel):
    """Configuration for a sheet processor"""
    sheet_pattern: str = Field(..., min_length=1, description="Pattern to match sheet names")
    header_row: int = Field(..., ge=0, le=100, description="Header row index (0-based)")
    table_name: str = Field(..., min_length=1, description="Database table name")
    
    @field_validator('sheet_pattern')
    def validate_sheet_pattern(cls, v):
        if not v.strip():
            raise ValueError("Sheet pattern cannot be empty")
        return v.strip().lower()
    
    @field_validator('table_name')
    def validate_table_name(cls, v):
        if not v.strip():
            raise ValueError("Table name cannot be empty")
        return v.strip()


class InteriorProcessorConfig(ProcessorConfig):
    """Interior processor specific configuration"""
    column_mapping: InteriorColumnMapping = Field(..., description="Column mapping for interior sheets")


class SystemProcessorConfig(ProcessorConfig):
    """System processor specific configuration"""
    column_mapping: SystemColumnMapping = Field(..., description="Column mapping for system sheets")


class ProcessorConfigs(BaseModel):
    """Complete configuration for all processors"""
    interior: InteriorProcessorConfig
    ac: SystemProcessorConfig
    electrical: SystemProcessorConfig
    fp: SystemProcessorConfig
    
    @classmethod
    def get_default_config(cls) -> 'ProcessorConfigs':
        """Get default configuration for all processors"""
        return cls(
            interior=InteriorProcessorConfig(
                sheet_pattern="int",
                header_row=9,
                table_name="interior_items",
                column_mapping=InteriorColumnMapping(
                    code=2,                    # Column B
                    name=3,                    # Column C
                    quantity=4,                # Column D
                    unit=5,                    # Column E
                    material_unit_cost=6,      # Column F
                    labor_unit_cost=7,         # Column G
                    total_unit_cost=8,         # Column H
                    total_cost=9               # Column I
                )
            ),
            ac=SystemProcessorConfig(
                sheet_pattern="ac",
                header_row=5,
                table_name="ac_items",
                column_mapping=SystemColumnMapping(
                    code=2,                    # Column B
                    name=4,                    # Column D
                    unit=6,                    # Column F
                    quantity=7,                # Column G
                    total_row_col=3,           # Column C
                    material_unit_cost=8,      # Column H
                    material_cost=9,           # Column I
                    labor_unit_cost=10,        # Column J
                    labor_cost=11,             # Column K
                    total_cost=12              # Column L
                )
            ),
            electrical=SystemProcessorConfig(
                sheet_pattern="ee",
                header_row=7,
                table_name="ee_items",
                column_mapping=SystemColumnMapping(
                    code=2,                    # Column B
                    name=4,                    # Column D
                    unit=6,                    # Column F
                    quantity=7,                # Column G
                    total_row_col=3,           # Column C
                    material_unit_cost=8,      # Column H
                    material_cost=9,           # Column I
                    labor_unit_cost=10,        # Column J
                    labor_cost=11,             # Column K
                    total_cost=12              # Column L
                )
            ),
            fp=SystemProcessorConfig(
                sheet_pattern="fp",
                header_row=7,
                table_name="fp_items",
                column_mapping=SystemColumnMapping(
                    code=2,                    # Column B
                    name=4,                    # Column D
                    unit=6,                    # Column F
                    quantity=7,                # Column G
                    total_row_col=3,           # Column C
                    material_unit_cost=8,      # Column H
                    material_cost=9,           # Column I
                    labor_unit_cost=10,        # Column J
                    labor_cost=11,             # Column K
                    total_cost=12              # Column L
                )
            )
        )


class ConfigUpdateRequest(BaseModel):
    """Request model for updating processor configuration"""
    processor_name: ProcessorType = Field(..., description="Name of processor to update")
    header_row: Optional[int] = Field(None, ge=0, le=100, description="New header row")
    column_mapping: Optional[Dict[str, int]] = Field(None, description="New column mapping")
    
    @field_validator('column_mapping')
    def validate_column_mapping(cls, v):
        if v is not None:
            # Check required fields
            required_fields = ["code", "name"]
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Missing required field: {field}")
                if v[field] <= 0:
                    raise ValueError(f"Column number for '{field}' must be positive")
        return v


class ConfigInquiryResponse(BaseModel):
    """Response model for configuration inquiry"""
    success: bool
    configs: Optional[ProcessorConfigs] = None
    error: Optional[str] = None


class ConfigUpdateResponse(BaseModel):
    """Response model for configuration update"""
    success: bool
    message: str
    updated_processor: Optional[str] = None
    error: Optional[str] = None