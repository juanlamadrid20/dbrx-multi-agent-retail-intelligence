"""
Table Cleanup Utilities for Fashion Retail Data Generation

This module provides utilities for cleaning up tables created by the Fashion Retail
data generation pipeline. It includes functionality to list, drop, and manage
the lifecycle of generated tables.
"""

import logging
from typing import List, Dict, Optional, Union
from pyspark.sql import SparkSession
from .config import FashionRetailConfig

logger = logging.getLogger(__name__)


class TableCleanup:
    """Utility class for managing Fashion Retail table cleanup operations."""
    
    def __init__(self, spark: SparkSession, config: Union[FashionRetailConfig, Dict]):
        self.spark = spark
        
        # Handle both config objects and dictionaries for backward compatibility
        if isinstance(config, dict):
            self.catalog = config['catalog']
            self.schema = config['schema']
        else:
            self.catalog = config.catalog
            self.schema = config.schema
            
        self.full_schema = f"{self.catalog}.{self.schema}"
        
        # Define all Fashion Retail tables that can be created
        self.fashion_retail_tables = [
            # Dimension tables
            'gold_customer_dim',
            'gold_product_dim', 
            'gold_location_dim',
            'gold_date_dim',
            'gold_channel_dim',
            'gold_time_dim',
            
            # Fact tables
            'gold_sales_fact',
            'gold_inventory_fact',
            'gold_customer_event_fact',
            'gold_cart_abandonment_fact',
            'gold_demand_forecast_fact',
            'gold_stockout_events',
            
            # Bridge/Aggregate tables
            'gold_customer_product_affinity_agg',
            'gold_size_fit_bridge',
            'gold_inventory_movement_fact',
            
            # Utility tables
            'sample_queries'
        ]
    
    def list_tables(self, show_details: bool = True) -> List[Dict]:
        """
        List all Fashion Retail tables in the schema.
        
        Args:
            show_details: If True, includes row counts and size information
            
        Returns:
            List of dictionaries with table information
        """
        logger.info(f"Listing tables in schema: {self.full_schema}")
        
        try:
            # Get all tables in the schema
            all_tables = self.spark.sql(f"""
                SHOW TABLES IN {self.full_schema}
            """).collect()
            
            fashion_tables = []
            
            for row in all_tables:
                table_name = row['tableName']
                
                # Only include Fashion Retail tables
                if table_name in self.fashion_retail_tables:
                    table_info = {
                        'table_name': table_name,
                        'full_name': f"{self.full_schema}.{table_name}",
                        'exists': True
                    }
                    
                    if show_details:
                        try:
                            # Get row count
                            count_result = self.spark.sql(f"""
                                SELECT COUNT(*) as row_count 
                                FROM {self.full_schema}.{table_name}
                            """).collect()
                            table_info['row_count'] = count_result[0]['row_count']
                            
                            # Get table details
                            details = self.spark.sql(f"""
                                DESCRIBE DETAIL {self.full_schema}.{table_name}
                            """).collect()
                            
                            if details:
                                detail = details[0]
                                table_info['size_in_bytes'] = detail.get('sizeInBytes', 0)
                                table_info['num_files'] = detail.get('numFiles', 0)
                                table_info['created_at'] = detail.get('createdAt')
                                table_info['last_modified'] = detail.get('lastModified')
                                
                        except Exception as e:
                            logger.warning(f"Could not get details for {table_name}: {str(e)}")
                            table_info['row_count'] = 'Unknown'
                            table_info['size_in_bytes'] = 'Unknown'
                    
                    fashion_tables.append(table_info)
            
            logger.info(f"Found {len(fashion_tables)} Fashion Retail tables")
            return fashion_tables
            
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            return []
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a specific table exists."""
        try:
            self.spark.sql(f"DESCRIBE TABLE {self.full_schema}.{table_name}")
            return True
        except Exception:
            return False
    
    def get_table_dependencies(self) -> Dict[str, List[str]]:
        """
        Get table dependencies to determine safe drop order.
        
        Returns:
            Dictionary mapping table names to their dependencies
        """
        # Define dependencies (tables that depend on others)
        dependencies = {
            # Facts depend on dimensions
            'gold_sales_fact': ['gold_customer_dim', 'gold_product_dim', 'gold_location_dim', 'gold_date_dim', 'gold_channel_dim', 'gold_time_dim'],
            'gold_inventory_fact': ['gold_product_dim', 'gold_location_dim', 'gold_date_dim'],
            'gold_customer_event_fact': ['gold_customer_dim', 'gold_product_dim', 'gold_date_dim', 'gold_channel_dim', 'gold_time_dim'],
            'gold_cart_abandonment_fact': ['gold_customer_dim', 'gold_product_dim', 'gold_date_dim', 'gold_channel_dim'],
            'gold_demand_forecast_fact': ['gold_product_dim', 'gold_location_dim', 'gold_date_dim'],
            'gold_stockout_events': ['gold_product_dim', 'gold_location_dim', 'gold_date_dim'],
            
            # Aggregates depend on facts and dimensions
            'gold_customer_product_affinity_agg': ['gold_sales_fact', 'gold_customer_event_fact'],
            'gold_size_fit_bridge': ['gold_sales_fact'],
            'gold_inventory_movement_fact': ['gold_inventory_fact'],
        }
        
        return dependencies
    
    def get_drop_order(self, tables_to_drop: List[str]) -> List[str]:
        """
        Determine the safe order to drop tables based on dependencies.
        
        Args:
            tables_to_drop: List of table names to drop
            
        Returns:
            List of tables in safe drop order (dependents first)
        """
        dependencies = self.get_table_dependencies()
        
        # Start with tables that have dependencies (drop them first)
        ordered_tables = []
        remaining_tables = tables_to_drop.copy()
        
        # First, add tables that are dependencies of others (in reverse dependency order)
        for table in tables_to_drop:
            if table in dependencies:
                if table not in ordered_tables:
                    ordered_tables.append(table)
                    remaining_tables.remove(table)
        
        # Then add remaining tables (dimensions, etc.)
        ordered_tables.extend(remaining_tables)
        
        return ordered_tables
    
    def drop_tables(self, table_names: List[str], confirm: bool = False) -> Dict[str, bool]:
        """
        Drop specific tables.
        
        Args:
            table_names: List of table names to drop
            confirm: If True, skip confirmation prompt
            
        Returns:
            Dictionary mapping table names to success status
        """
        if not table_names:
            logger.warning("No tables specified for deletion")
            return {}
        
        # Filter to only include Fashion Retail tables
        valid_tables = [t for t in table_names if t in self.fashion_retail_tables]
        invalid_tables = [t for t in table_names if t not in self.fashion_retail_tables]
        
        if invalid_tables:
            logger.warning(f"Ignoring non-Fashion Retail tables: {invalid_tables}")
        
        if not valid_tables:
            logger.warning("No valid Fashion Retail tables to drop")
            return {}
        
        # Check which tables actually exist
        existing_tables = [t for t in valid_tables if self.table_exists(t)]
        missing_tables = [t for t in valid_tables if not self.table_exists(t)]
        
        if missing_tables:
            logger.info(f"Tables already missing: {missing_tables}")
        
        if not existing_tables:
            logger.info("No existing tables to drop")
            return {t: True for t in missing_tables}  # Consider missing tables as "successfully dropped"
        
        logger.info(f"Planning to drop {len(existing_tables)} tables: {existing_tables}")
        
        if not confirm:
            logger.warning("This operation will permanently delete tables. Use confirm=True to proceed.")
            return {}
        
        # Get safe drop order
        drop_order = self.get_drop_order(existing_tables)
        logger.info(f"Drop order: {drop_order}")
        
        results = {}
        
        for table_name in drop_order:
            try:
                logger.info(f"Dropping table: {table_name}")
                self.spark.sql(f"DROP TABLE IF EXISTS {self.full_schema}.{table_name}")
                results[table_name] = True
                logger.info(f"✅ Successfully dropped: {table_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to drop {table_name}: {str(e)}")
                results[table_name] = False
        
        return results
    
    def drop_all_tables(self, confirm: bool = False) -> Dict[str, bool]:
        """
        Drop all Fashion Retail tables.
        
        Args:
            confirm: If True, skip confirmation prompt
            
        Returns:
            Dictionary mapping table names to success status
        """
        logger.info("Planning to drop ALL Fashion Retail tables")
        
        # Get existing tables
        existing_tables = [t for t in self.fashion_retail_tables if self.table_exists(t)]
        
        if not existing_tables:
            logger.info("No Fashion Retail tables found to drop")
            return {}
        
        logger.warning(f"This will drop {len(existing_tables)} tables: {existing_tables}")
        
        return self.drop_tables(existing_tables, confirm=confirm)
    
    def backup_tables(self, table_names: Optional[List[str]] = None, backup_suffix: str = "_backup") -> Dict[str, bool]:
        """
        Create backup copies of tables before deletion.
        
        Args:
            table_names: List of table names to backup (None for all existing tables)
            backup_suffix: Suffix to add to backup table names
            
        Returns:
            Dictionary mapping table names to backup success status
        """
        if table_names is None:
            # Backup all existing Fashion Retail tables
            table_names = [t for t in self.fashion_retail_tables if self.table_exists(t)]
        
        if not table_names:
            logger.info("No tables to backup")
            return {}
        
        logger.info(f"Creating backups for {len(table_names)} tables")
        
        results = {}
        
        for table_name in table_names:
            if not self.table_exists(table_name):
                logger.warning(f"Table {table_name} does not exist, skipping backup")
                results[table_name] = False
                continue
            
            backup_name = f"{table_name}{backup_suffix}"
            
            try:
                logger.info(f"Creating backup: {table_name} -> {backup_name}")
                
                # Create backup table
                self.spark.sql(f"""
                    CREATE OR REPLACE TABLE {self.full_schema}.{backup_name}
                    AS SELECT * FROM {self.full_schema}.{table_name}
                """)
                
                results[table_name] = True
                logger.info(f"✅ Backup created: {backup_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to backup {table_name}: {str(e)}")
                results[table_name] = False
        
        return results
    
    def get_schema_summary(self) -> Dict:
        """Get a summary of the schema and its tables."""
        tables = self.list_tables(show_details=True)
        
        summary = {
            'schema': self.full_schema,
            'total_tables': len(tables),
            'total_rows': sum(t.get('row_count', 0) for t in tables if isinstance(t.get('row_count'), int)),
            'total_size_bytes': sum(t.get('size_in_bytes', 0) for t in tables if isinstance(t.get('size_in_bytes'), int)),
            'tables': tables
        }
        
        return summary
