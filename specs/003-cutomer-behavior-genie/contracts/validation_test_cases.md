# Validation Test Cases: Customer Behavior Genie Configuration

**Purpose**: Document specific test cases for validating the Customer Behavior Genie space configuration

**Configuration Location**: `10-genie-rooms/genie-configs/customer-behavior/`
**Genie Space ID**: `01f09cdbacf01b5fa7ff7c237365502c`

---

## Test Case Categories

1. **Simple Query Tests** (Expected <10 seconds)
2. **Medium Complexity Query Tests** (Expected <30 seconds)
3. **Complex Query Tests** (Expected <60 seconds)
4. **Error Handling Tests** (FR-022)
5. **Multi-Domain Detection Tests** (FR-021)
6. **Response Quality Tests** (FR-012, FR-020)

---

## Simple Query Test Cases (<10 seconds)

### TC-001: Customer Segmentation Query
**Query**: "What are the key customer segments?"

**Expected Response**:
- ✅ List of customer segments (VIP, Premium, Loyal, Regular, New)
- ✅ Segment descriptions or characteristics
- ✅ Natural language format (not raw SQL)
- ✅ Actionable recommendations (1-3 suggestions)
- ✅ Proactive suggestions for related insights

**Validation Criteria**:
- Response time: < 10 seconds
- Response contains segment names
- Response is in natural language (not SQL)
- Response includes recommendations
- Response includes insights

**Data Sources**: `gold_customer_dim` (filtered by `is_current = TRUE`)

---

### TC-002: Trending Products Query
**Query**: "What products are trending?"

**Expected Response**:
- ✅ List of trending products
- ✅ Growth metrics (growth rate, purchase frequency)
- ✅ Customer segments driving the trend
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 10 seconds
- Response contains product names
- Response includes growth metrics
- Response includes segment information
- Response includes recommendations

**Data Sources**: `gold_sales_fact` + `gold_product_dim` + `gold_date_dim`

**Acceptance Scenario**: #1 from spec.md

---

### TC-003: Cart Abandonment Rate Query
**Query**: "What is the rate of cart abandonment?"

**Expected Response**:
- ✅ Overall abandonment rate percentage
- ✅ Breakdown by product, category, or segment
- ✅ Natural language format
- ✅ Actionable recommendations for improving abandonment
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 10 seconds
- Response contains abandonment rate percentage
- Response includes breakdown
- Response includes recommendations

**Data Sources**: `gold_cart_abandonment_fact`

---

### TC-004: Channel Preferences Query
**Query**: "Through which channels do customers prefer to shop?"

**Expected Response**:
- ✅ Channel preferences by customer segment
- ✅ Preference percentages or metrics
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 10 seconds
- Response contains channel names
- Response includes segment breakdown
- Response includes recommendations

**Data Sources**: `gold_sales_fact` + `gold_channel_dim` + `gold_customer_dim`

**Acceptance Scenario**: #3 from spec.md

---

### TC-005: Funnel Conversion Rates Query
**Query**: "What are the conversion rates at each stage of the engagement funnel?"

**Expected Response**:
- ✅ Conversion rates for View → Cart → Purchase stages
- ✅ Drop-off analysis
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 10 seconds
- Response contains conversion rates for each stage
- Response includes drop-off analysis
- Response includes recommendations

**Data Sources**: `gold_customer_event_fact` + `gold_sales_fact`

**Acceptance Scenario**: #9 from spec.md

---

## Medium Complexity Query Test Cases (<30 seconds)

### TC-006: Customer Segments and CLTV Query
**Query**: "What are the key customer segments, and how do their lifetime values differ?"

**Expected Response**:
- ✅ Detailed segment analysis with CLTV comparisons
- ✅ Segment characteristics
- ✅ Average order value comparisons
- ✅ Purchase frequency metrics
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 30 seconds
- Response contains segment names and CLTV values
- Response includes comparisons
- Response includes recommendations

**Data Sources**: `gold_customer_dim`

**Acceptance Scenario**: #5 from spec.md

---

### TC-007: RFM Analysis Query
**Query**: "Which customers are at risk of churning, and which are the most loyal?"

**Expected Response**:
- ✅ Lists of at-risk customers and highly loyal customers
- ✅ RFM scores or indicators
- ✅ Supporting metrics
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 30 seconds
- Response contains customer lists or segments
- Response includes RFM indicators
- Response includes recommendations

**Data Sources**: `gold_sales_fact` + `gold_customer_dim` + `gold_date_dim` (RFM calculation)

