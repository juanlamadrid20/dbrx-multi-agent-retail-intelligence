-- ============================================================================
-- Table and Column Comments for Customer Behavior Analytics Genie Space
-- ============================================================================
-- Purpose: Enable automatic schema discovery for Databricks Genie
-- Tables: Core customer behavior fact tables and supporting dimension tables
-- Schema: Set via session variables (catalog_name, schema_name) below
-- Date: 2025-01-27
-- ============================================================================

-- =============================================================================
-- Configuration: Set target catalog and schema
-- =============================================================================
DECLARE OR REPLACE VARIABLE catalog_name STRING DEFAULT 'juan_use1_catalog';
DECLARE OR REPLACE VARIABLE schema_name STRING DEFAULT 'retail';
USE CATALOG IDENTIFIER(catalog_name);
USE SCHEMA IDENTIFIER(schema_name);

-- ============================================================================
-- CORE CUSTOMER BEHAVIOR FACT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- gold_sales_fact: Customer purchase transactions - primary source for customer behavior analysis
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_sales_fact IS 
'Customer purchase transactions fact table. Grain: Transaction Line Item (one record per product in a transaction). 
Primary source for customer behavior analysis including RFM analysis, purchase patterns, channel behavior, and customer segmentation. 
Tracks sales, returns, exchanges, and inventory constraints. Use is_return = FALSE for revenue analysis. 
Enables customer lifetime value calculation, purchase frequency analysis, recency analysis, and average order value calculation. 
Join with gold_customer_dim for segmentation analysis, gold_product_dim for product trends, gold_date_dim for temporal patterns, and gold_channel_dim for channel behavior.';

-- Primary identifiers
ALTER TABLE gold_sales_fact ALTER COLUMN transaction_id COMMENT 'Unique transaction identifier. Groups multiple line items into a single purchase. Use COUNT(DISTINCT transaction_id) to calculate purchase frequency per customer. Join with other fact tables using transaction_id for basket analysis.';
ALTER TABLE gold_sales_fact ALTER COLUMN line_item_id COMMENT 'Unique line item identifier within a transaction. Primary key. One record per product purchased in a transaction.';
ALTER TABLE gold_sales_fact ALTER COLUMN order_number COMMENT 'Order number grouping line items. Use for order-level analysis and fulfillment tracking.';

-- Foreign keys and dimensions
ALTER TABLE gold_sales_fact ALTER COLUMN customer_key COMMENT 'Foreign key to gold_customer_dim. Links transaction to customer master data. Use for customer segmentation analysis, RFM scoring, and customer lifetime value calculation. Always join with gold_customer_dim WHERE is_current = TRUE for current customer data.';
ALTER TABLE gold_sales_fact ALTER COLUMN product_key COMMENT 'Foreign key to gold_product_dim. Links transaction to product master data. Use for product trend analysis, basket analysis, and category-level behavior.';
ALTER TABLE gold_sales_fact ALTER COLUMN date_key COMMENT 'Transaction date in YYYYMMDD format. Foreign key to gold_date_dim. Use for temporal analysis, recency calculation, and seasonal pattern analysis. Calculate recency as DATEDIFF(CURRENT_DATE, MAX(date_key)) per customer.';
ALTER TABLE gold_sales_fact ALTER COLUMN time_key COMMENT 'Transaction time in HHMM format. Use for time-of-day purchase pattern analysis.';
ALTER TABLE gold_sales_fact ALTER COLUMN channel_key COMMENT 'Foreign key to gold_channel_dim. Links transaction to sales channel. Use for channel behavior analysis, channel migration patterns, and multi-channel customer identification.';
ALTER TABLE gold_sales_fact ALTER COLUMN location_key COMMENT 'Foreign key to gold_location_dim. Links transaction to physical location. Use for location-based customer behavior analysis.';

-- Quantity fields
ALTER TABLE gold_sales_fact ALTER COLUMN quantity_sold COMMENT 'Actual quantity purchased. May be less than quantity_requested if inventory constrained. Use for purchase quantity analysis and basket size calculations.';
ALTER TABLE gold_sales_fact ALTER COLUMN quantity_requested COMMENT 'Quantity customer wanted to purchase. When quantity_requested > quantity_sold, customer intent was not fully satisfied. Use for customer satisfaction analysis and inventory constraint impact on customer behavior.';
ALTER TABLE gold_sales_fact ALTER COLUMN is_inventory_constrained COMMENT 'TRUE when quantity_sold < quantity_requested due to inventory limits. Use to analyze impact of inventory constraints on customer experience and purchase behavior.';

