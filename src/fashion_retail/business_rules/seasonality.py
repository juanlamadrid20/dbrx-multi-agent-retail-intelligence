"""
Seasonality Business Rules

Provides seasonality multipliers and calculations for fashion retail.
Extracted from FactGenerator._apply_seasonality_multiplier() for reuse
in both batch and streaming data generation.

Usage:
    from fashion_retail.business_rules import apply_seasonality_multiplier, SeasonalityContext
    
    # Create context from date information
    ctx = SeasonalityContext(
        date_key=20260123,
        is_peak_season=False,
        is_sale_period=True,
        is_holiday=False,
        is_weekend=True
    )
    
    # Apply to base value
    adjusted = apply_seasonality_multiplier(100.0, ctx)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Union

from ..constants import MONTHLY_SEASONALITY, PEAK_SEASON_MONTHS


@dataclass
class SeasonalityContext:
    """
    Context object containing date attributes for seasonality calculations.
    
    Can be constructed from:
    - A date_key (YYYYMMDD integer)
    - A datetime object
    - Individual boolean flags
    """
    date_key: int
    is_peak_season: bool = False
    is_sale_period: bool = False
    is_holiday: bool = False
    is_weekend: bool = False
    
    @classmethod
    def from_date(cls, dt: datetime, is_sale_period: bool = False, is_holiday: bool = False) -> "SeasonalityContext":
        """
        Create SeasonalityContext from a datetime object.
        
        Args:
            dt: datetime object
            is_sale_period: Whether this is during a sale period
            is_holiday: Whether this is a holiday
            
        Returns:
            SeasonalityContext with derived values
        """
        date_key = int(dt.strftime("%Y%m%d"))
        month = dt.month
        is_weekend = dt.weekday() >= 5  # Saturday=5, Sunday=6
        is_peak = month in PEAK_SEASON_MONTHS
        
        return cls(
            date_key=date_key,
            is_peak_season=is_peak,
            is_sale_period=is_sale_period,
            is_holiday=is_holiday,
            is_weekend=is_weekend
        )
    
    @classmethod
    def from_dict(cls, date_info: Dict) -> "SeasonalityContext":
        """
        Create SeasonalityContext from a dictionary (e.g., from gold_date_dim row).
        
        Args:
            date_info: Dictionary with keys: date_key, is_peak_season, is_sale_period, 
                      is_holiday, is_weekend
                      
        Returns:
            SeasonalityContext
        """
        return cls(
            date_key=date_info.get('date_key', 0),
            is_peak_season=date_info.get('is_peak_season', False),
            is_sale_period=date_info.get('is_sale_period', False),
            is_holiday=date_info.get('is_holiday', False),
            is_weekend=date_info.get('is_weekend', False)
        )
    
    @property
    def month(self) -> int:
        """Extract month from date_key."""
        return int(str(self.date_key)[4:6])


def get_monthly_multiplier(month: int) -> float:
    """
    Get the seasonality multiplier for a given month.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Multiplier from MONTHLY_SEASONALITY (1.0 = baseline)
    """
    return MONTHLY_SEASONALITY.get(month, 1.0)


def is_peak_season(month: int) -> bool:
    """
    Check if a month is in peak season.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        True if month is in PEAK_SEASON_MONTHS
    """
    return month in PEAK_SEASON_MONTHS


def apply_seasonality_multiplier(
    base_value: float, 
    context: Union[SeasonalityContext, Dict]
) -> float:
    """
    Apply seasonality multipliers to a base value.
    
    This is the core seasonality calculation extracted from FactGenerator.
    It applies multiple multipliers based on:
    - Peak season (Nov-Dec): 1.5x
    - Sale period: 1.3x
    - Holiday: 1.8x
    - Weekend: 1.2x
    - Monthly pattern: varies by month
    
    Args:
        base_value: Base numeric value to adjust
        context: SeasonalityContext or dict with date attributes
        
    Returns:
        Adjusted value with all seasonality multipliers applied
        
    Example:
        >>> ctx = SeasonalityContext(date_key=20261125, is_peak_season=True, 
        ...                          is_sale_period=True, is_weekend=True)
        >>> apply_seasonality_multiplier(100.0, ctx)
        351.0  # 100 * 1.5 * 1.3 * 1.2 * 1.5 (November)
    """
    # Convert dict to SeasonalityContext if needed
    if isinstance(context, dict):
        context = SeasonalityContext.from_dict(context)
    
    multiplier = 1.0
    
    # Event-based multipliers
    if context.is_peak_season:
        multiplier *= 1.5
    if context.is_sale_period:
        multiplier *= 1.3
    if context.is_holiday:
        multiplier *= 1.8
    if context.is_weekend:
        multiplier *= 1.2
    
    # Monthly pattern from constants
    multiplier *= get_monthly_multiplier(context.month)
    
    return base_value * multiplier


def calculate_transaction_volume(
    base_daily_transactions: int,
    context: Union[SeasonalityContext, Dict],
    variance: float = 0.2
) -> int:
    """
    Calculate the number of transactions for a given day.
    
    Applies seasonality to base transaction count and adds random variance.
    
    Args:
        base_daily_transactions: Average daily transactions (baseline)
        context: SeasonalityContext or dict with date attributes
        variance: Standard deviation as fraction of mean (default 0.2 = 20%)
        
    Returns:
        Integer number of transactions for the day
    """
    import random
    
    adjusted = apply_seasonality_multiplier(base_daily_transactions, context)
    # Add gaussian variance
    return max(1, int(random.gauss(adjusted, adjusted * variance)))
