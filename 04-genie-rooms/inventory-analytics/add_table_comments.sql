-- ============================================================================
-- Table and Column Comments for Inventory Analytics Genie Space
-- ============================================================================
-- Purpose: Enable automatic schema discovery for Databricks Genie
-- Tables: Core inventory fact tables and supporting dimension tables
-- Schema: juan_dev.retail
-- Date: 2025-01-27
-- ============================================================================

-- ============================================================================
-- CORE INVENTORY FACT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- gold_inventory_fact: Daily inventory snapshot fact table
-- ----------------------------------------------------------------------------
COMMENT ON TABLE juan_dev.retail.gold_inventory_fact IS 
'Daily inventory snapshot fact table. Grain: Product × Location × Date. 
Tracks inventory levels, stockout status, days of supply, reorder points, and inventory values. 
Use is_stockout flag to identify current stockouts. Use stockout_duration_days for extended stockout analysis. 
Query latest date_key for current inventory state. Enables stockout risk assessment, overstock identification, and inventory value analysis.';

-- Foreign keys and dimensions
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN product_key COMMENT 'Foreign key to gold_product_dim. Links inventory records to product master data.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN location_key COMMENT 'Foreign key to gold_location_dim. Links inventory records to location master data.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN date_key COMMENT 'Date in YYYYMMDD format. Foreign key to gold_date_dim. Use MAX(date_key) to get current inventory state.';

-- Quantity fields
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN quantity_on_hand COMMENT 'Total physical inventory at location. Sum of quantity_available + quantity_reserved + quantity_damaged.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN quantity_available COMMENT 'Available for sale after deductions from sales. Never negative. If quantity_available = 0, then is_stockout = TRUE. Use for stockout identification and risk assessment.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN quantity_reserved COMMENT 'Inventory reserved for orders but not yet shipped. Part of quantity_on_hand but not available for sale.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN quantity_in_transit COMMENT 'Inventory currently being shipped to location. Use for in-transit inventory analysis and expected arrival tracking.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN quantity_damaged COMMENT 'Damaged or unsellable inventory. Part of quantity_on_hand but not available for sale.';

-- Stockout flags and duration
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN is_stockout COMMENT 'TRUE when quantity_available = 0. Use to identify products currently out of stock. Filter by latest date_key for current stockout status.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN stockout_duration_days COMMENT 'Consecutive days at zero inventory. NULL if not currently in stockout. Use to identify extended stockouts (e.g., >7 days) requiring urgent attention.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN is_overstock COMMENT 'TRUE when inventory exceeds normal levels based on days of supply thresholds. Use for overstock identification and excess inventory analysis.';

-- Supply and risk metrics
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN days_of_supply COMMENT 'Projected days until stockout based on current inventory levels and demand patterns. Lower values indicate higher stockout risk. Use for stockout risk assessment: <=3 days = High Risk, <=7 days = Medium Risk. Also used for overstock identification: >60 days = Moderate Overstock, >90 days = Severe Overstock.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN stock_cover_days COMMENT 'Days of inventory coverage. Alternative metric to days_of_supply. Use for supply status assessment.';

-- Reorder management
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN reorder_point COMMENT 'Inventory threshold quantity that triggers a reorder. When quantity_available <= reorder_point, product needs reordering. Use for reorder identification and stockout risk assessment (combine with days_of_supply for risk levels).';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN reorder_quantity COMMENT 'Standard quantity to order when reorder point is reached. Use for reorder recommendations.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN last_replenishment_date COMMENT 'Most recent inventory receipt date. Use to track replenishment history and calculate days since last replenishment.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN next_replenishment_date COMMENT 'Scheduled next receipt date (fixed schedule). NULL if no scheduled replenishment. Use for in-transit inventory analysis and replenishment schedule tracking. Calculate days_until_arrival = DATEDIFF(next_replenishment_date, CURRENT_DATE).';

-- Inventory value
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN inventory_value_cost COMMENT 'Inventory valued at cost. Use for inventory value analysis by location, category, or product. Sum for total inventory value at cost.';
ALTER TABLE juan_dev.retail.gold_inventory_fact ALTER COLUMN inventory_value_retail COMMENT 'Inventory valued at retail price. Use for inventory value analysis. Total margin = inventory_value_retail - inventory_value_cost.';


