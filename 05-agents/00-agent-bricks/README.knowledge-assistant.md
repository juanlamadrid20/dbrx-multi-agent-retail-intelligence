# Customer Reviews Knowledge Assistant

**Documentation Reference:** https://docs.databricks.com/aws/en/generative-ai/agent-bricks/knowledge-assistant

---

## Overview

The Customer Reviews Knowledge Assistant is a standalone Agent Brick that provides semantic search capabilities over customer feedback. It uses Vector Search to enable natural language queries about product reviews, shopping experiences, and return feedback.

**Integration Point**: This agent complements the Customer Behavior and Inventory Genie agents, completing the "trifecta" of retail intelligence:

| Agent | Type | Domain |
|-------|------|--------|
| Customer Behavior | Genie Space | Quantitative customer analytics |
| Inventory Operations | Genie Space | Supply chain intelligence |
| **Customer Reviews** | **Knowledge Assistant** | **Qualitative voice of customer** |

Once deployed, this Knowledge Assistant can be added to a Multi-Agent Supervisor via its Agent Endpoint.

---

## Prerequisites

Before creating the Knowledge Assistant, ensure:

1. **Vector Search Index exists**: `juan_use1_catalog.retail.gold_customer_reviews_idx`
2. **Source table exists**: `juan_use1_catalog.retail.gold_customer_reviews`
3. **Index is synced** and ready for queries

---

## Knowledge Assistant Configuration

### Basic Info

| Field | Value |
|-------|-------|
| **Name** | `retail-intelligence-customer-reviews` |

**Description:**

```
Customer Reviews Knowledge Agent for Fashion Retail Intelligence. Answers questions 
about customer feedback, product reviews, shopping experiences, and return feedback 
using semantic search over 5,000+ customer reviews.
```

---

### Knowledge Sources

| Field | Value |
|-------|-------|
| **Type** | Vector Search Index |
| **Source** | `juan_use1_catalog.retail.gold_customer_reviews_idx` |
| **Name** | `gold_customer_reviews_idx` |
| **Doc URI Column** | `review_id` |
| **Text Column** | `review_text` |

**Content Description:**

```
Customer reviews for a fashion retail company including:
- Product reviews: feedback on apparel, footwear, and accessories covering fit, quality, 
  fabric, sizing, comfort, and style
- Purchase experience reviews: shipping speed, packaging quality, customer service, and 
  checkout experience
- Return feedback: return reasons, exchange experiences, and refund processing

Reviews include ratings (1-5 stars), are linked to customer segments (VIP, Premium, Loyal, 
Regular, New), and cover product categories like tops, dresses, outerwear, sneakers, boots, 
bags, and jewelry. Use this to answer questions about customer sentiment, common complaints, 
product quality feedback, and shopping experience insights.
```

---

### Instructions (Optional)

```
You are a Customer Reviews Analyst for a fashion retail company. When answering questions:

1. **Cite specific reviews**: Reference review IDs and quote relevant excerpts
2. **Summarize sentiment**: Indicate overall sentiment (positive/negative/mixed) with approximate percentages when relevant
3. **Identify patterns**: Look for common themes across multiple reviews
4. **Be specific about products**: Mention product categories, brands, or specific items when referenced in reviews
5. **Distinguish review types**: Clarify if feedback is about the product itself, the shopping/shipping experience, or a return

For quantitative questions, explain that you're providing qualitative insights from review text, not aggregated statistics. Direct users to the Customer Behavior agent for numerical analytics.

Always be helpful and provide actionable insights from customer feedback.
```

---

## Data Source Details

| Property | Value |
|----------|-------|
| Source Table | `juan_use1_catalog.retail.gold_customer_reviews` |
| Vector Search Index | `juan_use1_catalog.retail.gold_customer_reviews_idx` |
| Total Reviews | ~5,000 |
| Embedding Column | `review_text` |

### Review Types Distribution

| Type | Percentage | Description |
|------|------------|-------------|
| Product Reviews | 60% | Quality, fit, style, fabric feedback |
| Purchase Experience | 20% | Shipping, packaging, service |
| Return Feedback | 20% | Return reasons, exchange experiences |

---