-- Financial fields
ALTER TABLE gold_sales_fact ALTER COLUMN unit_price COMMENT 'Price per unit at time of sale. Use for pricing analysis and margin calculations.';
ALTER TABLE gold_sales_fact ALTER COLUMN discount_amount COMMENT 'Discount applied to transaction. Use for promotional impact analysis and discount effectiveness measurement.';
ALTER TABLE gold_sales_fact ALTER COLUMN tax_amount COMMENT 'Tax amount for transaction. Use for total order value calculations.';
ALTER TABLE gold_sales_fact ALTER COLUMN net_sales_amount COMMENT 'Total sales amount after discount, before tax. Primary metric for revenue analysis. Use SUM(net_sales_amount) for total revenue, AVG(net_sales_amount) per transaction for average order value (AOV), SUM(net_sales_amount) per customer for monetary value (RFM M score). Filter by is_return = FALSE for revenue analysis.';
ALTER TABLE gold_sales_fact ALTER COLUMN gross_margin_amount COMMENT 'Gross margin from transaction. Use for profitability analysis by customer segment, product, or channel.';

-- Transaction flags
ALTER TABLE gold_sales_fact ALTER COLUMN is_return COMMENT 'TRUE for return transactions. Always filter by is_return = FALSE for purchase analysis and revenue calculations. Use is_return = TRUE for return pattern analysis and return rate by segment, product, or channel.';
ALTER TABLE gold_sales_fact ALTER COLUMN is_exchange COMMENT 'TRUE for exchange transactions. Use for exchange pattern analysis.';
ALTER TABLE gold_sales_fact ALTER COLUMN is_promotional COMMENT 'TRUE for promotional pricing. Use for promotional campaign effectiveness analysis and promotional purchase behavior by segment.';
ALTER TABLE gold_sales_fact ALTER COLUMN is_clearance COMMENT 'TRUE for clearance pricing. Use for clearance purchase patterns and end-of-life product analysis.';

-- Fulfillment and payment
ALTER TABLE gold_sales_fact ALTER COLUMN fulfillment_type COMMENT 'Fulfillment method: ship, pickup, same_day, in_store. Use for fulfillment preference analysis by customer segment and channel.';
ALTER TABLE gold_sales_fact ALTER COLUMN payment_method COMMENT 'Payment method used. Use for payment preference analysis by customer segment.';

-- Store-specific fields
ALTER TABLE gold_sales_fact ALTER COLUMN pos_terminal_id COMMENT 'POS terminal ID for in-store purchases. NULL for online transactions. Use for store-level behavior analysis.';
ALTER TABLE gold_sales_fact ALTER COLUMN sales_associate_id COMMENT 'Sales associate ID for in-store purchases. NULL for online transactions. Use for associate performance analysis.';

-- Return processing
ALTER TABLE gold_sales_fact ALTER COLUMN return_restocked_date_key COMMENT 'Date inventory was replenished from return (1-3 days after return date). NULL if not a return. Use for return processing time analysis and restock delay impact.';


-- ----------------------------------------------------------------------------
-- gold_cart_abandonment_fact: Cart abandonment events with recovery tracking
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_cart_abandonment_fact IS 
'Cart abandonment event tracking with recovery metrics. Grain: One record per cart abandonment event. 
Tracks when customers add items to cart but do not complete purchase. Includes abandonment stage, recovery campaigns, and recovery success. 
Use for cart abandonment rate analysis, recovery effectiveness measurement, lost revenue calculation, and abandonment pattern analysis by segment, channel, or product category. 
Only available for digital channels (check channel_key). Join with gold_customer_dim for segment analysis, gold_date_dim for temporal trends, and gold_channel_dim for channel-specific abandonment patterns.';

-- Primary identifiers
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN abandonment_id COMMENT 'Auto-increment primary key. Unique identifier for each cart abandonment event.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN cart_id COMMENT 'Unique cart identifier. Links abandonment to cart session. Use for cart-level analysis and recovery tracking.';

-- Foreign keys and dimensions
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN customer_key COMMENT 'Foreign key to gold_customer_dim. Links abandonment to customer. Use for segment-based abandonment analysis and customer abandonment frequency. Always join with gold_customer_dim WHERE is_current = TRUE.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN date_key COMMENT 'Abandonment date in YYYYMMDD format. Foreign key to gold_date_dim. Use for temporal abandonment trend analysis and seasonal abandonment patterns.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN time_key COMMENT 'Abandonment time in HHMM format. Use for time-of-day abandonment analysis.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN channel_key COMMENT 'Foreign key to gold_channel_dim. Digital channels only (cart abandonment tracked for online/mobile). Use for channel-specific abandonment analysis.';