**Acceptance Scenario**: #6 from spec.md

---

### TC-008: Cart Abandonment and Recovery Query
**Query**: "What is the rate of cart abandonment, and how effective are recovery campaigns?"

**Expected Response**:
- ✅ Abandonment rate percentage
- ✅ Recovery effectiveness metrics
- ✅ Recovery email sent rate
- ✅ Recovery conversion rate
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 30 seconds
- Response contains abandonment rate
- Response includes recovery metrics
- Response includes recommendations

**Data Sources**: `gold_cart_abandonment_fact`

**Acceptance Scenario**: #7 from spec.md

---

### TC-009: Channel Migration Query
**Query**: "How do customers migrate between acquisition and preferred channels over time?"

**Expected Response**:
- ✅ Migration patterns showing channel transitions
- ✅ Time-series data
- ✅ Segment breakdown
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 30 seconds
- Response contains migration patterns
- Response includes time-series information
- Response includes recommendations

**Data Sources**: `gold_customer_dim` (acquisition_channel vs preferred_channel) + `gold_date_dim`

**Acceptance Scenario**: #10 from spec.md

---

### TC-010: Personalization Effectiveness Query
**Query**: "Which segments respond best to personalization?"

**Expected Response**:
- ✅ Segment ranking by personalization response rates
- ✅ Response rate metrics
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 30 seconds
- Response contains segment ranking
- Response includes response rate metrics
- Response includes recommendations

**Data Sources**: `gold_customer_product_affinity_agg` + `gold_customer_dim`

**Acceptance Scenario**: #4 from spec.md

---

## Complex Query Test Cases (<60 seconds)

### TC-011: RFM Patterns Across Segments
**Query**: "Analyze RFM patterns across customer segments and identify migration trends"

**Expected Response**:
- ✅ RFM analysis by segment
- ✅ Migration patterns over time
- ✅ Trends and insights
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 60 seconds
- Response contains RFM analysis by segment
- Response includes migration patterns
- Response includes recommendations

**Data Sources**: `gold_sales_fact` + `gold_customer_dim` + `gold_date_dim` (time-series analysis)

---

### TC-012: Product Trends with Segments
**Query**: "Analyze product trends with customer segments driving the trends and growth patterns"

**Expected Response**:
- ✅ Trending products with segment breakdown
- ✅ Growth patterns
- ✅ Time-series insights
- ✅ Natural language format
- ✅ Actionable recommendations
- ✅ Proactive suggestions

**Validation Criteria**:
- Response time: < 60 seconds
- Response contains trending products
- Response includes segment breakdown
- Response includes growth patterns
- Response includes recommendations

**Data Sources**: `gold_sales_fact` + `gold_product_dim` + `gold_customer_dim` + `gold_date_dim`

---

## Error Handling Test Cases (FR-022)

### TC-013: Ambiguous Query Handling
**Query**: "Show me customer data"

**Expected Response**:
- ✅ Multiple interpretations with recommendations
- ✅ Specific guidance on how to refine query
- ✅ Natural language format
- ✅ Suggestions for clarification

**Validation Criteria**:
- Response provides multiple interpretations
- Response includes specific guidance
- Response suggests how to refine query

**Acceptance Scenario**: Edge case from spec.md

---

### TC-014: Vague Query Handling
**Query**: "What are the trends?"

**Expected Response**:
- ✅ Multiple interpretations (product trends, customer trends, channel trends)
- ✅ Specific guidance on how to refine query
- ✅ Natural language format
- ✅ Suggestions for clarification

**Validation Criteria**:
- Response provides multiple interpretations
- Response includes specific guidance
- Response suggests how to refine query

---

### TC-015: Permission Error Handling
**Query**: "Show me customer purchase data from schema X" (where user lacks permissions)

**Expected Response**:
- ✅ Clear error message indicating which data is unavailable
- ✅ Specific guidance on how to request access
- ✅ Actionable suggestions
- ✅ Natural language format

**Validation Criteria**:
- Response indicates permission error
- Response specifies which data is unavailable
- Response includes actionable guidance (how to request access)

**Acceptance Scenario**: #12 from spec.md

---

