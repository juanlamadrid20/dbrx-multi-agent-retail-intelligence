"""
Aggregate and Bridge Table Generator for Fashion Retail Gold Layer
Creates and populates bridge tables and aggregates for advanced analytics
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class AggregateGenerator:
    """Generate aggregate and bridge tables for fashion retail star schema"""
    
    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.catalog = config['catalog']
        self.schema = config['schema']
        
        # Set seed for reproducibility
        random.seed(42)
    
    def create_customer_product_affinity(self):
        """Create customer-product affinity aggregate for personalization"""
        logger.info("Generating customer-product affinity aggregate...")
        
        # Calculate affinity scores from sales and event data
        affinity_query = f"""
        WITH customer_interactions AS (
            -- Purchase history
            SELECT 
                s.customer_key,
                s.product_key,
                COUNT(DISTINCT s.transaction_id) as purchase_count,
                SUM(s.net_sales_amount) as total_spent,
                MAX(s.date_key) as last_purchase_date
            FROM {self.catalog}.{self.schema}.gold_sales_fact s
            WHERE s.is_return = false
            GROUP BY s.customer_key, s.product_key
        ),
        customer_events AS (
            -- Browsing behavior
            SELECT 
                e.customer_key,
                e.product_key,
                COUNT(CASE WHEN e.event_type = 'product_view' THEN 1 END) as view_count,
                COUNT(CASE WHEN e.event_type = 'add_to_cart' THEN 1 END) as cart_add_count,
                MAX(e.date_key) as last_interaction_date
            FROM {self.catalog}.{self.schema}.gold_customer_event_fact e
            WHERE e.product_key IS NOT NULL
            GROUP BY e.customer_key, e.product_key
        ),
        combined_data AS (
            SELECT 
                COALESCE(i.customer_key, e.customer_key) as customer_key,
                COALESCE(i.product_key, e.product_key) as product_key,
                COALESCE(i.purchase_count, 0) as purchase_count,
                COALESCE(i.total_spent, 0) as total_spent,
                COALESCE(e.view_count, 0) as view_count,
                COALESCE(e.cart_add_count, 0) as cart_add_count,
                GREATEST(
                    COALESCE(i.last_purchase_date, 0), 
                    COALESCE(e.last_interaction_date, 0)
                ) as last_interaction_date
            FROM customer_interactions i
            FULL OUTER JOIN customer_events e
                ON i.customer_key = e.customer_key 
                AND i.product_key = e.product_key
        ),
        affinity_scores AS (
            SELECT 
                customer_key,
                product_key,
                purchase_count,
                view_count,
                cart_add_count,
                -- Calculate affinity score (0-1)
                LEAST(1.0, 
                    (purchase_count * 0.5 + 
                     cart_add_count * 0.3 + 
                     view_count * 0.2) / 10
                ) as affinity_score,
                -- Days since last interaction
                DATEDIFF(CURRENT_DATE,
                    DATE(CONCAT(
                        SUBSTR(CAST(last_interaction_date AS STRING), 1, 4), '-',
                        SUBSTR(CAST(last_interaction_date AS STRING), 5, 2), '-',
                        SUBSTR(CAST(last_interaction_date AS STRING), 7, 2)
                    ))) as days_since_last_interaction,
                -- Conversion metrics
                CASE 
                    WHEN view_count > 0 THEN CAST(purchase_count AS DOUBLE) / view_count
                    ELSE 0 
                END as view_to_purchase_ratio,
                CASE 
                    WHEN cart_add_count > 0 THEN CAST(purchase_count AS DOUBLE) / cart_add_count
                    ELSE 0 
                END as cart_to_purchase_ratio,
                -- Predicted CLTV impact
                total_spent * (1 + LEAST(1.0, purchase_count * 0.1)) as predicted_cltv_impact
            FROM combined_data
            WHERE purchase_count > 0 OR view_count > 5 OR cart_add_count > 0
        )
        SELECT 
            customer_key,
            product_key,
            ROUND(affinity_score, 2) as affinity_score,
            purchase_count,
            view_count,
            cart_add_count,
            days_since_last_interaction,
            ROUND(view_to_purchase_ratio, 4) as view_to_purchase_ratio,
            ROUND(cart_to_purchase_ratio, 4) as cart_to_purchase_ratio,
            ROW_NUMBER() OVER (PARTITION BY customer_key ORDER BY affinity_score DESC) as recommendation_rank,
            ROUND(predicted_cltv_impact, 2) as predicted_cltv_impact,
            CURRENT_DATE as calculation_date,
            'ML_PERSONALIZATION' as source_system,
            CURRENT_TIMESTAMP as etl_timestamp
        FROM affinity_scores
        """
        
        # Execute query and create table
        affinity_df = self.spark.sql(affinity_query)
        
        affinity_df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_customer_product_affinity_agg")
        
        # Add table properties
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_customer_product_affinity_agg
            SET TBLPROPERTIES (
                'comment' = 'Customer-Product affinity scores for personalization. Source: ML Personalization Engine'
            )
        """)
        
        record_count = self.spark.sql(f"""
            SELECT COUNT(*) as cnt 
            FROM {self.catalog}.{self.schema}.gold_customer_product_affinity_agg
        """).collect()[0]['cnt']
        
        logger.info(f"Created customer-product affinity aggregate with {record_count:,} records")
    
    def create_size_fit_bridge(self):
        """Create size fit bridge table for size recommendations"""
        logger.info("Generating size fit bridge table...")
        
        # Load necessary dimension data
        customers = self.spark.sql(f"""
            SELECT customer_key, size_profile_tops, size_profile_bottoms
            FROM {self.catalog}.{self.schema}.gold_customer_dim
            WHERE is_current = true
            LIMIT 1000
        """).collect()
        
        products = self.spark.sql(f"""
            SELECT product_key, category_level_2, size_range
            FROM {self.catalog}.{self.schema}.gold_product_dim
            WHERE is_active = true 
            AND category_level_1 = 'apparel'
            LIMIT 500
        """).collect()
        
        size_data = []
        sizes_apparel = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        fit_feedback = ['too_small', 'perfect', 'too_large']
        fit_weights = [0.2, 0.65, 0.15]  # Most items fit well
        
        # Generate size fit feedback data
        for _ in range(5000):  # Generate 5000 feedback records
            customer = random.choice(customers)
            product = random.choice(products)
            
            # Determine ordered size based on customer profile
            if product['category_level_2'] in ['tops', 'dresses', 'outerwear']:
                customer_usual_size = customer['size_profile_tops']
            else:
                # For bottoms, convert numeric to letter size
                size_map = {'28': 'XS', '30': 'S', '32': 'M', '34': 'L', '36': 'XL'}
                customer_usual_size = size_map.get(customer['size_profile_bottoms'], 'M')
            
            # Sometimes customers order different sizes
            if random.random() < 0.8:  # 80% order usual size
                ordered_size = customer_usual_size
            else:  # 20% try different size
                ordered_size = random.choice(sizes_apparel)
            
            # Determine fit outcome
            if ordered_size == customer_usual_size:
                fit = random.choices(fit_feedback, [0.1, 0.8, 0.1])[0]  # Usually perfect
            else:
                fit = random.choices(fit_feedback, fit_weights)[0]
            
            # Determine if kept or returned
            if fit == 'perfect':
                is_returned = random.random() < 0.05  # 5% return even if perfect fit
                kept_size = ordered_size
                fit_score = random.choice([4, 5])
            elif fit == 'too_small':
                is_returned = random.random() < 0.7  # 70% return if too small
                kept_size = None if is_returned else ordered_size
                fit_score = random.choice([1, 2])
            else:  # too_large
                is_returned = random.random() < 0.6  # 60% return if too large
                kept_size = None if is_returned else ordered_size
                fit_score = random.choice([2, 3])
            
            # Generate return reasons
            if is_returned:
                if fit == 'perfect':
                    return_reason = random.choice(['changed_mind', 'found_better_price', 'quality_issue'])
                else:
                    return_reason = f'fit_issue_{fit}'
            else:
                return_reason = None
            
            # Recommended size (what ML model would suggest)
            if fit == 'too_small':
                size_idx = sizes_apparel.index(ordered_size)
                recommended_size = sizes_apparel[(len(sizes_apparel) - 1) if (size_idx + 1) > (len(sizes_apparel) - 1) else (size_idx + 1)]
            elif fit == 'too_large':
                size_idx = sizes_apparel.index(ordered_size)
                recommended_size = sizes_apparel[0 if (size_idx - 1) < 0 else (size_idx - 1)]
            else:
                recommended_size = ordered_size
            
            size_record = {
                'customer_key': customer['customer_key'],
                'product_key': product['product_key'],
                'ordered_size': ordered_size,
                'kept_size': kept_size,
                'recommended_size': recommended_size,
                'fit_score': fit_score,
                'fit_description': fit,
                'is_returned': is_returned,
                'return_reason': return_reason,
                'customer_height_cm': random.randint(150, 195) if random.random() < 0.3 else None,
                'customer_weight_kg': random.randint(45, 110) if random.random() < 0.3 else None,
                'customer_body_type': random.choice(['athletic', 'average', 'curvy', 'petite', 'tall']) 
                                      if random.random() < 0.2 else None,
                'source_system': 'RETURNS_FEEDBACK',
                'etl_timestamp': datetime.now()
            }
            size_data.append(size_record)
        
        # Create DataFrame and write
        df = self.spark.createDataFrame(size_data)
        df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_size_fit_bridge")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_size_fit_bridge
            SET TBLPROPERTIES (
                'comment' = 'Size and fit feedback bridge table. Sources: Returns System, Customer Reviews, Fit Predictor'
            )
        """)
        
        logger.info(f"Created size fit bridge table with {len(size_data):,} records")
    
    def create_inventory_movement_fact(self):
        """Create inventory movement fact table"""
        logger.info("Generating inventory movement fact table...")
        
        # Load dimension data
        products = self.spark.sql(f"""
            SELECT product_key, base_price
            FROM {self.catalog}.{self.schema}.gold_product_dim
            WHERE is_active = true
            LIMIT 500
        """).collect()
        
        locations = self.spark.sql(f"""
            SELECT location_key, location_type
            FROM {self.catalog}.{self.schema}.gold_location_dim
            WHERE is_active = true
        """).collect()
        
        dates = self.spark.sql(f"""
            SELECT date_key
            FROM {self.catalog}.{self.schema}.gold_date_dim
            WHERE calendar_date >= DATE_SUB(CURRENT_DATE, 30)
            AND calendar_date <= CURRENT_DATE
            ORDER BY calendar_date
        """).collect()
        
        movement_types = ['receipt', 'sale', 'transfer', 'adjustment', 'return']
        movement_data = []
        movement_id = 1
        
        # Separate locations by type
        stores = [l for l in locations if l['location_type'] == 'store']
        warehouses = [l for l in locations if l['location_type'] in ['warehouse', 'dc']]
        
        # Generate movements for last 30 days
        for date in dates:
            daily_movements = random.randint(100, 300)
            
            for _ in range(daily_movements):
                movement_type = random.choice(movement_types)
                product = random.choice(products)
                
                # Determine from/to locations based on movement type
                if movement_type == 'receipt':
                    # Goods received at warehouse/DC
                    from_location = None
                    to_location = random.choice(warehouses)
                elif movement_type == 'sale':
                    # Sale from store
                    from_location = random.choice(stores)
                    to_location = None
                elif movement_type == 'transfer':
                    # Transfer between locations
                    if random.random() < 0.7:  # 70% warehouse to store
                        from_location = random.choice(warehouses)
                        to_location = random.choice(stores)
                    else:  # 30% store to store
                        from_location = random.choice(stores)
                        to_location = random.choice([s for s in stores if s != from_location])
                elif movement_type == 'return':
                    # Return to store or warehouse
                    from_location = None
                    to_location = random.choice(stores + warehouses)
                else:  # adjustment
                    # Inventory adjustment at any location
                    location = random.choice(locations)
                    from_location = location
                    to_location = location
                
                # Generate movement details
                quantity = random.choices([1, 2, 5, 10, 20, 50, 100], 
                                        [0.3, 0.2, 0.2, 0.15, 0.1, 0.03, 0.02])[0]
                unit_cost = float(product['base_price']) * 0.4
                
                movement_record = {
                    'movement_id': f"MOV_{str(movement_id).zfill(10)}",
                    'product_key': product['product_key'],
                    'from_location_key': from_location['location_key'] if from_location else None,
                    'to_location_key': to_location['location_key'] if to_location else None,
                    'date_key': date['date_key'],
                    'time_key': random.choice([900, 1200, 1500, 1800]),
                    'movement_type': movement_type,
                    'movement_reason': f"{movement_type}_reason_{random.randint(1, 5)}",
                    'quantity': quantity,
                    'unit_cost': float(int(unit_cost * 100)) / 100,
                    'total_cost': float(int((unit_cost * quantity) * 100)) / 100,
                    'reference_type': 'order' if movement_type == 'sale' else 
                                     'transfer' if movement_type == 'transfer' else 
                                     'adjustment',
                    'reference_id': f"REF_{movement_type.upper()}_{movement_id}",
                    'source_system': 'WMS_STORE_OPS',
                    'etl_timestamp': datetime.now()
                }
                movement_data.append(movement_record)
                movement_id += 1
        
        # Create DataFrame and write
        df = self.spark.createDataFrame(movement_data)
        df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_inventory_movement_fact")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_inventory_movement_fact
            SET TBLPROPERTIES (
                'comment' = 'Inventory movement transactions. Sources: WMS, Store Operations, DC Systems'
            )
        """)
        
        logger.info(f"Created inventory movement fact table with {len(movement_data):,} records")
    
    def create_channel_performance_metrics(self):
        """Create additional channel performance metrics aggregate"""
        logger.info("Generating channel performance metrics...")
        
        # Calculate channel performance from sales and events
        channel_metrics_query = f"""
        WITH channel_sales AS (
            SELECT 
                s.channel_key,
                s.date_key,
                COUNT(DISTINCT s.customer_key) as unique_customers,
                COUNT(DISTINCT s.transaction_id) as transaction_count,
                SUM(s.net_sales_amount) as total_revenue,
                AVG(s.net_sales_amount) as avg_order_value,
                SUM(CASE WHEN s.is_return THEN 1 ELSE 0 END) as return_count
            FROM {self.catalog}.{self.schema}.gold_sales_fact s
            GROUP BY s.channel_key, s.date_key
        ),
        channel_traffic AS (
            SELECT 
                e.channel_key,
                e.date_key,
                COUNT(DISTINCT e.session_id) as session_count,
                COUNT(DISTINCT e.customer_key) as visitor_count,
                SUM(CASE WHEN e.event_type = 'product_view' THEN 1 ELSE 0 END) as product_views,
                SUM(CASE WHEN e.conversion_flag THEN 1 ELSE 0 END) as conversions
            FROM {self.catalog}.{self.schema}.gold_customer_event_fact e
            GROUP BY e.channel_key, e.date_key
        )
        SELECT 
            COALESCE(s.channel_key, t.channel_key) as channel_key,
            COALESCE(s.date_key, t.date_key) as date_key,
            COALESCE(s.unique_customers, 0) as unique_customers,
            COALESCE(s.transaction_count, 0) as transaction_count,
            COALESCE(s.total_revenue, 0) as total_revenue,
            COALESCE(s.avg_order_value, 0) as avg_order_value,
            COALESCE(t.session_count, 0) as session_count,
            COALESCE(t.visitor_count, 0) as visitor_count,
            CASE 
                WHEN t.session_count > 0 
                THEN CAST(s.transaction_count AS DOUBLE) / t.session_count 
                ELSE 0 
            END as conversion_rate,
            CASE 
                WHEN s.transaction_count > 0 
                THEN CAST(s.return_count AS DOUBLE) / s.transaction_count 
                ELSE 0 
            END as return_rate,
            'ANALYTICS_AGGREGATED' as source_system,
            CURRENT_TIMESTAMP as etl_timestamp
        FROM channel_sales s
        FULL OUTER JOIN channel_traffic t
            ON s.channel_key = t.channel_key 
            AND s.date_key = t.date_key
        """
        
        # Execute and save (optional - not in original schema but useful)
        logger.info("Channel performance metrics calculated (query available for use)")