-- Cart details
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN cart_value COMMENT 'Total value of abandoned cart. Use for lost revenue calculation. SUM(cart_value) WHERE is_recovered = FALSE for total lost revenue. SUM(cart_value) WHERE is_recovered = TRUE for recovered revenue.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN items_count COMMENT 'Number of items in abandoned cart. Use for basket size analysis and abandonment patterns by cart size.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN minutes_in_cart COMMENT 'Time spent in cart before abandonment. Use for abandonment timing analysis and urgency indicators.';

-- Abandonment characteristics
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN abandonment_stage COMMENT 'Stage where abandonment occurred: cart, shipping, payment. Use for funnel analysis and stage-specific abandonment rate calculation. Identify which stage has highest abandonment for targeted improvement.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN suspected_reason COMMENT 'Suspected reason for abandonment: high_shipping, price_concern, out_of_stock, technical_issue, payment_issue. Use for root cause analysis and abandonment reason distribution.';

-- Inventory correlation
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN low_inventory_trigger COMMENT 'TRUE if any item had inventory < 5 units at time of abandonment. Use to analyze inventory impact on cart abandonment. Abandonment rate typically ~10pp higher when low_inventory_trigger = TRUE.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN inventory_constrained_items COMMENT 'Count of items with quantity_available < 5 in cart. Use for inventory constraint impact analysis. Must be <= items_count.';

-- Recovery tracking
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN recovery_email_sent COMMENT 'TRUE if recovery email was sent. Use for recovery campaign coverage analysis.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN recovery_email_opened COMMENT 'TRUE if recovery email was opened. Use for email engagement metrics.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN recovery_email_clicked COMMENT 'TRUE if recovery email link was clicked. Use for email click-through rate analysis.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN is_recovered COMMENT 'TRUE if cart was later converted to purchase. Use for recovery rate calculation: COUNT(*) WHERE is_recovered = TRUE / COUNT(*) WHERE recovery_email_sent = TRUE. Also use for recovery effectiveness by segment, stage, or reason.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN recovery_date_key COMMENT 'Date of recovery purchase (if is_recovered = TRUE). NULL if not recovered. Use for recovery time analysis and days-to-recovery calculation.';
ALTER TABLE gold_cart_abandonment_fact ALTER COLUMN recovery_revenue COMMENT 'Revenue from recovered cart. Use for recovery revenue calculation and ROI analysis of recovery campaigns.';


-- ----------------------------------------------------------------------------
-- gold_customer_product_affinity_agg: Pre-aggregated customer-product affinity scores
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_customer_product_affinity_agg IS 
'Pre-aggregated customer-product affinity scores and engagement metrics. Grain: Customer × Product. 
Contains calculated affinity scores, purchase/view ratios, and predicted CLTV impact for personalization and recommendation systems. 
Use for product recommendations, personalization targeting, basket analysis, and predicted customer lifetime value impact. 
Join with gold_customer_dim for segment-based affinity, gold_product_dim for product category affinity, and gold_sales_fact for validation. 
High affinity scores (>0.7) indicate strong customer-product match. Use recommendation_rank for ranking recommendations.';

-- Composite key
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN customer_key COMMENT 'Foreign key to gold_customer_dim. Links affinity record to customer. Use for customer-specific recommendations and personalization. Always join with gold_customer_dim WHERE is_current = TRUE.';
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN product_key COMMENT 'Foreign key to gold_product_dim. Links affinity record to product. Use for product-level affinity analysis and category affinity aggregation.';

-- Affinity metrics
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN affinity_score COMMENT 'Customer-product affinity score (0.0-1.0). Higher scores indicate stronger match. Scores >0.7 are high affinity. Use for recommendation ranking and personalization targeting. Filter by affinity_score > threshold for high-quality recommendations.';
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN recommendation_rank COMMENT 'Ranking of this product for this customer (1 = highest recommended). Use for recommendation ordering and top-N recommendation queries.';

-- Engagement metrics
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN purchase_count COMMENT 'Number of times customer purchased this product. Use for purchase frequency analysis and repeat purchase identification.';
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN view_count COMMENT 'Number of times customer viewed this product. Use for engagement analysis and view-to-purchase conversion tracking.';
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN cart_add_count COMMENT 'Number of times customer added this product to cart. Use for cart engagement analysis and cart-to-purchase conversion tracking.';
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN days_since_last_interaction COMMENT 'Days since customer last interacted with this product (view, cart, or purchase). Use for recency-based filtering and stale recommendation identification.';

-- Conversion ratios
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN view_to_purchase_ratio COMMENT 'Ratio of purchases to views. Higher values indicate strong purchase intent. Use for conversion analysis and product interest measurement.';
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN cart_to_purchase_ratio COMMENT 'Ratio of purchases to cart adds. Higher values indicate high cart conversion. Use for cart abandonment analysis and purchase intent measurement.';

