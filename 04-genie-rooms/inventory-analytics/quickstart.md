# Quickstart Guide: Applying Inventory Analytics Genie Configuration

This guide provides step-by-step instructions for creating and configuring the Inventory Analytics Genie space to enable natural language queries about inventory levels, stockout risks, overstock, replenishment, inventory movements, and inventory value.

---

## Prerequisites

- Access to the Databricks workspace
- Admin or owner permissions for creating/configuring a Genie space
- Inventory tables available in Unity Catalog (`juan_dev.retail` schema):
  - `gold_inventory_fact`
  - `gold_stockout_events`
  - `gold_inventory_movement_fact`
  - Supporting dimension tables: `gold_product_dim`, `gold_location_dim`, `gold_date_dim`
- Configuration artifacts ready in this folder:
  - `instructions.md` - Genie space instructions
  - `sample-queries/sample_queries.ipynb` - Sample queries organized by category
  - `data_model.md` - Data model documentation

**Important**: Tables must have proper comments and descriptions for automatic schema discovery to work effectively.

---

## Step 1: Verify Table Comments

Before adding tables to the Genie space, ensure they have comprehensive comments:

1. **Check Table Comments**
   - Verify that `gold_inventory_fact`, `gold_stockout_events`, and `gold_inventory_movement_fact` have table-level comments
   - Verify key columns have column-level comments
   - Comments should describe purpose, grain, relationships, and key metrics

2. **Add Comments if Missing** (if needed)
   ```sql
   -- Example: Add table comment
   COMMENT ON TABLE gold_inventory_fact IS 
   'Daily inventory snapshot fact table. Grain: Product × Location × Date. 
   Tracks inventory levels, stockout status, days of supply, reorder points, and inventory values.';
   
   -- Example: Add column comment
   COMMENT ON COLUMN gold_inventory_fact.quantity_available IS 
   'Available for sale after deductions from sales. Never negative. 
   If quantity_available = 0, then is_stockout = TRUE';
   ```

3. **Reference Data Model Documentation**
   - See `data_model.md` in this folder for recommended comment formats
   - See `add_table_comments.sql` for complete table and column comments

---

## Step 2: Create Genie Space

1. **Navigate to Genie in Databricks**
   - Log in to your Databricks workspace
   - Navigate to the Genie interface
   - Click "Create Space" or "New Space"

2. **Create New Space**
   - Name: "Inventory Analytics" (or your preferred name)
   - Description: "Natural language queries for inventory analytics, stockout risk, overstock, replenishment, and inventory movements"
   - Click "Create" to create the space

3. **Note Space ID**
   - After creation, note the Genie space ID (will be needed for testing)
   - The space ID appears in the URL or space settings

---

## Step 3: Add Tables to Genie Space

1. **Navigate to Space Settings**
   - In the Genie space, click on settings/configuration icon
   - Navigate to "Data" or "Tables" section

2. **Add Core Inventory Tables**
   - Add `juan_dev.retail.gold_inventory_fact`
   - Add `juan_dev.retail.gold_stockout_events`
   - Add `juan_dev.retail.gold_inventory_movement_fact`

3. **Add Supporting Dimension Tables**
   - Add `juan_dev.retail.gold_product_dim`
   - Add `juan_dev.retail.gold_location_dim`
   - Add `juan_dev.retail.gold_date_dim`

4. **Verify Table Access**
   - Ensure Unity Catalog permissions allow access to these tables
   - Verify tables appear in the Genie space data list
   - Genie will automatically discover schema from table comments

---

## Step 4: Add Genie Instructions

1. **Open Instructions Configuration**
   - In the Genie space settings, locate the "Instructions" or "System Prompt" section
   - Click "Edit" to modify the instructions

2. **Copy Instructions Content**
   - Open `instructions.md` in this folder
   - Copy the entire content (all sections including Business Context, Key Business Terms, Common Analysis Patterns, Response Guidelines, Error Handling)

3. **Paste and Apply**
   - Paste the content into the Instructions field
   - Click "Save" or "Apply" to save the configuration
   - Wait for confirmation that changes have been saved

4. **Verify Instructions Applied**
   - Check that the instructions are visible in the configuration
   - Review that all sections are present:
     - Business Context
     - Key Business Terms
     - Common Analysis Patterns
     - Response Guidelines
     - Error Handling
     - Multi-Domain Detection
     - Forecasting Boundaries

---

## Step 5: Add Sample Queries

