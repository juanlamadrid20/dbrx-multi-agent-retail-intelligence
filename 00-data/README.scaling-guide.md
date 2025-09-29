# Fashion Retail Pipeline Scaling Guide

This guide provides recommendations for scaling the fashion retail data generation pipeline from testing to production-like volumes.

## Current Test Configuration

```python
config = {
    'customers': 10,
    'products': 5,
    'locations': 13,
    'historical_days': 30,
    'events_per_day': 10
}
```

**Current Data Volumes:**
- Sales Fact: ~150 records
- Customer Events: ~300 records
- Inventory Fact: ~1,950 records
- Cart Abandonment: ~2,310 records
- Demand Forecast: ~750 records

## Scaling Recommendations

### 1. Small Business Scale
```python
config = {
    'customers': 5_000,      # Small boutique chain
    'products': 500,         # Focused product catalog
    'locations': 13,         # Keep existing (realistic for small chain)
    'historical_days': 90,   # Quarterly analysis
    'events_per_day': 1_000  # Moderate web traffic
}
```

**Expected Volumes:**
- Sales Fact: ~135,000 records (5K customers × 90 days × ~0.3 purchase rate)
- Customer Events: ~90,000 records (90 days × 1K events)
- Inventory Fact: ~585,000 records (500 products × 13 locations × 90 days)
- Customer-Product Affinity: ~250,000 records (interactions subset)

**Performance Impact:**
- Generation Time: ~5-10 minutes
- Storage: ~500MB total
- Memory: Standard cluster sufficient

### 2. Mid-Market Retailer
```python
config = {
    'customers': 50_000,     # Regional retailer
    'products': 2_000,       # Broader catalog
    'locations': 25,         # More stores + warehouses
    'historical_days': 365,  # Full year of data
    'events_per_day': 10_000 # Higher web traffic
}
```

**Expected Volumes:**
- Sales Fact: ~5.5M records (50K customers × 365 days × ~0.3 purchase rate)
- Customer Events: ~3.65M records (365 days × 10K events)
- Inventory Fact: ~18.25M records (2K products × 25 locations × 365 days)
- Customer-Product Affinity: ~2M records

**Performance Impact:**
- Generation Time: ~30-60 minutes
- Storage: ~5-10GB total
- Memory: Recommend 4-8 worker cluster

### 3. Enterprise Scale
```python
config = {
    'customers': 500_000,    # Large national retailer
    'products': 10_000,      # Full department store catalog
    'locations': 50,         # National footprint
    'historical_days': 730,  # 2 years of history
    'events_per_day': 100_000 # High web traffic
}
```

**Expected Volumes:**
- Sales Fact: ~55M records (500K customers × 730 days × ~0.15 purchase rate)
- Customer Events: ~73M records (730 days × 100K events)
- Inventory Fact: ~365M records (10K products × 50 locations × 730 days)
- Customer-Product Affinity: ~15M records

**Performance Impact:**
- Generation Time: ~2-4 hours
- Storage: ~50-100GB total
- Memory: Recommend 8-16 worker cluster with 32GB+ per worker

### 4. Large E-commerce Platform
```python
config = {
    'customers': 2_000_000,  # Major e-commerce platform
    'products': 50_000,      # Marketplace-scale catalog
    'locations': 100,        # Global distribution network
    'historical_days': 730,  # 2 years of history
    'events_per_day': 1_000_000 # Very high web traffic
}
```

**Expected Volumes:**
- Sales Fact: ~220M records (2M customers × 730 days × ~0.15 purchase rate)
- Customer Events: ~730M records (730 days × 1M events)
- Inventory Fact: ~3.65B records (50K products × 100 locations × 730 days)
- Customer-Product Affinity: ~50M records

**Performance Impact:**
- Generation Time: ~8-12 hours
- Storage: ~500GB-1TB total
- Memory: Recommend 16-32 worker cluster with 64GB+ per worker

## Data Volume Calculation Formulas

