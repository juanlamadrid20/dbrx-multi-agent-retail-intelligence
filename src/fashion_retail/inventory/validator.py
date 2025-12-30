"""
SalesValidator: Validates and allocates inventory for sales transactions

This class works with InventoryManager to ensure all sales transactions are
constrained by available inventory. It implements random allocation when multiple
customers compete for limited inventory.

Key Responsibilities:
- Validate purchase requests against available inventory
- Allocate limited inventory randomly among competing purchases
- Track inventory-constrained transactions
- Calculate inventory snapshots at time of purchase

Design Decisions:
- Random allocation via shuffle for fairness
- Batch processing for performance (50K record batches)
- Tracks both requested and allocated quantities
- Returns detailed allocation results for analytics

Requirements: FR-001 (inventory constraints), FR-002 (random allocation), 
              FR-003 (real-time deduction), FR-004 (quantity_requested tracking)
"""

import random
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import logging

from .manager import InventoryManager

logger = logging.getLogger(__name__)


@dataclass
class PurchaseRequest:
    """
    Represents a purchase request from a customer.

    Attributes:
        request_id: Unique identifier (e.g., transaction_id)
        product_key: Product being purchased
        location_key: Location of purchase
        date_key: Date of purchase (YYYYMMDD)
        requested_quantity: Quantity customer wants to buy
        customer_key: Customer making the purchase
        priority: Optional priority for allocation (default 0)
    """
    request_id: str
    product_key: int
    location_key: int
    date_key: int
    requested_quantity: int
    customer_key: int
    priority: int = 0


@dataclass
class AllocationResult:
    """
    Result of inventory allocation for a purchase request.

    Attributes:
        request_id: Unique identifier matching PurchaseRequest
        requested_quantity: Original quantity requested
        allocated_quantity: Actual quantity allocated (may be less)
        is_inventory_constrained: True if allocated < requested
        inventory_at_purchase: Inventory snapshot before allocation
        allocation_success: True if any inventory was allocated
    """
    request_id: str
    requested_quantity: int
    allocated_quantity: int
    is_inventory_constrained: bool
    inventory_at_purchase: int
    allocation_success: bool