1. **Open Sample Queries Configuration**
   - In the Genie space settings, locate the "Sample Queries" section
   - Click "Edit" to add or modify sample queries

2. **Organize by Category**
   - The sample queries notebook (`sample-queries/sample_queries.ipynb`) is organized by analytical category:
     - Current Stock Status & Levels
     - Stockout Risk & Analysis
     - Overstock Identification & Analysis
     - Inventory Value & Financial Metrics
     - Days of Supply & Reorder Management
     - Inventory Movements & Replenishment
     - Inventory Turnover & Efficiency
     - Stockout Events & Lost Sales Impact
     - Location & Regional Comparisons
     - Historical Trends & Patterns
     - Inventory Health Metrics
     - Follow-Up Questions
     - Error Handling Scenarios
     - Multi-Domain Detection Test Queries

3. **Add Sample Queries**
   - For each category, copy the relevant queries from `sample-queries/sample_queries.ipynb`
   - Paste into the Sample Queries section
   - **Important**: Include the query text, complexity level (Simple/Medium/Complex), and expected response patterns
   - Format: Copy the query text (e.g., "What products are currently out of stock?") and any relevant metadata

4. **Recommended Approach**
   - Start with Simple queries from each category
   - Add Medium complexity queries next
   - Add Complex queries last
   - Include error handling and multi-domain detection queries

5. **Save Sample Queries**
   - Click "Save" or "Apply" to save the sample queries
   - Wait for confirmation that changes have been saved

---

## Step 6: Deploy Metric Views (Optional)

Metric views provide pre-aggregated KPIs that improve query performance and ensure consistent calculations.

1. **Open the Metric Views Notebook**
   - Navigate to `metric-views/inventory_metric_views.ipynb`
   - This notebook contains DDL statements to create metric views

2. **Execute the Notebook in Databricks**
   - Open the notebook in Databricks
   - Update the catalog/schema references if needed (default: `juan_dev.retail`)
   - Run all cells to create the metric views

3. **Grant Permissions**
   ```sql
   -- Grant SELECT to Genie users
   GRANT SELECT ON juan_dev.retail.<metric_view_name> TO `genie_users`;
   ```

4. **Add Metric Views to Genie Space**
   - In the Genie space settings, add the metric views as data sources
   - This allows Genie to use pre-aggregated data for faster responses

5. **Test Metric View Queries**
   - See `metric-views/inventory_metric_view_queries.ipynb` for example queries
   - Verify metric views return expected results

---

## Step 7: Validation Checklist

After applying the configuration, validate that everything is working correctly:

### Configuration Validation

- [ ] **Instructions Applied**
  - [ ] Business Context section is visible
  - [ ] Key Business Terms section is present
  - [ ] Common Analysis Patterns section is present
  - [ ] Response Guidelines section is present
  - [ ] Multi-Domain Queries section is present

- [ ] **Sample Queries Added**
  - [ ] At least 1 query from each analytical category
  - [ ] Simple, Medium, and Complex queries represented
  - [ ] Error handling queries included
  - [ ] Multi-domain detection queries included

- [ ] **Data Model Documentation**
  - [ ] All inventory tables documented
  - [ ] All dimension tables documented
  - [ ] Join patterns included
  - [ ] Key metrics and calculations documented

- [ ] **Metric Views Deployed** (Optional)
  - [ ] Metric views created in Databricks
  - [ ] Permissions granted to Genie users
  - [ ] Metric views added to Genie space

### Functional Validation

- [ ] **Test Simple Query**
  - Query: "What products are currently out of stock?"
  - Expected: Response includes product names, locations, stockout duration
  - Performance: Response time < 10 seconds

- [ ] **Test Medium Complexity Query**
  - Query: "Which products are at risk of stockout?"
  - Expected: Response includes risk levels, days of supply, recommendations
  - Performance: Response time < 30 seconds

- [ ] **Test Error Handling**
  - Query: "What will inventory levels be next month?"
  - Expected: Clear message that forecasting is out of scope

- [ ] **Test Multi-Domain Detection**
  - Query: "Which customers are affected by stockouts?"
  - Expected: Multi-domain redirect message

- [ ] **Test Follow-Up Question**
  - Query 1: "Which products are at risk of stockout?"
  - Query 2: "What about their replenishment schedule?"
  - Expected: Context-aware response

---

## Step 8: Table Access Permissions

### Required Tables

