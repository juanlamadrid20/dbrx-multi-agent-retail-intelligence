# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 3: Test Bronze Pipeline
# MAGIC 
# MAGIC This notebook helps verify the Bronze pipeline is working:
# MAGIC 
# MAGIC 1. Generate test data to the POS volume
# MAGIC 2. Create/run the pipeline
# MAGIC 3. Verify data in bronze_pos_transactions table
# MAGIC 
# MAGIC **Note:** The actual pipeline runs via DLT/SDP. This notebook is for:
# MAGIC - Pre-requisite data generation
# MAGIC - Post-pipeline validation

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Ensure Test Data Exists

# COMMAND ----------

# Check if POS files exist
VOLUME_PATH = "/Volumes/juan_dev/retail/data/pos"

try:
    files = dbutils.fs.ls(VOLUME_PATH)
    print(f"✅ Found {len(files)} file(s) in POS volume:")
    for f in files:
        print(f"   - {f.name} ({f.size} bytes)")
except Exception as e:
    print(f"⚠️ No files found. Generate test data first.")
    print(f"   Run notebook: 02-test-pos-generator.py")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Generate More Test Data (Optional)

# COMMAND ----------

# Add generators to path
import sys
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
repo_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, repo_root)

from generators.pos_generator import POSEventGenerator

# Generate additional test data
generator = POSEventGenerator(
    volume_path=VOLUME_PATH,
    batch_size=50,
    random_seed=123
)

# Write a batch
file_path = generator.write_batch_dbutils(dbutils, num_events=50)
print(f"✅ Generated test data: {file_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create the Pipeline
# MAGIC 
# MAGIC **Option A: Via Databricks UI**
# MAGIC 1. Go to Jobs & Pipelines > Delta Live Tables
# MAGIC 2. Create Pipeline with:
# MAGIC    - Name: `retail-bronze-test`
# MAGIC    - Target: `juan_dev.retail`
# MAGIC    - Notebook: `40-medallion-pipeline/pipelines/bronze_pipeline.py`
# MAGIC 
# MAGIC **Option B: Via databricks.yml (recommended for production)**
# MAGIC See the databricks.yml configuration below.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pipeline Configuration for databricks.yml
# MAGIC 
# MAGIC Add this to your `databricks.yml`:
# MAGIC 
# MAGIC ```yaml
# MAGIC resources:
# MAGIC   pipelines:
# MAGIC     retail_bronze_pipeline:
# MAGIC       name: "retail-intelligence-bronze-pipeline"
# MAGIC       target: "juan_dev.retail"
# MAGIC       development: true
# MAGIC       continuous: false
# MAGIC       channel: "PREVIEW"
# MAGIC       libraries:
# MAGIC         - notebook:
# MAGIC             path: ./40-medallion-pipeline/pipelines/bronze_pipeline.py
# MAGIC       configuration:
# MAGIC         volume_base: "/Volumes/juan_dev/retail/data"
# MAGIC         checkpoint_base: "/Volumes/juan_dev/retail/checkpoints"
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Verify Bronze Table (After Pipeline Runs)

# COMMAND ----------

# Check if bronze table exists
CATALOG = "juan_dev"
SCHEMA = "retail"
TABLE = "bronze_pos_transactions"

try:
    df = spark.table(f"{CATALOG}.{SCHEMA}.{TABLE}")
    count = df.count()
    print(f"✅ Table {CATALOG}.{SCHEMA}.{TABLE} exists with {count} rows")
    
    # Show schema
    print("\n📋 Schema:")
    df.printSchema()
    
    # Show sample data
    print("\n📊 Sample Data:")
    display(df.limit(5))
    
except Exception as e:
    print(f"⚠️ Table not found: {e}")
    print(f"\n   Run the Bronze pipeline first via:")
    print(f"   1. Databricks UI: Jobs & Pipelines > Create Pipeline")
    print(f"   2. Or: databricks bundle deploy && databricks bundle run retail_bronze_pipeline")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Validate Data Quality

# COMMAND ----------

# Only run this cell after pipeline has executed
try:
    df = spark.table(f"{CATALOG}.{SCHEMA}.{TABLE}")
    
    # Check for metadata columns
    print("📋 Validation Checks:")
    print("=" * 50)
    
    # Check _ingestion_timestamp
    has_ingestion_ts = "_ingestion_timestamp" in df.columns
    print(f"✅ _ingestion_timestamp column: {'Present' if has_ingestion_ts else 'Missing'}")
    
    # Check _source_file
    has_source_file = "_source_file" in df.columns
    print(f"✅ _source_file column: {'Present' if has_source_file else 'Missing'}")
    
    # Check items array
    has_items = "items" in df.columns
    print(f"✅ items array column: {'Present' if has_items else 'Missing'}")
    
    # Count null customer_ids (should be ~30%)
    from pyspark.sql.functions import col, count, when
    
    stats = df.agg(
        count("*").alias("total"),
        count(when(col("customer_id").isNull(), 1)).alias("null_customers")
    ).collect()[0]
    
    null_pct = (stats["null_customers"] / stats["total"]) * 100 if stats["total"] > 0 else 0
    print(f"✅ Null customer_id rate: {null_pct:.1f}% (expected ~30%)")
    
    # Check store distribution
    print("\n📍 Store Distribution:")
    display(df.groupBy("store_id").count().orderBy("count", ascending=False))
    
except Exception as e:
    print(f"⚠️ Cannot validate - table not found: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Expand Items Array (Preview Silver Logic)

# COMMAND ----------

# Preview what the Silver layer will do
try:
    from pyspark.sql.functions import explode, col
    
    df = spark.table(f"{CATALOG}.{SCHEMA}.{TABLE}")
    
    # Expand items array (this will be done in Silver layer)
    expanded = df.select(
        col("transaction_id"),
        col("store_id"),
        col("customer_id"),
        col("timestamp"),
        col("payment_method"),
        explode(col("items")).alias("item")
    ).select(
        "*",
        col("item.sku").alias("sku"),
        col("item.qty").alias("qty"),
        col("item.price").alias("price"),
        col("item.discount").alias("discount")
    ).drop("item")
    
    print(f"📊 Expanded to {expanded.count()} line items")
    display(expanded.limit(10))
    
except Exception as e:
    print(f"⚠️ Cannot preview - table not found: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 3 Complete!

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 3 VALIDATION                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  To complete Stage 3:                                            ║
║                                                                  ║
║  1. Create a DLT Pipeline in Databricks UI:                      ║
║     - Name: retail-bronze-test                                   ║
║     - Target: juan_dev.retail                                    ║
║     - Notebook: 40-medallion-pipeline/pipelines/bronze_pipeline  ║
║                                                                  ║
║  2. Run the pipeline (triggered mode)                            ║
║                                                                  ║
║  3. Verify bronze_pos_transactions table has data                ║
║                                                                  ║
║  Expected Results:                                               ║
║  ├── Rows ingested from /Volumes/.../pos/*.json                  ║
║  ├── _ingestion_timestamp column added                           ║
║  ├── _source_file column added                                   ║
║  ├── items array preserved                                       ║
║  └── ~30% null customer_id (guest checkouts)                     ║
║                                                                  ║
║  Next Step: Stage 4 - Create Silver Pipeline                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
