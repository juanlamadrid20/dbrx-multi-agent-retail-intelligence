# Quickstart Guide: Applying Customer Behavior Genie Configuration

**Genie Space ID**: `01f09cdbacf01b5fa7ff7c237365502c`
**Configuration Location**: `10-genie-rooms/genie-configs/customer-behavior/`

This guide provides step-by-step instructions for applying the Customer Behavior Genie configuration to improve query understanding and response quality.

---

## Prerequisites

- Access to the Databricks workspace
- Admin or owner permissions for the Genie space (Space ID: `01f09cdbacf01b5fa7ff7c237365502c`)
- Configuration artifacts ready in `10-genie-rooms/genie-configs/customer-behavior/`:
  - `instructions.md` - Genie space instructions
  - `sample_queries.md` - Sample queries organized by category
  - `data_model.md` - Data model documentation

---

## Step 1: Navigate to Genie Space Configuration

1. **Open Databricks Workspace**
   - Log in to your Databricks workspace
   - Navigate to the Genie interface

2. **Access Genie Space Settings**
   - Locate the Customer Behavior Genie space (ID: `01f09cdbacf01b5fa7ff7c237365502c`)
   - Click on the space settings/configuration icon
   - Navigate to "Settings" or "Configuration" tab

3. **Locate Configuration Sections**
   - Look for sections:
     - **Instructions** (or System Prompt)
     - **Sample Queries**
     - **Data Model Documentation** (may be in a separate section)

---

## Step 2: Add Genie Instructions

1. **Open Instructions Configuration**
   - In the Genie space settings, locate the "Instructions" or "System Prompt" section
   - Click "Edit" to modify the instructions

2. **Copy Instructions Content**
   - Open `10-genie-rooms/genie-configs/customer-behavior/instructions.md`
   - Copy the entire content (all sections including Business Context, Key Business Terms, Common Analysis Patterns, Response Guidelines, Multi-Domain Queries)

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
     - Multi-Domain Queries
   - Note: Instructions are condensed (~37 lines) and focus on business context, key terms, and actionable patterns. Genie learns data model from tables and query patterns from sample queries.

---

## Step 3: Add Sample Queries

1. **Open Sample Queries Configuration**
   - In the Genie space settings, locate the "Sample Queries" section
   - Click "Edit" to add or modify sample queries

2. **Organize by Category**
   - The sample queries document (`sample_queries.md`) is organized by analytical category:
     - Customer Segmentation & Value
     - Purchase Patterns & RFM Analysis
     - Product & Category Affinity
     - Channel Behavior & Migration
     - Engagement & Funnel Analysis
     - Abandonment & Recovery
     - Personalization & Affinity Impact
     - Stockout Risk Based on Customer Demand
     - Follow-Up Questions
     - Error Handling Scenarios
     - Multi-Domain Detection Test Queries

3. **Add Sample Queries**
   - For each category, copy the relevant queries from `sample_queries.md`
   - Paste into the Sample Queries section
   - **Important**: Include the query text, complexity level (Simple/Medium/Complex), and expected response patterns
   - Format: Copy the query text (e.g., "What are the key customer segments?") and any relevant metadata

4. **Recommended Approach**
   - Start with Simple queries from each category
   - Add Medium complexity queries next
   - Add Complex queries last
   - Include error handling and multi-domain detection queries

5. **Save Sample Queries**
   - Click "Save" or "Apply" to save the sample queries
   - Wait for confirmation

6. **Verify Sample Queries**
   - Check that queries are organized by category
   - Verify that all 48 sample queries (Q1-Q48) are included or at least represented
   - Ensure queries cover all functional requirements (FR-001 through FR-022)

---

## Step 4: Add Data Model Documentation

1. **Locate Data Model Documentation Section**
   - In the Genie space settings, locate the "Data Model" or "Documentation" section
   - This may be in a separate tab or section