**Core Inventory Tables**:
- `juan_dev.retail.gold_inventory_fact`
- `juan_dev.retail.gold_stockout_events`
- `juan_dev.retail.gold_inventory_movement_fact`

**Supporting Dimension Tables**:
- `juan_dev.retail.gold_product_dim`
- `juan_dev.retail.gold_location_dim`
- `juan_dev.retail.gold_date_dim`

### Permission Requirements

**Unity Catalog Permissions**:
- Users accessing the Genie space must have **SELECT** permission on all tables listed above
- Permission should be granted at the schema level (`juan_dev.retail`) or individually per table
- Genie space owner must have permissions to add tables to the space

### Verification Steps

1. **Verify Schema Access**:
   ```sql
   SHOW TABLES IN juan_dev.retail;
   ```

2. **Verify Table Access**:
   ```sql
   SELECT * FROM juan_dev.retail.gold_inventory_fact LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_stockout_events LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_inventory_movement_fact LIMIT 1;
   ```

3. **Verify Dimension Tables**:
   ```sql
   SELECT * FROM juan_dev.retail.gold_product_dim LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_location_dim LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_date_dim LIMIT 1;
   ```

### Granting Permissions

If permissions are missing, the Genie space owner or catalog administrator should grant:

```sql
-- Grant SELECT on schema (recommended)
GRANT SELECT ON SCHEMA juan_dev.retail TO `user@example.com`;

-- Or grant individually per table
GRANT SELECT ON TABLE juan_dev.retail.gold_inventory_fact TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_stockout_events TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_inventory_movement_fact TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_product_dim TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_location_dim TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_date_dim TO `user@example.com`;
```

---

## Troubleshooting

### Issue: Genie doesn't understand inventory queries

**Solutions**:
- Verify table comments are comprehensive and descriptive
- Check that instructions are properly formatted and saved
- Ensure sample queries cover the query type being tested
- Review Genie error messages for specific guidance

### Issue: Tables not found

**Solutions**:
- Verify Unity Catalog permissions allow access to `juan_dev.retail` schema
- Check that tables are added to the Genie space
- Verify table names match exactly (case-sensitive)

### Issue: Schema discovery not working

**Solutions**:
- Verify tables have table-level and column-level comments
- Check comment format matches recommended patterns
- Review `data_model.md` for comment examples

### Issue: Multi-domain queries not detected

**Solutions**:
- Verify multi-domain detection instructions are in place
- Check that sample queries include multi-domain detection examples
- Review instructions for keywords that trigger detection

### Issue: Forecasting queries not rejected

**Solutions**:
- Verify forecasting boundary instructions are in place
- Check that sample queries include forecasting rejection examples
- Ensure instructions clearly state forecasting is out of scope

### Issue: Queries fail with permission errors

**Solutions**:
- Ensure users have SELECT permission on all required tables
- Grant permissions at schema level or per table (see Step 8)
- Verify Genie space owner has table access

---

## Next Steps

After configuration is complete:

1. **User Testing**: Have inventory analysts test the Genie space with real queries
2. **Feedback Collection**: Gather feedback on query quality and response accuracy
3. **Iterative Improvement**: Update instructions and sample queries based on feedback
4. **Documentation**: Create user-facing documentation for inventory analysts
5. **Monitoring**: Monitor query performance and response quality metrics

---

## Configuration Files Reference

All configuration artifacts are in this folder:
- `instructions.md` - Genie space instructions
- `sample-queries/sample_queries.ipynb` - Sample queries by category
- `data_model.md` - Data model documentation
- `metric-views/` - Metric views for performance optimization
- `add_table_comments.sql` - SQL to add table/column comments

---

## Support

If you encounter issues applying the configuration:

1. Review the configuration artifacts to ensure they're correctly formatted
2. Check Databricks documentation for Genie space configuration
3. Verify you have the necessary permissions
4. Contact the Genie space administrator if needed

---

## Configuration Summary

**What Will Be Configured**:
- Genie space instructions (comprehensive domain guidance)
- Sample queries (covering all functional requirements)
- Data model documentation (table schemas, relationships, metrics)

**Expected Improvements**:
- Better query understanding and accuracy
- Improved response quality with actionable recommendations
- Better error handling with specific guidance
- Multi-domain query detection and redirection
- Performance optimization for medium-scale data

**Configuration Date**: [Date when configuration was applied]
**Applied By**: [Name/Email of person who applied configuration]
