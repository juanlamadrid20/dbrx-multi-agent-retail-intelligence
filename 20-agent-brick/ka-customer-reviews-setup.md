# Customer Reviews Knowledge Assistant Agent Setup

This document describes the configuration for the Customer Reviews Knowledge Assistant Agent Brick in Databricks.

## Overview

The Customer Reviews Knowledge Agent uses Vector Search to provide semantic search capabilities over customer feedback, enabling natural language queries about product reviews, shopping experiences, and return feedback.

**Integration Point**: This agent complements the existing Customer Behavior and Inventory Genie agents, completing the "trifecta" of retail intelligence:
- **Customer Behavior Genie**: Quantitative customer analytics (purchases, revenue, segments)
- **Inventory Genie**: Stock levels, stockouts, replenishment
- **Customer Reviews Agent**: Qualitative customer sentiment and feedback

---

## Data Source

| Property | Value |
|----------|-------|
| Table | `juan_dev.retail.gold_customer_reviews` |
| Vector Search Index | `juan_dev.retail.gold_customer_reviews_idx` |
| Total Reviews | ~5,000 |
| Embedding Column | `review_text` |

### Review Types Distribution
| Type | Percentage | Description |
|------|------------|-------------|
| Product Reviews | 60% | Quality, fit, style, fabric feedback |
| Purchase Experience | 20% | Shipping, packaging, service |
| Return Feedback | 20% | Return reasons, exchange experiences |

---

## Agent Brick Configuration

### Basic Info

| Field | Value |
|-------|-------|
| **Name** | `retail-intelligence-customer-reviews` |
| **Description** | Customer Reviews Knowledge Agent for Fashion Retail Intelligence. Answers questions about customer feedback, product reviews, shopping experiences, and return feedback using semantic search over 5,000+ customer reviews. |

### Knowledge Sources

| Field | Value |
|-------|-------|
| **Type** | Vector Search Index |
| **Source** | `juan_dev.retail.gold_customer_reviews_idx` |
| **Name** | `gold_customer_reviews_idx` |
| **Doc URI Column** | `review_id` |
| **Text Column** | `review_text` |

### Content Description

```
Customer reviews for a fashion retail company including:
- Product reviews: feedback on apparel, footwear, and accessories covering fit, quality, fabric, sizing, comfort, and style
- Purchase experience reviews: shipping speed, packaging quality, customer service, and checkout experience  
- Return feedback: return reasons, exchange experiences, and refund processing

Reviews include ratings (1-5 stars), are linked to customer segments (VIP, Premium, Loyal, Regular, New), and cover product categories like tops, dresses, outerwear, sneakers, boots, bags, and jewelry. Use this to answer questions about customer sentiment, common complaints, product quality feedback, and shopping experience insights.
```

### Instructions

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

## Test Queries

### Vector Search Index Queries

Use these queries to test the raw vector search index directly in Databricks:

#### Product Quality Queries
```sql
-- Test similarity search for sizing issues
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'sizing runs small need to order larger',
  num_results => 10
)

-- join product
SELECT vs.*, pd.*
FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'fabric quality feels cheap scratchy uncomfortable',
  num_results => 10
) AS vs
LEFT JOIN juan_dev.retail.gold_product_dim AS pd
  ON vs.product_key = pd.product_key
```

```sql
-- Test search for fabric quality feedback
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'fabric quality feels cheap scratchy uncomfortable',
  num_results => 10
)
```

```sql
-- Test search for positive footwear reviews
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'comfortable shoes great arch support all day wear',
  num_results => 10
)
```

#### Shopping Experience Queries
```sql
-- Test search for shipping complaints
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'shipping took too long delayed package',
  num_results => 10
)
```

```sql
-- Test search for positive delivery experiences
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'fast shipping beautiful packaging arrived early',
  num_results => 10
)
```

#### Return Feedback Queries
```sql
-- Test search for return process feedback
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'return process refund exchange difficult',
  num_results => 10
)
```