-- Predictive metrics
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN predicted_cltv_impact COMMENT 'Predicted impact on customer lifetime value from this affinity relationship. Use for CLTV-based recommendation prioritization and personalization ROI analysis. Sum for total predicted CLTV impact by segment or product category.';

-- Temporal tracking
ALTER TABLE gold_customer_product_affinity_agg ALTER COLUMN calculation_date COMMENT 'Date when affinity score was calculated. Use for freshness analysis and recommendation update tracking.';


-- ----------------------------------------------------------------------------
-- gold_customer_event_fact: Customer engagement events for funnel analysis
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_customer_event_fact IS 
'Customer engagement events fact table. Grain: One record per customer engagement event. 
Tracks customer interactions including views, clicks, add-to-cart, wishlist, and other engagement events. 
Use for engagement funnel analysis (View → Add to Cart → Purchase), conversion rate calculation, channel behavior analysis, and attribution analysis. 
Join with gold_customer_dim for segment-based engagement, gold_product_dim for product engagement, gold_channel_dim for channel analysis, and gold_sales_fact for conversion tracking. 
Use event_type and event_category for funnel stage identification.';

-- Primary identifier
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_id COMMENT 'Auto-increment primary key. Unique identifier for each engagement event.';

-- Foreign keys and dimensions
ALTER TABLE gold_customer_event_fact ALTER COLUMN customer_key COMMENT 'Foreign key to gold_customer_dim. Links event to customer. Use for customer-level engagement analysis and segment-based funnel analysis. Always join with gold_customer_dim WHERE is_current = TRUE.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN product_key COMMENT 'Foreign key to gold_product_dim. Optional - NULL for non-product events. Links event to product. Use for product engagement analysis and product-level funnel tracking.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN location_key COMMENT 'Foreign key to gold_location_dim. Optional - NULL for online events. Use for location-based engagement analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN channel_key COMMENT 'Foreign key to gold_channel_dim. Links event to channel. Use for channel-specific engagement analysis and channel conversion comparison.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN date_key COMMENT 'Event date in YYYYMMDD format. Foreign key to gold_date_dim. Use for temporal engagement analysis and time-series funnel analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN time_key COMMENT 'Event time in HHMM format. Use for time-of-day engagement pattern analysis.';

-- Session tracking
ALTER TABLE gold_customer_event_fact ALTER COLUMN session_id COMMENT 'Session identifier. Groups events into user sessions. Use for session-level analysis, session duration calculation, and funnel analysis within sessions.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_timestamp COMMENT 'Exact timestamp of event. Use for precise timing analysis and session sequencing.';

-- Event classification
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_type COMMENT 'Event type: view, click, add_to_cart, wishlist, purchase_intent, etc. Use for funnel stage identification. Filter by event_type = ''view'' for views, ''add_to_cart'' for cart additions. Join with gold_sales_fact for purchase conversion.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_category COMMENT 'Event category for hierarchical classification. Use for category-level engagement analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_action COMMENT 'Event action details. Use for detailed action tracking and granular analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_label COMMENT 'Event label for additional context. Use for custom event tracking and detailed analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN event_value COMMENT 'Numeric value associated with event (if applicable). Use for value-based event analysis.';

-- Engagement metrics
ALTER TABLE gold_customer_event_fact ALTER COLUMN time_on_page_seconds COMMENT 'Time spent on page in seconds. Use for engagement depth analysis and content effectiveness measurement.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN bounce_flag COMMENT 'TRUE if this was a bounce (single-page session). Use for bounce rate analysis by segment, channel, or product.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN conversion_flag COMMENT 'TRUE if event led to conversion (purchase). Use for conversion attribution and conversion path analysis.';

-- Web analytics
ALTER TABLE gold_customer_event_fact ALTER COLUMN page_url COMMENT 'URL of page where event occurred. Use for page-level engagement analysis and content effectiveness.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN referrer_url COMMENT 'Referrer URL for traffic source analysis. Use for referral source identification and traffic source effectiveness.';

-- Attribution tracking
ALTER TABLE gold_customer_event_fact ALTER COLUMN utm_source COMMENT 'UTM source parameter for campaign attribution. Use for marketing campaign attribution and source effectiveness analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN utm_medium COMMENT 'UTM medium parameter for campaign attribution. Use for marketing medium analysis (email, social, paid search, etc.).';
ALTER TABLE gold_customer_event_fact ALTER COLUMN utm_campaign COMMENT 'UTM campaign parameter for campaign attribution. Use for specific campaign tracking and campaign effectiveness measurement.';

