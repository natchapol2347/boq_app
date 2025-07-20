#!/usr/bin/env python3
"""
Pydantic models specific to interior sheet processing.
Interior sheets have material and labor costs but no separate quantity-based calculations.
"""

from pydantic import BaseModel
from .base_models import ItemData, ColumnMapping, SectionStructure


class InteriorColumnMapping(ColumnMapping):
    """Interior sheet Excel column definitions"""
    material_cost: int
    labor_cost: int
    total_cost: int


class InteriorItemData(ItemData):
    """Interior sheet item structure from master data"""
    material_unit_cost: float
    labor_unit_cost: float
    
    @property
    def total_unit_cost(self) -> float:
        """Calculated total unit cost"""
        return self.material_unit_cost + self.labor_unit_cost


class InteriorCostCalculation(BaseModel):
    """Interior cost calculation result for a single item"""
    material_unit_cost: float
    labor_unit_cost: float
    material_unit_total: float  # Same as material_unit_cost for interior
    labor_unit_total: float     # Same as labor_unit_cost for interior
    total_unit_cost: float
    total_cost: float          # total_unit_cost * quantity


class InteriorSectionTotals(BaseModel):
    """Interior section totals calculation result"""
    material_unit_sum: float
    labor_unit_sum: float
    total_unit_sum: float
    total_sum: float
    item_count: int