```sql
-- Test search for sizing-related returns
SELECT * FROM VECTOR_SEARCH(
  index => 'juan_dev.retail.gold_customer_reviews_idx',
  query => 'had to return wrong size didnt fit',
  num_results => 10
)
```


---

### Knowledge Assistant Agent Queries

Use these natural language queries to test the Knowledge Assistant Agent:

#### Product Feedback Questions

| Category | Query |
|----------|-------|
| **Sizing** | "What are customers saying about sizing accuracy for apparel?" |
| **Sizing** | "Do shoes run true to size or should customers order up?" |
| **Quality** | "What's the feedback on fabric quality for our tops and dresses?" |
| **Quality** | "Are there complaints about products falling apart or poor stitching?" |
| **Fit** | "What do customers say about the fit of our outerwear?" |
| **Value** | "Do customers feel our products are worth the price?" |

#### Category-Specific Questions

| Category | Query |
|----------|-------|
| **Footwear** | "What are the most common complaints about our footwear?" |
| **Footwear** | "How do customers describe the comfort of our shoes?" |
| **Apparel** | "What do customers love most about our clothing?" |
| **Accessories** | "Are customers happy with the quality of our bags and accessories?" |

#### Sentiment Analysis Questions

| Category | Query |
|----------|-------|
| **Negative** | "What are the top reasons customers give negative reviews?" |
| **Negative** | "Show me reviews from frustrated customers" |
| **Positive** | "What makes customers give 5-star reviews?" |
| **Mixed** | "Find reviews where customers had both positive and negative things to say" |

#### Shopping Experience Questions

| Category | Query |
|----------|-------|
| **Shipping** | "What do customers think about our shipping speed?" |
| **Packaging** | "How do customers describe our packaging quality?" |
| **Service** | "Are there complaints about customer service?" |
| **Website** | "Any feedback about the checkout or ordering process?" |

#### Return Experience Questions

| Category | Query |
|----------|-------|
| **Process** | "How easy do customers find our return process?" |
| **Reasons** | "What are the main reasons customers return products?" |
| **Refunds** | "Are customers happy with refund timing?" |

#### Customer Segment Questions

| Category | Query |
|----------|-------|
| **VIP** | "What are VIP customers saying in their reviews?" |
| **New** | "What's the experience like for first-time customers?" |
| **Loyal** | "How do loyal customers describe their shopping experience?" |

#### Cross-Domain Questions (Multi-Agent)

These questions can bridge to other agents:

| Query | Bridges To |
|-------|------------|
| "Are there complaints about products that are frequently out of stock?" | Inventory Agent |
| "What do our highest-spending customers complain about most?" | Customer Behavior Agent |
| "Do customers mention waiting for items to come back in stock?" | Inventory Agent |
| "What feedback do customers in different segments give about product quality?" | Customer Behavior Agent |

---

## Validation Checklist

After creating the agent, verify:

- [ ] Agent responds to natural language queries
- [ ] Reviews are cited with `review_id` references
- [ ] Responses distinguish between product reviews, purchase experience, and return feedback
- [ ] Agent correctly identifies sentiment patterns
- [ ] Agent provides actionable insights
- [ ] Agent appropriately defers quantitative questions to other agents

---

## Integration Notes

### Future Multi-Agent Integration

When integrating with the supervisor agent:

1. **Routing Logic**: Route questions containing keywords like "reviews", "feedback", "complaints", "customers say", "sentiment" to this agent

2. **Handoff Context**: When handing off from Customer Behavior agent, include relevant customer segment or product category context

3. **Combined Insights**: For cross-domain questions, aggregate responses from:
   - Customer Reviews Agent (qualitative sentiment)
   - Customer Behavior Genie (quantitative metrics)
   - Inventory Genie (stock availability)

### Example Cross-Domain Query Flow

**User**: "Why are we losing VIP customers?"

1. **Customer Behavior Agent**: Identifies VIP customers with declining purchase frequency
2. **Customer Reviews Agent**: Surfaces negative feedback from VIP segment
3. **Inventory Agent**: Checks if products favored by VIPs have stockout issues
4. **Supervisor**: Synthesizes insights into actionable recommendation