-- Device and technical
ALTER TABLE gold_customer_event_fact ALTER COLUMN device_type COMMENT 'Device type: desktop, mobile, tablet. Use for device-specific behavior analysis and responsive design effectiveness.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN browser COMMENT 'Browser name and version. Use for browser compatibility analysis and technical issue identification.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN operating_system COMMENT 'Operating system name and version. Use for platform-specific behavior analysis.';

-- Geographic
ALTER TABLE gold_customer_event_fact ALTER COLUMN geo_city COMMENT 'City where event occurred. Use for city-level engagement analysis.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN geo_region COMMENT 'Geographic region where event occurred. Use for regional engagement analysis and regional behavior patterns.';
ALTER TABLE gold_customer_event_fact ALTER COLUMN geo_country COMMENT 'Country where event occurred. Use for country-level engagement analysis.';


-- ============================================================================
-- SUPPORTING DIMENSION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- gold_customer_dim: Customer master data with segmentation and lifetime value
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_customer_dim IS 
'Customer master data dimension table with segmentation and lifetime value metrics. Uses SCD Type 2 for historical tracking. 
Contains customer attributes including segment, lifetime value, acquisition details, preferred channels/categories, loyalty tier, and geographic information. 
Use for customer segmentation analysis, RFM scoring, channel migration analysis, and customer identification. 
ALWAYS filter by is_current = TRUE for current customer data. Join with fact tables via customer_key for customer behavior analysis. 
Links to gold_sales_fact, gold_cart_abandonment_fact, gold_customer_product_affinity_agg, and gold_customer_event_fact.';

-- Primary identifiers
ALTER TABLE gold_customer_dim ALTER COLUMN customer_key COMMENT 'Primary key. Surrogate key for customers. Foreign key used in gold_sales_fact, gold_cart_abandonment_fact, gold_customer_product_affinity_agg, and gold_customer_event_fact.';
ALTER TABLE gold_customer_dim ALTER COLUMN customer_id COMMENT 'Business key. Unique customer identifier. Use for customer identification and external system integration.';

-- Customer information
ALTER TABLE gold_customer_dim ALTER COLUMN email COMMENT 'Customer email address. Use for customer communication and email campaign targeting.';
ALTER TABLE gold_customer_dim ALTER COLUMN first_name COMMENT 'Customer first name. Use for personalization and customer identification.';
ALTER TABLE gold_customer_dim ALTER COLUMN last_name COMMENT 'Customer last name. Use for personalization and customer identification.';

-- Segmentation
ALTER TABLE gold_customer_dim ALTER COLUMN segment COMMENT 'Customer segment: VIP, Premium, Loyal, Regular, New. Use for segment-based analysis, segment behavior comparison, and targeted marketing. Join with fact tables to analyze behavior by segment.';
ALTER TABLE gold_customer_dim ALTER COLUMN loyalty_tier COMMENT 'Loyalty program tier. Use for loyalty program analysis and tier-based behavior comparison.';

-- Customer value
ALTER TABLE gold_customer_dim ALTER COLUMN lifetime_value COMMENT 'Customer lifetime value (CLTV). Pre-calculated sum of all historical purchases. Use for value-based segmentation and high-value customer identification. Can also be calculated from gold_sales_fact: SUM(net_sales_amount) WHERE is_return = FALSE GROUP BY customer_key.';

-- Acquisition
ALTER TABLE gold_customer_dim ALTER COLUMN acquisition_date COMMENT 'Date when customer was acquired. Use for customer acquisition trend analysis and cohort analysis. Calculate customer age as DATEDIFF(CURRENT_DATE, acquisition_date).';
ALTER TABLE gold_customer_dim ALTER COLUMN acquisition_channel COMMENT 'Channel where customer was acquired (e.g., "Online", "In-Store", "Social Media"). Use for acquisition channel effectiveness analysis and channel migration patterns. Compare with preferred_channel to identify channel migration.';

-- Preferences
ALTER TABLE gold_customer_dim ALTER COLUMN preferred_channel COMMENT 'Customer''s preferred shopping channel. Use for channel preference analysis and channel migration identification. Compare with acquisition_channel to analyze channel migration patterns.';
ALTER TABLE gold_customer_dim ALTER COLUMN preferred_category COMMENT 'Customer''s preferred product category. Use for category preference analysis and personalized category targeting.';

-- Size and fit
ALTER TABLE gold_customer_dim ALTER COLUMN size_profile_tops COMMENT 'Customer size profile for tops. Use for size recommendation and fit analysis.';
ALTER TABLE gold_customer_dim ALTER COLUMN size_profile_bottoms COMMENT 'Customer size profile for bottoms. Use for size recommendation and fit analysis.';

