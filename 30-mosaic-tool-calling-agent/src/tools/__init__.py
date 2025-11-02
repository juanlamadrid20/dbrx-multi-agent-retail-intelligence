"""
Genie tool functions for multi-domain querying.

This module contains Unity Catalog Functions that query Databricks Genie spaces
for customer behavior and inventory management data.
"""

from .customer_behavior import query_customer_behavior_genie, register_customer_behavior_tool
from .inventory import query_inventory_genie, register_inventory_tool

__all__ = [
    'query_customer_behavior_genie',
    'register_customer_behavior_tool',
    'query_inventory_genie',
    'register_inventory_tool',
]
