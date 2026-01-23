"""
Pricing Business Rules

Provides discount and pricing calculations for fashion retail.
Extracted from FactGenerator for reuse in both batch and streaming.

Usage:
    from fashion_retail.business_rules import calculate_discount, PricingContext
    
    # Create pricing context
    ctx = PricingContext(
        customer_segment="premium",
        is_sale_period=True,
        is_clearance=False,
        product_season="spring",
        current_season="summer"
    )
    
    # Calculate discount
    discount_pct, discount_type = calculate_discount(ctx)
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import random

from ..constants import CUSTOMER_SEGMENTS, SEGMENT_DISCOUNT_RANGES


@dataclass
class PricingContext:
    """
    Context object for pricing calculations.
    
    Attributes:
        customer_segment: Customer segment (vip, premium, loyal, regular, new)
        is_sale_period: Whether this is during a promotional sale period
        is_clearance: Whether the product is on clearance
        product_season: The season the product is designed for
        current_season: The current season
        random_seed: Optional seed for reproducibility
    """
    customer_segment: str = "regular"
    is_sale_period: bool = False
    is_clearance: bool = False
    product_season: Optional[str] = None
    current_season: Optional[str] = None
    random_seed: Optional[int] = None
    
    def __post_init__(self):
        self._rng = random.Random(self.random_seed)
    
    @property
    def is_off_season(self) -> bool:
        """Check if product is off-season (eligible for clearance)."""
        if self.product_season is None or self.current_season is None:
            return False
        return self.product_season != self.current_season


def get_segment_config(segment: str) -> Dict:
    """
    Get the configuration for a customer segment.
    
    Args:
        segment: Customer segment name
        
    Returns:
        Segment configuration dict with items_range, discount_probability, etc.
    """
    return CUSTOMER_SEGMENTS.get(segment, CUSTOMER_SEGMENTS['regular'])


def get_segment_discount_range(segment: str) -> Tuple[float, float]:
    """
    Get the discount range for a customer segment.
    
    Args:
        segment: Customer segment name
        
    Returns:
        Tuple of (min_discount, max_discount) as decimals (e.g., 0.10, 0.20)
    """
    return SEGMENT_DISCOUNT_RANGES.get(segment, (0.10, 0.20))


def get_items_per_basket(segment: str, rng: Optional[random.Random] = None) -> int:
    """
    Get number of items in basket based on customer segment.
    
    Args:
        segment: Customer segment name
        rng: Random number generator (uses global if None)
        
    Returns:
        Number of items for the basket
    """
    rng = rng or random.Random()
    config = get_segment_config(segment)
    return rng.choice(config['items_range'])


def get_discount_probability(segment: str) -> float:
    """
    Get the probability that a customer segment receives a discount.
    
    Args:
        segment: Customer segment name
        
    Returns:
        Probability as decimal (0.0 to 1.0)
    """
    config = get_segment_config(segment)
    return config['discount_probability']


def get_return_probability(segment: str) -> float:
    """
    Get the probability of return for a customer segment.
    
    Args:
        segment: Customer segment name
        
    Returns:
        Probability as decimal (0.0 to 1.0)
    """
    config = get_segment_config(segment)
    return config['return_probability']


def determine_discount_type(
    context: PricingContext,
    rng: Optional[random.Random] = None
) -> Tuple[str, bool]:
    """
    Determine the type of discount to apply.
    
    Priority order:
    1. Clearance (off-season product)
    2. Promotional (sale period)
    3. Segment discount (loyalty-based)
    4. None
    
    Args:
        context: PricingContext with discount determination factors
        rng: Random number generator
        
    Returns:
        Tuple of (discount_type, should_apply) where discount_type is one of:
        'clearance', 'promotional', 'segment', 'none'
    """
    rng = rng or context._rng or random.Random()
    
    # Check for clearance (off-season product)
    if context.is_clearance or (context.is_off_season and rng.random() < 0.2):
        return ('clearance', True)
    
    # Check for promotional discount during sale period
    if context.is_sale_period and rng.random() < 0.3:
        return ('promotional', True)
    
    # Check for segment-based discount
    discount_prob = get_discount_probability(context.customer_segment)
    if rng.random() < discount_prob:
        return ('segment', True)
    
    return ('none', False)


def calculate_discount(
    context: PricingContext,
    rng: Optional[random.Random] = None
) -> Tuple[float, str]:
    """
    Calculate the discount percentage based on context.
    
    This is the main pricing calculation extracted from FactGenerator.
    It determines both the discount type and amount.
    
    Discount ranges by type:
    - Clearance: 30-50%
    - Promotional: 10-30%
    - Segment: varies by segment (5-30% depending on tier)
    - None: 0%
    
    Args:
        context: PricingContext with all pricing factors
        rng: Optional random number generator
        
    Returns:
        Tuple of (discount_percentage, discount_type) where percentage is
        a decimal (e.g., 0.15 for 15%)
        
    Example:
        >>> ctx = PricingContext(customer_segment="vip", is_sale_period=True)
        >>> discount_pct, discount_type = calculate_discount(ctx)
        >>> print(f"{discount_type}: {discount_pct*100:.0f}%")
        promotional: 25%
    """
    rng = rng or context._rng or random.Random()
    
    discount_type, should_apply = determine_discount_type(context, rng)
    
    if not should_apply:
        return (0.0, 'none')
    
    if discount_type == 'clearance':
        discount_pct = rng.uniform(0.30, 0.50)
    elif discount_type == 'promotional':
        discount_pct = rng.uniform(0.10, 0.30)
    elif discount_type == 'segment':
        min_disc, max_disc = get_segment_discount_range(context.customer_segment)
        discount_pct = rng.uniform(min_disc, max_disc)
    else:
        discount_pct = 0.0
    
    return (discount_pct, discount_type)


def calculate_unit_price(
    base_price: float,
    discount_pct: float
) -> float:
    """
    Calculate the final unit price after discount.
    
    Args:
        base_price: Original price
        discount_pct: Discount as decimal (e.g., 0.20 for 20%)
        
    Returns:
        Final price after discount
    """
    return base_price * (1 - discount_pct)


def calculate_discount_amount(
    base_price: float,
    quantity: int,
    discount_pct: float
) -> float:
    """
    Calculate the total discount amount for a line item.
    
    Args:
        base_price: Original unit price
        quantity: Number of units
        discount_pct: Discount as decimal
        
    Returns:
        Total discount amount
    """
    return base_price * quantity * discount_pct


def calculate_tax(
    net_amount: float,
    tax_rate: float = 0.07
) -> float:
    """
    Calculate tax amount.
    
    Args:
        net_amount: Amount before tax
        tax_rate: Tax rate as decimal (default 7%)
        
    Returns:
        Tax amount
    """
    return net_amount * tax_rate


def calculate_gross_margin(
    net_sales: float,
    unit_cost: float,
    quantity: int
) -> float:
    """
    Calculate gross margin for a line item.
    
    Args:
        net_sales: Net sales amount (after discount, before tax)
        unit_cost: Cost per unit
        quantity: Number of units
        
    Returns:
        Gross margin (net_sales - total_cost)
    """
    return net_sales - (unit_cost * quantity)