class SalesValidator:
    """
    Validates sales transactions against inventory and allocates limited inventory.

    This class is the bridge between sales generation and inventory management.
    It ensures that the synthetic data generation respects inventory constraints
    while maintaining realistic customer behavior patterns.
    
    Thread Safety:
        NOT thread-safe. Uses instance-level random generator and mutable statistics.
        Create separate instances for parallel processing with different seeds.

    Usage:
        validator = SalesValidator(inventory_manager, config)

        # Single purchase validation:
        result = validator.validate_purchase(
            product_key=123, location_key=1, date_key=20250101,
            requested_qty=2, customer_key=456
        )
        if result.allocation_success:
            # Create sale record with result.allocated_quantity
            pass

        # Batch allocation (recommended for performance):
        requests = [PurchaseRequest(...), ...]
        results = validator.allocate_batch(requests)
    """

    def __init__(self, inventory_manager: 'InventoryManager', config: dict):
        """
        Initialize SalesValidator.

        Args:
            inventory_manager: InventoryManager instance
            config: Configuration dictionary with keys:
                - random_seed: Random seed for reproducibility
                - allocation_strategy: 'random' or 'priority' (default: 'random')
        """
        self.inventory_manager = inventory_manager
        self.config = config
        self.random_seed = config.get('random_seed', 42)
        self.allocation_strategy = config.get('allocation_strategy', 'random')

        # Statistics
        self.total_requests = 0
        self.constrained_requests = 0
        self.failed_requests = 0

        # Use instance-level random generator for reproducibility
        self._rng = random.Random(self.random_seed)

        logger.info(f"SalesValidator initialized with allocation_strategy={self.allocation_strategy}")

    def validate_purchase(self, product_key: int, location_key: int, date_key: int,
                         requested_qty: int, customer_key: int) -> AllocationResult:
        """
        Validate and allocate inventory for a single purchase request.

        This is a simplified version for single-request validation.
        For better performance with multiple concurrent requests, use allocate_batch().

        Args:
            product_key: Product being purchased
            location_key: Location of purchase
            date_key: Date of purchase (YYYYMMDD)
            requested_qty: Quantity requested
            customer_key: Customer making purchase

        Returns:
            AllocationResult with allocation details
        """
        self.total_requests += 1

        # Get current inventory
        available = self.inventory_manager.get_available_quantity(
            product_key, location_key, date_key
        )

        # Determine allocation
        if available == 0:
            # Complete stockout - no allocation
            self.failed_requests += 1
            return AllocationResult(
                request_id=f"{customer_key}_{product_key}_{date_key}",
                requested_quantity=requested_qty,
                allocated_quantity=0,
                is_inventory_constrained=True,
                inventory_at_purchase=0,
                allocation_success=False
            )

        # Allocate available inventory (may be partial)
        allocated = min(requested_qty, available)
        is_constrained = allocated < requested_qty

        if is_constrained:
            self.constrained_requests += 1

        # Deduct from inventory
        success = self.inventory_manager.deduct_inventory(
            product_key, location_key, date_key, allocated
        )

        if not success:
            logger.warning(
                f"Inventory deduction failed: product_key={product_key}, "
                f"location_key={location_key}, date_key={date_key}, qty={allocated}"
            )
            self.failed_requests += 1

        return AllocationResult(
            request_id=f"{customer_key}_{product_key}_{date_key}",
            requested_quantity=requested_qty,
            allocated_quantity=allocated if success else 0,
            is_inventory_constrained=is_constrained,
            inventory_at_purchase=available,
            allocation_success=success
        )

    def allocate_batch(self, requests: List[PurchaseRequest]) -> Dict[str, AllocationResult]:
        """
        Allocate inventory for a batch of purchase requests.

        This method handles competing requests for the same inventory position
        by randomly shuffling requests (fair allocation) or using priority-based
        allocation if configured.

        This is the RECOMMENDED method for sales generation as it properly handles
        concurrent requests for limited inventory.

        Args:
            requests: List of PurchaseRequest objects

        Returns:
            Dictionary mapping request_id to AllocationResult
        """
        logger.info(f"Processing batch of {len(requests)} purchase requests...")

        # Group requests by (product_key, location_key, date_key)
        grouped_requests: Dict[Tuple[int, int, int], List[PurchaseRequest]] = {}
        for request in requests:
            key = (request.product_key, request.location_key, request.date_key)
            if key not in grouped_requests:
                grouped_requests[key] = []
            grouped_requests[key].append(request)

        # Allocate for each group
        results = {}

        for (product_key, location_key, date_key), group_requests in grouped_requests.items():
            # Get available inventory for this position
            available = self.inventory_manager.get_available_quantity(
                product_key, location_key, date_key
            )

            # Randomize order for fair allocation
            if self.allocation_strategy == 'random':
                self._rng.shuffle(group_requests)
            elif self.allocation_strategy == 'priority':
                # Sort by priority (higher priority first)
                group_requests.sort(key=lambda r: r.priority, reverse=True)

            # Allocate inventory in order
            remaining_inventory = available

            for request in group_requests:
                self.total_requests += 1

                if remaining_inventory == 0:
                    # No inventory left - complete stockout
                    self.failed_requests += 1
                    results[request.request_id] = AllocationResult(
                        request_id=request.request_id,
                        requested_quantity=request.requested_quantity,
                        allocated_quantity=0,
                        is_inventory_constrained=True,
                        inventory_at_purchase=available,  # Snapshot at start
                        allocation_success=False
                    )
                    continue

                # Allocate what we can
                allocated = min(request.requested_quantity, remaining_inventory)
                is_constrained = allocated < request.requested_quantity

                if is_constrained:
                    self.constrained_requests += 1

                # Deduct from inventory manager
                success = self.inventory_manager.deduct_inventory(
                    product_key, location_key, date_key, allocated
                )

                if success:
                    remaining_inventory -= allocated

                results[request.request_id] = AllocationResult(
                    request_id=request.request_id,
                    requested_quantity=request.requested_quantity,
                    allocated_quantity=allocated if success else 0,
                    is_inventory_constrained=is_constrained,
                    inventory_at_purchase=available,  # Snapshot at start
                    allocation_success=success
                )

                if not success:
                    self.failed_requests += 1

        logger.info(
            f"Batch allocation complete: {len(results)} results, "
            f"{self.constrained_requests} constrained, {self.failed_requests} failed"
        )

        return results

    def check_inventory_availability(self, product_key: int, location_key: int,
                                    date_key: int, requested_qty: int) -> Tuple[bool, int]:
        """
        Check if requested quantity is available without allocating.

        Useful for cart abandonment logic and customer event generation.

        Args:
            product_key: Product identifier
            location_key: Location identifier
            date_key: Date key (YYYYMMDD)
            requested_qty: Quantity to check

        Returns:
            Tuple of (is_available, available_quantity)
                is_available: True if requested_qty <= available_quantity
                available_quantity: Current available quantity
        """
        available = self.inventory_manager.get_available_quantity(
            product_key, location_key, date_key
        )

        is_available = available >= requested_qty
        return is_available, available

    def is_low_inventory(self, product_key: int, location_key: int, date_key: int) -> bool:
        """
        Check if inventory is below low threshold.

        Used for cart abandonment logic (triggers +10pp abandonment rate).

        Args:
            product_key: Product identifier
            location_key: Location identifier
            date_key: Date key (YYYYMMDD)

        Returns:
            True if inventory is at or below low_inventory_threshold
        """
        return self.inventory_manager.is_low_inventory(product_key, location_key, date_key)

    def get_statistics(self) -> dict:
        """
        Get SalesValidator statistics.

        Returns:
            Dictionary with statistics
        """
        constraint_rate = (
            (self.constrained_requests / self.total_requests * 100)
            if self.total_requests > 0 else 0
        )
        failure_rate = (
            (self.failed_requests / self.total_requests * 100)
            if self.total_requests > 0 else 0
        )

        return {
            'total_requests': self.total_requests,
            'constrained_requests': self.constrained_requests,
            'failed_requests': self.failed_requests,
            'constraint_rate_pct': constraint_rate,
            'failure_rate_pct': failure_rate,
        }

    def log_statistics(self):
        """Log current sales validation statistics."""
        stats = self.get_statistics()
        logger.info("=" * 60)
        logger.info("SALES VALIDATOR STATISTICS")
        logger.info(f"Total Purchase Requests: {stats['total_requests']:,}")
        logger.info(f"Inventory-Constrained Requests: {stats['constrained_requests']:,} ({stats['constraint_rate_pct']:.2f}%)")
        logger.info(f"Failed Requests (Stockout): {stats['failed_requests']:,} ({stats['failure_rate_pct']:.2f}%)")
        logger.info("=" * 60)

    def reset_statistics(self):
        """Reset statistics counters."""
        self.total_requests = 0
        self.constrained_requests = 0
        self.failed_requests = 0


