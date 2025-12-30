"""
Dimension Table Generator for Fashion Retail Gold Layer
Creates and populates all dimension tables with realistic synthetic data
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, current_timestamp
from pyspark.sql.types import (
    StructType, StructField, IntegerType, StringType, DoubleType,
    DateType, TimestampType, BooleanType
)
from datetime import datetime, timedelta
import random
import logging
from typing import Dict, List, Iterator, Any

# Try to import Faker for realistic names, fall back gracefully if not installed
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

from ..constants import CUSTOMER_SEGMENTS, SOURCE_SYSTEMS

logger = logging.getLogger(__name__)


class DimensionGenerator:
    """Generate dimension tables for fashion retail star schema.
    
    Uses batch processing for memory-efficient generation of large datasets.
    Each instance maintains its own random number generator for reproducibility.
    """
    
    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.catalog = config['catalog']
        self.schema = config['schema']
        
        # Use instance-level random generator for reproducibility
        # This avoids affecting global random state
        random_seed = config.get('random_seed', 42)
        self._rng = random.Random(random_seed)
        
        # Batch size for memory-efficient processing (default matches config.py)
        self._batch_size = config.get('batch_size', 10_000)
        
        # Initialize Faker with seed for reproducible realistic names
        if FAKER_AVAILABLE:
            self.fake = Faker()
            Faker.seed(random_seed)
            logger.info("Faker library available - using realistic customer names")
        else:
            self.fake = None
            logger.warning("Faker library not installed - using generated names. Install with: pip install faker")
        
    def _get_customer_schema(self) -> StructType:
        """Return schema for customer dimension table."""
        return StructType([
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

    def _generate_customer_batch(
        self,
        start_idx: int,
        batch_size: int,
        segment_assignments: List[str],
        customer_segments: Dict,
        geo_data: Dict,
        size_profiles: Dict
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate a batch of customers using a generator for memory efficiency.
        
        Args:
            start_idx: Starting customer index
            batch_size: Number of customers in this batch
            segment_assignments: Pre-calculated segment for each customer
            customer_segments: Segment configuration dictionary
            geo_data: Geographic regions and cities
            size_profiles: Size profile options
            
        Yields:
            Customer dictionaries
        """
        end_idx = min(start_idx + batch_size, len(segment_assignments))
        
        for i in range(start_idx, end_idx):
            segment = segment_assignments[i]
            segment_config = customer_segments[segment]
            
            # Generate customer based on segment characteristics
            acquisition_date = datetime(2023, 1, 1) - timedelta(days=self._rng.randint(0, 730))
            geo_region = self._rng.choice(segment_config['geo_regions'])
            geo_city = self._rng.choice(geo_data[geo_region])
            
            # Generate realistic names using Faker if available
            if self.fake:
                first_name = self.fake.first_name()
                last_name = self.fake.last_name()
                email_domain = self._rng.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'icloud.com', 'hotmail.com'])
                email = f"{first_name.lower()}.{last_name.lower()}{self._rng.randint(1, 999)}@{email_domain}"
            else:
                first_name = f"First{i+1}"
                last_name = f"Last{i+1}"
                email = f"customer_{i+1}@test.com"
            
            yield {
                'customer_key': i + 1,
                'customer_id': f"CUST_{i+1:08d}",
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'segment': segment,
                'lifetime_value': float(int(self._rng.uniform(*segment_config['lifetime_value_range']) * 100)) / 100,
                'acquisition_date': acquisition_date.date(),
                'acquisition_channel': self._rng.choice(segment_config['acquisition_channels']),
                'preferred_channel': self._rng.choice(segment_config['preferred_channels']),
                'preferred_category': self._rng.choice(segment_config['preferred_categories']),
                'size_profile_tops': self._rng.choice(size_profiles['tops']),
                'size_profile_bottoms': self._rng.choice(size_profiles['bottoms']),
                'geo_region': geo_region,
                'geo_city': geo_city,
                'nearest_store_id': self._rng.randint(1, 10),
                'loyalty_tier': self._rng.choice(segment_config['loyalty_tiers']),
                'email_subscribe_flag': self._rng.random() < segment_config['email_subscribe_rate'],
                'sms_subscribe_flag': self._rng.random() < segment_config['sms_subscribe_rate'],
                'effective_date': datetime(2023, 1, 1).date(),
                'expiration_date': datetime(9999, 12, 31).date(),
                'is_current': True,
                'source_system': SOURCE_SYSTEMS['customer'],
                'etl_timestamp': datetime.now()
            }

    def create_customer_dimension(self) -> None:
        """Create and populate customer dimension with SCD Type 2.
        
        Uses batch processing for memory-efficient generation of large datasets.
        """
        logger.info("Generating customer dimension...")

        num_customers = self.config['customers']
        
        if num_customers > 100000:
            logger.warning(f"Generating {num_customers:,} customers - this may take significant time")
        elif num_customers > 50000:
            logger.info(f"Generating {num_customers:,} customers - this may take several minutes")
        
        logger.info(f"Generating {num_customers:,} customers in batches of {self._batch_size:,}...")

        # Customer segment configurations with realistic distributions
        customer_segments = {
            'vip': {
                'probability': 0.05,
                'lifetime_value_range': (5000, 25000),
                'acquisition_channels': ['store', 'referral', 'social'],
                'preferred_channels': ['store', 'web'],
                'preferred_categories': ['outerwear', 'dresses', 'accessories'],
                'loyalty_tiers': ['platinum', 'gold'],
                'geo_regions': ['Northeast', 'West'],
                'email_subscribe_rate': 0.95,
                'sms_subscribe_rate': 0.80
            },
            'premium': {
                'probability': 0.15,
                'lifetime_value_range': (2000, 8000),
                'acquisition_channels': ['web', 'store', 'social'],
                'preferred_channels': ['web', 'app'],
                'preferred_categories': ['dresses', 'outerwear', 'tops'],
                'loyalty_tiers': ['gold', 'silver'],
                'geo_regions': ['Northeast', 'West', 'Southeast'],
                'email_subscribe_rate': 0.85,
                'sms_subscribe_rate': 0.60
            },
            'loyal': {
                'probability': 0.25,
                'lifetime_value_range': (800, 3000),
                'acquisition_channels': ['web', 'store', 'email'],
                'preferred_channels': ['web', 'store'],
                'preferred_categories': ['tops', 'bottoms', 'dresses'],
                'loyalty_tiers': ['silver', 'bronze'],
                'geo_regions': ['Northeast', 'West', 'Southeast', 'Midwest'],
                'email_subscribe_rate': 0.70,
                'sms_subscribe_rate': 0.40
            },
            'regular': {
                'probability': 0.35,
                'lifetime_value_range': (200, 1200),
                'acquisition_channels': ['web', 'social', 'search'],
                'preferred_channels': ['web', 'app'],
                'preferred_categories': ['tops', 'bottoms', 'accessories'],
                'loyalty_tiers': ['bronze', 'silver'],
                'geo_regions': ['West', 'Southeast', 'Midwest', 'Southwest'],
                'email_subscribe_rate': 0.50,
                'sms_subscribe_rate': 0.25
            },
            'new': {
                'probability': 0.20,
                'lifetime_value_range': (50, 500),
                'acquisition_channels': ['web', 'social', 'search', 'paid'],
                'preferred_channels': ['web', 'app', 'social'],
                'preferred_categories': ['tops', 'bottoms', 'accessories'],
                'loyalty_tiers': ['bronze'],
                'geo_regions': ['West', 'Southeast', 'Midwest', 'Southwest', 'Northeast'],
                'email_subscribe_rate': 0.30,
                'sms_subscribe_rate': 0.15
            }
        }

        geo_data = {
            'Northeast': ['New York', 'Boston', 'Philadelphia', 'Washington DC'],
            'West': ['Seattle', 'Los Angeles', 'San Francisco', 'Portland'],
            'Southeast': ['Miami', 'Atlanta', 'Charlotte', 'Tampa'],
            'Midwest': ['Chicago', 'Detroit', 'Cleveland', 'Milwaukee'],
            'Southwest': ['Dallas', 'Houston', 'Phoenix', 'Austin']
        }

        size_profiles = {
            'tops': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
            'bottoms': ['26', '28', '30', '32', '34', '36', '38', '40']
        }

        # Pre-calculate segment assignments based on probabilities
        segment_assignments: List[str] = []
        for segment, config in customer_segments.items():
            count = int(num_customers * config['probability'])
            segment_assignments.extend([segment] * count)

        # Fill remaining slots with 'regular' if needed
        while len(segment_assignments) < num_customers:
            segment_assignments.append('regular')

        # Shuffle using instance random for reproducibility
        self._rng.shuffle(segment_assignments)

        # Get schema once
        customer_schema = self._get_customer_schema()
        
        # Process in batches for memory efficiency
        is_first_batch = True
        total_written = 0
        
        try:
            for batch_start in range(0, num_customers, self._batch_size):
                # Generate batch using generator (memory efficient)
                batch_data = list(self._generate_customer_batch(
                    batch_start,
                    self._batch_size,
                    segment_assignments,
                    customer_segments,
                    geo_data,
                    size_profiles
                ))
                
                # Create DataFrame from batch
                batch_df = self.spark.createDataFrame(batch_data, schema=customer_schema)
                
                # Write batch
                write_mode = "overwrite" if is_first_batch else "append"
                batch_df.write \
                    .mode(write_mode) \
                    .format("delta") \
                    .saveAsTable(f"{self.catalog}.{self.schema}.gold_customer_dim")
                
                is_first_batch = False
                total_written += len(batch_data)
                
                # Log progress
                progress_pct = (total_written / num_customers) * 100
                logger.info(f"Written {total_written:,}/{num_customers:,} customers ({progress_pct:.1f}%)")

        except Exception as e:
            logger.error(f"Error generating customer data at batch starting {batch_start}: {str(e)}")
            raise
        
        # Add table comment
        self.spark.sql(f"""
            ALTER TABLE {self.catalog}.{self.schema}.gold_customer_dim
            SET TBLPROPERTIES (
                'comment' = 'Customer dimension with slowly changing attributes. Sources: Salesforce CRM, Segment CDP, Loyalty Platform'
            )
        """)
        
        logger.info(f"Created customer dimension with {total_written:,} records")
    
    def create_product_dimension(self) -> None:
        """Create and populate product dimension."""
        logger.info("Generating product dimension...")
        
        num_products = self.config['products']
        
        if num_products > 50000:
            logger.warning(f"Generating {num_products:,} products - this may take significant time")
        elif num_products > 20000:
            logger.info(f"Generating {num_products:,} products - this may take several minutes")
        
        logger.info(f"Generating {num_products:,} products...")
        
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
        total_subcategories = sum(
            len(cat3_list)
            for cat2_dict in categories.values()
            for cat3_list in cat2_dict.values()
        )

        products_per_cat = max(1, num_products // total_subcategories)

        # Generate products
        products_data = []
        product_id = 1

        for cat1, cat2_dict in categories.items():
            for cat2, cat3_list in cat2_dict.items():
                for cat3 in cat3_list:
                    
                    for _ in range(products_per_cat):
                        sku = f"SKU_{product_id:06d}"
                        base_price = float(int(self._rng.uniform(29.99, 299.99) * 100)) / 100
                        
                        product = {
                            'product_key': product_id,
                            'product_id': f"PROD_{product_id:06d}",
                            'sku': sku,
                            'product_name': f"{self._rng.choice(brands)} {cat3.title()} {product_id}",
                            'brand': self._rng.choice(brands),
                            'category_level_1': cat1,
                            'category_level_2': cat2,
                            'category_level_3': cat3,
                            'color_family': self._rng.choice(['Neutral', 'Bright', 'Dark', 'Pastel']),
                            'color_name': self._rng.choice(colors),
                            'size_range': 'XS-XL' if cat1 == 'apparel' else 'ONE SIZE',
                            'material_primary': self._rng.choice(materials),
                            'material_composition': f"{self._rng.randint(60, 100)}% {self._rng.choice(materials)}",
                            'season_code': self._rng.choice(seasons),
                            'collection_name': f"{self._rng.choice(seasons)} {datetime.now().year} Collection",
                            'launch_date': (datetime.now() - timedelta(days=self._rng.randint(1, 730))).date(),
                            'end_of_life_date': None if self._rng.random() > 0.2 else (datetime.now() + timedelta(days=self._rng.randint(30, 365))).date(),
                            'base_price': base_price,
                            'unit_cost': float(int(base_price * self._rng.uniform(0.3, 0.5) * 100)) / 100,
                            'margin_percent': float(int(self._rng.uniform(40, 70) * 100)) / 100,
                            'price_tier': 'luxury' if base_price > 200 else 'premium' if base_price > 100 else 'mid' if base_price > 50 else 'budget',
                            'sustainability_flag': self._rng.choice([True, False]),
                            'is_active': self._rng.random() > 0.1,
                            'source_system': SOURCE_SYSTEMS['product'],
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
        final_products = products_data[:num_products]
        product_df = self.spark.createDataFrame(final_products, schema=product_schema)
        
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
        
        logger.info(f"Created product dimension with {len(final_products):,} records")
    
    def create_location_dimension(self) -> None:
        """Create and populate location dimension.
        
        Note: Location dimension uses a fixed set of 13 locations (10 stores, 2 warehouses, 1 DC).
        The configured 'locations' parameter is currently ignored. This is by design to maintain
        realistic geographic distribution and store formats. To add more locations, modify the
        locations_data list below.
        """
        logger.info("Generating location dimension...")
        
        configured_locations = self.config.get('locations', 13)
        if configured_locations != 13:
            logger.warning(
                f"Location dimension uses a fixed set of 13 locations. "
                f"Configured value ({configured_locations}) is ignored. "
                f"To customize locations, modify the locations_data list in create_location_dimension()."
            )
        
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
        
        # State-level sales tax rates (approximate averages including local taxes)
        state_tax_rates = {
            'NY': 0.08875,  # New York (8.875% NYC)
            'CA': 0.0725,   # California (7.25% state average)
            'IL': 0.0825,   # Illinois (8.25% Chicago)
            'FL': 0.06,     # Florida (6% no state income tax)
            'TX': 0.0625,   # Texas (6.25% no state income tax)
            'NV': 0.0685,   # Nevada (6.85%)
            'MA': 0.0625,   # Massachusetts (6.25%)
            'WA': 0.065,    # Washington (6.5%)
            'GA': 0.04,     # Georgia (4% state)
            'NJ': 0.06625,  # New Jersey (6.625%)
            'OH': 0.0575,   # Ohio (5.75%)
        }
        
        # Enrich location data
        for i, loc in enumerate(locations_data):
            state = loc['state_province']
            loc.update({
                'location_key': int(i + 1),
                'channel': 'physical' if loc['location_type'] == 'store' else 'digital',
                'district': f"District_{loc['region'][:2].upper()}",
                'postal_code': f"{self._rng.randint(10000, 99999)}",
                'latitude': float(int(self._rng.uniform(25.0, 49.0) * 1000000)) / 1000000,
                'longitude': float(int(self._rng.uniform(-125.0, -66.0) * 1000000)) / 1000000,
                'total_sqft': float(loc['total_sqft']),
                'open_date': (datetime.now() - timedelta(days=self._rng.randint(365, 3650))).date(),
                'close_date': None,
                'is_active': True,
                'timezone': 'America/New_York' if loc['region'] == 'Northeast' else 
                           'America/Chicago' if loc['region'] == 'Midwest' else
                           'America/Denver' if loc['region'] == 'Southwest' else
                           'America/Los_Angeles',
                'state_tax_rate': state_tax_rates.get(state, 0.07),
                'source_system': SOURCE_SYSTEMS['location'],
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
            StructField("state_tax_rate", DoubleType(), True),
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
    
    def create_date_dimension(self) -> None:
        """Create and populate date dimension."""
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
    
    def create_channel_dimension(self) -> None:
        """Create and populate channel dimension."""
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
                'source_system': SOURCE_SYSTEMS['channel'],
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
    
    def create_time_dimension(self) -> None:
        """Create and populate time dimension (hourly granularity)."""
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
                    'hour_minute': f"{hour:02d}:{minute:02d}",
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