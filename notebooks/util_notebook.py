# Databricks notebook source
# MAGIC %md
# MAGIC # Fashion Retail - Table Cleanup Utilities
# MAGIC
# MAGIC This notebook provides utilities for managing and cleaning up tables created by the Fashion Retail data generation pipeline.
# MAGIC
# MAGIC ## Features:
# MAGIC - ✅ List all Fashion Retail tables with details
# MAGIC - ✅ Drop specific tables safely (respects dependencies)
# MAGIC - ✅ Drop all tables with confirmation
# MAGIC - ✅ Create backups before deletion
# MAGIC - ✅ Show schema summary and statistics
# MAGIC
# MAGIC ## Safety Features:
# MAGIC - 🛡️ Only operates on Fashion Retail tables (prevents accidental deletion of other tables)
# MAGIC - 🛡️ Respects table dependencies (drops in correct order)
# MAGIC - 🛡️ Requires explicit confirmation for destructive operations
# MAGIC - 🛡️ Provides detailed logging and status reporting

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Import Fashion Retail Package

# COMMAND ----------

import sys
import os

# Add the src directory to Python path for clean imports
sys.path.append('../src')

# Import the cleanup utilities and configuration
from fashion_retail.cleanup import TableCleanup
from fashion_retail.config import get_config, get_small_config