-- ----------------------------------------------------------------------------
-- gold_stockout_events: Stockout event tracking with lost sales metrics
-- ----------------------------------------------------------------------------
COMMENT ON TABLE juan_dev.retail.gold_stockout_events IS 
'Stockout event tracking with lost sales metrics. Grain: One record per stockout event (product × location × stockout period). 
Tracks stockout duration, lost sales attempts, lost sales quantity, and lost sales revenue. 
Use for stockout impact analysis, lost sales assessment, and peak season stockout comparison. 
Links to gold_inventory_fact via product_key + location_key + date_key.';

-- Primary key and foreign keys
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN stockout_id COMMENT 'Auto-increment primary key. Unique identifier for each stockout event.';
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN product_key COMMENT 'Foreign key to gold_product_dim. Links stockout event to product master data.';
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN location_key COMMENT 'Foreign key to gold_location_dim. Links stockout event to location master data.';

-- Stockout dates and duration
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN stockout_start_date_key COMMENT 'First date with zero inventory (YYYYMMDD format). Start of stockout period.';
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN stockout_end_date_key COMMENT 'Last date with zero inventory (YYYYMMDD format). NULL if stockout is ongoing. End of stockout period.';
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN stockout_duration_days COMMENT 'Number of consecutive stockout days. Calculated from stockout_start_date_key to stockout_end_date_key. Use for extended stockout analysis (e.g., stockouts >7 days).';

-- Lost sales metrics
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN lost_sales_attempts COMMENT 'Number of purchase attempts during stockout period. Count of customer attempts to purchase when inventory was unavailable.';
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN lost_sales_quantity COMMENT 'Total quantity requested but unavailable during stockout. Sum of quantities from failed purchase attempts. Always >= lost_sales_attempts (customers may want multiple units).';
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN lost_sales_revenue COMMENT 'Estimated revenue lost due to stockout. Calculated from lost sales quantity and unit price. Use for stockout impact analysis and revenue loss assessment. Sum for total lost sales revenue by product, location, or category.';

-- Context flags
ALTER TABLE juan_dev.retail.gold_stockout_events ALTER COLUMN peak_season_flag COMMENT 'TRUE if stockout occurred during peak season. Use for peak season stockout impact analysis and comparison with regular season stockouts.';


-- ----------------------------------------------------------------------------
-- gold_inventory_movement_fact: Inventory movement transactions
-- ----------------------------------------------------------------------------
COMMENT ON TABLE juan_dev.retail.gold_inventory_movement_fact IS 
'Inventory movement transactions fact table. Grain: One record per inventory movement event. 
Tracks all inventory changes including receipts, transfers, sales, returns, and adjustments. 
Use for replenishment analysis, movement reconciliation, and return processing time analysis. 
Links to gold_inventory_fact via product_key + location_key + date_key. 
Links to gold_sales_fact via reference_transaction_id for SALE movements.';

-- Primary key and foreign keys
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN movement_id COMMENT 'Auto-increment primary key. Unique identifier for each inventory movement event.';
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN product_key COMMENT 'Foreign key to gold_product_dim. Links movement to product master data.';
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN location_key COMMENT 'Foreign key to gold_location_dim. Links movement to location master data.';
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN date_key COMMENT 'Movement date in YYYYMMDD format. Foreign key to gold_date_dim. Use for time-series analysis of inventory movements.';

-- Movement details
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN movement_type COMMENT 'Type of inventory movement: SALE (deduction), RETURN (addition with delay), RECEIPT (replenishment addition), TRANSFER (between locations), ADJUSTMENT (corrections). Filter by movement_type for specific movement analysis (e.g., RECEIPT for replenishment activity).';
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN quantity_change COMMENT 'Change in inventory quantity. Positive for additions (RECEIPT, RETURN), negative for deductions (SALE). Use for movement reconciliation and total movement analysis. Sum of movements should reconcile with inventory_fact changes.';
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN reference_transaction_id COMMENT 'Links to sales transaction if movement_type = SALE. Foreign key to gold_sales_fact.transaction_id. Use to join movements with sales data.';

-- Return processing
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN is_return_delayed COMMENT 'TRUE for returns with 1-3 day processing delay. Use for return processing time analysis.';
ALTER TABLE juan_dev.retail.gold_inventory_movement_fact ALTER COLUMN return_delay_days COMMENT 'Days between return transaction and restock (1-3 days). NULL if not a return or if delay not applicable. Use for return processing time analysis and average return delay calculation.';


