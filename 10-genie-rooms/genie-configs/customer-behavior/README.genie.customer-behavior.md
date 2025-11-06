# Customer Behavior Genie

**Genie Space ID**: `01f09cdbacf01b5fa7ff7c237365502c`

---

## About

The Customer Behavior Genie space provides natural language querying of customer behavior data, enabling analysts to understand customer purchasing patterns, segmentation, cart abandonment, product affinity, channel behavior, and engagement metrics.

---

## Genie Space Configuration

The Genie space has been configured with comprehensive instructions, sample queries, and data model documentation to improve query understanding and response quality.

### Configuration Artifacts

Configuration artifacts are located in `10-genie-rooms/genie-configs/customer-behavior/`:

- **`instructions.md`**: Concise business-focused instructions (~37 lines) covering business context, key terms, common analysis patterns, response guidelines, and multi-domain boundaries
- **`sample_queries.md`**: 48 sample queries organized by analytical category and complexity, covering all functional requirements and acceptance scenarios
- **`data_model.md`**: Data model documentation describing customer behavior tables, relationships, key metrics, and best practices

### Applying Configuration

To apply the configuration to the Genie space, follow the step-by-step guide in:
- **Quickstart Guide**: `specs/003-cutomer-behavior-genie/quickstart.md`

### Testing Configuration

After applying the configuration, validate it using:
- **Test Notebook**: `10-genie-rooms/notebooks/test-genie-configuration.ipynb`
- **Validation Test Cases**: `specs/003-cutomer-behavior-genie/contracts/validation_test_cases.md`

### Configuration Summary

For a comprehensive overview of the configuration, see:
- **Configuration Summary**: `specs/003-cutomer-behavior-genie/contracts/configuration_summary.md`

---

## Customer Behavior Analysis

A customer behavior analyst would ask questions that help uncover patterns, trends, and actionable insights about how customers interact with products, channels, and the brand.

### Example Questions

- What products are trending?
- Which products or categories are at risk of stockout or overstock?
- Through which channels do customers prefer to shop?
- Which segments respond best to personalization?

---

## Analytical Categories

### Customer Segmentation & Value

- What are the key customer segments, and how do their lifetime values differ?
- Which segments have the highest average order value or frequency?
- What is the distribution of customer lifetime value across segments?

### Purchase Patterns & RFM Analysis

- How frequently do customers make purchases, and how recently?
- Which customers are at risk of churning, and which are the most loyal?
- What is the average time between purchases for different segments?

### Product & Category Affinity

- Which product categories are most often purchased together?
- What are the most common product pairings in a single transaction?
- How does category affinity differ by customer segment?

### Channel Behavior & Migration

- Through which channels do customers prefer to shop?
- How do customers migrate between acquisition and preferred channels over time?
- What is the impact of channel on purchase frequency and value?

### Engagement & Funnel Analysis

- What are the conversion rates at each stage of the engagement funnel (view, cart, purchase)?
- Which channels drive the most engagement and conversions?
- Where are customers dropping off in the purchase funnel?

### Abandonment & Recovery

- What is the rate of cart abandonment, and how effective are recovery campaigns?
- Which stages of the funnel have the highest abandonment rates?
- What is the revenue recovery rate from abandoned carts?

### Personalization & Affinity Impact

- How effective are personalized recommendations in driving purchases?
- Which segments respond best to personalization?
- What is the predicted impact of affinity-based targeting on CLTV?

---

## Sample Queries

For comprehensive sample queries covering all analytical categories, see:
- **Sample Queries Document**: `10-genie-rooms/genie-configs/customer-behavior/sample_queries.md`

The sample queries document includes:
- 48 sample queries organized by category
- Complexity indicators (Simple, Medium, Complex)
- Expected response patterns
- Data sources for each query
- Acceptance scenario mappings

---

## Data Model

For detailed information about the customer behavior data model, see:
- **Data Model Documentation**: `10-genie-rooms/genie-configs/customer-behavior/data_model.md`

The data model documentation includes:
- Core dimension tables (customer, product, date, channel)
- Core fact tables (sales, cart abandonment, affinity, events)
- Table relationships and join patterns
- Key metrics and calculations
- Data quality notes and best practices

---

## Response Quality

The Genie space is configured to provide:

- **Natural Language Responses**: Conversational, business-friendly language (FR-012)
- **Actionable Recommendations**: 1-3 specific recommendations per response (FR-020)
- **Proactive Suggestions**: Related insights to enhance discovery (FR-014)
- **Error Handling**: Specific error details with actionable guidance (FR-022)
- **Multi-Domain Detection**: Clear redirection for multi-domain queries (FR-021)

---

## Performance Targets

- **Simple Queries**: < 10 seconds (e.g., single table with filters, simple aggregations)
- **Medium Complexity Queries**: < 30 seconds (e.g., multi-table joins, aggregations)
- **Complex Queries**: < 60 seconds (e.g., complex joins, window functions, time-series analysis)

---

## References

- **Feature Specification**: `specs/003-cutomer-behavior-genie/spec.md`
- **Implementation Plan**: `specs/003-cutomer-behavior-genie/plan.md`
- **Configuration Artifacts**: `10-genie-rooms/genie-configs/customer-behavior/`
- **Quickstart Guide**: `specs/003-cutomer-behavior-genie/quickstart.md`
- **Test Notebook**: `10-genie-rooms/notebooks/test-genie-configuration.ipynb`

---

These questions help analysts identify opportunities for targeted marketing, retention strategies, product bundling, and channel optimization. They also support data-driven decision-making for improving customer experience and business outcomes.