print("✅ Fashion Retail cleanup utilities imported successfully!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration Setup

# COMMAND ----------

# Choose your configuration - this determines which schema to operate on
config = get_config()  # Default: juan_dev.retail

# Alternative configurations:
# config = get_small_config()  # For testing environments
# config = get_config(catalog="your_catalog", schema="your_schema")  # Custom

print(f"🎯 Target Schema: {config.catalog}.{config.schema}")
print(f"📊 Configuration: {config.customers:,} customers, {config.products:,} products")

# Initialize the cleanup utility
cleanup = TableCleanup(spark, config)

print("✅ Cleanup utility initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 List All Fashion Retail Tables
# MAGIC
# MAGIC This cell shows all Fashion Retail tables in the target schema with detailed information.

# COMMAND ----------

# Get detailed information about all Fashion Retail tables
tables = cleanup.list_tables(show_details=True)

if not tables:
    print("ℹ️  No Fashion Retail tables found in the schema")
else:
    print(f"📊 Found {len(tables)} Fashion Retail tables:")
    print("=" * 80)
    
    # Display table information
    import pandas as pd
    
    # Create a summary DataFrame for better display
    table_data = []
    for table in tables:
        table_data.append({
            'Table Name': table['table_name'],
            'Row Count': f"{table.get('row_count', 'Unknown'):,}" if isinstance(table.get('row_count'), int) else table.get('row_count', 'Unknown'),
            'Size (MB)': f"{table.get('size_in_bytes', 0) / (1024*1024):.2f}" if isinstance(table.get('size_in_bytes'), int) else 'Unknown',
            'Files': table.get('num_files', 'Unknown'),
            'Last Modified': str(table.get('last_modified', 'Unknown'))[:19] if table.get('last_modified') else 'Unknown'
        })
    
    df_tables = pd.DataFrame(table_data)
    display(df_tables)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Schema Summary
# MAGIC
# MAGIC Get an overview of the entire schema including totals and statistics.

# COMMAND ----------

# Get schema summary
summary = cleanup.get_schema_summary()

print(f"📊 Schema Summary: {summary['schema']}")
print("=" * 50)
print(f"📋 Total Tables: {summary['total_tables']}")
print(f"📊 Total Rows: {summary['total_rows']:,}")
print(f"💾 Total Size: {summary['total_size_bytes'] / (1024*1024*1024):.2f} GB")

if summary['tables']:
    print("\n🔝 Largest Tables by Row Count:")
    sorted_tables = sorted(summary['tables'], key=lambda x: x.get('row_count', 0) if isinstance(x.get('row_count'), int) else 0, reverse=True)
    for i, table in enumerate(sorted_tables[:5]):
        row_count = table.get('row_count', 'Unknown')
        if isinstance(row_count, int):
            print(f"  {i+1}. {table['table_name']}: {row_count:,} rows")
        else:
            print(f"  {i+1}. {table['table_name']}: {row_count} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🗑️ Drop Specific Tables
# MAGIC
# MAGIC **⚠️ WARNING: This will permanently delete the specified tables!**
# MAGIC
# MAGIC Uncomment and modify the cell below to drop specific tables.

# COMMAND ----------

# Example: Drop specific tables
# UNCOMMENT THE LINES BELOW AND MODIFY AS NEEDED

# tables_to_drop = [
#     'gold_sales_fact',
#     'gold_inventory_fact'
# ]

# print(f"⚠️  Planning to drop {len(tables_to_drop)} tables: {tables_to_drop}")
# print("🛡️  This operation respects table dependencies and will drop in safe order")

# # SAFETY: Set confirm=True to actually perform the deletion
# results = cleanup.drop_tables(tables_to_drop, confirm=False)  # Change to confirm=True

# print("\n📊 Drop Results:")
# for table, success in results.items():
#     status = "✅ Success" if success else "❌ Failed"
#     print(f"  {table}: {status}")

print("ℹ️  Uncomment and modify the code above to drop specific tables")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Create Backups Before Deletion
# MAGIC
# MAGIC Create backup copies of tables before deleting them (recommended for safety).

# COMMAND ----------

# Example: Create backups of specific tables
# UNCOMMENT THE LINES BELOW AND MODIFY AS NEEDED

# tables_to_backup = [
#     'gold_sales_fact',
#     'gold_customer_dim'
# ]

# print(f"💾 Creating backups for {len(tables_to_backup)} tables...")

# backup_results = cleanup.backup_tables(tables_to_backup, backup_suffix="_backup_" + str(int(time.time())))

# print("\n📊 Backup Results:")
# for table, success in backup_results.items():
#     status = "✅ Success" if success else "❌ Failed"
#     print(f"  {table}: {status}")

print("ℹ️  Uncomment and modify the code above to create backups")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧹 Drop All Fashion Retail Tables
# MAGIC
# MAGIC **⚠️ DANGER: This will delete ALL Fashion Retail tables in the schema!**
# MAGIC
# MAGIC Use this for complete cleanup when starting fresh.

# COMMAND ----------

# Get list of existing tables first
existing_tables = [t['table_name'] for t in cleanup.list_tables(show_details=False)]

if existing_tables:
    print(f"⚠️  WARNING: This will delete ALL {len(existing_tables)} Fashion Retail tables:")
    for table in existing_tables:
        print(f"    - {table}")
    
    print(f"\n🎯 Target Schema: {cleanup.full_schema}")
    print("🛡️  Only Fashion Retail tables will be affected")
    print("🛡️  Tables will be dropped in dependency-safe order")
    
    # SAFETY: Uncomment and set confirm=True to actually perform the deletion
    # results = cleanup.drop_all_tables(confirm=True)  # UNCOMMENT AND SET TO TRUE
    
    # print("\n📊 Drop Results:")
    # for table, success in results.items():
    #     status = "✅ Success" if success else "❌ Failed"
    #     print(f"  {table}: {status}")
    
    print("\n🔒 SAFETY: Uncomment the lines above and set confirm=True to proceed")
    
else:
    print("ℹ️  No Fashion Retail tables found to delete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Check Table Dependencies
# MAGIC
# MAGIC View the dependency relationships between tables to understand drop order.

# COMMAND ----------

# Show table dependencies
dependencies = cleanup.get_table_dependencies()

print("🔗 Table Dependencies:")
print("=" * 50)

if dependencies:
    for table, deps in dependencies.items():
        if cleanup.table_exists(table):
            print(f"📋 {table}")
            print(f"   └── Depends on: {', '.join(deps)}")
            print()
else:
    print("ℹ️  No dependencies defined")

# Show safe drop order for all existing tables
existing_tables = [t['table_name'] for t in cleanup.list_tables(show_details=False)]
if existing_tables:
    drop_order = cleanup.get_drop_order(existing_tables)
    print("🗑️  Safe Drop Order (if dropping all tables):")
    for i, table in enumerate(drop_order, 1):
        print(f"  {i}. {table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔄 Refresh Table List
# MAGIC
# MAGIC Run this cell to refresh the table list after making changes.

# COMMAND ----------

# Refresh and display current state
print("🔄 Refreshing table list...")

current_tables = cleanup.list_tables(show_details=True)

if current_tables:
    print(f"📊 Current State: {len(current_tables)} Fashion Retail tables found")
    
    # Quick summary
    total_rows = sum(t.get('row_count', 0) for t in current_tables if isinstance(t.get('row_count'), int))
    total_size_mb = sum(t.get('size_in_bytes', 0) for t in current_tables if isinstance(t.get('size_in_bytes'), int)) / (1024*1024)
    
    print(f"📊 Total Rows: {total_rows:,}")
    print(f"💾 Total Size: {total_size_mb:.2f} MB")
    
    # List table names
    table_names = [t['table_name'] for t in current_tables]
    print(f"\n📋 Tables: {', '.join(table_names)}")
    
else:
    print("✨ Schema is clean - no Fashion Retail tables found")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Cleanup Operations Complete
# MAGIC
# MAGIC ### 🛡️ Safety Features Used:
# MAGIC - Only Fashion Retail tables are affected (other tables are protected)
# MAGIC - Table dependencies are respected (safe drop order)
# MAGIC - Explicit confirmation required for destructive operations
# MAGIC - Detailed logging and status reporting
# MAGIC
# MAGIC ### 📋 Available Operations:
# MAGIC 1. **List Tables**: View all Fashion Retail tables with details
# MAGIC 2. **Schema Summary**: Get overview with totals and statistics  
# MAGIC 3. **Drop Specific Tables**: Delete selected tables safely
# MAGIC 4. **Create Backups**: Backup tables before deletion
# MAGIC 5. **Drop All Tables**: Complete cleanup (with confirmation)
# MAGIC 6. **Check Dependencies**: View table relationships
# MAGIC 7. **Refresh Status**: Update table list after changes
# MAGIC
# MAGIC ### 🚀 Next Steps:
# MAGIC - Use the data generation notebook to recreate tables if needed
# MAGIC - Monitor table sizes and optimize as necessary
# MAGIC - Set up automated cleanup jobs for development environments
