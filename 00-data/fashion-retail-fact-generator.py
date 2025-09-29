"""
Fact Table Generator for Fashion Retail Gold Layer
Creates and populates all fact tables with realistic transactional data
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random
import math
import logging

logger = logging.getLogger(__name__)

class FactGenerator:
    """Generate fact tables for fashion retail star schema"""
    
    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.catalog = config['catalog']
        self.schema = config['schema']
        
        # Load dimension data for foreign keys
        self._load_dimensions()
        
        # Set seed for reproducibility
        random.seed(42)
    
    def _load_dimensions(self):
        """Load dimension data for generating foreign keys"""
        logger.info("Loading dimension data...")
        
        # Load customer keys
        self.customer_keys = self.spark.sql(f"""
            SELECT customer_key, customer_id, segment, preferred_channel, lifetime_value
            FROM {self.catalog}.{self.schema}.gold_customer_dim
            WHERE is_current = true
        """).collect()
        
        # Load product keys
        self.product_keys = self.spark.sql(f"""
            SELECT product_key, product_id, category_level_1, category_level_2, 
                   base_price, season_code, brand
            FROM {self.catalog}.{self.schema}.gold_product_dim
            WHERE is_active = true
        """).collect()
        
        # Load location keys
        self.location_keys = self.spark.sql(f"""
            SELECT location_key, location_id, location_type
            FROM {self.catalog}.{self.schema}.gold_location_dim
            WHERE is_active = true
        """).collect()
        
        # Separate store and warehouse locations
        self.store_locations = [l for l in self.location_keys if l['location_type'] == 'store']
        self.warehouse_locations = [l for l in self.location_keys if l['location_type'] in ['warehouse', 'dc']]
        
        # Load date keys
        self.date_keys = self.spark.sql(f"""
            SELECT date_key, calendar_date, is_weekend, is_holiday, 
                   is_peak_season, is_sale_period, season
            FROM {self.catalog}.{self.schema}.gold_date_dim
            WHERE calendar_date >= DATE_SUB(CURRENT_DATE, {self.config['historical_days']})
                AND calendar_date <= CURRENT_DATE
            ORDER BY calendar_date
        """).collect()
        
        # Load channel keys
        self.channel_keys = self.spark.sql(f"""
            SELECT channel_key, channel_code, is_digital
            FROM {self.catalog}.{self.schema}.gold_channel_dim
        """).collect()
        
        logger.info(f"Loaded dimensions: {len(self.customer_keys)} customers, "
                   f"{len(self.product_keys)} products, {len(self.location_keys)} locations")
    
    def _apply_seasonality_multiplier(self, base_value, date_info):
        """Apply seasonality to a base value"""
        multiplier = 1.0
        
        # Seasonal multipliers
        if date_info['is_peak_season']:
            multiplier *= 1.5
        if date_info['is_sale_period']:
            multiplier *= 1.3
        if date_info['is_holiday']:
            multiplier *= 1.8
        if date_info['is_weekend']:
            multiplier *= 1.2
        
        # Monthly patterns
        month = int(str(date_info['date_key'])[4:6])
        monthly_factors = {
            1: 0.7,   # Post-holiday slowdown
            2: 0.8,
            3: 1.0,   # Spring launch
            4: 1.2,
            5: 1.1,
            6: 1.0,
            7: 0.9,   # Summer slowdown
            8: 0.9,
            9: 1.1,   # Back to school
            10: 1.2,
            11: 1.5,  # Black Friday
            12: 1.8   # Holiday peak
        }
        multiplier *= monthly_factors.get(month, 1.0)
        
        return base_value * multiplier
    
    def create_sales_fact(self):
        """Create and populate sales fact table"""
        logger.info("Generating sales fact table...")
        
        sales_data = []
        transaction_id = 1
        line_item_id = 1
        
        # Calculate daily transaction volume
        total_days = len(self.date_keys)
        avg_transactions_per_day = 500  # Base rate
        
        for date_info in self.date_keys:
            # Determine number of transactions for this day
            base_transactions = self._apply_seasonality_multiplier(
                avg_transactions_per_day, 
                date_info
            )
            num_transactions = int(random.gauss(base_transactions, base_transactions * 0.2))
            
            for _ in range(num_transactions):
                # Select random customer
                customer = random.choice(self.customer_keys)
                
                # Customer segment affects purchase behavior
                segment = customer['segment']
                if segment == 'vip':
                    items_in_basket = random.choice([3, 4, 5, 6, 7, 8])  # VIP customers buy more
                    discount_probability = 0.15  # Low discount rate for VIP
                    return_probability = 0.05  # Lower return rate
                elif segment == 'premium':
                    items_in_basket = random.choice([2, 3, 4, 5, 6])  # Premium customers buy multiple items
                    discount_probability = 0.25
                    return_probability = 0.08
                elif segment == 'loyal':
                    items_in_basket = random.choice([2, 3, 4, 5])  # Loyal customers consistent purchases
                    discount_probability = 0.30  # Moderate discounts for loyalty
                    return_probability = 0.10
                elif segment == 'regular':
                    items_in_basket = random.choice([1, 2, 3, 4])  # Regular purchasing pattern
                    discount_probability = 0.35
                    return_probability = 0.12
                else:  # new customers
                    items_in_basket = random.choice([1, 2, 3])  # New customers start small
                    discount_probability = 0.40  # Higher discounts to attract new customers
                    return_probability = 0.15  # Higher return rate due to uncertainty
                
                # Select channel based on customer preference
                if random.random() < 0.7:  # 70% chance of preferred channel
                    channel = next((c for c in self.channel_keys 
                                   if customer['preferred_channel'] in c['channel_code'].lower()), 
                                  random.choice(self.channel_keys))
                else:
                    channel = random.choice(self.channel_keys)
                
                # Select location
                if channel['is_digital']:
                    location = random.choice(self.warehouse_locations)
                else:
                    location = random.choice(self.store_locations)
                
                # Generate transaction items
                order_number = f"ORD_{str(transaction_id).zfill(10)}"
                
                for item_num in range(items_in_basket):
                    # Select product (with bias towards popular items)
                    # Select product (simplified to avoid random.choices)
                    product = random.choice(self.product_keys)
                    
                    # Calculate pricing
                    base_price = float(product['base_price'])
                    
                    # Apply discounts (influenced by customer segment)
                    is_promotional = date_info['is_sale_period'] and random.random() < 0.3
                    is_clearance = product['season_code'] != date_info['season'] and random.random() < 0.2
                    has_segment_discount = random.random() < discount_probability

                    if is_clearance:
                        discount_pct = random.uniform(0.3, 0.5)
                    elif is_promotional:
                        discount_pct = random.uniform(0.1, 0.3)
                    elif has_segment_discount:
                        # Segment-based discount amount varies by segment
                        if segment == 'vip':
                            discount_pct = random.uniform(0.05, 0.15)  # Smaller discounts for VIP
                        elif segment == 'premium':
                            discount_pct = random.uniform(0.08, 0.18)
                        elif segment == 'loyal':
                            discount_pct = random.uniform(0.10, 0.20)
                        elif segment == 'regular':
                            discount_pct = random.uniform(0.12, 0.25)
                        else:  # new customers
                            discount_pct = random.uniform(0.15, 0.30)  # Larger discounts for new customers
                    else:
                        discount_pct = 0.0
                    
                    unit_price = base_price
                    discount_amount = float(int(base_price * discount_pct * 100)) / 100
                    quantity = random.choice([1, 2, 3])
                    
                    # Calculate amounts
                    net_sales = float(int((unit_price - discount_amount) * quantity * 100)) / 100
                    tax_amount = float(int(net_sales * 0.08 * 100)) / 100  # 8% tax
                    gross_margin = float(int(net_sales * random.uniform(0.4, 0.6) * 100)) / 100
                    
                    # Return probability (influenced by customer segment and channel)
                    base_return_rate = return_probability
                    channel_multiplier = 1.2 if channel['is_digital'] else 0.8  # Digital has higher returns
                    is_return = random.random() < (base_return_rate * channel_multiplier)
                    
                    sales_record = {
                        'transaction_id': f"TXN_{str(transaction_id).zfill(10)}",
                        'line_item_id': f"LINE_{str(line_item_id).zfill(12)}",
                        'customer_key': customer['customer_key'],
                        'product_key': product['product_key'],
                        'date_key': date_info['date_key'],
                        'time_key': random.choice([900, 1200, 1500, 1800, 2000]),  # Peak hours
                        'location_key': location['location_key'],
                        'channel_key': channel['channel_key'],
                        'order_number': order_number,
                        'pos_terminal_id': f"POS_{location['location_key']}" if not channel['is_digital'] else None,
                        'sales_associate_id': f"SA_{random.randint(1, 100)}" if not channel['is_digital'] else None,
                        'quantity_sold': quantity,
                        'unit_price': unit_price,
                        'discount_amount': discount_amount,
                        'tax_amount': tax_amount,
                        'net_sales_amount': net_sales,
                        'gross_margin_amount': gross_margin,
                        'is_return': is_return,
                        'is_exchange': is_return and random.random() < 0.3,
                        'is_promotional': is_promotional,
                        'is_clearance': is_clearance,
                        'fulfillment_type': random.choice(['ship', 'pickup', 'same_day']) if channel['is_digital'] 
                                           else 'in_store',
                        'payment_method': random.choice(['credit_card', 'debit_card', 'paypal', 'apple_pay']),
                        'source_system': 'OMS_POS_ECOMM',
                        'etl_timestamp': datetime.now()
                    }
                    sales_data.append(sales_record)
                    line_item_id += 1
                
                transaction_id += 1
                
                # Batch write every 100K records
                if len(sales_data) >= 100000:
                    self._write_batch(sales_data, 'gold_sales_fact', mode='append' if transaction_id > 100001 else 'overwrite')
                    sales_data = []
        
        # Write remaining records
        if sales_data:
            self._write_batch(sales_data, 'gold_sales_fact', mode='append' if transaction_id > 100001 else 'overwrite')
        
        # Add table properties
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_sales_fact
            SET TBLPROPERTIES (
                'comment' = 'Sales transaction fact table. Sources: OMS, POS System, Shopify, Store Operations'
            )
        """)
        
        logger.info(f"Created sales fact table with ~{transaction_id:,} transactions")
    
    def create_inventory_fact(self):
        """Create and populate inventory fact table (daily snapshots)"""
        logger.info("Generating inventory fact table...")
        
        inventory_data = []
        
        # For each date, create inventory snapshot for all product-location combinations
        for date_info in self.date_keys[-30:]:  # Last 30 days for demo (full would be huge)
            for product in self.product_keys[:1000]:  # Limit products for demo
                for location in self.location_keys:
                    # Base inventory levels vary by location type
                    if location['location_type'] == 'dc':
                        base_qty = random.randint(500, 2000)
                    elif location['location_type'] == 'warehouse':
                        base_qty = random.randint(200, 800)
                    else:  # store
                        base_qty = random.randint(10, 100)
                    
                    # Apply seasonality and randomness
                    qty_on_hand = int(self._apply_seasonality_multiplier(base_qty, date_info) * 
                                     random.uniform(0.5, 1.5))
                    
                    # Calculate other inventory metrics
                    qty_reserved = int(qty_on_hand * random.uniform(0, 0.3))
                    qty_available = qty_on_hand - qty_reserved
                    qty_in_transit = random.randint(0, 50) if random.random() < 0.2 else 0
                    qty_damaged = random.randint(0, 5) if random.random() < 0.1 else 0
                    
                    # Financial metrics
                    unit_cost = float(product['base_price']) * 0.4
                    inventory_value_cost = float(int(qty_on_hand * unit_cost * 100)) / 100
                    inventory_value_retail = float(int(qty_on_hand * float(product['base_price']) * 100)) / 100
                    
                    # Inventory health metrics
                    days_of_supply = random.randint(5, 90)
                    stock_cover_days = random.randint(7, 60)
                    reorder_point = random.randint(20, 200)
                    reorder_quantity = random.randint(50, 500)
                    
                    # Flags
                    is_stockout = qty_available <= 0
                    is_overstock = days_of_supply > 60
                    
                    inventory_record = {
                        'product_key': product['product_key'],
                        'location_key': location['location_key'],
                        'date_key': date_info['date_key'],
                        'quantity_on_hand': qty_on_hand,
                        'quantity_available': qty_available,
                        'quantity_reserved': qty_reserved,
                        'quantity_in_transit': qty_in_transit,
                        'quantity_damaged': qty_damaged,
                        'inventory_value_cost': inventory_value_cost,
                        'inventory_value_retail': inventory_value_retail,
                        'days_of_supply': days_of_supply,
                        'stock_cover_days': stock_cover_days,
                        'reorder_point': reorder_point,
                        'reorder_quantity': reorder_quantity,
                        'is_stockout': is_stockout,
                        'is_overstock': is_overstock,
                        'is_discontinued': False,
                        'source_system': 'WMS_STORE_INV',
                        'etl_timestamp': datetime.now()
                    }
                    inventory_data.append(inventory_record)
                    
                    # Batch write
                    if len(inventory_data) >= 100000:
                        self._write_batch(inventory_data, 'gold_inventory_fact', mode='append' if len(inventory_data) > 100000 else 'overwrite')
                        inventory_data = []
        
        # Write remaining records
        if inventory_data:
            self._write_batch(inventory_data, 'gold_inventory_fact', mode='append')
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_inventory_fact
            SET TBLPROPERTIES (
                'comment' = 'Daily inventory snapshot fact. Sources: WMS, Store Inventory, RFID Systems'
            )
        """)
        
        logger.info(f"Created inventory fact table with daily snapshots")
    
    def create_customer_event_fact(self):
        """Create and populate customer event fact table"""
        logger.info("Generating customer event fact table...")
        
        event_types = ['page_view', 'product_view', 'search', 'add_to_cart', 'remove_from_cart', 
                      'checkout_start', 'checkout_complete', 'filter_apply', 'size_guide_view']
        
        events_data = []
        event_id = 1
        
        # Generate events for last 30 days (for demo)
        for date_info in self.date_keys[-30:]:
            # Number of events varies by day
            base_events = self._apply_seasonality_multiplier(self.config['events_per_day'], date_info)
            num_events = int(random.gauss(base_events, base_events * 0.2))
            
            for _ in range(num_events):
                customer = random.choice(self.customer_keys)
                product = random.choice(self.product_keys) if random.random() < 0.7 else None
                channel = random.choice([c for c in self.channel_keys if c['is_digital']])
                
                event_type = random.choice(event_types)
                
                # Generate session ID
                session_id = f"SESSION_{customer['customer_key']}_{date_info['date_key']}_{random.randint(1, 10)}"
                
                # Event value depends on type
                if event_type == 'checkout_complete':
                    event_value = random.uniform(50, 500)
                    conversion_flag = True
                elif event_type == 'add_to_cart':
                    event_value = float(product['base_price']) if product else 0
                    conversion_flag = False
                else:
                    event_value = 0
                    conversion_flag = False
                
                event_record = {
                    'event_id': event_id,
                    'session_id': session_id,
                    'customer_key': customer['customer_key'],
                    'product_key': product['product_key'] if product else None,
                    'date_key': date_info['date_key'],
                    'time_key': random.choice([900, 1200, 1500, 1800, 2000]),
                    'channel_key': channel['channel_key'],
                    'location_key': None,  # Digital events don't have physical location
                    'event_type': event_type,
                    'event_category': 'engagement' if 'view' in event_type else 'conversion' if 'checkout' in event_type else 'interaction',
                    'event_action': event_type,
                    'event_label': product['category_level_2'] if product else None,
                    'event_value': float(int(event_value * 100)) / 100,
                    'time_on_page_seconds': random.randint(5, 300) if 'view' in event_type else 0,
                    'bounce_flag': random.random() < 0.3 if event_type == 'page_view' else False,
                    'conversion_flag': conversion_flag,
                    'page_url': f"/products/{product['product_id']}" if product else "/home",
                    'referrer_url': random.choice(['google.com', 'facebook.com', 'instagram.com', 'direct', 'email']),
                    'search_term': f"{product['category_level_2']} {product['brand']}" if event_type == 'search' and product else None,
                    'source_system': 'GA4_ADOBE_STORE',
                    'etl_timestamp': datetime.now()
                }
                events_data.append(event_record)
                event_id += 1
                
                # Batch write
                if len(events_data) >= 100000:
                    self._write_batch(events_data, 'gold_customer_event_fact', 
                                    mode='append' if event_id > 100001 else 'overwrite')
                    events_data = []
        
        # Write remaining records
        if events_data:
            self._write_batch(events_data, 'gold_customer_event_fact', mode='append')
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_customer_event_fact
            SET TBLPROPERTIES (
                'comment' = 'Customer interaction events fact. Sources: GA4, Adobe Analytics, Store Traffic Counters'
            )
        """)
        
        logger.info(f"Created customer event fact table with ~{event_id:,} events")
    
    def create_cart_abandonment_fact(self):
        """Create and populate cart abandonment fact table"""
        logger.info("Generating cart abandonment fact table...")
        
        abandonment_data = []
        
        # Generate cart abandonments for last 90 days
        for date_info in self.date_keys[-90:]:
            # Daily abandonment rate varies
            daily_abandonments = int(self._apply_seasonality_multiplier(50, date_info))
            
            for i in range(daily_abandonments):
                customer = random.choice(self.customer_keys)
                channel = random.choice([c for c in self.channel_keys if c['is_digital']])
                
                # Cart value and items
                items_count = random.choice([1, 2, 3, 4, 5])
                cart_value = float(int(random.uniform(50, 500) * 100)) / 100
                
                # Recovery metrics
                recovery_email_sent = random.random() < 0.8
                recovery_email_opened = recovery_email_sent and random.random() < 0.4
                recovery_email_clicked = recovery_email_opened and random.random() < 0.3
                is_recovered = recovery_email_clicked and random.random() < 0.25
                
                abandonment_record = {
                    'abandonment_id': i + 1,
                    'cart_id': f"CART_{date_info['date_key']}_{i}",
                    'customer_key': customer['customer_key'],
                    'date_key': date_info['date_key'],
                    'time_key': random.choice([900, 1200, 1500, 1800, 2000]),
                    'channel_key': channel['channel_key'],
                    'cart_value': cart_value,
                    'items_count': items_count,
                    'minutes_in_cart': random.randint(5, 180),
                    'recovery_email_sent': recovery_email_sent,
                    'recovery_email_opened': recovery_email_opened,
                    'recovery_email_clicked': recovery_email_clicked,
                    'is_recovered': is_recovered,
                    'recovery_date_key': date_info['date_key'] + random.randint(1, 7) if is_recovered else None,
                    'recovery_revenue': cart_value * random.uniform(0.7, 1.0) if is_recovered else 0.0,
                    'abandonment_stage': random.choice(['cart', 'shipping', 'payment']),
                    'suspected_reason': random.choice(['high_shipping', 'price_concern', 'comparison_shopping', 
                                                      'technical_issue', 'payment_issue']),
                    'source_system': 'SHOPIFY_MOBILE_APP',
                    'etl_timestamp': datetime.now()
                }
                abandonment_data.append(abandonment_record)
        
        # Define explicit schema for cart abandonment fact
        abandonment_schema = StructType([
            StructField("abandonment_id", IntegerType(), False),
            StructField("cart_id", StringType(), True),
            StructField("customer_key", IntegerType(), True),
            StructField("date_key", IntegerType(), True),
            StructField("time_key", IntegerType(), True),
            StructField("channel_key", IntegerType(), True),
            StructField("cart_value", DoubleType(), True),
            StructField("items_count", IntegerType(), True),
            StructField("minutes_in_cart", IntegerType(), True),
            StructField("recovery_email_sent", BooleanType(), True),
            StructField("recovery_email_opened", BooleanType(), True),
            StructField("recovery_email_clicked", BooleanType(), True),
            StructField("is_recovered", BooleanType(), True),
            StructField("recovery_date_key", IntegerType(), True),
            StructField("recovery_revenue", DoubleType(), True),
            StructField("abandonment_stage", StringType(), True),
            StructField("suspected_reason", StringType(), True),
            StructField("source_system", StringType(), True),
            StructField("etl_timestamp", TimestampType(), True)
        ])

        # Create DataFrame with explicit schema
        df = self.spark.createDataFrame(abandonment_data, schema=abandonment_schema)
        df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_cart_abandonment_fact")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_cart_abandonment_fact
            SET TBLPROPERTIES (
                'comment' = 'Cart abandonment tracking fact. Sources: Shopify, Mobile App, Email Marketing Platform'
            )
        """)
        
        logger.info(f"Created cart abandonment fact table with {len(abandonment_data):,} records")
    
    def create_demand_forecast_fact(self):
        """Create and populate demand forecast fact table"""
        logger.info("Generating demand forecast fact table...")
        
        forecast_data = []
        forecast_id = 1

        # Generate forecasts for last 30 days and next 30 days
        forecast_dates = self.date_keys[-30:] + self.date_keys[:30] if len(self.date_keys) > 60 else self.date_keys

        for date_info in forecast_dates[-30:]:  # Limited for demo
            # Generate forecasts for top products and key locations
            for product in self.product_keys[:100]:  # Top 100 products
                for location in self.store_locations[:5]:  # Top 5 stores
                    # Base forecast
                    base_demand = random.randint(10, 100)
                    forecast_quantity = float(int(self._apply_seasonality_multiplier(base_demand, date_info)))
                    
                    # Confidence intervals
                    confidence_level = 0.95
                    margin = forecast_quantity * 0.2
                    confidence_lower = 0.0 if int(forecast_quantity - margin) < 0 else float(int(forecast_quantity - margin))
                    confidence_upper = float(int(forecast_quantity + margin))
                    
                    # Actual demand (for historical dates)
                    if date_info['calendar_date'] < datetime.now().date():
                        # Add some noise to forecast for actuals
                        actual_quantity_calc = int(forecast_quantity + random.gauss(0, forecast_quantity * 0.15))
                        actual_quantity = 0.0 if actual_quantity_calc < 0 else float(actual_quantity_calc)
                        actual_revenue = float(actual_quantity) * float(product['base_price'])
                        
                        # Calculate accuracy metrics
                        if actual_quantity > 0:
                            diff = forecast_quantity - actual_quantity
                            mape = (diff if diff >= 0 else -diff) / actual_quantity * 100
                            forecast_accuracy = 0.0 if (100 - mape) < 0 else (100 - mape)
                            bias = (forecast_quantity - actual_quantity) / actual_quantity * 100
                        else:
                            mape = 0.0
                            forecast_accuracy = 100.0 if forecast_quantity == 0 else 0.0
                            bias = 0.0
                    else:
                        actual_quantity = None
                        actual_revenue = None
                        mape = None
                        forecast_accuracy = None
                        bias = None
                    
                    forecast_record = {
                        'forecast_id': forecast_id,
                        'forecast_date': date_info['calendar_date'],
                        'product_key': product['product_key'],
                        'location_key': location['location_key'],
                        'date_key': date_info['date_key'],
                        'forecast_quantity': forecast_quantity,
                        'forecast_revenue': forecast_quantity * float(product['base_price']),
                        'confidence_lower_bound': confidence_lower,
                        'confidence_upper_bound': confidence_upper,
                        'confidence_level': confidence_level,
                        'actual_quantity': actual_quantity,
                        'actual_revenue': actual_revenue,
                        'forecast_accuracy': forecast_accuracy,
                        'mape': mape,
                        'bias': bias,
                        'model_version': 'v2.3.1',
                        'model_type': 'ensemble_xgboost_lstm',
                        'source_system': 'ML_PLATFORM_PLANNING',
                        'etl_timestamp': datetime.now()
                    }
                    forecast_data.append(forecast_record)
                    forecast_id += 1
        
        # Define explicit schema for demand forecast fact
        forecast_schema = StructType([
            StructField("forecast_id", IntegerType(), False),
            StructField("forecast_date", DateType(), True),
            StructField("product_key", IntegerType(), True),
            StructField("location_key", IntegerType(), True),
            StructField("date_key", IntegerType(), True),
            StructField("forecast_quantity", DoubleType(), True),
            StructField("forecast_revenue", DoubleType(), True),
            StructField("confidence_lower_bound", DoubleType(), True),
            StructField("confidence_upper_bound", DoubleType(), True),
            StructField("confidence_level", DoubleType(), True),
            StructField("actual_quantity", DoubleType(), True),
            StructField("actual_revenue", DoubleType(), True),
            StructField("forecast_accuracy", DoubleType(), True),
            StructField("mape", DoubleType(), True),
            StructField("bias", DoubleType(), True),
            StructField("model_version", StringType(), True),
            StructField("model_type", StringType(), True),
            StructField("source_system", StringType(), True),
            StructField("etl_timestamp", TimestampType(), True)
        ])

        # Create DataFrame with explicit schema
        df = self.spark.createDataFrame(forecast_data, schema=forecast_schema)
        df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_demand_forecast_fact")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_demand_forecast_fact
            SET TBLPROPERTIES (
                'comment' = 'Demand forecasting fact with accuracy metrics. Sources: DataRobot, Planning System, ML Platform'
            )
        """)
        
        logger.info(f"Created demand forecast fact table with {len(forecast_data):,} records")
    
    def _write_batch(self, data, table_name, mode='append'):
        """Helper function to write data in batches"""

        # Define schema based on table type
        if table_name == 'gold_customer_event_fact':
            schema = StructType([
                StructField("event_id", LongType(), False),
                StructField("customer_key", IntegerType(), True),
                StructField("product_key", IntegerType(), True),
                StructField("location_key", IntegerType(), True),
                StructField("channel_key", IntegerType(), True),
                StructField("date_key", IntegerType(), True),
                StructField("time_key", IntegerType(), True),
                StructField("session_id", StringType(), True),
                StructField("event_timestamp", TimestampType(), True),
                StructField("event_type", StringType(), True),
                StructField("event_category", StringType(), True),
                StructField("event_action", StringType(), True),
                StructField("event_label", StringType(), True),
                StructField("event_value", DoubleType(), True),
                StructField("time_on_page_seconds", IntegerType(), True),
                StructField("bounce_flag", BooleanType(), True),
                StructField("conversion_flag", BooleanType(), True),
                StructField("page_url", StringType(), True),
                StructField("referrer_url", StringType(), True),
                StructField("utm_source", StringType(), True),
                StructField("utm_medium", StringType(), True),
                StructField("utm_campaign", StringType(), True),
                StructField("device_type", StringType(), True),
                StructField("browser", StringType(), True),
                StructField("operating_system", StringType(), True),
                StructField("geo_city", StringType(), True),
                StructField("geo_region", StringType(), True),
                StructField("geo_country", StringType(), True),
                StructField("source_system", StringType(), True),
                StructField("etl_timestamp", TimestampType(), True)
            ])
            df = self.spark.createDataFrame(data, schema=schema)
        else:
            df = self.spark.createDataFrame(data)
        
        if mode == 'overwrite':
            df.write \
                .mode("overwrite") \
                .option("delta.columnMapping.mode", "name") \
                .option("mergeSchema", "true") \
                .saveAsTable(f"{self.catalog}.{self.schema}.{table_name}")
        else:
            df.write \
                .mode("append") \
                .option("mergeSchema", "true") \
                .saveAsTable(f"{self.catalog}.{self.schema}.{table_name}")
        
        logger.info(f"Wrote {len(data):,} records to {table_name}")