-- Geographic
ALTER TABLE gold_customer_dim ALTER COLUMN geo_region COMMENT 'Geographic region. Use for regional customer behavior analysis and regional segmentation.';
ALTER TABLE gold_customer_dim ALTER COLUMN geo_city COMMENT 'City name. Use for city-level customer analysis.';
ALTER TABLE gold_customer_dim ALTER COLUMN nearest_store_id COMMENT 'Nearest store location ID. Use for store-based customer analysis and proximity-based recommendations.';

-- Communication preferences
ALTER TABLE gold_customer_dim ALTER COLUMN email_subscribe_flag COMMENT 'TRUE if customer subscribed to email communications. Use for email campaign targeting and communication preference analysis.';
ALTER TABLE gold_customer_dim ALTER COLUMN sms_subscribe_flag COMMENT 'TRUE if customer subscribed to SMS communications. Use for SMS campaign targeting and communication preference analysis.';

-- SCD Type 2 tracking
ALTER TABLE gold_customer_dim ALTER COLUMN effective_date COMMENT 'Date when this customer record became effective (SCD Type 2). Use for historical customer data analysis.';
ALTER TABLE gold_customer_dim ALTER COLUMN expiration_date COMMENT 'Date when this customer record expired (SCD Type 2). NULL for current record. Use for historical customer data analysis.';
ALTER TABLE gold_customer_dim ALTER COLUMN is_current COMMENT 'TRUE for current customer record. ALWAYS filter by is_current = TRUE for current customer data. FALSE indicates historical record in SCD Type 2 schema. Use for time-point analysis and historical customer data tracking.';


-- ----------------------------------------------------------------------------
-- gold_channel_dim: Sales channel definitions for channel behavior analysis
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_channel_dim IS 
'Sales channel dimension table. Contains channel attributes including name, type, digital/physical classification, and ownership. 
Use for channel behavior analysis, channel migration patterns, multi-channel customer identification, and channel-specific conversion analysis. 
Join with gold_sales_fact for channel sales analysis, gold_cart_abandonment_fact for channel abandonment (digital only), and gold_customer_event_fact for channel engagement.';

-- Primary identifier
ALTER TABLE gold_channel_dim ALTER COLUMN channel_key COMMENT 'Primary key. Surrogate key for channels. Foreign key used in gold_sales_fact, gold_cart_abandonment_fact, and gold_customer_event_fact.';

-- Channel identification
ALTER TABLE gold_channel_dim ALTER COLUMN channel_name COMMENT 'Channel name (e.g., "Online", "In-Store", "Mobile App", "Social Commerce"). Use for channel identification in queries and results.';
ALTER TABLE gold_channel_dim ALTER COLUMN channel_code COMMENT 'Channel code for system integration. Use for technical channel identification.';
ALTER TABLE gold_channel_dim ALTER COLUMN channel_category COMMENT 'Channel category for hierarchical classification. Use for category-level channel analysis.';

-- Channel classification
ALTER TABLE gold_channel_dim ALTER COLUMN channel_type COMMENT 'Channel type classification. Use for channel type analysis and grouping.';
ALTER TABLE gold_channel_dim ALTER COLUMN is_digital COMMENT 'TRUE for digital channels (online, mobile, app). Use to identify digital vs physical channels. Important for cart abandonment analysis (only digital channels have cart abandonment).';
ALTER TABLE gold_channel_dim ALTER COLUMN is_owned COMMENT 'TRUE for owned channels (company-operated). FALSE for third-party channels. Use for owned vs third-party channel analysis.';
ALTER TABLE gold_channel_dim ALTER COLUMN device_category COMMENT 'Device category for digital channels (mobile, desktop, tablet). Use for device-specific channel analysis.';

-- Channel economics
ALTER TABLE gold_channel_dim ALTER COLUMN commission_rate COMMENT 'Commission rate for third-party channels. NULL for owned channels. Use for channel profitability analysis and cost comparison.';


-- ----------------------------------------------------------------------------
-- gold_product_dim: Product master data (customer behavior context added)
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_product_dim IS 
'Product master data dimension table. Contains product attributes including name, category hierarchy, brand, pricing, and product lifecycle. 
Use for product filtering, category-level aggregation, product trend analysis, basket analysis, and product identification in customer behavior queries. 
Filter by is_active = TRUE for current products only. Join with gold_sales_fact for product purchase patterns, gold_cart_abandonment_fact for product abandonment, gold_customer_product_affinity_agg for affinity analysis, and gold_customer_event_fact for product engagement.';