### Key Multipliers
```python
# Sales transactions per customer per day
sales_rate = 0.3 for small business down to 0.15 for enterprise

# Event distribution
events_per_customer_ratio = 0.7  # 70% of events have customer context
product_interaction_ratio = 0.6  # 60% of events involve products

# Inventory calculations
inventory_records = products × locations × historical_days

# Affinity calculations (subset of interactions)
affinity_records = customers × products × 0.1  # 10% have meaningful interactions
```

### Storage Estimates
```python
# Approximate bytes per record
sales_fact_bytes = 200
customer_events_bytes = 150
inventory_fact_bytes = 100
dimension_bytes = 300

# Total storage (compressed Delta)
total_storage = (
    (sales_records * sales_fact_bytes) +
    (event_records * customer_events_bytes) +
    (inventory_records * inventory_fact_bytes) +
    (dimension_records * dimension_bytes)
) * 0.3  # Delta compression factor
```

## Performance Optimization Recommendations

### For Mid-Market and Above:

1. **Enable Liquid Clustering**
   ```python
   'enable_liquid_clustering': True
   ```

2. **Optimize Z-ORDER Keys**
   ```python
   'z_order_keys': {
       'gold_sales_fact': ['date_key', 'customer_key', 'product_key'],
       'gold_inventory_fact': ['date_key', 'product_key', 'location_key'],
       'gold_customer_event_fact': ['date_key', 'customer_key', 'event_type']
   }
   ```

3. **Partition Strategy**
   ```python
   # Consider partitioning large tables by date for performance
   partition_columns = ['year', 'month'] # for tables > 100M records
   ```

4. **Batch Processing**
   ```python
   # Process in smaller batches for very large datasets
   'batch_size': 100_000,  # Records per batch
   'parallel_workers': 8   # Concurrent batch processing
   ```

## Cluster Sizing Recommendations

### Small Business (5K customers)
- **Driver**: 8GB RAM, 2 cores
- **Workers**: 2-4 workers, 16GB RAM each
- **Runtime**: Standard Databricks Runtime

### Mid-Market (50K customers)
- **Driver**: 16GB RAM, 4 cores
- **Workers**: 4-8 workers, 32GB RAM each
- **Runtime**: ML Runtime (for advanced analytics)

### Enterprise (500K+ customers)
- **Driver**: 32GB RAM, 8 cores
- **Workers**: 8-16 workers, 64GB RAM each
- **Runtime**: ML Runtime with GPU (for ML workloads)

## Cost Implications

### Databricks Unit (DBU) Estimates
- **Small Business**: ~20-50 DBUs per run
- **Mid-Market**: ~100-300 DBUs per run
- **Enterprise**: ~500-1,500 DBUs per run
- **Large E-commerce**: ~2,000-5,000 DBUs per run

### Storage Costs (Delta Lake)
- **Small Business**: ~$10-25/month
- **Mid-Market**: ~$50-150/month
- **Enterprise**: ~$500-1,000/month
- **Large E-commerce**: ~$2,000-5,000/month

## Recommended Scaling Path

1. **Start with Small Business scale** to validate all use cases
2. **Monitor performance metrics** during generation
3. **Scale up gradually** by 2-5x increments
4. **Optimize cluster size** based on actual resource usage
5. **Enable partitioning and clustering** for large datasets

## Monitoring Key Metrics

```sql
-- Monitor table sizes
SELECT
    table_name,
    size_in_bytes / 1024 / 1024 / 1024 as size_gb,
    num_files,
    last_modified
FROM INFORMATION_SCHEMA.TABLE_STORAGE_METADATA
WHERE schema_name = 'retail'
ORDER BY size_in_bytes DESC;

-- Monitor query performance
SELECT
    statement_type,
    avg(execution_time_ms) as avg_execution_time,
    avg(rows_read) as avg_rows_read
FROM system.access.query_history
WHERE schema_name = 'retail'
GROUP BY statement_type;
```

Choose your scale based on:
- **Use case requirements** (real-time vs batch analytics)
- **Budget constraints** (compute and storage costs)
- **Performance targets** (query response times)
- **Data retention needs** (historical analysis depth)