### TC-016: No Results Error Handling
**Query**: "Show me sales for Product X in January 2020" (product doesn't exist or no sales in that period)

**Expected Response**:
- ✅ Clear error message indicating no data found
- ✅ Available data range specified
- ✅ Alternative suggestions
- ✅ Natural language format

**Validation Criteria**:
- Response indicates no results
- Response specifies available data range
- Response includes alternative suggestions

---

## Multi-Domain Detection Test Cases (FR-021)

### TC-017: Multi-Domain Query Detection
**Query**: "Which products are frequently abandoned in carts and do we have inventory issues with those items?"

**Expected Response**:
- ✅ Multi-domain redirect message
- ✅ Explanation why query is out of scope
- ✅ Suggestion to use multi-domain agent
- ✅ Natural language format

**Validation Criteria**:
- Response detects multi-domain query
- Response explains why it's out of scope
- Response suggests multi-domain agent
- Response includes suggested rephrased query

**Keywords Triggering Detection**: "inventory issues"

---

### TC-018: Stock Levels Query Detection
**Query**: "Show me products with high cart abandonment and their current stock levels"

**Expected Response**:
- ✅ Multi-domain redirect message
- ✅ Explanation why query is out of scope
- ✅ Suggestion to use multi-domain agent
- ✅ Natural language format

**Validation Criteria**:
- Response detects multi-domain query
- Response explains why it's out of scope
- Response suggests multi-domain agent

**Keywords Triggering Detection**: "stock levels"

---

### TC-019: Out of Stock Query Detection
**Query**: "Which customer segments buy products that are out of stock?"

**Expected Response**:
- ✅ Multi-domain redirect message
- ✅ Explanation why query is out of scope
- ✅ Suggestion to use multi-domain agent
- ✅ Natural language format

**Validation Criteria**:
- Response detects multi-domain query
- Response explains why it's out of scope
- Response suggests multi-domain agent

**Keywords Triggering Detection**: "out of stock"

---

## Response Quality Validation Criteria

### Natural Language (FR-012)
- ✅ Response is in conversational, business-friendly language
- ✅ No raw SQL unless specifically requested
- ✅ Clear, simple explanations
- ✅ Structured with bullet points or numbered lists

### Actionable Recommendations (FR-020)
- ✅ Response includes 1-3 actionable recommendations
- ✅ Recommendations are specific and actionable
- ✅ Recommendations are relevant to the query

### Proactive Suggestions (FR-014)
- ✅ Response includes 1-3 related insights at the end
- ✅ Suggestions are specific and actionable
- ✅ Suggestions complement the current answer

### Response Structure
- ✅ Direct answer to question
- ✅ Key metrics with specific numbers
- ✅ Insights explaining what data means
- ✅ Actionable recommendations
- ✅ Source citation (indicates data sources)

---

## Performance Benchmarks

### Simple Queries
- **Target**: < 10 seconds
- **Acceptable**: < 15 seconds
- **Unacceptable**: >= 15 seconds

### Medium Complexity Queries
- **Target**: < 30 seconds
- **Acceptable**: < 45 seconds
- **Unacceptable**: >= 45 seconds

### Complex Queries
- **Target**: < 60 seconds
- **Acceptable**: < 90 seconds
- **Unacceptable**: >= 90 seconds

---

## Validation Checklist

After running all test cases, verify:

- [ ] **Simple Queries**: All 5 test cases pass, response time < 10 seconds
- [ ] **Medium Complexity Queries**: All 5 test cases pass, response time < 30 seconds
- [ ] **Complex Queries**: All 2 test cases pass, response time < 60 seconds
- [ ] **Error Handling**: All 4 test cases pass, responses include actionable guidance
- [ ] **Multi-Domain Detection**: All 3 test cases pass, queries are detected and redirected
- [ ] **Response Quality**: All responses are in natural language, include recommendations and insights
- [ ] **Performance Targets**: All queries meet performance targets
- [ ] **Acceptance Scenarios**: All 12 acceptance scenarios from spec.md are covered

---

## Test Execution

Use the test notebook `10-genie-rooms/notebooks/test-genie-configuration.ipynb` to execute these test cases.

**Test Notebook Features**:
- Automated test execution
- Response quality validation
- Performance measurement
- Error handling validation
- Multi-domain detection validation
- Summary reporting

---

## References

- **Sample Queries**: `10-genie-rooms/genie-configs/customer-behavior/sample_queries.md`
- **Genie Instructions**: `10-genie-rooms/genie-configs/customer-behavior/instructions.md`
- **Data Model**: `10-genie-rooms/genie-configs/customer-behavior/data_model.md`
- **Feature Specification**: `specs/003-cutomer-behavior-genie/spec.md`
- **Test Notebook**: `10-genie-rooms/notebooks/test-genie-configuration.ipynb`

