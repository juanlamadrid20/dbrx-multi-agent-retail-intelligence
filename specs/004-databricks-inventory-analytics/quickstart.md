# Quickstart Guide: Applying Inventory Analytics Genie Configuration

**Configuration Location**: `10-genie-rooms/genie-configs/inventory-analytics/`

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
- Configuration artifacts ready in `10-genie-rooms/genie-configs/inventory-analytics/`:
  - `instructions.md` - Genie space instructions
  - `sample_queries.md` - Sample queries organized by category

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
   - See `specs/004-databricks-inventory-analytics/data-model.md` for recommended comment formats
   - See `specs/001-i-want-to/data-model.md` for complete data model details

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
   - Open `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
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
   - The sample queries document (`sample_queries.md`) is organized by analytical category:
     - Current Stock Status & Levels
     - Stockout Risk & Analysis
     - Overstock Identification & Analysis
     - Inventory Value & Financial Metrics
     - Days of Supply & Reorder Management
     - Inventory Movements & Replenishment
     - Inventory Turnover & Efficiency
     - Stockout Events & Lost Sales Impact
     - In-Transit Inventory
     - Location & Regional Comparisons
     - Historical Trends & Patterns
     - Inventory Health Metrics
     - Follow-Up Questions
     - Error Handling Scenarios
     - Multi-Domain Detection Test Queries

3. **Add Sample Queries**
   - For each category, copy the relevant queries from `sample_queries.md`
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

## Step 6: Verify Configuration

1. **Test Sample Queries**
   - In the Genie space, try a simple query: "What products are currently out of stock?"
   - Verify response includes:
     - Natural language explanation
     - Structured data (tables)
     - Actionable insights/recommendations
   - Test a medium complexity query: "Which products are at risk of stockout?"
   - Test a follow-up question: "What about their replenishment schedule?"

2. **Test Error Handling**
   - Try an ambiguous query: "inventory"
   - Verify Genie asks clarifying questions or provides multiple interpretations
   - Try a future date query: "What will inventory levels be next month?"
   - Verify Genie explains forecasting is out of scope

3. **Test Multi-Domain Detection**
   - Try a multi-domain query: "What products are out of stock and which customers are affected?"
   - Verify Genie detects multi-domain query and redirects appropriately

4. **Test Performance**
   - Simple queries should respond in <10 seconds
   - Complex queries should respond in <60 seconds

---

## Step 7: Document Configuration

1. **Update Configuration Documentation**
   - Document the Genie space ID in `10-genie-rooms/genie-configs/inventory-analytics/README.md` (if created)
   - Note any customizations or deviations from standard configuration
   - Document table access permissions and Unity Catalog settings

2. **Version Control**
   - Ensure configuration artifacts are committed to version control
   - Document configuration date and any changes made

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
- Review data model documentation for comment examples

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

- **Instructions**: `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
- **Sample Queries**: `10-genie-rooms/genie-configs/inventory-analytics/sample_queries.md`
- **Data Model Reference**: `specs/004-databricks-inventory-analytics/data-model.md`
- **Specification**: `specs/004-databricks-inventory-analytics/spec.md`
- **Data Model Alignment**: `specs/004-databricks-inventory-analytics/DATA_MODEL_ALIGNMENT.md`

---

**Configuration Complete**: Once all steps are complete, the Inventory Analytics Genie space is ready for use by inventory analysts, operations managers, and supply chain analysts.