-- Primary identifier and basic info
ALTER TABLE gold_product_dim ALTER COLUMN product_key COMMENT 'Primary key. Surrogate key for products. Foreign key used in gold_sales_fact, gold_cart_abandonment_fact, gold_customer_product_affinity_agg, gold_customer_event_fact, and inventory tables.';
ALTER TABLE gold_product_dim ALTER COLUMN product_id COMMENT 'Business key. Unique product identifier. Use for product identification and external system integration.';
ALTER TABLE gold_product_dim ALTER COLUMN sku COMMENT 'Stock keeping unit. Use for inventory and product identification.';
ALTER TABLE gold_product_dim ALTER COLUMN product_name COMMENT 'Product name. Use for product identification in queries, results, and customer-facing displays.';

-- Category hierarchy
ALTER TABLE gold_product_dim ALTER COLUMN category_level_1 COMMENT 'Top-level product category (e.g., "Apparel"). Use for top-level category analysis, category-level customer behavior analysis, and high-level product grouping.';
ALTER TABLE gold_product_dim ALTER COLUMN category_level_2 COMMENT 'Second-level product category (e.g., "Women''s"). Use for subcategory analysis, customer preference analysis by category, and basket analysis at category level.';
ALTER TABLE gold_product_dim ALTER COLUMN category_level_3 COMMENT 'Third-level product category (e.g., "Tops"). Use for detailed category analysis, specific product trend analysis, and granular customer behavior tracking.';

-- Product attributes
ALTER TABLE gold_product_dim ALTER COLUMN brand COMMENT 'Product brand name. Use for brand-level customer behavior analysis, brand preference by segment, and brand-based recommendations.';
ALTER TABLE gold_product_dim ALTER COLUMN color_family COMMENT 'Color family classification. Use for color preference analysis and color-based customer behavior.';
ALTER TABLE gold_product_dim ALTER COLUMN color_name COMMENT 'Specific color name. Use for detailed color preference analysis.';
ALTER TABLE gold_product_dim ALTER COLUMN size_range COMMENT 'Size range available. Use for size preference analysis and size-based customer segmentation.';
ALTER TABLE gold_product_dim ALTER COLUMN material_primary COMMENT 'Primary material. Use for material preference analysis.';
ALTER TABLE gold_product_dim ALTER COLUMN material_composition COMMENT 'Material composition details. Use for detailed material analysis.';

-- Product lifecycle
ALTER TABLE gold_product_dim ALTER COLUMN season_code COMMENT 'Season code (Spring, Summer, Fall, Winter). Use for seasonal customer behavior analysis and seasonal purchase patterns.';
ALTER TABLE gold_product_dim ALTER COLUMN collection_name COMMENT 'Collection name. Use for collection-based customer behavior analysis and collection trends.';
ALTER TABLE gold_product_dim ALTER COLUMN launch_date COMMENT 'Product launch date. Use for new product analysis and launch campaign effectiveness.';
ALTER TABLE gold_product_dim ALTER COLUMN end_of_life_date COMMENT 'Product end-of-life date. NULL for active products. Use for product lifecycle analysis and clearance behavior.';

-- Pricing
ALTER TABLE gold_product_dim ALTER COLUMN base_price COMMENT 'Base retail price per unit. Use for pricing analysis, margin calculations, price sensitivity analysis, and customer segment price preferences.';
ALTER TABLE gold_product_dim ALTER COLUMN unit_cost COMMENT 'Unit cost for margin calculation. Use for profitability analysis by product and customer segment.';
ALTER TABLE gold_product_dim ALTER COLUMN margin_percent COMMENT 'Margin percentage. Use for profitability analysis.';
ALTER TABLE gold_product_dim ALTER COLUMN price_tier COMMENT 'Price tier classification. Use for price tier-based customer behavior analysis and price sensitivity by segment.';

-- Flags
ALTER TABLE gold_product_dim ALTER COLUMN sustainability_flag COMMENT 'TRUE for sustainable products. Use for sustainability-focused customer behavior analysis and eco-conscious customer identification.';
ALTER TABLE gold_product_dim ALTER COLUMN is_active COMMENT 'TRUE for active products. Filter by is_active = TRUE to exclude discontinued products from customer behavior analysis, product recommendations, and active product queries.';


-- ----------------------------------------------------------------------------
-- gold_date_dim: Date dimension with calendar and fiscal attributes (customer behavior context added)
-- ----------------------------------------------------------------------------
COMMENT ON TABLE gold_date_dim IS 
'Date dimension table with calendar and fiscal attributes. Contains date_key, calendar date, and temporal attributes for time-based analysis. 
Use for time-based filtering, seasonal analysis, historical trend analysis, peak season customer behavior, holiday impact analysis, and temporal customer behavior patterns. 
date_key format is YYYYMMDD (integer). Join fact tables using date_key for time-series analysis. 
Includes dates from historical through +365 days in the future for forecasting. Always filter by calendar_date when querying time periods.';

