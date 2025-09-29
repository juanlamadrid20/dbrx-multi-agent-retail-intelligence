"""
Dimension Table Generator for Fashion Retail Gold Layer
Creates and populates all dimension tables with realistic synthetic data
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class DimensionGenerator:
    """Generate dimension tables for fashion retail star schema"""
    
    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.catalog = config['catalog']
        self.schema = config['schema']
        
        # Set seed for reproducibility
        random.seed(42)
        
    def create_customer_dimension(self):
        """Create and populate customer dimension with SCD Type 2"""
        logger.info("Generating customer dimension...")

        # Use configured number of customers, with a reasonable max for testing
        configured_customers = self.config['customers']
        num_customers = configured_customers if configured_customers <= 10000 else 10000
        logger.info(f"Generating {num_customers} customers (from config: {configured_customers})...")

        # Generate simple customer data
        customers_data = []

        try:
            for i in range(num_customers):
                # Create very simple customer record
                customer = {
                    'customer_key': i + 1,  # Add customer_key for fact tables
                    'customer_id': f"CUST_{i+1:08d}",
                    'email': f"customer_{i+1}@test.com",
                    'first_name': f"First{i+1}",
                    'last_name': f"Last{i+1}",
                    'segment': 'regular',
                    'lifetime_value': 100.0 + i * 10.0,
                    'acquisition_date': datetime(2023, 1, 1).date(),
                    'acquisition_channel': 'web',
                    'preferred_channel': 'web',
                    'preferred_category': 'tops',
                    'size_profile_tops': 'M',
                    'size_profile_bottoms': '32',
                    'geo_region': 'West',
                    'geo_city': 'Seattle',
                    'nearest_store_id': 1,
                    'loyalty_tier': 'bronze',
                    'email_subscribe_flag': True,
                    'sms_subscribe_flag': False,
                    'effective_date': datetime(2023, 1, 1).date(),
                    'expiration_date': datetime(9999, 12, 31).date(),
                    'is_current': True,
                    'source_system': 'CRM_SALESFORCE',
                    'etl_timestamp': datetime.now()
                }
                customers_data.append(customer)

                logger.info(f"Generated customer {i+1}")

        except Exception as e:
            logger.error(f"Error generating customer data: {str(e)}")
            raise
        
        # Define schema for customer dimension
        customer_schema = StructType([
            StructField("customer_key", IntegerType(), False),
            StructField("customer_id", StringType(), False),
            StructField("email", StringType(), True),
            StructField("first_name", StringType(), True),
            StructField("last_name", StringType(), True),
            StructField("segment", StringType(), True),
            StructField("lifetime_value", DoubleType(), True),
            StructField("acquisition_date", DateType(), True),
            StructField("acquisition_channel", StringType(), True),
            StructField("preferred_channel", StringType(), True),
            StructField("preferred_category", StringType(), True),
            StructField("size_profile_tops", StringType(), True),
            StructField("size_profile_bottoms", StringType(), True),
            StructField("geo_region", StringType(), True),
            StructField("geo_city", StringType(), True),
            StructField("nearest_store_id", IntegerType(), True),
            StructField("loyalty_tier", StringType(), True),
            StructField("email_subscribe_flag", BooleanType(), True),
            StructField("sms_subscribe_flag", BooleanType(), True),
            StructField("effective_date", DateType(), True),
            StructField("expiration_date", DateType(), True),
            StructField("is_current", BooleanType(), True),
            StructField("source_system", StringType(), True),
            StructField("etl_timestamp", TimestampType(), True)
        ])

        # Create DataFrame with explicit schema
        logger.info("Creating customer DataFrame...")
        customer_df = self.spark.createDataFrame(customers_data, schema=customer_schema)
        logger.info(f"DataFrame created successfully with {customer_df.count()} rows")
        
        # Write to Delta table (simplified for compatibility)
        customer_df.write \
            .mode("overwrite") \
            .format("delta") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_customer_dim")
        
        # Add table comment
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_customer_dim
            SET TBLPROPERTIES (
                'comment' = 'Customer dimension with slowly changing attributes. Sources: Salesforce CRM, Segment CDP, Loyalty Platform'
            )
        """)
        
        logger.info(f"Created customer dimension with {num_customers:,} records")
    
    def create_product_dimension(self):
        """Create and populate product dimension"""
        logger.info("Generating product dimension...")
        
        # Use configured number of products, with a reasonable max for testing
        configured_products = self.config['products']
        num_products = configured_products if configured_products <= 5000 else 5000
        logger.info(f"Generating {num_products} products (from config: {configured_products})...")
        
        # Product hierarchies
        categories = {
            'apparel': {
                'tops': ['shirts', 'blouses', 't-shirts', 'sweaters', 'hoodies'],
                'bottoms': ['jeans', 'trousers', 'shorts', 'skirts', 'leggings'],
                'dresses': ['casual', 'formal', 'maxi', 'mini', 'midi'],
                'outerwear': ['jackets', 'coats', 'blazers', 'vests']
            },
            'accessories': {
                'bags': ['handbags', 'backpacks', 'clutches', 'totes'],
                'jewelry': ['necklaces', 'bracelets', 'earrings', 'rings'],
                'scarves': ['silk', 'wool', 'cotton', 'cashmere']
            },
            'footwear': {
                'shoes': ['sneakers', 'boots', 'heels', 'flats', 'sandals']
            }
        }
        
        brands = ['Urban Style', 'Classic Comfort', 'Eco Threads', 'Luxe Label', 
                 'Street Wear Co', 'Vintage Vibes', 'Modern Minimal', 'Bold Basics']
        
        colors = ['Black', 'White', 'Navy', 'Grey', 'Blue', 'Red', 'Green', 
                 'Pink', 'Beige', 'Brown', 'Purple', 'Yellow']
        
        materials = ['Cotton', 'Polyester', 'Wool', 'Silk', 'Linen', 'Denim', 
                    'Leather', 'Synthetic', 'Cashmere', 'Modal']
        
        seasons = ['Spring', 'Summer', 'Fall', 'Winter', 'Year-round']
        
        # Calculate total subcategories first
        total_subcategories = 0
        for cat2_dict in categories.values():
            for cat3_list in cat2_dict.values():
                total_subcategories += len(cat3_list)

        products_per_cat = 1 if (num_products // total_subcategories) < 1 else (num_products // total_subcategories)  # At least 1 product per subcategory

        # Generate products
        products_data = []
        product_id = 1

        for cat1, cat2_dict in categories.items():
            for cat2, cat3_list in cat2_dict.items():
                for cat3 in cat3_list:
                    
                    for _ in range(products_per_cat):
                        sku = f"SKU_{str(product_id).zfill(6)}"
                        base_price = float(int(random.uniform(29.99, 299.99) * 100)) / 100
                        
                        product = {
                            'product_key': product_id,
                            'product_id': f"PROD_{str(product_id).zfill(6)}",
                            'sku': sku,
                            'product_name': f"{random.choice(brands)} {cat3.title()} {product_id}",
                            'brand': random.choice(brands),
                            'category_level_1': cat1,
                            'category_level_2': cat2,
                            'category_level_3': cat3,
                            'color_family': random.choice(['Neutral', 'Bright', 'Dark', 'Pastel']),
                            'color_name': random.choice(colors),
                            'size_range': 'XS-XL' if cat1 == 'apparel' else 'ONE SIZE',
                            'material_primary': random.choice(materials),
                            'material_composition': f"{random.randint(60, 100)}% {random.choice(materials)}",
                            'season_code': random.choice(seasons),
                            'collection_name': f"{random.choice(seasons)} {datetime.now().year} Collection",
                            'launch_date': (datetime.now() - timedelta(days=random.randint(1, 730))).date(),
                            'end_of_life_date': None if random.random() > 0.2 else (datetime.now() + timedelta(days=random.randint(30, 365))).date(),
                            'base_price': base_price,
                            'unit_cost': float(int(base_price * random.uniform(0.3, 0.5) * 100)) / 100,
                            'margin_percent': float(int(random.uniform(40, 70) * 100)) / 100,
                            'price_tier': 'luxury' if base_price > 200 else 'premium' if base_price > 100 else 'mid' if base_price > 50 else 'budget',
                            'sustainability_flag': random.choice([True, False]),
                            'is_active': random.random() > 0.1,
                            'source_system': 'PLM_SYSTEM',
                            'etl_timestamp': datetime.now()
                        }
                        products_data.append(product)
                        product_id += 1
                        
                        if product_id > num_products:
                            break
                    if product_id > num_products:
                        break
                if product_id > num_products:
                    break
            if product_id > num_products:
                break
        
        # Define explicit schema for product dimension
        product_schema = StructType([
            StructField("product_key", IntegerType(), False),
            StructField("product_id", StringType(), False),
            StructField("sku", StringType(), True),
            StructField("product_name", StringType(), True),
            StructField("brand", StringType(), True),
            StructField("category_level_1", StringType(), True),
            StructField("category_level_2", StringType(), True),
            StructField("category_level_3", StringType(), True),
            StructField("color_family", StringType(), True),
            StructField("color_name", StringType(), True),
            StructField("size_range", StringType(), True),
            StructField("material_primary", StringType(), True),
            StructField("material_composition", StringType(), True),
            StructField("season_code", StringType(), True),
            StructField("collection_name", StringType(), True),
            StructField("launch_date", DateType(), True),
            StructField("end_of_life_date", DateType(), True),
            StructField("base_price", DoubleType(), True),
            StructField("unit_cost", DoubleType(), True),
            StructField("margin_percent", DoubleType(), True),
            StructField("price_tier", StringType(), True),
            StructField("sustainability_flag", BooleanType(), True),
            StructField("is_active", BooleanType(), True),
            StructField("source_system", StringType(), True),
            StructField("etl_timestamp", TimestampType(), True)
        ])

        # Create DataFrame with explicit schema
        product_df = self.spark.createDataFrame(products_data[:num_products], schema=product_schema)
        
        # Write to Delta table
        product_df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_product_dim")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_product_dim
            SET TBLPROPERTIES (
                'comment' = 'Product master dimension. Sources: PLM System, Merchandising Platform, Pricing Engine'
            )
        """)
        
        logger.info(f"Created product dimension with {len(products_data[:num_products]):,} records")
    
    def create_location_dimension(self):
        """Create and populate location dimension"""
        logger.info("Generating location dimension...")
        
        locations_data = [
            # Flagship stores
            {'location_id': 'LOC_001', 'location_name': 'NYC Flagship', 'location_type': 'store',
             'store_format': 'flagship', 'city': 'New York', 'state_province': 'NY',
             'region': 'Northeast', 'country': 'USA', 'selling_sqft': 15000.0, 'total_sqft': 22500.0},
            {'location_id': 'LOC_002', 'location_name': 'LA Flagship', 'location_type': 'store',
             'store_format': 'flagship', 'city': 'Los Angeles', 'state_province': 'CA',
             'region': 'West', 'country': 'USA', 'selling_sqft': 12000.0, 'total_sqft': 18000.0},

            # Regular stores
            {'location_id': 'LOC_003', 'location_name': 'Chicago Store', 'location_type': 'store',
             'store_format': 'standard', 'city': 'Chicago', 'state_province': 'IL',
             'region': 'Midwest', 'country': 'USA', 'selling_sqft': 8000.0, 'total_sqft': 12000.0},
            {'location_id': 'LOC_004', 'location_name': 'Miami Store', 'location_type': 'store',
             'store_format': 'standard', 'city': 'Miami', 'state_province': 'FL',
             'region': 'Southeast', 'country': 'USA', 'selling_sqft': 7500.0, 'total_sqft': 11250.0},
            {'location_id': 'LOC_005', 'location_name': 'Dallas Store', 'location_type': 'store',
             'store_format': 'standard', 'city': 'Dallas', 'state_province': 'TX',
             'region': 'Southwest', 'country': 'USA', 'selling_sqft': 7000.0, 'total_sqft': 10500.0},

            # Outlet stores
            {'location_id': 'LOC_006', 'location_name': 'Orlando Outlet', 'location_type': 'store',
             'store_format': 'outlet', 'city': 'Orlando', 'state_province': 'FL',
             'region': 'Southeast', 'country': 'USA', 'selling_sqft': 5000.0, 'total_sqft': 7500.0},
            {'location_id': 'LOC_007', 'location_name': 'Las Vegas Outlet', 'location_type': 'store',
             'store_format': 'outlet', 'city': 'Las Vegas', 'state_province': 'NV',
             'region': 'West', 'country': 'USA', 'selling_sqft': 4500.0, 'total_sqft': 6750.0},

            # Additional stores
            {'location_id': 'LOC_008', 'location_name': 'Boston Store', 'location_type': 'store',
             'store_format': 'standard', 'city': 'Boston', 'state_province': 'MA',
             'region': 'Northeast', 'country': 'USA', 'selling_sqft': 6000.0, 'total_sqft': 9000.0},
            {'location_id': 'LOC_009', 'location_name': 'Seattle Store', 'location_type': 'store',
             'store_format': 'standard', 'city': 'Seattle', 'state_province': 'WA',
             'region': 'West', 'country': 'USA', 'selling_sqft': 5500.0, 'total_sqft': 8250.0},
            {'location_id': 'LOC_010', 'location_name': 'Atlanta Store', 'location_type': 'store',
             'store_format': 'standard', 'city': 'Atlanta', 'state_province': 'GA',
             'region': 'Southeast', 'country': 'USA', 'selling_sqft': 6500.0, 'total_sqft': 9750.0},

            # Warehouses
            {'location_id': 'LOC_011', 'location_name': 'East Coast Warehouse', 'location_type': 'warehouse',
             'store_format': None, 'city': 'Newark', 'state_province': 'NJ',
             'region': 'Northeast', 'country': 'USA', 'selling_sqft': 0.0, 'total_sqft': 50000.0},
            {'location_id': 'LOC_012', 'location_name': 'West Coast Warehouse', 'location_type': 'warehouse',
             'store_format': None, 'city': 'Ontario', 'state_province': 'CA',
             'region': 'West', 'country': 'USA', 'selling_sqft': 0.0, 'total_sqft': 45000.0},

            # Distribution Center
            {'location_id': 'LOC_013', 'location_name': 'Central DC', 'location_type': 'dc',
             'store_format': None, 'city': 'Columbus', 'state_province': 'OH',
             'region': 'Midwest', 'country': 'USA', 'selling_sqft': 0.0, 'total_sqft': 100000.0}
        ]
        
        # Enrich location data
        for i, loc in enumerate(locations_data):
            loc.update({
                'location_key': int(i + 1),
                'channel': 'physical' if loc['location_type'] == 'store' else 'digital',
                'district': f"District_{loc['region'][:2].upper()}",
                'postal_code': f"{random.randint(10000, 99999)}",
                'latitude': float(int(random.uniform(25.0, 49.0) * 1000000)) / 1000000,
                'longitude': float(int(random.uniform(-125.0, -66.0) * 1000000)) / 1000000,
                'total_sqft': float(loc['total_sqft']),
                'open_date': (datetime.now() - timedelta(days=random.randint(365, 3650))).date(),
                'close_date': None,
                'is_active': True,
                'timezone': 'America/New_York' if loc['region'] == 'Northeast' else 
                           'America/Chicago' if loc['region'] == 'Midwest' else
                           'America/Denver' if loc['region'] == 'Southwest' else
                           'America/Los_Angeles',
                'source_system': 'STORE_OPS_WMS',
                'etl_timestamp': datetime.now()
            })
        
        # Define explicit schema for location dimension
        location_schema = StructType([
            StructField("location_id", StringType(), False),
            StructField("location_name", StringType(), True),
            StructField("location_type", StringType(), True),
            StructField("store_format", StringType(), True),
            StructField("city", StringType(), True),
            StructField("state_province", StringType(), True),
            StructField("region", StringType(), True),
            StructField("country", StringType(), True),
            StructField("selling_sqft", DoubleType(), True),
            StructField("total_sqft", DoubleType(), True),
            StructField("location_key", IntegerType(), True),
            StructField("channel", StringType(), True),
            StructField("district", StringType(), True),
            StructField("postal_code", StringType(), True),
            StructField("latitude", DoubleType(), True),
            StructField("longitude", DoubleType(), True),
            StructField("open_date", DateType(), True),
            StructField("close_date", DateType(), True),
            StructField("is_active", BooleanType(), True),
            StructField("timezone", StringType(), True),
            StructField("source_system", StringType(), True),
            StructField("etl_timestamp", TimestampType(), True)
        ])

        # Create DataFrame with explicit schema
        location_df = self.spark.createDataFrame(locations_data, schema=location_schema)
        
        # Write to Delta table
        location_df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_location_dim")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_location_dim
            SET TBLPROPERTIES (
                'comment' = 'Location dimension for stores and warehouses. Sources: Store Operations, WMS, Real Estate DB'
            )
        """)
        
        logger.info(f"Created location dimension with {len(locations_data)} records")
    
    def create_date_dimension(self):
        """Create and populate date dimension"""
        logger.info("Generating date dimension...")
        
        start_date = datetime.now() - timedelta(days=self.config['historical_days'])
        end_date = datetime.now() + timedelta(days=365)  # Include future dates for planning
        
        dates_data = []
        current_date = start_date
        date_key = 1
        
        # Define retail calendar events
        holidays = {
            1: [('New Year', 1)],
            2: [('Valentine\'s Day', 14)],
            3: [],
            4: [('Easter', 15)],  # Approximate
            5: [('Memorial Day', 30)],
            6: [],
            7: [('Independence Day', 4)],
            8: [],
            9: [('Labor Day', 5)],
            10: [('Halloween', 31)],
            11: [('Black Friday', 25), ('Thanksgiving', 24)],
            12: [('Christmas', 25), ('Boxing Day', 26)]
        }
        
        sale_periods = {
            1: 'Winter Clearance',
            2: 'President\'s Day Sale',
            3: 'Spring Sale',
            5: 'Memorial Day Sale',
            7: 'Summer Sale',
            9: 'Back to School',
            11: 'Black Friday',
            12: 'Holiday Sale'
        }
        
        while current_date <= end_date:
            month = current_date.month
            day = current_date.day
            
            # Determine season
            if month in [3, 4, 5]:
                season = 'Spring'
            elif month in [6, 7, 8]:
                season = 'Summer'
            elif month in [9, 10, 11]:
                season = 'Fall'
            else:
                season = 'Winter'
            
            # Check for holidays
            is_holiday = False
            holiday_name = None
            for holiday, holiday_day in holidays.get(month, []):
                if day == holiday_day:
                    is_holiday = True
                    holiday_name = holiday
                    break
            
            # Peak season (November-December, March-April)
            is_peak = month in [11, 12, 3, 4]
            
            # Sale period
            is_sale = month in sale_periods
            sale_event = sale_periods.get(month, None)
            
            date_record = {
                'date_key': int(current_date.strftime('%Y%m%d')),
                'calendar_date': current_date.date(),
                'year': current_date.year,
                'quarter': (month - 1) // 3 + 1,
                'month': month,
                'month_name': current_date.strftime('%B'),
                'week_of_year': current_date.isocalendar()[1],
                'day_of_month': day,
                'day_of_week': current_date.weekday() + 1,
                'day_name': current_date.strftime('%A'),
                'is_weekend': current_date.weekday() >= 5,
                'is_holiday': is_holiday,
                'holiday_name': holiday_name,
                'fiscal_year': current_date.year if month >= 2 else current_date.year - 1,
                'fiscal_quarter': ((month - 2) % 12) // 3 + 1,
                'fiscal_month': ((month - 2) % 12) + 1,
                'season': season,
                'is_peak_season': is_peak,
                'is_sale_period': is_sale,
                'sale_event_name': sale_event,
                'etl_timestamp': datetime.now()
            }
            dates_data.append(date_record)
            
            current_date += timedelta(days=1)
            date_key += 1
        
        # Create DataFrame
        date_df = self.spark.createDataFrame(dates_data)
        
        # Write to Delta table
        date_df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_date_dim")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_date_dim
            SET TBLPROPERTIES (
                'comment' = 'Date dimension with retail calendar. Source: Generated Reference Data'
            )
        """)
        
        logger.info(f"Created date dimension with {len(dates_data):,} records")
    
    def create_channel_dimension(self):
        """Create and populate channel dimension"""
        logger.info("Generating channel dimension...")
        
        channels_data = [
            {
                'channel_key': 1,
                'channel_code': 'WEB_DESKTOP',
                'channel_name': 'Website - Desktop',
                'channel_type': 'online',
                'channel_category': 'web',
                'device_category': 'desktop',
                'is_digital': True,
                'is_owned': True,
                'commission_rate': 0.0
            },
            {
                'channel_key': 2,
                'channel_code': 'WEB_MOBILE',
                'channel_name': 'Website - Mobile',
                'channel_type': 'online',
                'channel_category': 'web',
                'device_category': 'mobile',
                'is_digital': True,
                'is_owned': True,
                'commission_rate': 0.0
            },
            {
                'channel_key': 3,
                'channel_code': 'APP_IOS',
                'channel_name': 'iOS Mobile App',
                'channel_type': 'online',
                'channel_category': 'mobile_app',
                'device_category': 'mobile',
                'is_digital': True,
                'is_owned': True,
                'commission_rate': 0.0
            },
            {
                'channel_key': 4,
                'channel_code': 'APP_ANDROID',
                'channel_name': 'Android Mobile App',
                'channel_type': 'online',
                'channel_category': 'mobile_app',
                'device_category': 'mobile',
                'is_digital': True,
                'is_owned': True,
                'commission_rate': 0.0
            },
            {
                'channel_key': 5,
                'channel_code': 'STORE_POS',
                'channel_name': 'Physical Store - POS',
                'channel_type': 'offline',
                'channel_category': 'store',
                'device_category': 'pos',
                'is_digital': False,
                'is_owned': True,
                'commission_rate': 0.0
            },
            {
                'channel_key': 6,
                'channel_code': 'STORE_KIOSK',
                'channel_name': 'In-Store Kiosk',
                'channel_type': 'hybrid',
                'channel_category': 'store',
                'device_category': 'kiosk',
                'is_digital': True,
                'is_owned': True,
                'commission_rate': 0.0
            },
            {
                'channel_key': 7,
                'channel_code': 'SOCIAL_FB',
                'channel_name': 'Facebook Shop',
                'channel_type': 'online',
                'channel_category': 'social',
                'device_category': 'mobile',
                'is_digital': True,
                'is_owned': False,
                'commission_rate': 5.0
            },
            {
                'channel_key': 8,
                'channel_code': 'MARKETPLACE_AMAZON',
                'channel_name': 'Amazon Marketplace',
                'channel_type': 'online',
                'channel_category': 'marketplace',
                'device_category': 'desktop',
                'is_digital': True,
                'is_owned': False,
                'commission_rate': 15.0
            }
        ]
        
        # Add audit fields
        for channel in channels_data:
            channel.update({
                'source_system': 'CHANNEL_MASTER',
                'etl_timestamp': datetime.now()
            })
        
        # Create DataFrame
        channel_df = self.spark.createDataFrame(channels_data)
        
        # Write to Delta table
        channel_df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_channel_dim")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_channel_dim
            SET TBLPROPERTIES (
                'comment' = 'Channel dimension for omnichannel operations. Sources: GA4, Store POS, Mobile Analytics'
            )
        """)
        
        logger.info(f"Created channel dimension with {len(channels_data)} records")
    
    def create_time_dimension(self):
        """Create and populate time dimension (hourly granularity)"""
        logger.info("Generating time dimension...")
        
        times_data = []
        
        for hour in range(24):
            for minute in [0, 15, 30, 45]:  # 15-minute intervals
                time_key = hour * 100 + minute
                
                # Determine time period
                if 6 <= hour < 12:
                    period = 'Morning'
                elif 12 <= hour < 17:
                    period = 'Afternoon'
                elif 17 <= hour < 21:
                    period = 'Evening'
                else:
                    period = 'Night'
                
                # Peak hours for retail (lunch, after work, evening)
                is_peak = hour in [12, 13, 17, 18, 19, 20]
                
                time_record = {
                    'time_key': time_key,
                    'hour': hour,
                    'minute': minute,
                    'hour_minute': f"{str(hour).zfill(2)}:{str(minute).zfill(2)}",
                    'am_pm': 'AM' if hour < 12 else 'PM',
                    'hour_12': hour if hour <= 12 else hour - 12,
                    'period_of_day': period,
                    'is_business_hours': 9 <= hour < 21,
                    'is_peak_hours': is_peak,
                    'etl_timestamp': datetime.now()
                }
                times_data.append(time_record)
        
        # Create DataFrame
        time_df = self.spark.createDataFrame(times_data)
        
        # Write to Delta table
        time_df.write \
            .mode("overwrite") \
            .option("delta.columnMapping.mode", "name") \
            .saveAsTable(f"{self.catalog}.{self.schema}.gold_time_dim")
        
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_time_dim
            SET TBLPROPERTIES (
                'comment' = 'Time dimension with 15-minute granularity. Source: Generated Reference Data'
            )
        """)
        
        logger.info(f"Created time dimension with {len(times_data)} records")