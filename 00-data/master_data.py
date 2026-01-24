"""
Master Data Configuration - Single Source of Truth

This module defines all reference/master data used by:
- Streaming event generators (POS, e-commerce, inventory, clickstream)
- Gold dimension table derivation in the pipeline

NO external dependencies (no Spark, no database queries).
This enables:
- Generators to run without database connectivity
- Local testing without Databricks
- True raw → bronze → silver → gold flow (no circular dependency)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random

# ============================================================================
# PRODUCT CATALOG
# ============================================================================

CATEGORIES = {
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

BRANDS = [
    'Urban Style', 'Classic Comfort', 'Eco Threads', 'Luxe Label',
    'Street Wear Co', 'Vintage Vibes', 'Modern Minimal', 'Bold Basics'
]

COLORS = [
    'Black', 'White', 'Navy', 'Grey', 'Blue', 'Red', 'Green',
    'Pink', 'Beige', 'Brown', 'Purple', 'Yellow'
]

MATERIALS = [
    'Cotton', 'Polyester', 'Wool', 'Silk', 'Linen', 'Denim',
    'Leather', 'Synthetic', 'Cashmere', 'Modal'
]

SEASONS = ['Spring', 'Summer', 'Fall', 'Winter', 'Year-round']


@dataclass
class Product:
    """Product master data record."""
    sku: str
    product_id: str
    product_name: str
    brand: str
    category_l1: str
    category_l2: str
    category_l3: str
    base_price: float
    unit_cost: float
    color: str
    material: str
    season: str
    price_tier: str
    is_active: bool = True


def generate_product_catalog(num_products: int = 500, seed: int = 42) -> List[Product]:
    """
    Generate a reproducible product catalog.
    
    Args:
        num_products: Number of products to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of Product objects
    """
    rng = random.Random(seed)
    products = []
    product_id = 1
    
    # Count total subcategories for distribution
    total_subcats = sum(
        len(cat3_list)
        for cat2_dict in CATEGORIES.values()
        for cat3_list in cat2_dict.values()
    )
    products_per_subcat = max(1, num_products // total_subcats)
    
    for cat1, cat2_dict in CATEGORIES.items():
        for cat2, cat3_list in cat2_dict.items():
            for cat3 in cat3_list:
                for _ in range(products_per_subcat):
                    if product_id > num_products:
                        break
                    
                    base_price = round(rng.uniform(29.99, 299.99), 2)
                    unit_cost = round(base_price * rng.uniform(0.3, 0.5), 2)
                    
                    # Determine price tier
                    if base_price > 200:
                        price_tier = 'luxury'
                    elif base_price > 100:
                        price_tier = 'premium'
                    elif base_price > 50:
                        price_tier = 'mid'
                    else:
                        price_tier = 'budget'
                    
                    brand = rng.choice(BRANDS)
                    products.append(Product(
                        sku=f"SKU_{product_id:06d}",
                        product_id=f"PROD_{product_id:06d}",
                        product_name=f"{brand} {cat3.title()} {product_id}",
                        brand=brand,
                        category_l1=cat1,
                        category_l2=cat2,
                        category_l3=cat3,
                        base_price=base_price,
                        unit_cost=unit_cost,
                        color=rng.choice(COLORS),
                        material=rng.choice(MATERIALS),
                        season=rng.choice(SEASONS),
                        price_tier=price_tier,
                        is_active=rng.random() > 0.1,
                    ))
                    product_id += 1
                    
                if product_id > num_products:
                    break
            if product_id > num_products:
                break
        if product_id > num_products:
            break
    
    return products


# Pre-generate default catalog (500 products)
PRODUCT_CATALOG: List[Product] = generate_product_catalog(500)
SKUS: List[str] = [p.sku for p in PRODUCT_CATALOG]
ACTIVE_SKUS: List[str] = [p.sku for p in PRODUCT_CATALOG if p.is_active]


# ============================================================================
# LOCATIONS (Stores, Warehouses, DCs)
# ============================================================================

@dataclass
class Location:
    """Location master data record."""
    location_id: str
    location_name: str
    location_type: str  # 'store', 'warehouse', 'dc'
    store_format: Optional[str]  # 'flagship', 'standard', 'outlet', None
    city: str
    state: str
    region: str
    country: str = 'USA'
    tax_rate: float = 0.07
    selling_sqft: float = 0.0
    total_sqft: float = 0.0
    is_active: bool = True


LOCATIONS: List[Location] = [
    # Flagship stores
    Location('LOC_001', 'NYC Flagship', 'store', 'flagship', 'New York', 'NY', 'Northeast', tax_rate=0.08875, selling_sqft=15000, total_sqft=22500),
    Location('LOC_002', 'LA Flagship', 'store', 'flagship', 'Los Angeles', 'CA', 'West', tax_rate=0.0725, selling_sqft=12000, total_sqft=18000),
    
    # Standard stores
    Location('LOC_003', 'Chicago Store', 'store', 'standard', 'Chicago', 'IL', 'Midwest', tax_rate=0.0825, selling_sqft=8000, total_sqft=12000),
    Location('LOC_004', 'Miami Store', 'store', 'standard', 'Miami', 'FL', 'Southeast', tax_rate=0.06, selling_sqft=7500, total_sqft=11250),
    Location('LOC_005', 'Dallas Store', 'store', 'standard', 'Dallas', 'TX', 'Southwest', tax_rate=0.0625, selling_sqft=7000, total_sqft=10500),
    Location('LOC_006', 'Boston Store', 'store', 'standard', 'Boston', 'MA', 'Northeast', tax_rate=0.0625, selling_sqft=6000, total_sqft=9000),
    Location('LOC_007', 'Seattle Store', 'store', 'standard', 'Seattle', 'WA', 'West', tax_rate=0.065, selling_sqft=5500, total_sqft=8250),
    Location('LOC_008', 'Atlanta Store', 'store', 'standard', 'Atlanta', 'GA', 'Southeast', tax_rate=0.04, selling_sqft=6500, total_sqft=9750),
    
    # Outlet stores
    Location('LOC_009', 'Orlando Outlet', 'store', 'outlet', 'Orlando', 'FL', 'Southeast', tax_rate=0.06, selling_sqft=5000, total_sqft=7500),
    Location('LOC_010', 'Las Vegas Outlet', 'store', 'outlet', 'Las Vegas', 'NV', 'West', tax_rate=0.0685, selling_sqft=4500, total_sqft=6750),
    
    # Warehouses
    Location('LOC_011', 'East Coast Warehouse', 'warehouse', None, 'Newark', 'NJ', 'Northeast', tax_rate=0.06625, total_sqft=50000),
    Location('LOC_012', 'West Coast Warehouse', 'warehouse', None, 'Ontario', 'CA', 'West', tax_rate=0.0725, total_sqft=45000),
    
    # Distribution Center
    Location('LOC_013', 'Central DC', 'dc', None, 'Columbus', 'OH', 'Midwest', tax_rate=0.0575, total_sqft=100000),
]

# Convenience lists
STORE_IDS: List[str] = [loc.location_id for loc in LOCATIONS if loc.location_type == 'store']
WAREHOUSE_IDS: List[str] = [loc.location_id for loc in LOCATIONS if loc.location_type == 'warehouse']
DC_IDS: List[str] = [loc.location_id for loc in LOCATIONS if loc.location_type == 'dc']
ALL_LOCATION_IDS: List[str] = [loc.location_id for loc in LOCATIONS]


# ============================================================================
# CHANNELS
# ============================================================================

@dataclass
class Channel:
    """Channel master data record."""
    channel_code: str
    channel_name: str
    channel_type: str  # 'online', 'offline', 'hybrid'
    channel_category: str  # 'web', 'mobile_app', 'store', 'social', 'marketplace'
    device_category: str
    is_digital: bool
    is_owned: bool
    commission_rate: float = 0.0


CHANNELS: List[Channel] = [
    Channel('WEB_DESKTOP', 'Website - Desktop', 'online', 'web', 'desktop', True, True, 0.0),
    Channel('WEB_MOBILE', 'Website - Mobile', 'online', 'web', 'mobile', True, True, 0.0),
    Channel('APP_IOS', 'iOS Mobile App', 'online', 'mobile_app', 'mobile', True, True, 0.0),
    Channel('APP_ANDROID', 'Android Mobile App', 'online', 'mobile_app', 'mobile', True, True, 0.0),
    Channel('STORE_POS', 'Physical Store - POS', 'offline', 'store', 'pos', False, True, 0.0),
    Channel('STORE_KIOSK', 'In-Store Kiosk', 'hybrid', 'store', 'kiosk', True, True, 0.0),
    Channel('SOCIAL_FB', 'Facebook Shop', 'online', 'social', 'mobile', True, False, 5.0),
    Channel('MARKETPLACE_AMAZON', 'Amazon Marketplace', 'online', 'marketplace', 'desktop', True, False, 15.0),
]

# Convenience lists
CHANNEL_CODES: List[str] = [ch.channel_code for ch in CHANNELS]
ECOMMERCE_CHANNELS: List[str] = [ch.channel_code for ch in CHANNELS if ch.channel_type == 'online']
POS_CHANNEL: str = 'STORE_POS'


# ============================================================================
# CUSTOMER SEGMENTS
# ============================================================================

CUSTOMER_SEGMENTS: Dict[str, Dict[str, Any]] = {
    'vip': {
        'probability': 0.05,
        'lifetime_value_range': (5000, 25000),
        'basket_size_range': (3, 8),
        'discount_sensitivity': 0.2,  # Less price sensitive
        'return_rate': 0.05,
        'preferred_channels': ['store', 'web'],
        'loyalty_tiers': ['platinum', 'gold'],
    },
    'premium': {
        'probability': 0.15,
        'lifetime_value_range': (2000, 8000),
        'basket_size_range': (2, 5),
        'discount_sensitivity': 0.4,
        'return_rate': 0.08,
        'preferred_channels': ['web', 'app'],
        'loyalty_tiers': ['gold', 'silver'],
    },
    'loyal': {
        'probability': 0.25,
        'lifetime_value_range': (800, 3000),
        'basket_size_range': (2, 4),
        'discount_sensitivity': 0.5,
        'return_rate': 0.10,
        'preferred_channels': ['web', 'store'],
        'loyalty_tiers': ['silver', 'bronze'],
    },
    'regular': {
        'probability': 0.35,
        'lifetime_value_range': (200, 1200),
        'basket_size_range': (1, 3),
        'discount_sensitivity': 0.7,
        'return_rate': 0.12,
        'preferred_channels': ['web', 'app'],
        'loyalty_tiers': ['bronze', 'silver'],
    },
    'new': {
        'probability': 0.20,
        'lifetime_value_range': (50, 500),
        'basket_size_range': (1, 2),
        'discount_sensitivity': 0.9,  # Very price sensitive
        'return_rate': 0.15,
        'preferred_channels': ['web', 'app', 'social'],
        'loyalty_tiers': ['bronze'],
    }
}

# Segment discount ranges (min, max discount %)
SEGMENT_DISCOUNT_RANGES: Dict[str, Tuple[float, float]] = {
    'vip': (0.0, 0.10),      # 0-10% - rarely need discounts
    'premium': (0.0, 0.15),   # 0-15%
    'loyal': (0.05, 0.20),    # 5-20%
    'regular': (0.10, 0.30),  # 10-30%
    'new': (0.15, 0.40),      # 15-40% - need incentives
}


def generate_customer_ids(num_customers: int = 10000, seed: int = 42) -> List[str]:
    """
    Generate a pool of customer IDs with segment assignments.
    
    Args:
        num_customers: Number of customer IDs to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of customer ID strings
    """
    return [f"CUST_{i:08d}" for i in range(1, num_customers + 1)]


def generate_customer_segments(num_customers: int = 10000, seed: int = 42) -> Dict[str, str]:
    """
    Generate customer ID to segment mapping.
    
    Args:
        num_customers: Number of customers
        seed: Random seed
        
    Returns:
        Dict mapping customer_id to segment name
    """
    rng = random.Random(seed)
    customer_ids = generate_customer_ids(num_customers, seed)
    
    # Pre-calculate segment assignments
    assignments = []
    for segment, config in CUSTOMER_SEGMENTS.items():
        count = int(num_customers * config['probability'])
        assignments.extend([segment] * count)
    
    # Fill remaining with 'regular'
    while len(assignments) < num_customers:
        assignments.append('regular')
    
    rng.shuffle(assignments)
    
    return {cid: seg for cid, seg in zip(customer_ids, assignments)}


# Pre-generate customer data
CUSTOMER_IDS: List[str] = generate_customer_ids(10000)
CUSTOMER_SEGMENT_MAP: Dict[str, str] = generate_customer_segments(10000)


# ============================================================================
# SEASONALITY & BUSINESS RULES
# ============================================================================

MONTHLY_SEASONALITY: Dict[int, float] = {
    1: 0.7,   # January - post-holiday slump
    2: 0.75,  # February - Valentine's
    3: 0.9,   # March - Spring arrivals
    4: 1.0,   # April - Easter
    5: 0.95,  # May - Mother's Day
    6: 0.85,  # June - Summer start
    7: 0.8,   # July - Summer sales
    8: 0.9,   # August - Back to school
    9: 0.95,  # September - Fall arrivals
    10: 1.0,  # October - Fall season
    11: 1.3,  # November - Black Friday
    12: 1.5,  # December - Holiday peak
}

PEAK_SEASON_MONTHS: List[int] = [11, 12, 3, 4]

SALE_PERIODS: Dict[int, str] = {
    1: 'Winter Clearance',
    2: "President's Day Sale",
    3: 'Spring Sale',
    5: 'Memorial Day Sale',
    7: 'Summer Sale',
    9: 'Back to School',
    11: 'Black Friday',
    12: 'Holiday Sale'
}

HOLIDAYS: Dict[int, List[Tuple[str, int]]] = {
    1: [('New Year', 1)],
    2: [("Valentine's Day", 14)],
    4: [('Easter', 15)],
    5: [('Memorial Day', 30)],
    7: [('Independence Day', 4)],
    9: [('Labor Day', 5)],
    10: [('Halloween', 31)],
    11: [('Black Friday', 25), ('Thanksgiving', 24)],
    12: [('Christmas', 25), ('Boxing Day', 26)]
}


# ============================================================================
# HELPER FUNCTIONS FOR GENERATORS
# ============================================================================

def get_product_by_sku(sku: str) -> Optional[Product]:
    """Look up product details by SKU."""
    for p in PRODUCT_CATALOG:
        if p.sku == sku:
            return p
    return None


def get_product_dict(product: Product) -> Dict[str, Any]:
    """Convert Product dataclass to dictionary."""
    return {
        'sku': product.sku,
        'product_id': product.product_id,
        'product_name': product.product_name,
        'brand': product.brand,
        'category_l1': product.category_l1,
        'category_l2': product.category_l2,
        'category_l3': product.category_l3,
        'base_price': product.base_price,
        'unit_cost': product.unit_cost,
        'color': product.color,
        'material': product.material,
        'season': product.season,
        'price_tier': product.price_tier,
        'is_active': product.is_active,
    }


def get_location_by_id(location_id: str) -> Optional[Location]:
    """Look up location details by ID."""
    for loc in LOCATIONS:
        if loc.location_id == location_id:
            return loc
    return None


def get_location_dict(location: Location) -> Dict[str, Any]:
    """Convert Location dataclass to dictionary."""
    return {
        'location_id': location.location_id,
        'location_name': location.location_name,
        'location_type': location.location_type,
        'store_format': location.store_format,
        'city': location.city,
        'state': location.state,
        'region': location.region,
        'country': location.country,
        'tax_rate': location.tax_rate,
        'selling_sqft': location.selling_sqft,
        'total_sqft': location.total_sqft,
        'is_active': location.is_active,
    }


def get_channel_by_code(code: str) -> Optional[Channel]:
    """Look up channel by code."""
    for ch in CHANNELS:
        if ch.channel_code == code:
            return ch
    return None


def get_channel_dict(channel: Channel) -> Dict[str, Any]:
    """Convert Channel dataclass to dictionary."""
    return {
        'channel_code': channel.channel_code,
        'channel_name': channel.channel_name,
        'channel_type': channel.channel_type,
        'channel_category': channel.channel_category,
        'device_category': channel.device_category,
        'is_digital': channel.is_digital,
        'is_owned': channel.is_owned,
        'commission_rate': channel.commission_rate,
    }


def get_random_customer_segment(rng: Optional[random.Random] = None) -> str:
    """Get a random customer segment based on probability distribution."""
    rng = rng or random.Random()
    r = rng.random()
    cumulative = 0.0
    for segment, config in CUSTOMER_SEGMENTS.items():
        cumulative += config['probability']
        if r <= cumulative:
            return segment
    return 'regular'


def get_customer_segment(customer_id: str) -> str:
    """Get the segment for a specific customer ID."""
    return CUSTOMER_SEGMENT_MAP.get(customer_id, 'regular')


def get_segment_basket_size(segment: str, rng: Optional[random.Random] = None) -> int:
    """Get random basket size for a customer segment."""
    rng = rng or random.Random()
    config = CUSTOMER_SEGMENTS.get(segment, CUSTOMER_SEGMENTS['regular'])
    min_size, max_size = config['basket_size_range']
    return rng.randint(min_size, max_size)


def get_segment_discount(segment: str, rng: Optional[random.Random] = None) -> float:
    """Get random discount percentage for a customer segment."""
    rng = rng or random.Random()
    min_disc, max_disc = SEGMENT_DISCOUNT_RANGES.get(segment, (0.10, 0.30))
    return round(rng.uniform(min_disc, max_disc), 2)


def get_seasonality_multiplier(month: int) -> float:
    """Get seasonality multiplier for a given month."""
    return MONTHLY_SEASONALITY.get(month, 1.0)


def is_sale_period(month: int) -> bool:
    """Check if the month is a sale period."""
    return month in SALE_PERIODS


def is_peak_season(month: int) -> bool:
    """Check if the month is peak season."""
    return month in PEAK_SEASON_MONTHS


# ============================================================================
# DIMENSION TABLE DATA (for gold pipeline)
# ============================================================================

def get_products_for_dimension(seed: int = 42) -> List[Dict[str, Any]]:
    """
    Get product data formatted for gold_product_dim table.
    
    Matches original dimension_generator.py schema for metric view compatibility.
    """
    rng = random.Random(seed)
    products = []
    current_year = datetime.now().year
    
    for i, p in enumerate(PRODUCT_CATALOG):
        # Calculate color family
        if p.color in ['Black', 'White', 'Grey', 'Beige', 'Brown']:
            color_family = 'Neutral'
        elif p.color in ['Red', 'Yellow', 'Pink']:
            color_family = 'Bright'
        elif p.color in ['Navy', 'Blue', 'Purple']:
            color_family = 'Dark'
        else:
            color_family = 'Pastel'
        
        # Material composition (e.g., "80% Cotton, 20% Polyester")
        primary_pct = rng.randint(60, 100)
        if primary_pct < 100:
            secondary_material = rng.choice([m for m in MATERIALS if m != p.material])
            material_composition = f"{primary_pct}% {p.material}, {100-primary_pct}% {secondary_material}"
        else:
            material_composition = f"100% {p.material}"
        
        # Collection name
        collection_name = f"{p.season} {current_year} Collection"
        
        # Launch date (within last 2 years)
        launch_date = datetime.now() - timedelta(days=rng.randint(1, 730))
        
        # End of life date (20% have EOL set in future)
        end_of_life_date = None
        if rng.random() < 0.2:
            end_of_life_date = datetime.now() + timedelta(days=rng.randint(30, 365))
        
        # Sustainability flag (eco-friendly products)
        sustainability_flag = rng.choice([True, False])
        
        products.append({
            'product_key': i + 1,
            'product_id': p.product_id,
            'sku': p.sku,
            'product_name': p.product_name,
            'brand': p.brand,
            'category_level_1': p.category_l1,
            'category_level_2': p.category_l2,
            'category_level_3': p.category_l3,
            'color_family': color_family,
            'color_name': p.color,
            'size_range': 'XS-XL' if p.category_l1 == 'apparel' else 'ONE SIZE',
            'material_primary': p.material,
            'material_composition': material_composition,
            'season_code': p.season,
            'collection_name': collection_name,
            'launch_date': launch_date.date(),
            'end_of_life_date': end_of_life_date.date() if end_of_life_date else None,
            'base_price': p.base_price,
            'unit_cost': p.unit_cost,
            'margin_percent': round((p.base_price - p.unit_cost) / p.base_price * 100, 2),
            'price_tier': p.price_tier,
            'sustainability_flag': sustainability_flag,
            'is_active': p.is_active,
            'source_system': 'MASTER_DATA',
        })
    
    return products


def get_locations_for_dimension(seed: int = 42) -> List[Dict[str, Any]]:
    """
    Get location data formatted for gold_location_dim table.
    
    Matches original dimension_generator.py schema for metric view compatibility.
    """
    rng = random.Random(seed)
    locations = []
    
    # Timezone mapping by region
    TIMEZONES = {
        'Northeast': 'America/New_York',
        'Midwest': 'America/Chicago',
        'Southwest': 'America/Denver',
        'West': 'America/Los_Angeles',
        'Southeast': 'America/New_York',
    }
    
    # Approximate lat/lon ranges by region
    LAT_LON_RANGES = {
        'Northeast': ((38, 45), (-80, -70)),
        'Midwest': ((38, 48), (-95, -82)),
        'Southwest': ((30, 38), (-115, -100)),
        'West': ((32, 49), (-125, -115)),
        'Southeast': ((25, 36), (-90, -75)),
    }
    
    for i, loc in enumerate(LOCATIONS):
        # Generate latitude/longitude
        lat_range, lon_range = LAT_LON_RANGES.get(loc.region, ((30, 45), (-100, -80)))
        latitude = round(rng.uniform(lat_range[0], lat_range[1]), 6)
        longitude = round(rng.uniform(lon_range[0], lon_range[1]), 6)
        
        # Generate postal code
        postal_code = f"{rng.randint(10000, 99999)}"
        
        # District naming
        district = f"District_{loc.region[:2].upper()}"
        
        # Open date (1-10 years ago)
        open_date = datetime.now() - timedelta(days=rng.randint(365, 3650))
        
        # Channel based on location type
        channel = 'physical' if loc.location_type == 'store' else 'fulfillment'
        
        # Timezone
        timezone = TIMEZONES.get(loc.region, 'America/New_York')
        
        locations.append({
            'location_key': i + 1,
            'location_id': loc.location_id,
            'location_name': loc.location_name,
            'location_type': loc.location_type,
            'store_format': loc.store_format,
            'channel': channel,
            'district': district,
            'city': loc.city,
            'state_province': loc.state,
            'postal_code': postal_code,
            'region': loc.region,
            'country': loc.country,
            'latitude': latitude,
            'longitude': longitude,
            'selling_sqft': float(loc.selling_sqft),
            'total_sqft': float(loc.total_sqft),
            'open_date': open_date.date(),
            'close_date': None,  # Active locations have no close date
            'is_active': loc.is_active,
            'timezone': timezone,
            'state_tax_rate': float(loc.tax_rate),
            'source_system': 'MASTER_DATA',
        })
    
    return locations


def get_channels_for_dimension() -> List[Dict[str, Any]]:
    """Get channel data formatted for gold_channel_dim table."""
    return [
        {
            'channel_key': i + 1,
            'channel_code': ch.channel_code,
            'channel_name': ch.channel_name,
            'channel_type': ch.channel_type,
            'channel_category': ch.channel_category,
            'device_category': ch.device_category,
            'is_digital': ch.is_digital,
            'is_owned': ch.is_owned,
            'commission_rate': ch.commission_rate,
            'source_system': 'MASTER_DATA',
        }
        for i, ch in enumerate(CHANNELS)
    ]


def get_customers_for_dimension(seed: int = 42) -> List[Dict[str, Any]]:
    """
    Get customer data formatted for gold_customer_dim table.
    
    Matches original dimension_generator.py schema for metric view compatibility.
    """
    rng = random.Random(seed)
    
    # Geographic data
    GEO_DATA = {
        'Northeast': ['New York', 'Boston', 'Philadelphia', 'Washington DC'],
        'West': ['Seattle', 'Los Angeles', 'San Francisco', 'Portland'],
        'Southeast': ['Miami', 'Atlanta', 'Charlotte', 'Tampa'],
        'Midwest': ['Chicago', 'Detroit', 'Cleveland', 'Milwaukee'],
        'Southwest': ['Dallas', 'Houston', 'Phoenix', 'Austin']
    }
    
    SIZE_PROFILES = {
        'tops': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        'bottoms': ['26', '28', '30', '32', '34', '36', '38', '40']
    }
    
    ACQUISITION_CHANNELS = ['store', 'web', 'social', 'search', 'referral', 'email', 'paid']
    PREFERRED_CATEGORIES = ['tops', 'bottoms', 'dresses', 'outerwear', 'accessories']
    LOYALTY_TIERS = ['platinum', 'gold', 'silver', 'bronze']
    EMAIL_DOMAINS = ['gmail.com', 'yahoo.com', 'outlook.com', 'icloud.com', 'hotmail.com']
    
    customers = []
    base_date = datetime(2023, 1, 1)
    
    for i, customer_id in enumerate(CUSTOMER_IDS):
        segment = CUSTOMER_SEGMENT_MAP.get(customer_id, 'regular')
        segment_info = CUSTOMER_SEGMENTS.get(segment, CUSTOMER_SEGMENTS['regular'])
        
        # Generate lifetime value within segment range
        ltv_range = segment_info.get('lifetime_value_range', (100, 500))
        lifetime_value = round(rng.uniform(ltv_range[0], ltv_range[1]), 2)
        
        # Generate realistic names
        first_name = f"First{i+1}"
        last_name = f"Last{i+1}"
        email_domain = rng.choice(EMAIL_DOMAINS)
        email = f"{first_name.lower()}.{last_name.lower()}{rng.randint(1, 999)}@{email_domain}"
        
        # Determine channels based on segment
        preferred_channels = segment_info.get('preferred_channels', ['web', 'app'])
        preferred_channel = rng.choice(preferred_channels)
        acquisition_channel = rng.choice(ACQUISITION_CHANNELS)
        
        # Geography - VIP/premium more likely in Northeast/West
        if segment in ['vip', 'premium']:
            geo_region = rng.choice(['Northeast', 'West'])
        else:
            geo_region = rng.choice(list(GEO_DATA.keys()))
        geo_city = rng.choice(GEO_DATA[geo_region])
        
        # Loyalty tiers based on segment
        segment_tiers = segment_info.get('loyalty_tiers', ['bronze'])
        loyalty_tier = rng.choice(segment_tiers)
        
        # Acquisition date (within last 2 years)
        acquisition_date = base_date - timedelta(days=rng.randint(0, 730))
        
        # Email/SMS subscription rates based on segment
        email_subscribe_rate = 0.8 if segment == 'vip' else 0.6 if segment == 'premium' else 0.4
        sms_subscribe_rate = 0.6 if segment == 'vip' else 0.4 if segment == 'premium' else 0.2
        
        customers.append({
            'customer_key': i + 1,
            'customer_id': customer_id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'segment': segment,
            'lifetime_value': lifetime_value,
            'acquisition_date': acquisition_date.date(),
            'acquisition_channel': acquisition_channel,
            'preferred_channel': preferred_channel,
            'preferred_category': rng.choice(PREFERRED_CATEGORIES),
            'size_profile_tops': rng.choice(SIZE_PROFILES['tops']),
            'size_profile_bottoms': rng.choice(SIZE_PROFILES['bottoms']),
            'geo_region': geo_region,
            'geo_city': geo_city,
            'nearest_store_id': rng.randint(1, 10),
            'loyalty_tier': loyalty_tier,
            'email_subscribe_flag': rng.random() < email_subscribe_rate,
            'sms_subscribe_flag': rng.random() < sms_subscribe_rate,
            'effective_date': datetime(2023, 1, 1).date(),
            'expiration_date': datetime(9999, 12, 31).date(),
            'is_current': True,
            'source_system': 'MASTER_DATA',
        })
    return customers


# ============================================================================
# MODULE INFO
# ============================================================================

__all__ = [
    # Products
    'PRODUCT_CATALOG', 'SKUS', 'ACTIVE_SKUS', 'Product',
    'CATEGORIES', 'BRANDS', 'COLORS', 'MATERIALS', 'SEASONS',
    'generate_product_catalog', 'get_product_by_sku', 'get_product_dict',
    
    # Locations
    'LOCATIONS', 'STORE_IDS', 'WAREHOUSE_IDS', 'DC_IDS', 'ALL_LOCATION_IDS', 'Location',
    'get_location_by_id', 'get_location_dict',
    
    # Channels
    'CHANNELS', 'CHANNEL_CODES', 'ECOMMERCE_CHANNELS', 'POS_CHANNEL', 'Channel',
    'get_channel_by_code', 'get_channel_dict',
    
    # Customers
    'CUSTOMER_IDS', 'CUSTOMER_SEGMENT_MAP', 'CUSTOMER_SEGMENTS', 'SEGMENT_DISCOUNT_RANGES',
    'generate_customer_ids', 'generate_customer_segments',
    'get_random_customer_segment', 'get_customer_segment',
    'get_segment_basket_size', 'get_segment_discount',
    
    # Seasonality
    'MONTHLY_SEASONALITY', 'PEAK_SEASON_MONTHS', 'SALE_PERIODS', 'HOLIDAYS',
    'get_seasonality_multiplier', 'is_sale_period', 'is_peak_season',
    
    # Dimension table data
    'get_products_for_dimension', 'get_locations_for_dimension', 
    'get_channels_for_dimension', 'get_customers_for_dimension',
]
