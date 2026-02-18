"""
StockoutGenerator: Generates stockout event records from inventory history

This class analyzes inventory positions to identify and record stockout events.
It creates the gold_stockout_events fact table with detailed stockout analytics
including lost sales estimation and duration tracking.

Key Responsibilities:
- Identify stockout periods from InventoryManager history
- Calculate stockout durations
- Estimate lost sales (attempts, quantity, revenue)
- Flag peak season stockouts
- Generate stockout event records

Design Decisions:
- Post-processing approach (run after all sales/inventory generated)
- Lost sales estimation based on avg daily sales during stockout
- Peak season detection via date_dim calendar attributes
- Auto-incrementing stockout_id

Requirements: FR-013 (stockout events table), FR-014 (lost sales), FR-015 (peak season)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StockoutEvent:
    """
    Represents a single stockout event.

    Attributes:
        stockout_id: Auto-incrementing identifier
        product_key: Product identifier
        location_key: Location identifier
        stockout_start_date_key: Start date (YYYYMMDD)
        stockout_end_date_key: End date (YYYYMMDD)
        stockout_duration_days: Duration in days
        lost_sales_attempts: Estimated number of lost purchase attempts
        lost_sales_quantity: Estimated lost quantity
        lost_sales_revenue: Estimated lost revenue
        peak_season_flag: True if occurred during peak season
    """
    stockout_id: int
    product_key: int
    location_key: int
    stockout_start_date_key: int
    stockout_end_date_key: int
    stockout_duration_days: int
    lost_sales_attempts: int
    lost_sales_quantity: int
    lost_sales_revenue: float
    peak_season_flag: bool


class StockoutGenerator:
    """
    Generates stockout event records from inventory manager history.

    This class performs post-processing analysis of inventory positions to create
    the gold_stockout_events fact table. It identifies stockout periods, calculates
    durations, and estimates lost sales impact.

    Usage:
        generator = StockoutGenerator(spark, config)
        stockout_events = generator.generate_stockout_events(
            inventory_manager=inventory_manager,
            sales_df=sales_fact_df,
            products_df=product_dim_df,
            dates_df=date_dim_df
        )

        # Save to Delta table
        stockout_events_df = spark.createDataFrame(stockout_events)
        stockout_events_df.write.format("delta").mode("overwrite").saveAsTable(
            f"{catalog}.{schema}.gold_stockout_events"
        )
    """

    def __init__(self, spark, config: dict):
        """
        Initialize StockoutGenerator.

        Args:
            spark: SparkSession instance
            config: Configuration dictionary with keys:
                - catalog: Unity Catalog name
                - schema: Schema name
                - peak_season_months: List of peak months (default: [11, 12])
        """
        self.spark = spark
        self.config = config
        self.catalog = config.get('catalog', 'juan_use1_catalog')
        self.schema = config.get('schema', 'retail')
        self.peak_season_months = config.get('peak_season_months', [11, 12])  # Nov, Dec

        # Statistics
        self.total_stockout_events = 0
        self.peak_season_events = 0
        self.total_lost_sales = 0

        logger.info(f"StockoutGenerator initialized for {self.catalog}.{self.schema}")

    def generate_stockout_events(self, inventory_manager, sales_df,
                                 products_df, dates_df) -> List[Dict]:
        """
        Generate stockout events from inventory manager history.

        Args:
            inventory_manager: InventoryManager instance with stockout history
            sales_df: Sales fact DataFrame for lost sales estimation
            products_df: Product dimension DataFrame for revenue calculation
            dates_df: Date dimension DataFrame for peak season detection

        Returns:
            List of dictionaries representing stockout events
        """
        logger.info("Generating stockout events from inventory history...")

        # Collect data needed for calculations
        product_prices = self._get_product_prices(products_df)
        peak_season_dates = self._get_peak_season_dates(dates_df)
        avg_daily_sales = self._calculate_avg_daily_sales(sales_df)

        stockout_events = []
        stockout_id = 1

        # Extract stockout history from all positions
        for (product_key, location_key), position in inventory_manager.positions.items():
            # Process completed stockout periods
            for start_date_key, end_date_key in position.stockout_history:
                event = self._create_stockout_event(
                    stockout_id=stockout_id,
                    product_key=product_key,
                    location_key=location_key,
                    start_date_key=start_date_key,
                    end_date_key=end_date_key,
                    product_prices=product_prices,
                    peak_season_dates=peak_season_dates,
                    avg_daily_sales=avg_daily_sales
                )

                stockout_events.append(event)
                stockout_id += 1
                self.total_stockout_events += 1

                if event['peak_season_flag']:
                    self.peak_season_events += 1

                self.total_lost_sales += event['lost_sales_attempts']

            # Also process ongoing stockouts (if any)
            if position.stockout_start_date is not None:
                # Use current date as end date (or last date in dataset)
                # For now, we'll skip ongoing stockouts as they're incomplete
                pass

        logger.info(
            f"Generated {len(stockout_events)} stockout events "
            f"({self.peak_season_events} during peak season)"
        )

        return stockout_events

    def _create_stockout_event(self, stockout_id: int, product_key: int,
                              location_key: int, start_date_key: int,
                              end_date_key: int, product_prices: Dict[int, float],
                              peak_season_dates: set, avg_daily_sales: Dict) -> Dict:
        """
        Create a single stockout event record.

        Args:
            stockout_id: Unique identifier
            product_key: Product identifier
            location_key: Location identifier
            start_date_key: Stockout start date
            end_date_key: Stockout end date
            product_prices: Map of product_key to price
            peak_season_dates: Set of date_keys in peak season
            avg_daily_sales: Average daily sales by product-location

        Returns:
            Dictionary representing stockout event
        """
        # Calculate duration
        from datetime import timedelta
        start_date = datetime.strptime(str(start_date_key), '%Y%m%d')
        end_date = datetime.strptime(str(end_date_key), '%Y%m%d')
        duration_days = (end_date - start_date).days + 1  # Inclusive

        # Determine if peak season - check if any day in the stockout period is in peak season
        is_peak_season = False
        current_date = start_date
        for i in range(duration_days):
            date_to_check = current_date + timedelta(days=i)
            date_key_to_check = int(date_to_check.strftime('%Y%m%d'))
            if date_key_to_check in peak_season_dates:
                is_peak_season = True
                break

        # Estimate lost sales
        key = (product_key, location_key)
        if key in avg_daily_sales:
            avg_sales_data = avg_daily_sales[key]
            avg_attempts_per_day = avg_sales_data.get('attempts', 2.0)
            avg_qty_per_day = avg_sales_data.get('quantity', 2.5)
        else:
            avg_attempts_per_day = 2.0  # Default 2 attempts/day
            avg_qty_per_day = 2.5  # Default 2.5 units/day

        # Lost sales estimation
        lost_sales_attempts = int(avg_attempts_per_day * duration_days)
        lost_sales_quantity = int(avg_qty_per_day * duration_days)

        # Revenue estimation
        if product_key in product_prices:
            product_price = product_prices[product_key]
        else:
            product_price = 50.0  # Default $50
        lost_sales_revenue = lost_sales_quantity * product_price

        # Increase estimates during peak season (1.5x multiplier)
        if is_peak_season:
            lost_sales_attempts = int(lost_sales_attempts * 1.5)
            lost_sales_quantity = int(lost_sales_quantity * 1.5)
            lost_sales_revenue = lost_sales_revenue * 1.5

        return {
            'stockout_id': stockout_id,
            'product_key': product_key,
            'location_key': location_key,
            'stockout_start_date_key': start_date_key,
            'stockout_end_date_key': end_date_key,
            'stockout_duration_days': duration_days,
            'lost_sales_attempts': lost_sales_attempts,
            'lost_sales_quantity': lost_sales_quantity,
            'lost_sales_revenue': round(lost_sales_revenue, 2),
            'peak_season_flag': is_peak_season,
            'source_system': 'synthetic_data_generator',
            'etl_timestamp': datetime.now()
        }

    def _get_product_prices(self, products_df) -> Dict[int, float]:
        """
        Extract product prices for revenue calculation.

        Args:
            products_df: Product dimension DataFrame

        Returns:
            Dictionary mapping product_key to base_price
        """
        prices = {}
        products = products_df.select('product_key', 'base_price').collect()

        for row in products:
            prices[row['product_key']] = float(row['base_price'])

        logger.info(f"Extracted prices for {len(prices)} products")
        return prices

    def _get_peak_season_dates(self, dates_df) -> set:
        """
        Identify peak season dates.

        Args:
            dates_df: Date dimension DataFrame

        Returns:
            Set of date_keys in peak season
        """
        # Filter for peak season months (typically Nov, Dec for fashion retail)
        # Use column() method to avoid attribute access issues
        from pyspark.sql.functions import col
        peak_dates_df = dates_df.filter(
            col('month').isin(self.peak_season_months)
        )

        peak_dates = set()
        for row in peak_dates_df.select('date_key').collect():
            peak_dates.add(row['date_key'])

        logger.info(
            f"Identified {len(peak_dates)} peak season dates "
            f"(months: {self.peak_season_months})"
        )
        return peak_dates

    def _calculate_avg_daily_sales(self, sales_df) -> Dict[Tuple[int, int], Dict]:
        """
        Calculate average daily sales by product-location for lost sales estimation.

        Args:
            sales_df: Sales fact DataFrame

        Returns:
            Dictionary mapping (product_key, location_key) to avg sales metrics
        """
        logger.info("Calculating average daily sales for lost sales estimation...")

        # Aggregate sales by product-location-date
        from pyspark.sql import functions as F

        daily_sales = sales_df.groupBy(
            'product_key', 'location_key', 'date_key'
        ).agg(
            F.count('transaction_id').alias('attempts'),
            F.sum('quantity_sold').alias('quantity')
        )

        # Calculate averages by product-location
        avg_sales = daily_sales.groupBy('product_key', 'location_key').agg(
            F.avg('attempts').alias('avg_attempts'),
            F.avg('quantity').alias('avg_quantity')
        ).collect()

        # Convert to dictionary
        avg_daily_sales = {}
        for row in avg_sales:
            key = (row['product_key'], row['location_key'])
            avg_daily_sales[key] = {
                'attempts': float(row['avg_attempts']) if row['avg_attempts'] else 2.0,
                'quantity': float(row['avg_quantity']) if row['avg_quantity'] else 2.5
            }

        logger.info(f"Calculated avg daily sales for {len(avg_daily_sales)} product-location pairs")
        return avg_daily_sales

    def create_stockout_events_table(self, stockout_events: List[Dict]):
        """
        Create gold_stockout_events Delta table.

        Args:
            stockout_events: List of stockout event dictionaries
        """
        from pyspark.sql.types import (
            StructType, StructField, LongType, IntegerType,
            DoubleType, BooleanType, StringType, TimestampType
        )

        logger.info(f"Creating gold_stockout_events table with {len(stockout_events)} events...")

        # Define schema
        schema = StructType([
            StructField('stockout_id', LongType(), False),
            StructField('product_key', IntegerType(), False),
            StructField('location_key', IntegerType(), False),
            StructField('stockout_start_date_key', IntegerType(), False),
            StructField('stockout_end_date_key', IntegerType(), False),
            StructField('stockout_duration_days', IntegerType(), False),
            StructField('lost_sales_attempts', IntegerType(), False),
            StructField('lost_sales_quantity', IntegerType(), False),
            StructField('lost_sales_revenue', DoubleType(), False),
            StructField('peak_season_flag', BooleanType(), False),
            StructField('source_system', StringType(), False),
            StructField('etl_timestamp', TimestampType(), False)
        ])

        # Create DataFrame
        if stockout_events:
            stockout_df = self.spark.createDataFrame(stockout_events, schema=schema)
        else:
            # Create empty DataFrame with schema
            stockout_df = self.spark.createDataFrame([], schema=schema)

        # Write to Delta table
        table_name = f"{self.catalog}.{self.schema}.gold_stockout_events"

        stockout_df.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)

        logger.info(f"Created table: {table_name}")

        # Compute statistics
        self.spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS")

    def get_statistics(self) -> dict:
        """
        Get StockoutGenerator statistics.

        Returns:
            Dictionary with statistics
        """
        peak_season_pct = (
            (self.peak_season_events / self.total_stockout_events * 100)
            if self.total_stockout_events > 0 else 0
        )

        return {
            'total_stockout_events': self.total_stockout_events,
            'peak_season_events': self.peak_season_events,
            'peak_season_pct': peak_season_pct,
            'total_lost_sales_attempts': self.total_lost_sales,
        }

    def log_statistics(self):
        """Log stockout generation statistics."""
        stats = self.get_statistics()
        logger.info("=" * 60)
        logger.info("STOCKOUT GENERATOR STATISTICS")
        logger.info(f"Total Stockout Events: {stats['total_stockout_events']:,}")
        logger.info(f"Peak Season Events: {stats['peak_season_events']:,} ({stats['peak_season_pct']:.2f}%)")
        logger.info(f"Total Lost Sales Attempts: {stats['total_lost_sales_attempts']:,}")
        logger.info("=" * 60)


class StockoutAnalyzer:
    """
    Helper class for analyzing stockout patterns and generating insights.

    Usage:
        analyzer = StockoutAnalyzer(spark, catalog, schema)
        insights = analyzer.analyze_stockout_patterns()
    """

    def __init__(self, spark, catalog: str, schema: str):
        """
        Initialize StockoutAnalyzer.

        Args:
            spark: SparkSession instance
            catalog: Unity Catalog name
            schema: Schema name
        """
        self.spark = spark
        self.catalog = catalog
        self.schema = schema

    def analyze_stockout_patterns(self) -> Dict:
        """
        Analyze stockout patterns from gold_stockout_events table.

        Returns:
            Dictionary with analysis results
        """
        from pyspark.sql import functions as F

        table_name = f"{self.catalog}.{self.schema}.gold_stockout_events"

        # Load stockout events
        stockout_df = self.spark.table(table_name)

        # Calculate key metrics
        total_events = stockout_df.count()

        avg_duration = stockout_df.select(
            F.avg('stockout_duration_days').alias('avg_duration')
        ).collect()[0]['avg_duration']

        total_lost_revenue = stockout_df.select(
            F.sum('lost_sales_revenue').alias('total_lost_revenue')
        ).collect()[0]['total_lost_revenue']

        peak_season_events = stockout_df.filter(
            F.col('peak_season_flag') == True
        ).count()

        # Top products with stockouts
        top_products = stockout_df.groupBy('product_key').agg(
            F.count('stockout_id').alias('stockout_count'),
            F.sum('lost_sales_revenue').alias('total_lost_revenue')
        ).orderBy(F.desc('stockout_count')).limit(10).collect()

        return {
            'total_events': total_events,
            'avg_duration_days': avg_duration,
            'total_lost_revenue': total_lost_revenue,
            'peak_season_events': peak_season_events,
            'top_products': [
                {'product_key': row['product_key'],
                 'stockout_count': row['stockout_count'],
                 'lost_revenue': row['total_lost_revenue']}
                for row in top_products
            ]
        }

    def log_analysis(self):
        """Analyze and log stockout patterns."""
        analysis = self.analyze_stockout_patterns()

        logger.info("=" * 60)
        logger.info("STOCKOUT PATTERN ANALYSIS")
        logger.info(f"Total Events: {analysis['total_events']:,}")
        logger.info(f"Avg Duration: {analysis['avg_duration_days']:.1f} days")
        logger.info(f"Total Lost Revenue: ${analysis['total_lost_revenue']:,.2f}")
        logger.info(f"Peak Season Events: {analysis['peak_season_events']:,}")
        logger.info("\nTop 10 Products by Stockout Frequency:")
        for i, product in enumerate(analysis['top_products'], 1):
            logger.info(
                f"  {i}. Product {product['product_key']}: "
                f"{product['stockout_count']} stockouts, "
                f"${product['lost_revenue']:,.2f} lost revenue"
            )
        logger.info("=" * 60)