2. **Copy Data Model Content**
   - Open `10-genie-rooms/genie-configs/customer-behavior/data_model.md`
   - Copy the entire content

3. **Paste Data Model**
   - Paste the content into the Data Model Documentation field
   - Click "Save" or "Apply"

4. **Verify Data Model**
   - Check that all sections are present:
     - Overview
     - Core Dimension Tables (gold_customer_dim, gold_product_dim, gold_date_dim, gold_channel_dim)
     - Core Fact Tables (gold_sales_fact, gold_cart_abandonment_fact, gold_customer_product_affinity_agg, gold_customer_event_fact)
     - Table Relationships and Join Patterns
     - Key Metrics and Calculations
     - Data Quality Notes
     - Best Practices for Genie Queries

---

## Step 5: Validation Checklist

After applying the configuration, validate that everything is working correctly:

### Configuration Validation

- [ ] **Instructions Applied**
  - [ ] Business Context section is visible
  - [ ] Key Business Terms section is present
  - [ ] Common Analysis Patterns section is present (numbered list)
  - [ ] Response Guidelines section is present
  - [ ] Multi-Domain Queries section is present
  - [ ] Instructions are condensed (~37 lines, business-focused)

- [ ] **Sample Queries Added**
  - [ ] At least 1 query from each analytical category
  - [ ] Simple, Medium, and Complex queries represented
  - [ ] Error handling queries included
  - [ ] Multi-domain detection queries included
  - [ ] All 12 acceptance scenarios covered

- [ ] **Data Model Documentation**
  - [ ] All dimension tables documented
  - [ ] All fact tables documented
  - [ ] Join patterns included
  - [ ] Key metrics and calculations documented
  - [ ] Data quality notes included

### Functional Validation

- [ ] **Test Simple Query**
  - Query: "What are the key customer segments?"
  - Expected: Response includes segment names, sizes, and characteristics
  - Performance: Response time < 10 seconds

- [ ] **Test Medium Complexity Query**
  - Query: "What is the rate of cart abandonment, and how effective are recovery campaigns?"
  - Expected: Response includes abandonment rate, recovery metrics, and recommendations
  - Performance: Response time < 30 seconds

- [ ] **Test Error Handling**
  - Query: "Show me customer purchase data from schema X" (where user lacks permissions)
  - Expected: Clear error message with actionable guidance
  - Response includes: Error type, specific message, suggestions

- [ ] **Test Multi-Domain Detection**
  - Query: "Which products are frequently abandoned in carts and do we have inventory issues with those items?"
  - Expected: Multi-domain redirect message explaining why it's out of scope and suggesting the multi-domain agent

- [ ] **Test Follow-Up Question**
  - Query 1: "What products are trending?"
  - Query 2: "What about their demographics?"
  - Expected: Response understands context from first query and provides demographics for trending products

### Response Quality Validation

- [ ] **Response Structure**
  - [ ] Direct answer to question
  - [ ] Key metrics with specific numbers
  - [ ] Insights explaining what data means
  - [ ] Actionable recommendations (1-3 suggestions)
  - [ ] Source citation indicating data sources

- [ ] **Natural Language**
  - [ ] Response is in conversational, business-friendly language
  - [ ] No raw SQL unless specifically requested
  - [ ] Clear, simple explanations
  - [ ] Structured with bullet points or numbered lists

- [ ] **Proactive Suggestions**
  - [ ] Response includes 1-3 related insights at the end
  - [ ] Suggestions are specific and actionable
  - [ ] Suggestions complement the current answer

---

## Step 6: Test Configuration

After applying the configuration, test the Genie space with sample queries:

### Test Queries by Category

1. **Customer Segmentation** (Simple)
   - Query: "What are the key customer segments?"
   - Verify: Response includes segment names and characteristics

2. **Cart Abandonment** (Medium)
   - Query: "What is the rate of cart abandonment, and how effective are recovery campaigns?"
   - Verify: Response includes abandonment rate, recovery metrics, and recommendations