-- ============================================================================
-- SUPPORTING DIMENSION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- gold_product_dim: Product master data
-- ----------------------------------------------------------------------------
COMMENT ON TABLE juan_dev.retail.gold_product_dim IS 
'Product master data dimension table. Contains product attributes including name, category hierarchy, brand, and pricing. 
Use for product filtering, category-level aggregation, and product identification in inventory queries. 
Filter by is_active = TRUE for current products only.';

ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN product_key COMMENT 'Primary key. Surrogate key for products. Foreign key used in gold_inventory_fact, gold_stockout_events, and gold_inventory_movement_fact.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN product_name COMMENT 'Product name. Use for product identification in queries and results.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN category_level_1 COMMENT 'Top-level product category (e.g., "Apparel"). Use for category-level inventory analysis and aggregation.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN category_level_2 COMMENT 'Second-level product category (e.g., "Women''s"). Use for subcategory analysis.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN category_level_3 COMMENT 'Third-level product category (e.g., "Tops"). Use for detailed category analysis.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN brand COMMENT 'Product brand name. Use for brand-level inventory analysis.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN base_price COMMENT 'Base retail price per unit. Use for pricing analysis and margin calculations.';
ALTER TABLE juan_dev.retail.gold_product_dim ALTER COLUMN is_active COMMENT 'TRUE for active products. Filter by is_active = TRUE to exclude discontinued products from inventory analysis.';


-- ----------------------------------------------------------------------------
-- gold_location_dim: Location master data
-- ----------------------------------------------------------------------------
COMMENT ON TABLE juan_dev.retail.gold_location_dim IS 
'Location master data dimension table. Contains location attributes including name, type, region, and city. 
Use for location filtering, regional aggregation, and location identification in inventory queries. 
Filter by is_active = TRUE for current locations only.';

ALTER TABLE juan_dev.retail.gold_location_dim ALTER COLUMN location_key COMMENT 'Primary key. Surrogate key for locations. Foreign key used in gold_inventory_fact, gold_stockout_events, and gold_inventory_movement_fact.';
ALTER TABLE juan_dev.retail.gold_location_dim ALTER COLUMN location_name COMMENT 'Location name. Use for location identification in queries and results.';
ALTER TABLE juan_dev.retail.gold_location_dim ALTER COLUMN location_type COMMENT 'Type of location (e.g., "Store", "Warehouse", "Distribution Center"). Use for location type analysis.';
ALTER TABLE juan_dev.retail.gold_location_dim ALTER COLUMN region COMMENT 'Geographic region. Use for regional inventory analysis and aggregation.';
ALTER TABLE juan_dev.retail.gold_location_dim ALTER COLUMN city COMMENT 'City name. Use for city-level inventory analysis.';
ALTER TABLE juan_dev.retail.gold_location_dim ALTER COLUMN is_active COMMENT 'TRUE for active locations. Filter by is_active = TRUE to exclude closed locations from inventory analysis.';


-- ----------------------------------------------------------------------------
-- gold_date_dim: Date dimension with calendar and fiscal attributes
-- ----------------------------------------------------------------------------
COMMENT ON TABLE juan_dev.retail.gold_date_dim IS 
'Date dimension table with calendar and fiscal attributes. Contains date_key, calendar date, and temporal attributes. 
Use for time-based filtering, seasonal analysis, and historical trend analysis. 
date_key format is YYYYMMDD (integer). Join fact tables using date_key for time-series analysis.';

ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN date_key COMMENT 'Primary key. Date in YYYYMMDD format (integer). Foreign key used in gold_inventory_fact and gold_inventory_movement_fact. Use MAX(date_key) from inventory_fact to get current inventory state.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN calendar_date COMMENT 'Actual calendar date (DATE type). Use for date range filtering and date calculations.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN year COMMENT 'Calendar year (integer). Use for year-level aggregation.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN quarter COMMENT 'Calendar quarter (integer: 1-4). Use for quarterly analysis.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN month COMMENT 'Calendar month (integer: 1-12). Use for monthly analysis.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN month_name COMMENT 'Month name (string: "January", "February", etc.). Use for month-level aggregation and display.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN day_name COMMENT 'Day of week name (string: "Monday", "Tuesday", etc.). Use for day-of-week analysis.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN season COMMENT 'Season (string: "Spring", "Summer", "Fall", "Winter"). Use for seasonal inventory analysis.';
ALTER TABLE juan_dev.retail.gold_date_dim ALTER COLUMN is_peak_season COMMENT 'TRUE during peak shopping seasons. Use for peak season stockout impact analysis and seasonal comparison.';