class BatchPurchaseBuilder:
    """
    Helper class to build batches of purchase requests for efficient allocation.

    Usage:
        builder = BatchPurchaseBuilder(batch_size=50000)

        for sale in sales_to_generate:
            builder.add_request(
                product_key=sale['product_key'],
                location_key=sale['location_key'],
                date_key=sale['date_key'],
                requested_qty=random.choice([1, 2, 3]),
                customer_key=sale['customer_key']
            )

            if builder.is_batch_full():
                results = validator.allocate_batch(builder.get_batch())
                builder.clear()

        # Process remaining
        if builder.has_requests():
            results = validator.allocate_batch(builder.get_batch())
    """

    def __init__(self, batch_size: int = 50000):
        """
        Initialize BatchPurchaseBuilder.

        Args:
            batch_size: Maximum requests per batch (default: 50000)
        """
        self.batch_size = batch_size
        self.requests: List[PurchaseRequest] = []
        self.request_counter = 0

    def add_request(self, product_key: int, location_key: int, date_key: int,
                   requested_qty: int, customer_key: int, priority: int = 0) -> str:
        """
        Add a purchase request to the batch.

        Args:
            product_key: Product identifier
            location_key: Location identifier
            date_key: Date key (YYYYMMDD)
            requested_qty: Quantity requested
            customer_key: Customer identifier
            priority: Optional priority (default: 0)

        Returns:
            request_id for tracking the result
        """
        self.request_counter += 1
        request_id = f"req_{self.request_counter}_{customer_key}_{product_key}"

        request = PurchaseRequest(
            request_id=request_id,
            product_key=product_key,
            location_key=location_key,
            date_key=date_key,
            requested_quantity=requested_qty,
            customer_key=customer_key,
            priority=priority
        )

        self.requests.append(request)
        return request_id

    def is_batch_full(self) -> bool:
        """Check if batch has reached capacity."""
        return len(self.requests) >= self.batch_size

    def has_requests(self) -> bool:
        """Check if there are any requests in the batch."""
        return len(self.requests) > 0

    def get_batch(self) -> List[PurchaseRequest]:
        """Get current batch of requests."""
        return self.requests.copy()

    def clear(self):
        """Clear the current batch."""
        self.requests = []

    def get_batch_size(self) -> int:
        """Get current number of requests in batch."""
        return len(self.requests)
