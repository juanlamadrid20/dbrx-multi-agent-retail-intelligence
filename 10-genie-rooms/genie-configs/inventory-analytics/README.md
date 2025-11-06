# Inventory Analytics Genie Configuration

**Configuration Location**: `10-genie-rooms/genie-configs/inventory-analytics/`  
**Configuration Date**: 2025-01-27  
**Specification**: `specs/004-databricks-inventory-analytics/`

## Overview

This directory contains configuration artifacts for the Inventory Analytics Genie space. The Genie space enables natural language queries about inventory levels, stockout risks, overstock, replenishment, inventory movements, and inventory value.

## Configuration Files

- **`instructions.md`**: Comprehensive Genie space instructions covering business context, key terms, analysis patterns, response guidelines, error handling, multi-domain detection, and forecasting boundaries
- **`sample_queries.md`**: Sample queries organized by analytical category, covering all functional requirements (FR-001 through FR-024)
- **`data-model.md`**: Reference documentation for inventory analytics data model (Genie uses automatic schema discovery from table comments)
- **`quickstart.md`**: Step-by-step guide for applying configuration to Genie space

## Genie Space Information

**Genie Space ID**: *[To be filled after space creation]*  
**Genie Space Name**: Inventory Analytics  
**Description**: Natural language queries for inventory analytics, stockout risk, overstock, replenishment, and inventory movements

## Tables Configured

### Core Inventory Tables
- `juan_dev.retail.gold_inventory_fact` - Daily inventory snapshot fact table
- `juan_dev.retail.gold_stockout_events` - Stockout event tracking
- `juan_dev.retail.gold_inventory_movement_fact` - Inventory movement transactions

### Supporting Dimension Tables
- `juan_dev.retail.gold_product_dim` - Product master data
- `juan_dev.retail.gold_location_dim` - Location master data
- `juan_dev.retail.gold_date_dim` - Date dimension

## Prerequisites

- Tables must have proper comments and descriptions for automatic schema discovery
- Unity Catalog permissions must allow access to `juan_dev.retail` schema
- See `quickstart.md` for detailed setup instructions

## Configuration Steps

1. Verify table comments exist (see `data-model.md` for examples)
2. Create Genie space in Databricks workspace
3. Add tables to Genie space
4. Apply instructions from `instructions.md`
5. Add sample queries from `sample_queries.md`
6. Test queries and validate configuration

See `quickstart.md` for detailed step-by-step instructions.

## Testing

After configuration, test the following scenarios:
- Simple queries: Current stock status
- Medium complexity: Stockout risk assessment
- Complex queries: Inventory turnover, historical trends
- Error handling: Ambiguous queries, future dates, non-existent entities
- Multi-domain detection: Queries combining inventory with customer behavior

See `sample_queries.md` for test query examples.

## Customizations

*[Document any customizations or deviations from standard configuration here]*

## Links

- **Specification**: `specs/004-databricks-inventory-analytics/spec.md`
- **Implementation Plan**: `specs/004-databricks-inventory-analytics/plan.md`
- **Data Model Alignment**: `specs/004-databricks-inventory-analytics/DATA_MODEL_ALIGNMENT.md`
- **Quickstart Guide**: `quickstart.md` (in this directory)

## Notes

- Genie relies on automatic schema discovery from table comments
- No explicit data model documentation is needed in Genie space (automatic discovery)
- Configuration is applied via Databricks UI
- English-only queries are supported
- Forecasting capabilities are out of scope (historical/current analysis only)