3. **Trending Products** (Simple)
   - Query: "What products are trending?"
   - Verify: Response includes trending products with growth metrics and segments driving trends

3. **Error Handling**
   - Query: "Show me customer purchase data from schema X" (where user lacks permissions)
   - Verify: Clear error message with actionable guidance

4. **Multi-Domain Detection**
   - Query: "Which products are frequently abandoned in carts and do we have inventory issues with those items?"
   - Verify: Multi-domain redirect message

5. **Follow-Up Question**
   - Query 1: "What products are trending?"
   - Query 2: "What about their demographics?"
   - Verify: Context-aware response

### Performance Testing

- [ ] **Simple Query Performance**
  - Query: "What are the key customer segments?"
  - Target: < 10 seconds
  - Actual: [Record time]

- [ ] **Medium Complexity Query Performance**
  - Query: "What is the rate of cart abandonment, and how effective are recovery campaigns?"
  - Target: < 30 seconds
  - Actual: [Record time]

- [ ] **Complex Query Performance**
  - Query: "Analyze RFM patterns across customer segments and identify migration trends"
  - Target: < 60 seconds
  - Actual: [Record time]

---

## Troubleshooting

### Instructions Not Saving
- **Issue**: Instructions field doesn't save changes
- **Solution**: 
  - Check that you have admin/owner permissions for the Genie space
  - Try refreshing the page and re-entering the instructions
  - Check for character limits and split instructions if needed

### Sample Queries Not Appearing
- **Issue**: Sample queries don't appear in the Genie interface
- **Solution**:
  - Verify that queries are in the correct format
  - Check that the Genie space supports sample queries feature
  - Try adding queries one category at a time

### Data Model Documentation Not Saving
- **Issue**: Data model documentation field doesn't save
- **Solution**:
  - Check for character limits
  - Try saving in sections if the content is too large
  - Verify the field supports markdown formatting

### Queries Not Working as Expected
- **Issue**: Genie responses don't match expected patterns
- **Solution**:
  - Review the instructions to ensure they're applied correctly
  - Verify that sample queries are properly formatted
  - Check that data model documentation is accessible to Genie
  - Test with simpler queries first to isolate issues

---

## Next Steps

After successfully applying the configuration:

1. **Monitor Performance**
   - Track query response times
   - Monitor error rates
   - Collect user feedback

2. **Iterate Based on Feedback**
   - Refine instructions based on query patterns
   - Add more sample queries for common use cases
   - Update data model documentation as needed

3. **Document Improvements**
   - Track quality metrics before/after configuration
   - Document any issues or improvements needed
   - Share learnings with the team

---

## References

- **Configuration Artifacts**: `10-genie-rooms/genie-configs/customer-behavior/`
  - `instructions.md` - Genie space instructions
  - `sample_queries.md` - Sample queries by category
  - `data_model.md` - Data model documentation

- **Feature Specification**: `specs/003-cutomer-behavior-genie/spec.md`
- **Implementation Plan**: `specs/003-cutomer-behavior-genie/plan.md`
- **Genie Space ID**: `01f09cdbacf01b5fa7ff7c237365502c`

---

## Support

If you encounter issues applying the configuration:

1. Review the configuration artifacts to ensure they're correctly formatted
2. Check Databricks documentation for Genie space configuration
3. Verify you have the necessary permissions
4. Contact the Genie space administrator if needed

---

## Configuration Summary

**What Was Configured**:
- ✅ Genie space instructions (comprehensive domain guidance)
- ✅ Sample queries (48 queries covering all functional requirements)
- ✅ Data model documentation (table schemas, relationships, metrics)

**Expected Improvements**:
- Better query understanding and accuracy
- Improved response quality with actionable recommendations
- Better error handling with specific guidance
- Multi-domain query detection and redirection
- Performance optimization for medium-scale data

**Configuration Date**: [Date when configuration was applied]
**Applied By**: [Name/Email of person who applied configuration]

