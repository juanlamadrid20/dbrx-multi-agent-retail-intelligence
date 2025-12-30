"""
InventoryManager: Stateful inventory tracking for aligned synthetic data generation

This class maintains in-memory state for inventory positions across all product-location
combinations throughout the data generation process. It provides the foundation for
inventory-constrained sales and cart abandonment data generation.

Key Responsibilities:
- Initialize inventory for all product-location combinations
- Track inventory deductions from sales in real-time
- Track inventory replenishments from returns (with 1-3 day delay)
- Maintain stockout periods for each position
- Provide inventory snapshots for any date

Design Decisions:
- In-memory dictionary for O(1) lookup performance (130K positions)
- Date-ordered event processing for deterministic state
- Stockout tracking with start/end dates
- Support for batch processing (50K record batches)

Thread Safety Note:
    This class is NOT thread-safe. It maintains mutable state (self.positions,
    self.pending_replenishments) that would require synchronization for concurrent
    access. For synthetic data generation (single-threaded), this is acceptable.
    For production use in multi-threaded environments, consider:
    - Using a thread-safe dictionary (e.g., from concurrent.futures)
    - Adding locks around state-modifying operations
    - Using a database-backed implementation

Requirements: FR-001 through FR-015 (inventory-aligned data generation)
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Tuple, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class InventoryPosition:
    """
    Represents the inventory state for a single product-location combination.

    Attributes:
        product_key: Product identifier
        location_key: Location identifier
        initial_quantity: Starting inventory quantity
        quantity_on_hand: Current total inventory
        quantity_available: Available for sale (on_hand - reserved - damaged)
        quantity_reserved: Reserved for orders
        quantity_damaged: Damaged/unsellable
        stockout_start_date: Date when stockout began (None if not in stockout)
        stockout_history: List of (start_date, end_date) tuples for past stockouts
    """

    def __init__(self, product_key: int, location_key: int, initial_quantity: int):
        self.product_key = product_key
        self.location_key = location_key
        self.initial_quantity = initial_quantity

        # Current state
        self.quantity_on_hand = initial_quantity
        self.quantity_available = initial_quantity
        self.quantity_reserved = 0
        self.quantity_damaged = 0

        # Stockout tracking
        self.stockout_start_date = None
        self.stockout_history: List[Tuple[int, int]] = []  # (start_date_key, end_date_key)

    def is_stockout(self) -> bool:
        """Check if position is currently in stockout."""
        return self.quantity_available == 0

    def deduct_inventory(self, quantity: int) -> bool:
        """
        Deduct inventory from available quantity.

        Args:
            quantity: Amount to deduct

        Returns:
            True if deduction successful, False if insufficient inventory
        """
        if quantity > self.quantity_available:
            return False

        self.quantity_available -= quantity
        self.quantity_on_hand -= quantity
        return True

    def replenish_inventory(self, quantity: int):
        """
        Add inventory back (e.g., from returns).

        Args:
            quantity: Amount to add back
        """
        self.quantity_available += quantity
        self.quantity_on_hand += quantity

    def start_stockout(self, date_key: int):
        """Mark the start of a stockout period."""
        if self.stockout_start_date is None:
            self.stockout_start_date = date_key

    def end_stockout(self, date_key: int):
        """Mark the end of a stockout period and record it in history."""
        if self.stockout_start_date is not None:
            self.stockout_history.append((self.stockout_start_date, date_key))
            self.stockout_start_date = None

    def get_stockout_duration_days(self) -> Optional[int]:
        """
        Calculate current stockout duration in days.

        Returns:
            Duration in days if in stockout, None otherwise
        """
        if self.stockout_start_date is None:
            return None

        # Would need current date_key to calculate - this is a placeholder
        # Actual implementation in create_inventory_fact will have date context
        return 0

    def to_dict(self) -> dict:
        """Convert position to dictionary for DataFrame creation."""
        return {
            'product_key': self.product_key,
            'location_key': self.location_key,
            'quantity_on_hand': self.quantity_on_hand,
            'quantity_available': self.quantity_available,
            'quantity_reserved': self.quantity_reserved,
            'quantity_damaged': self.quantity_damaged,
            'is_stockout': self.is_stockout(),
        }


class InventoryManager:
    """
    Manages inventory state across all product-location combinations.

    This class is the central coordinator for inventory-aligned data generation.
    It ensures that sales never exceed available inventory and tracks stockout
    periods for analytics.
    
    Thread Safety:
        NOT thread-safe. Uses instance-level random generator and mutable state.
        Create separate instances for parallel processing with different seeds.

    Usage:
        config = {'random_seed': 42, 'target_stockout_rate': 0.075, ...}
        manager = InventoryManager(spark, config)
        manager.initialize_inventory(products_df, locations_df)

        # During sales generation:
        available_qty = manager.get_available_quantity(product_key, location_key, date_key)
        manager.deduct_inventory(product_key, location_key, date_key, quantity_sold)

        # During return processing:
        manager.replenish_inventory(product_key, location_key, replenish_date_key, quantity_returned)
    """

    def __init__(self, spark, config: dict):
        """
        Initialize InventoryManager.

        Args:
            spark: SparkSession instance
            config: Configuration dictionary with keys:
                - random_seed: Random seed for reproducibility
                - target_stockout_rate: Target stockout rate (e.g., 0.075 for 7.5%)
                - low_inventory_threshold: Threshold for low inventory alerts
        """
        self.spark = spark
        self.config = config
        self.random_seed = config.get('random_seed', 42)
        self.target_stockout_rate = config.get('target_stockout_rate', 0.075)
        self.low_inventory_threshold = config.get('low_inventory_threshold', 5)

        # Main inventory state: (product_key, location_key) -> InventoryPosition
        self.positions: Dict[Tuple[int, int], InventoryPosition] = {}

        # Pending replenishments: date_key -> [(product_key, location_key, quantity), ...]
        self.pending_replenishments: Dict[int, List[Tuple[int, int, int]]] = defaultdict(list)

        # Statistics
        self.total_positions = 0
        self.total_sales_processed = 0
        self.total_returns_processed = 0

        # Use instance-level random generator for reproducibility
        # This avoids affecting global random state
        self._rng = random.Random(self.random_seed)

        logger.info(f"InventoryManager initialized with target_stockout_rate={self.target_stockout_rate}")

    def initialize_inventory(self, products_df, locations_df):
        """
        Initialize inventory for all product-location combinations.

        Strategy:
        - Allocate random initial quantities based on target stockout rate
        - Higher quantities for high-demand products
        - Lower quantities for slow-moving items to create natural stockouts

        Args:
            products_df: DataFrame with product_key and category information
            locations_df: DataFrame with location_key and location information
        """
        logger.info("Initializing inventory positions...")

        products = products_df.collect()
        locations = locations_df.collect()

        position_count = 0
        target_stockout_count = len(products) * len(locations) * self.target_stockout_rate
        stockout_positions_created = 0

        for product in products:
            for location in locations:
                product_key = product['product_key']
                location_key = location['location_key']

                # Determine if this position should be initialized for stockout
                # Distribute stockouts across all product-location combinations
                should_be_low = stockout_positions_created < target_stockout_count

                if should_be_low and self._rng.random() < 0.3:  # 30% chance if under target
                    # Initialize with low inventory (will stockout quickly)
                    initial_qty = self._rng.randint(0, 10)
                    stockout_positions_created += 1
                else:
                    # Initialize with normal inventory
                    # Higher for store locations, moderate for warehouses, lower for outlets
                    try:
                        location_type = location['location_type']
                    except (KeyError, TypeError):
                        location_type = 'store'

                    if location_type == 'warehouse':
                        initial_qty = self._rng.randint(100, 500)
                    elif location_type == 'store':
                        initial_qty = self._rng.randint(20, 100)
                    else:  # outlet
                        initial_qty = self._rng.randint(10, 50)

                position = InventoryPosition(product_key, location_key, initial_qty)
                self.positions[(product_key, location_key)] = position
                position_count += 1

        self.total_positions = position_count
        logger.info(f"Initialized {position_count:,} inventory positions")
        logger.info(f"Target stockouts: {target_stockout_count:,.0f}, Low inventory positions: {stockout_positions_created:,}")

    def get_available_quantity(self, product_key: int, location_key: int, date_key: int) -> int:
        """
        Get currently available inventory for a product-location on a specific date.

        Also processes any pending replenishments for this date.

        Args:
            product_key: Product identifier
            location_key: Location identifier
            date_key: Date key (YYYYMMDD format)

        Returns:
            Available quantity (0 if stockout)
        """
        # Process pending replenishments for this date
        self._process_pending_replenishments(date_key)

        position = self.positions.get((product_key, location_key))
        if position is None:
            logger.warning(f"Position not found: product_key={product_key}, location_key={location_key}")
            return 0

        return position.quantity_available

    def is_low_inventory(self, product_key: int, location_key: int, date_key: int) -> bool:
        """
        Check if inventory is below low threshold.

        Args:
            product_key: Product identifier
            location_key: Location identifier
            date_key: Date key (YYYYMMDD format)

        Returns:
            True if inventory <= low_inventory_threshold
        """
        available = self.get_available_quantity(product_key, location_key, date_key)
        return available <= self.low_inventory_threshold

    def deduct_inventory(self, product_key: int, location_key: int, date_key: int, quantity: int) -> bool:
        """
        Deduct inventory for a sale.

        Args:
            product_key: Product identifier
            location_key: Location identifier
            date_key: Date key when sale occurred
            quantity: Quantity sold

        Returns:
            True if deduction successful, False if insufficient inventory
        """
        position = self.positions.get((product_key, location_key))
        if position is None:
            logger.warning(f"Cannot deduct - position not found: product_key={product_key}, location_key={location_key}")
            return False

        success = position.deduct_inventory(quantity)

        if success:
            self.total_sales_processed += 1

            # Check if this created a stockout
            if position.is_stockout():
                position.start_stockout(date_key)

        return success

    def schedule_replenishment(self, product_key: int, location_key: int,
                              return_date_key: int, quantity: int, delay_days: int):
        """
        Schedule inventory replenishment from a return with delay.

        Args:
            product_key: Product identifier
            location_key: Location identifier
            return_date_key: Date key when return occurred
            quantity: Quantity being returned
            delay_days: Number of days delay before replenishment (1-3)
        """
        # Calculate replenishment date
        from datetime import datetime, timedelta
        return_date = datetime.strptime(str(return_date_key), '%Y%m%d')
        replenish_date = return_date + timedelta(days=delay_days)
        replenish_date_key = int(replenish_date.strftime('%Y%m%d'))

        # Schedule the replenishment
        self.pending_replenishments[replenish_date_key].append(
            (product_key, location_key, quantity)
        )

    def _process_pending_replenishments(self, date_key: int):
        """
        Process all pending replenishments for a given date.

        Args:
            date_key: Date key to process replenishments for
        """
        if date_key not in self.pending_replenishments:
            return

        replenishments = self.pending_replenishments[date_key]

        for product_key, location_key, quantity in replenishments:
            position = self.positions.get((product_key, location_key))
            if position is None:
                continue

            # Check if was in stockout before replenishment
            was_stockout = position.is_stockout()

            # Replenish inventory
            position.replenish_inventory(quantity)

            # If this ended a stockout, record it
            if was_stockout and not position.is_stockout():
                position.end_stockout(date_key)

            self.total_returns_processed += 1

        # Clear processed replenishments
        del self.pending_replenishments[date_key]

    def get_inventory_snapshot(self, date_key: int) -> List[dict]:
        """
        Get inventory snapshot for all positions on a specific date.

        Args:
            date_key: Date key for snapshot (YYYYMMDD format)

        Returns:
            List of dictionaries with inventory data for all positions
        """
        # Process any pending replenishments up to this date
        self._process_pending_replenishments(date_key)

        snapshot = []
        for position in self.positions.values():
            position_data = position.to_dict()
            position_data['date_key'] = date_key

            # Calculate stockout duration if in stockout
            if position.stockout_start_date is not None:
                # Convert date keys to dates for calculation
                start_date = datetime.strptime(str(position.stockout_start_date), '%Y%m%d')
                current_date = datetime.strptime(str(date_key), '%Y%m%d')
                duration = (current_date - start_date).days
                position_data['stockout_duration_days'] = duration
            else:
                position_data['stockout_duration_days'] = 0

            snapshot.append(position_data)

        return snapshot

    def get_stockout_rate(self) -> float:
        """
        Calculate current stockout rate across all positions.

        Returns:
            Stockout rate as percentage (0-100)
        """
        if not self.positions:
            return 0.0

        stockout_count = sum(1 for pos in self.positions.values() if pos.is_stockout())
        return (stockout_count / len(self.positions)) * 100.0

    def get_statistics(self) -> dict:
        """
        Get InventoryManager statistics.

        Returns:
            Dictionary with statistics
        """
        stockout_count = sum(1 for pos in self.positions.values() if pos.is_stockout())
        low_inventory_count = sum(
            1 for pos in self.positions.values()
            if 0 < pos.quantity_available <= self.low_inventory_threshold
        )

        return {
            'total_positions': self.total_positions,
            'stockout_positions': stockout_count,
            'stockout_rate_pct': (stockout_count / self.total_positions * 100) if self.total_positions > 0 else 0,
            'low_inventory_positions': low_inventory_count,
            'total_sales_processed': self.total_sales_processed,
            'total_returns_processed': self.total_returns_processed,
            'pending_replenishments': sum(len(v) for v in self.pending_replenishments.values()),
        }

    def log_statistics(self):
        """Log current inventory statistics."""
        stats = self.get_statistics()
        logger.info("=" * 60)
        logger.info("INVENTORY MANAGER STATISTICS")
        logger.info(f"Total Positions: {stats['total_positions']:,}")
        logger.info(f"Stockout Positions: {stats['stockout_positions']:,} ({stats['stockout_rate_pct']:.2f}%)")
        logger.info(f"Low Inventory Positions: {stats['low_inventory_positions']:,}")
        logger.info(f"Sales Processed: {stats['total_sales_processed']:,}")
        logger.info(f"Returns Processed: {stats['total_returns_processed']:,}")
        logger.info(f"Pending Replenishments: {stats['pending_replenishments']:,}")
        logger.info("=" * 60)