-- Primary identifier
ALTER TABLE gold_date_dim ALTER COLUMN date_key COMMENT 'Primary key. Date in YYYYMMDD format (integer). Foreign key used in gold_sales_fact, gold_cart_abandonment_fact, gold_customer_event_fact, and inventory tables. Use for time-series joins and temporal analysis.';
ALTER TABLE gold_date_dim ALTER COLUMN calendar_date COMMENT 'Actual calendar date (DATE type). Use for date range filtering, date calculations, and temporal analysis. Always filter by calendar_date when querying time periods (e.g., WHERE calendar_date >= DATE_SUB(CURRENT_DATE, 30)).';

-- Calendar components
ALTER TABLE gold_date_dim ALTER COLUMN year COMMENT 'Calendar year (integer). Use for year-level aggregation, year-over-year customer behavior comparison, and annual trend analysis.';
ALTER TABLE gold_date_dim ALTER COLUMN quarter COMMENT 'Calendar quarter (integer: 1-4). Use for quarterly customer behavior analysis and quarterly trend comparison.';
ALTER TABLE gold_date_dim ALTER COLUMN month COMMENT 'Calendar month (integer: 1-12). Use for monthly customer behavior analysis, monthly trend tracking, and seasonal pattern identification.';
ALTER TABLE gold_date_dim ALTER COLUMN month_name COMMENT 'Month name (string: "January", "February", etc.). Use for month-level aggregation, display in reports, and month-based customer behavior analysis.';
ALTER TABLE gold_date_dim ALTER COLUMN day_of_month COMMENT 'Day of month (integer: 1-31). Use for day-of-month customer behavior patterns and monthly cycle analysis.';
ALTER TABLE gold_date_dim ALTER COLUMN day_of_week COMMENT 'Day of week (integer: 1-7). Use for day-of-week customer behavior patterns.';
ALTER TABLE gold_date_dim ALTER COLUMN day_name COMMENT 'Day of week name (string: "Monday", "Tuesday", etc.). Use for day-of-week customer behavior analysis, weekend vs weekday patterns, and day-based segmentation.';
ALTER TABLE gold_date_dim ALTER COLUMN week_of_year COMMENT 'Week of year (integer: 1-52). Use for weekly customer behavior analysis and week-level trend tracking.';

-- Seasonal attributes
ALTER TABLE gold_date_dim ALTER COLUMN season COMMENT 'Season (string: "Spring", "Summer", "Fall", "Winter"). Use for seasonal customer behavior analysis, seasonal purchase patterns, and seasonal trend comparison.';
ALTER TABLE gold_date_dim ALTER COLUMN is_peak_season COMMENT 'TRUE during peak shopping seasons (holiday seasons, back-to-school, etc.). Use for peak season customer behavior analysis, peak season purchase patterns, peak season cart abandonment analysis, and peak season conversion rate comparison. Critical for understanding high-traffic periods and seasonal customer behavior.';
ALTER TABLE gold_date_dim ALTER COLUMN is_sale_period COMMENT 'TRUE during sale periods. Use for sale period customer behavior analysis and sale impact on purchase patterns.';
ALTER TABLE gold_date_dim ALTER COLUMN sale_event_name COMMENT 'Name of sale event (if applicable). Use for specific sale event analysis and sale campaign effectiveness.';

-- Temporal flags
ALTER TABLE gold_date_dim ALTER COLUMN is_weekend COMMENT 'TRUE for weekend days. Use for weekend vs weekday customer behavior comparison and weekend purchase pattern analysis.';
ALTER TABLE gold_date_dim ALTER COLUMN is_holiday COMMENT 'TRUE for holiday dates. Use for holiday customer behavior analysis and holiday impact on sales and engagement.';
ALTER TABLE gold_date_dim ALTER COLUMN holiday_name COMMENT 'Holiday name (if applicable). Use for specific holiday analysis and holiday-specific customer behavior patterns.';

-- Fiscal attributes
ALTER TABLE gold_date_dim ALTER COLUMN fiscal_year COMMENT 'Fiscal year. Use for fiscal year-based customer behavior analysis and fiscal period comparisons.';
ALTER TABLE gold_date_dim ALTER COLUMN fiscal_quarter COMMENT 'Fiscal quarter. Use for fiscal quarter-based customer behavior analysis.';
ALTER TABLE gold_date_dim ALTER COLUMN fiscal_month COMMENT 'Fiscal month. Use for fiscal month-based customer behavior analysis.';


