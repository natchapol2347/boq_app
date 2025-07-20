#!/usr/bin/env python3
"""
Pydantic models for system sheets processing (AC, EE, FP).
System sheets have material and labor costs that are calculated based on quantities,
creating separate unit costs and total costs.
"""

from pydantic import BaseModel
from .base_models import ItemData, ColumnMapping, SectionStructure


class SystemColumnMapping(ColumnMapping):
    """System sheets Excel column definitions (AC, EE, FP)"""
    total_row_col: int          # Column for รวมรายการ markers
    material_unit_cost: int
    material_cost: int          # material_unit_cost * quantity
    labor_unit_cost: int
    labor_cost: int            # labor_unit_cost * quantity
    total_cost: int            # material_cost + labor_cost


class SystemItemData(ItemData):
    """System sheets item structure from master data"""
    material_unit_cost: float
    material_cost: float        # material_unit_cost * quantity
    labor_unit_cost: float
    labor_cost: float          # labor_unit_cost * quantity
    
    @property
    def total_cost(self) -> float:
        """Calculated total cost"""
        return self.material_cost + self.labor_cost


class SystemCostCalculation(BaseModel):
    """System sheets cost calculation result for a single item"""
    material_unit_cost: float
    material_cost: float       # material_unit_cost * quantity
    labor_unit_cost: float
    labor_cost: float         # labor_unit_cost * quantity
    total_cost: float         # material_cost + labor_cost


class SystemSectionTotals(BaseModel):
    """System sheets section totals calculation result"""
    material_unit_sum: float
    material_sum: float
    labor_unit_sum: float
    labor_sum: float
    total_sum: float
    item_count: int


class ACItemData(SystemItemData):
    """AC sheet specific item data - inherits from SystemItemData"""
    pass


class EEItemData(SystemItemData):
    """EE sheet specific item data - inherits from SystemItemData"""
    pass


class FPItemData(SystemItemData):
    """FP sheet specific item data - inherits from SystemItemData"""
    pass