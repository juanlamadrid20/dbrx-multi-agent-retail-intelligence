"""
Fact Table Generator for Fashion Retail Gold Layer
Creates and populates all fact tables with realistic transactional data
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, sum as spark_sum, avg as spark_avg
from pyspark.sql.types import (
    StructType, StructField, IntegerType, LongType, StringType, DoubleType,
    DateType, TimestampType, BooleanType
)
from datetime import datetime as dt, timedelta
import random
import logging
from typing import Dict, List, Optional, Any

# Import new inventory-aligned components
from ..inventory.manager import InventoryManager
from ..inventory.validator import SalesValidator, PurchaseRequest, BatchPurchaseBuilder
from ..inventory.stockout_generator import StockoutGenerator
from ..constants import (
    DIGITAL_RETURN_MULTIPLIER, STORE_RETURN_MULTIPLIER,
    MONTHLY_SEASONALITY, SEGMENT_DISCOUNT_RANGES, CUSTOMER_SEGMENTS,
    SOURCE_SYSTEMS, MAX_RECORDS_BEFORE_WRITE,
)

logger = logging.getLogger(__name__)


class FactGenerator:
    """Generate fact tables for fashion retail star schema.
    
    Uses instance-level random number generator for reproducibility and
    batch processing for memory-efficient generation of large datasets.
    
    Thread Safety Note:
        This class is NOT thread-safe. Each instance maintains its own state
        and should be used from a single thread. For parallel processing,
        create separate instances per thread with different random seeds.
    """

    def __init__(
        self,
        spark: SparkSession,
        config: dict,
        inventory_manager: Optional[InventoryManager] = None,
        sales_validator: Optional[SalesValidator] = None
    ):
        self.spark = spark
        self.config = config
        self.catalog = config['catalog']
        self.schema = config['schema']

        # Inventory alignment components (passed from orchestrator)
        self.inventory_manager = inventory_manager
        self.sales_validator = sales_validator

        # Use instance-level random generator for reproducibility
        random_seed = config.get('random_seed', 42)
        self._rng = random.Random(random_seed)

        # Load dimension data for foreign keys
        self._load_dimensions()
    
    def _load_dimensions(self):
        """Load dimension data for generating foreign keys"""
        logger.info("Loading dimension data...")
        
        # Load customer keys
        self.customer_keys = self.spark.sql(f"""
            SELECT customer_key, customer_id, segment, preferred_channel, lifetime_value
            FROM {self.catalog}.{self.schema}.gold_customer_dim
            WHERE is_current = true
        """).collect()
        
        # Load product keys (including unit_cost for accurate margin calculation)
        self.product_keys = self.spark.sql(f"""
            SELECT product_key, product_id, category_level_1, category_level_2, 
                   base_price, unit_cost, season_code, brand
            FROM {self.catalog}.{self.schema}.gold_product_dim
            WHERE is_active = true
        """).collect()
        
        # Load location keys (including state_tax_rate for accurate tax calculation)
        self.location_keys = self.spark.sql(f"""
            SELECT location_key, location_id, location_type, 
                   COALESCE(state_tax_rate, 0.07) as state_tax_rate
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
    
    def _apply_seasonality_multiplier(self, base_value: float, date_info: Dict) -> float:
        """Apply seasonality to a base value.
        
        Args:
            base_value: Base numeric value to adjust
            date_info: Dictionary with date attributes (is_peak_season, is_sale_period, etc.)
            
        Returns:
            Adjusted value with seasonality multipliers applied
        """
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
        
        # Monthly patterns from constants
        month = int(str(date_info['date_key'])[4:6])
        multiplier *= MONTHLY_SEASONALITY.get(month, 1.0)
        
        return base_value * multiplier
    
    def create_sales_fact(self) -> None:
        """Create and populate sales fact table."""
        logger.info("Generating sales fact table...")
        
        sales_data: List[Dict[str, Any]] = []
        transaction_id = 1
        line_item_id = 1
        is_first_batch = True
        
        # Base rate for daily transactions
        avg_transactions_per_day = 500
        
        for date_info in self.date_keys:
            # Determine number of transactions for this day
            base_transactions = self._apply_seasonality_multiplier(
                avg_transactions_per_day, 
                date_info
            )
            num_transactions = int(self._rng.gauss(base_transactions, base_transactions * 0.2))
            
            for _ in range(num_transactions):
                # Select random customer
                customer = self._rng.choice(self.customer_keys)
                
                # Customer segment affects purchase behavior - use constants
                segment = customer['segment']
                segment_config = CUSTOMER_SEGMENTS.get(segment, CUSTOMER_SEGMENTS['regular'])
                
                items_in_basket = self._rng.choice(segment_config['items_range'])
                discount_probability = segment_config['discount_probability']
                return_probability = segment_config['return_probability']
                
                # Select channel based on customer preference
                if self._rng.random() < 0.7:  # 70% chance of preferred channel
                    channel = next((c for c in self.channel_keys 
                                   if customer['preferred_channel'] in c['channel_code'].lower()), 
                                  self._rng.choice(self.channel_keys))
                else:
                    channel = self._rng.choice(self.channel_keys)
                
                # Select location
                if channel['is_digital']:
                    location = self._rng.choice(self.warehouse_locations)
                else:
                    location = self._rng.choice(self.store_locations)
                
                # Generate transaction items
                order_number = f"ORD_{transaction_id:010d}"
                
                for item_num in range(items_in_basket):
                    product = self._rng.choice(self.product_keys)
                    
                    # Calculate pricing
                    base_price = float(product['base_price'])
                    
                    # Apply discounts (influenced by customer segment)
                    is_promotional = date_info['is_sale_period'] and self._rng.random() < 0.3
                    is_clearance = product['season_code'] != date_info['season'] and self._rng.random() < 0.2
                    has_segment_discount = self._rng.random() < discount_probability

                    if is_clearance:
                        discount_pct = self._rng.uniform(0.3, 0.5)
                    elif is_promotional:
                        discount_pct = self._rng.uniform(0.1, 0.3)
                    elif has_segment_discount:
                        # Use segment discount ranges from constants
                        discount_range = SEGMENT_DISCOUNT_RANGES.get(segment, (0.10, 0.20))
                        discount_pct = self._rng.uniform(*discount_range)
                    else:
                        discount_pct = 0.0
                    
                    unit_price = base_price
                    discount_amount = float(int(base_price * discount_pct * 100)) / 100
                    requested_quantity = self._rng.choice([1, 2, 3])

                    # INVENTORY VALIDATION - Feature: 001-i-want-to
                    # Validate purchase against available inventory
                    if self.sales_validator:
                        allocation_result = self.sales_validator.validate_purchase(
                            product_key=product['product_key'],
                            location_key=location['location_key'],
                            date_key=date_info['date_key'],
                            requested_qty=requested_quantity,
                            customer_key=customer['customer_key']
                        )

                        # Skip this sale if no inventory available (stockout)
                        if not allocation_result.allocation_success:
                            continue

                        quantity_sold = allocation_result.allocated_quantity
                        quantity_requested = allocation_result.requested_quantity
                        is_inventory_constrained = allocation_result.is_inventory_constrained
                        inventory_at_purchase = allocation_result.inventory_at_purchase
                    else:
                        # Fallback to old behavior if no validator (for backward compatibility)
                        quantity_sold = requested_quantity
                        quantity_requested = requested_quantity
                        is_inventory_constrained = False
                        inventory_at_purchase = None

                    # Calculate amounts based on ALLOCATED quantity
                    net_sales = float(int((unit_price - discount_amount) * quantity_sold * 100)) / 100
                    # Use location-specific tax rate instead of hardcoded 8%
                    location_tax_rate = float(location.get('state_tax_rate', 0.07) if hasattr(location, 'get') else location['state_tax_rate'])
                    tax_amount = float(int(net_sales * location_tax_rate * 100)) / 100
                    # Calculate gross margin from actual unit_cost instead of random percentage
                    product_unit_cost = float(product['unit_cost']) if product['unit_cost'] else float(base_price) * 0.4
                    gross_margin = float(int((net_sales - (quantity_sold * product_unit_cost)) * 100)) / 100

                    # Return probability (influenced by customer segment and channel)
                    # Fashion e-commerce typically has 25-40% return rates vs 8-10% in-store
                    base_return_rate = return_probability
                    channel_multiplier = DIGITAL_RETURN_MULTIPLIER if channel['is_digital'] else STORE_RETURN_MULTIPLIER
                    is_return = self._rng.random() < (base_return_rate * channel_multiplier)

                    # Calculate return restocking date (1-3 days after return)
                    return_restocked_date_key = None
                    if is_return and self.inventory_manager:
                        delay_days = self._rng.randint(*self.config.get('return_delay_days', (1, 3)))
                        return_date = dt.strptime(str(date_info['date_key']), '%Y%m%d')
                        restock_date = return_date + timedelta(days=delay_days)
                        return_restocked_date_key = int(restock_date.strftime('%Y%m%d'))

                        # Schedule replenishment in inventory manager
                        self.inventory_manager.schedule_replenishment(
                            product_key=product['product_key'],
                            location_key=location['location_key'],
                            return_date_key=date_info['date_key'],
                            quantity=quantity_sold,
                            delay_days=delay_days
                        )

                    sales_record = {
                        'transaction_id': f"TXN_{transaction_id:010d}",
                        'line_item_id': f"LINE_{line_item_id:012d}",
                        'customer_key': customer['customer_key'],
                        'product_key': product['product_key'],
                        'date_key': date_info['date_key'],
                        'time_key': self._rng.choice([900, 1200, 1500, 1800, 2000]),  # Peak hours
                        'location_key': location['location_key'],
                        'channel_key': channel['channel_key'],
                        'order_number': order_number,
                        'pos_terminal_id': f"POS_{location['location_key']}" if not channel['is_digital'] else None,
                        'sales_associate_id': f"SA_{self._rng.randint(1, 100)}" if not channel['is_digital'] else None,
                        'quantity_sold': quantity_sold,
                        'unit_price': unit_price,
                        'discount_amount': discount_amount,
                        'tax_amount': tax_amount,
                        'net_sales_amount': net_sales,
                        'gross_margin_amount': gross_margin,
                        'is_return': is_return,
                        'is_exchange': is_return and self._rng.random() < 0.3,
                        'is_promotional': is_promotional,
                        'is_clearance': is_clearance,
                        'fulfillment_type': self._rng.choice(['ship', 'pickup', 'same_day']) if channel['is_digital']
                                           else 'in_store',
                        'payment_method': self._rng.choice(['credit_card', 'debit_card', 'paypal', 'apple_pay']),
                        'quantity_requested': quantity_requested,
                        'is_inventory_constrained': is_inventory_constrained,
                        'inventory_at_purchase': inventory_at_purchase,
                        'return_restocked_date_key': return_restocked_date_key,
                        'source_system': SOURCE_SYSTEMS['sales'],
                        'etl_timestamp': dt.now()
                    }
                    sales_data.append(sales_record)
                    line_item_id += 1
                
                transaction_id += 1
                
                # Batch write every 100K records
                if len(sales_data) >= 100000:
                    self._write_batch(sales_data, 'gold_sales_fact', mode='overwrite' if is_first_batch else 'append')
                    is_first_batch = False
                    sales_data = []
        
        # Write remaining records
        if sales_data:
            self._write_batch(sales_data, 'gold_sales_fact', mode='overwrite' if is_first_batch else 'append')
        
        # Add table properties
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_sales_fact
            SET TBLPROPERTIES (
                'comment' = 'Sales transaction fact table. Sources: OMS, POS System, Shopify, Store Operations'
            )
        """)
        
        logger.info(f"Created sales fact table with ~{transaction_id:,} transactions")
    
    def create_inventory_fact(self) -> None:
        """Create and populate inventory fact table (daily snapshots)."""
        logger.info("Generating inventory fact table...")

        inventory_data: List[Dict[str, Any]] = []
        is_first_batch = True

        if self.inventory_manager:
            logger.info("Using InventoryManager for inventory snapshots...")

            snapshot_dates = self.date_keys[-30:] if self.config.get('test_mode') else self.date_keys

            for date_info in snapshot_dates:
                snapshot = self.inventory_manager.get_inventory_snapshot(date_info['date_key'])

                for position_data in snapshot:
                    product = next((p for p in self.product_keys if p['product_key'] == position_data['product_key']), None)
                    if not product:
                        continue

                    unit_cost = float(product['base_price']) * 0.4
                    qty_on_hand = position_data['quantity_on_hand']
                    inventory_value_cost = float(int(qty_on_hand * unit_cost * 100)) / 100
                    inventory_value_retail = float(int(qty_on_hand * float(product['base_price']) * 100)) / 100

                    days_of_supply = self._rng.randint(5, 90)
                    stock_cover_days = self._rng.randint(7, 60)
                    reorder_point = self._rng.randint(20, 200)
                    reorder_quantity = self._rng.randint(50, 500)

                    qty_in_transit = self._rng.randint(0, 50) if self._rng.random() < 0.2 else 0
                    is_overstock = days_of_supply > 60

                    last_replenishment_date = None
                    next_replenishment_date = None
                    if position_data['is_stockout']:
                        current_date = dt.strptime(str(date_info['date_key']), '%Y%m%d')
                        last_replenishment = current_date - timedelta(days=self._rng.randint(7, 30))
                        next_replenishment = current_date + timedelta(days=self._rng.randint(1, 7))
                        last_replenishment_date = last_replenishment.date()
                        next_replenishment_date = next_replenishment.date()

                    inventory_record = {
                        'product_key': position_data['product_key'],
                        'location_key': position_data['location_key'],
                        'date_key': position_data['date_key'],
                        'quantity_on_hand': position_data['quantity_on_hand'],
                        'quantity_available': position_data['quantity_available'],
                        'quantity_reserved': position_data['quantity_reserved'],
                        'quantity_in_transit': qty_in_transit,
                        'quantity_damaged': position_data['quantity_damaged'],
                        'inventory_value_cost': inventory_value_cost,
                        'inventory_value_retail': inventory_value_retail,
                        'days_of_supply': days_of_supply,
                        'stock_cover_days': stock_cover_days,
                        'reorder_point': reorder_point,
                        'reorder_quantity': reorder_quantity,
                        'is_stockout': position_data['is_stockout'],
                        'is_overstock': is_overstock,
                        'is_discontinued': False,
                        'stockout_duration_days': position_data.get('stockout_duration_days', 0),
                        'last_replenishment_date': last_replenishment_date,
                        'next_replenishment_date': next_replenishment_date,
                        'source_system': SOURCE_SYSTEMS['inventory'],
                        'etl_timestamp': dt.now()
                    }
                    inventory_data.append(inventory_record)

                if len(inventory_data) >= MAX_RECORDS_BEFORE_WRITE:
                    self._write_batch(inventory_data, 'gold_inventory_fact',
                                    mode='overwrite' if is_first_batch else 'append')
                    is_first_batch = False
                    inventory_data = []

        else:
            logger.warning("No InventoryManager provided - using legacy inventory generation")

            for date_info in self.date_keys[-30:]:
                for product in self.product_keys[:1000]:
                    for location in self.location_keys:
                        if location['location_type'] == 'dc':
                            base_qty = self._rng.randint(500, 2000)
                        elif location['location_type'] == 'warehouse':
                            base_qty = self._rng.randint(200, 800)
                        else:
                            base_qty = self._rng.randint(10, 100)

                        qty_on_hand = int(self._apply_seasonality_multiplier(base_qty, date_info) *
                                         self._rng.uniform(0.5, 1.5))

                        qty_reserved = int(qty_on_hand * self._rng.uniform(0, 0.3))
                        qty_available = qty_on_hand - qty_reserved
                        qty_in_transit = self._rng.randint(0, 50) if self._rng.random() < 0.2 else 0
                        qty_damaged = self._rng.randint(0, 5) if self._rng.random() < 0.1 else 0

                        unit_cost = float(product['base_price']) * 0.4
                        inventory_value_cost = float(int(qty_on_hand * unit_cost * 100)) / 100
                        inventory_value_retail = float(int(qty_on_hand * float(product['base_price']) * 100)) / 100

                        days_of_supply = self._rng.randint(5, 90)
                        stock_cover_days = self._rng.randint(7, 60)
                        reorder_point = self._rng.randint(20, 200)
                        reorder_quantity = self._rng.randint(50, 500)

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
                            'source_system': SOURCE_SYSTEMS['inventory'],
                            'etl_timestamp': dt.now()
                        }
                        inventory_data.append(inventory_record)

                        if len(inventory_data) >= MAX_RECORDS_BEFORE_WRITE:
                            self._write_batch(inventory_data, 'gold_inventory_fact',
                                            mode='overwrite' if is_first_batch else 'append')
                            is_first_batch = False
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
    
    def create_customer_event_fact(self) -> None:
        """Create and populate customer event fact table."""
        logger.info("Generating customer event fact table...")
        
        event_types = ['page_view', 'product_view', 'search', 'add_to_cart', 'remove_from_cart', 
                      'checkout_start', 'checkout_complete', 'filter_apply', 'size_guide_view']
        
        events_data: List[Dict[str, Any]] = []
        event_id = 1
        is_first_batch = True
        
        for date_info in self.date_keys[-30:]:
            base_events = self._apply_seasonality_multiplier(self.config['events_per_day'], date_info)
            num_events = int(self._rng.gauss(base_events, base_events * 0.2))
            
            for _ in range(num_events):
                customer = self._rng.choice(self.customer_keys)
                product = self._rng.choice(self.product_keys) if self._rng.random() < 0.7 else None
                channel = self._rng.choice([c for c in self.channel_keys if c['is_digital']])
                
                event_type = self._rng.choice(event_types)
                session_id = f"SESSION_{customer['customer_key']}_{date_info['date_key']}_{self._rng.randint(1, 10)}"
                
                if event_type == 'checkout_complete':
                    event_value = self._rng.uniform(50, 500)
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
                    'time_key': self._rng.choice([900, 1200, 1500, 1800, 2000]),
                    'channel_key': channel['channel_key'],
                    'location_key': None,
                    'event_type': event_type,
                    'event_category': 'engagement' if 'view' in event_type else 'conversion' if 'checkout' in event_type else 'interaction',
                    'event_action': event_type,
                    'event_label': product['category_level_2'] if product else None,
                    'event_value': float(int(event_value * 100)) / 100,
                    'time_on_page_seconds': self._rng.randint(5, 300) if 'view' in event_type else 0,
                    'bounce_flag': self._rng.random() < 0.3 if event_type == 'page_view' else False,
                    'conversion_flag': conversion_flag,
                    'page_url': f"/products/{product['product_id']}" if product else "/home",
                    'referrer_url': self._rng.choice(['google.com', 'facebook.com', 'instagram.com', 'direct', 'email']),
                    'search_term': f"{product['category_level_2']} {product['brand']}" if event_type == 'search' and product else None,
                    'source_system': SOURCE_SYSTEMS['events'],
                    'etl_timestamp': dt.now()
                }
                events_data.append(event_record)
                event_id += 1
                
                if len(events_data) >= MAX_RECORDS_BEFORE_WRITE:
                    self._write_batch(events_data, 'gold_customer_event_fact', 
                                    mode='overwrite' if is_first_batch else 'append')
                    is_first_batch = False
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
    
    def create_cart_abandonment_fact(self) -> None:
        """Create and populate cart abandonment fact table."""
        logger.info("Generating cart abandonment fact table...")
        
        abandonment_data: List[Dict[str, Any]] = []
        
        for date_info in self.date_keys[-90:]:
            daily_abandonments = int(self._apply_seasonality_multiplier(50, date_info))
            
            for i in range(daily_abandonments):
                customer = self._rng.choice(self.customer_keys)
                channel = self._rng.choice([c for c in self.channel_keys if c['is_digital']])

                items_count = self._rng.choice([1, 2, 3, 4, 5])
                cart_value = float(int(self._rng.uniform(50, 500) * 100)) / 100

                low_inventory_trigger = False
                inventory_constrained_items = 0

                if self.sales_validator:
                    for _ in range(items_count):
                        product = self._rng.choice(self.product_keys)
                        location = self._rng.choice(self.location_keys)

                        is_low_inv = self.sales_validator.is_low_inventory(
                            product_key=product['product_key'],
                            location_key=location['location_key'],
                            date_key=date_info['date_key']
                        )

                        if is_low_inv:
                            low_inventory_trigger = True
                            inventory_constrained_items += 1

                base_abandonment_rate = 0.25
                if low_inventory_trigger:
                    abandonment_rate = base_abandonment_rate + self.config.get('cart_abandonment_increase', 0.10)
                else:
                    abandonment_rate = base_abandonment_rate

                if self._rng.random() > abandonment_rate:
                    continue

                recovery_email_sent = self._rng.random() < 0.8
                recovery_email_opened = recovery_email_sent and self._rng.random() < 0.4
                recovery_email_clicked = recovery_email_opened and self._rng.random() < 0.3
                is_recovered = recovery_email_clicked and self._rng.random() < 0.25

                if low_inventory_trigger and self._rng.random() < 0.7:
                    suspected_reason = 'low_inventory'
                else:
                    suspected_reason = self._rng.choice(['high_shipping', 'price_concern', 'comparison_shopping',
                                                      'technical_issue', 'payment_issue'])

                abandonment_record = {
                    'abandonment_id': i + 1,
                    'cart_id': f"CART_{date_info['date_key']}_{i}",
                    'customer_key': customer['customer_key'],
                    'date_key': date_info['date_key'],
                    'time_key': self._rng.choice([900, 1200, 1500, 1800, 2000]),
                    'channel_key': channel['channel_key'],
                    'cart_value': cart_value,
                    'items_count': items_count,
                    'minutes_in_cart': self._rng.randint(5, 180),
                    'recovery_email_sent': recovery_email_sent,
                    'recovery_email_opened': recovery_email_opened,
                    'recovery_email_clicked': recovery_email_clicked,
                    'is_recovered': is_recovered,
                    'recovery_date_key': date_info['date_key'] + self._rng.randint(1, 7) if is_recovered else None,
                    'recovery_revenue': cart_value * self._rng.uniform(0.7, 1.0) if is_recovered else 0.0,
                    'abandonment_stage': self._rng.choice(['cart', 'shipping', 'payment']),
                    'suspected_reason': suspected_reason,
                    'low_inventory_trigger': low_inventory_trigger,
                    'inventory_constrained_items': inventory_constrained_items,
                    'source_system': SOURCE_SYSTEMS['cart_abandonment'],
                    'etl_timestamp': dt.now()
                }
                abandonment_data.append(abandonment_record)
        
        # Define explicit schema for cart abandonment fact (with new columns)
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
            StructField("low_inventory_trigger", BooleanType(), True),  # NEW
            StructField("inventory_constrained_items", IntegerType(), True),  # NEW
            StructField("source_system", StringType(), True),
            StructField("etl_timestamp", TimestampType(), True)
        ])

        # Create DataFrame with explicit schema
        df = self.spark.createDataFrame(abandonment_data, schema=abandonment_schema)
        df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .option("mergeSchema", "true") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_cart_abandonment_fact")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_cart_abandonment_fact
            SET TBLPROPERTIES (
                'comment' = 'Cart abandonment tracking fact. Sources: Shopify, Mobile App, Email Marketing Platform'
            )
        """)
        
        logger.info(f"Created cart abandonment fact table with {len(abandonment_data):,} records")

    def create_stockout_events(self) -> None:
        """Create and populate stockout events fact table."""
        logger.info("Generating stockout events fact table...")

        if not self.inventory_manager:
            logger.warning("No InventoryManager - skipping stockout events generation")
            return

        # Use StockoutGenerator to create events from inventory manager history
        # Import already available at top of file

        stockout_gen = StockoutGenerator(self.spark, self.config)

        # Load required dimension data
        products_df = self.spark.table(f"{self.catalog}.{self.schema}.gold_product_dim")
        dates_df = self.spark.table(f"{self.catalog}.{self.schema}.gold_date_dim")
        sales_df = self.spark.table(f"{self.catalog}.{self.schema}.gold_sales_fact")

        # Generate stockout events
        stockout_events = stockout_gen.generate_stockout_events(
            inventory_manager=self.inventory_manager,
            sales_df=sales_df,
            products_df=products_df,
            dates_df=dates_df
        )

        # Create the table
        stockout_gen.create_stockout_events_table(stockout_events)

        # Log statistics
        stockout_gen.log_statistics()

        logger.info(f"Created stockout events table with {len(stockout_events):,} events")

    def create_demand_forecast_fact(self) -> None:
        """Create and populate demand forecast fact table."""
        logger.info("Generating demand forecast fact table...")
        
        forecast_data: List[Dict[str, Any]] = []
        forecast_id = 1

        forecast_dates = self.date_keys[-30:] + self.date_keys[:30] if len(self.date_keys) > 60 else self.date_keys

        for date_info in forecast_dates[-30:]:
            for product in self.product_keys[:100]:
                for location in self.store_locations[:5]:
                    base_demand = self._rng.randint(10, 100)
                    forecast_quantity = float(int(self._apply_seasonality_multiplier(base_demand, date_info)))
                    
                    confidence_level = 0.95
                    margin = forecast_quantity * 0.2
                    confidence_lower = max(0.0, float(int(forecast_quantity - margin)))
                    confidence_upper = float(int(forecast_quantity + margin))
                    
                    if date_info['calendar_date'] < dt.now().date():
                        actual_quantity_calc = int(forecast_quantity + self._rng.gauss(0, forecast_quantity * 0.15))
                        actual_quantity = max(0.0, float(actual_quantity_calc))
                        actual_revenue = float(actual_quantity) * float(product['base_price'])
                        
                        if actual_quantity > 0:
                            diff = forecast_quantity - actual_quantity
                            mape = abs(diff) / actual_quantity * 100
                            forecast_accuracy = max(0.0, 100 - mape)
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
                        'source_system': SOURCE_SYSTEMS['forecast'],
                        'etl_timestamp': dt.now()
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