## Test Queries

### Vector Search Index (SQL)

Use these queries to test the vector search index directly in Databricks:

#### Product Quality

```sql
-- Sizing issues
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'sizing runs small need to order larger',
  num_results => 10
)

-- Fabric quality with product join
SELECT 
  vs.*, 
  pd.*
FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'fabric quality feels cheap scratchy uncomfortable',
  num_results => 10
) AS vs
LEFT JOIN juan_use1_catalog.retail.gold_product_dim AS pd
  ON vs.product_brand = pd.brand

-- Positive footwear reviews
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'comfortable shoes great arch support all day wear',
  num_results => 10
)
```

#### Shopping Experience

```sql
-- Shipping complaints
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'shipping took too long delayed package',
  num_results => 10
)

-- Positive delivery experiences
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'fast shipping beautiful packaging arrived early',
  num_results => 10
)
```

#### Return Feedback

```sql
-- Return process feedback
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'return process refund exchange difficult',
  num_results => 10
)

-- Sizing-related returns
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_use1_catalog.retail.gold_customer_reviews_idx',
  query => 'had to return wrong size didnt fit',
  num_results => 10
)
```

---

### Knowledge Assistant (Natural Language)

Use these queries to test the deployed Knowledge Assistant:

#### Product Feedback

| Category | Query |
|----------|-------|
| Sizing | "What are customers saying about sizing accuracy for apparel?" |
| Sizing | "Do shoes run true to size or should customers order up?" |
| Quality | "What's the feedback on fabric quality for our tops and dresses?" |
| Quality | "Are there complaints about products falling apart or poor stitching?" |
| Fit | "What do customers say about the fit of our outerwear?" |
| Value | "Do customers feel our products are worth the price?" |

#### Category-Specific

| Category | Query |
|----------|-------|
| Footwear | "What are the most common complaints about our footwear?" |
| Footwear | "How do customers describe the comfort of our shoes?" |
| Apparel | "What do customers love most about our clothing?" |
| Accessories | "Are customers happy with the quality of our bags and accessories?" |

#### Sentiment Analysis

| Category | Query |
|----------|-------|
| Negative | "What are the top reasons customers give negative reviews?" |
| Negative | "Show me reviews from frustrated customers" |
| Positive | "What makes customers give 5-star reviews?" |
| Mixed | "Find reviews where customers had both positive and negative things to say" |

#### Shopping Experience

| Category | Query |
|----------|-------|
| Shipping | "What do customers think about our shipping speed?" |
| Packaging | "How do customers describe our packaging quality?" |
| Service | "Are there complaints about customer service?" |

#### Return Experience

| Category | Query |
|----------|-------|
| Process | "How easy do customers find our return process?" |
| Reasons | "What are the main reasons customers return products?" |
| Refunds | "Are customers happy with refund timing?" |

#### Customer Segment

| Category | Query |
|----------|-------|
| VIP | "What are VIP customers saying in their reviews?" |
| New | "What's the experience like for first-time customers?" |
| Loyal | "How do loyal customers describe their shopping experience?" |

---

## Validation Checklist

After deploying the Knowledge Assistant, verify:

- [ ] Agent responds to natural language queries
- [ ] Reviews are cited with `review_id` references
- [ ] Responses distinguish between product reviews, purchase experience, and return feedback
- [ ] Agent correctly identifies sentiment patterns
- [ ] Agent provides actionable insights
- [ ] Agent appropriately defers quantitative questions

---

## Integration with Multi-Agent Supervisor

Once deployed, note your Knowledge Assistant's **Agent Endpoint** (visible in the Agent Brick list).

To add to a Multi-Agent Supervisor:

1. Open your Multi-Agent Supervisor configuration
2. Click "Add Agent"
3. Select your Knowledge Assistant by its Agent Endpoint
4. Add a content description for routing (see [README.multi-agent-supervisor.md](./README.multi-agent-supervisor.md))

---

## References

- [Databricks Knowledge Assistant Documentation](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/knowledge-assistant)
- [Vector Search Index Setup](../00-data/04-vector-search-create.ipynb)
- [Multi-Agent Supervisor Setup](./README.multi-agent-supervisor.md)

