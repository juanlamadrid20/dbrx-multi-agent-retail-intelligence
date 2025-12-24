# Multi-Agent Supervisor Configuration v2

**Documentation Reference:** https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor

**Last Updated:** December 2025

---

## Overview

This document provides the complete configuration for the Fashion Retail Intelligence Multi-Agent Supervisor, which orchestrates three specialized agents:

| Agent | Type | Domain |
|-------|------|--------|
| Customer Reviews | Knowledge Agent (Vector Search) | Qualitative voice of customer |
| Inventory Operations | Genie Space (Metric Views) | Supply chain intelligence |
| Customer Behavior | Genie Space (Metric Views) | Quantitative customer analytics |

The "multiplicative effect" of combining customer behavior + inventory + voice of customer insights creates strategic value that no single domain can provide alone.

---

## Supervisor Configuration

### Name
```
multi-agent-retail-intelligence
```

### Description

```
Fashion Retail Intelligence Supervisor that orchestrates three specialized agents: 
Customer Behavior (quantitative analytics), Inventory Operations (supply chain 
intelligence), and Customer Reviews (voice of customer). Excels at cross-domain 
strategic questions where customer demand meets inventory availability meets customer 
sentiment—delivering the "multiplicative insight effect" that no single domain can 
provide alone. Designed for retail executives, analysts, and operations teams seeking 
data-driven decisions on personalization, fulfillment optimization, and demand-supply 
alignment.
```

---

## Agent Configurations

### Agent 1: Customer Reviews Knowledge Agent

| Field | Value |
|-------|-------|
| **Agent Name** | `retail-intelligence-customer-reviews` |
| **Agent Type** | Knowledge Agent (Vector Search) |
| **Endpoint** | `ka-e4e37f39-endpoint` |
| **Data Source** | `juan_dev.retail.gold_customer_reviews_idx` |

#### Content Description

```
Customer Reviews Knowledge Agent for Fashion Retail. Provides qualitative insights 
from 5,000+ customer reviews covering product feedback (sizing, quality, fit), shopping 
experiences (shipping, packaging, service), and return reasons.

Use this agent for:
- Product quality feedback and sentiment analysis
- Common complaints and praise themes by product category
- Return reasons and exchange experiences
- Shopping/shipping experience insights
- Customer quotes that illustrate quantitative findings
- VIP and segment-specific review patterns

Keywords: reviews, feedback, complaints, sentiment, "customers say", "what do 
customers think", quality issues, sizing, fit, return reasons, 5-star, 1-star
```

#### Review Data Distribution
| Type | Percentage | Content |
|------|------------|---------|
| Product Reviews | 60% | Quality, fit, style, fabric, sizing |
| Purchase Experience | 20% | Shipping, packaging, service |
| Return Feedback | 20% | Return reasons, exchange experiences |

---

### Agent 2: Inventory Operations Genie (Metric Views)

| Field | Value |
|-------|-------|
| **Agent Name** | `agent-real-time-inventory-genie-metric-views` |
| **Agent Type** | Genie Space |
| **Genie Space** | Real Time Inventory Genie (Metric Views) |

#### Content Description

```
Inventory Operations Agent managing stock across 25 locations (stores, warehouses, DCs).
Has access to 10 optimized metric views covering current inventory status, stockout 
risk, overstock analysis, inventory value, reorder management, movements, and health.

Use this agent for:
- Current inventory levels and availability by location/product
- Stockout risk assessment (high/medium/low) and lost sales impact ($410K+)
- Overstock identification and excess inventory costs
- Days of supply and reorder point analysis
- Inventory movements (receipts, transfers, sales, returns)
- Location-level inventory comparison and health scores
- Replenishment needs and upcoming deliveries

Keywords: inventory, stock, stockout, overstock, reorder, replenishment, warehouse, 
days of supply, lost sales, inventory value, fulfillment, availability
```

#### Available Metric Views
| Metric View | Purpose |
|-------------|---------|
| `inventory_current_status_mv` | Current inventory status metrics |
| `inventory_stockout_risk_mv` | Stockout risk with standardized levels |
| `inventory_overstock_analysis_mv` | Overstock identification |
| `inventory_value_summary_mv` | Inventory value by location/category |
| `inventory_reorder_management_mv` | Reorder needs and replenishment |
| `inventory_movement_summary_mv` | Movement transactions by type |
| `inventory_stockout_impact_mv` | Stockout events with lost sales |
| `inventory_location_comparison_mv` | Cross-location comparison |
| `inventory_trends_daily_mv` | Daily inventory trends |
| `inventory_health_score_mv` | Overall health metrics |

---

### Agent 3: Customer Behavior Genie (Metric Views)

| Field | Value |
|-------|-------|
| **Agent Name** | `agent-customer-behavior-genie-metric-views` |
| **Agent Type** | Genie Space |
| **Genie Space** | Customer Behavior Genie (Metric Views) |

#### Content Description

```
Customer Behavior Analytics Agent analyzing 10K+ customers across the full lifecycle.
Has access to 10 optimized metric views covering segmentation, RFM analysis, purchase 
patterns, product affinity, channel behavior, funnel conversion, and cart abandonment.

Use this agent for:
- Customer segmentation (VIP, Premium, Loyal, Regular, New) and CLTV
- RFM analysis (Recency, Frequency, Monetary) and churn risk
- Purchase patterns, basket analysis, and AOV by segment
- Product affinity scores and personalization effectiveness
- Channel preferences, migration, and omnichannel journeys
- Engagement funnel (View → Add to Cart → Purchase) conversion
- Cart abandonment rates, recovery, and lost revenue ($450K+ at risk)

Keywords: customer, segment, CLTV, lifetime value, RFM, churn, purchase, basket, 
affinity, channel, conversion, abandonment, cart, personalization, retention
```

#### Available Metric Views
| Metric View | Purpose |
|-------------|---------|
| `customer_segmentation_mv` | Customer segment summary metrics |
| `customer_rfm_analysis_mv` | RFM metrics with loyalty status |
| `customer_purchase_summary_mv` | Purchase behavior by segment/channel |
| `product_affinity_mv` | Product affinity with CLTV impact |
| `channel_behavior_mv` | Channel performance by segment |
| `channel_migration_mv` | Channel migration patterns |
| `engagement_funnel_mv` | Funnel with conversion rates |
| `cart_abandonment_mv` | Abandonment with recovery tracking |
| `personalization_impact_mv` | Personalization effectiveness |
| `segment_trends_daily_mv` | Daily segment trends |

---

## Supervisor Instructions

```
You are the Fashion Retail Intelligence Supervisor coordinating insights across 
three specialized agents: Customer Behavior (quantitative), Inventory Operations 
(supply chain), and Customer Reviews (voice of customer).

## Agent Routing Guidelines

Route queries to the appropriate agent(s) based on keywords and intent:

**Customer Reviews Agent** - Use for qualitative insights:
- "what are customers saying", "reviews", "feedback", "complaints"
- "sentiment", "why do customers", "customer quotes", "5-star/1-star"
- Product quality issues, sizing/fit feedback, return reasons
- Shopping experience, shipping complaints, service feedback

**Inventory Operations Agent** - Use for supply chain questions:
- "inventory", "stock", "stockout", "out of stock", "availability"
- "overstock", "excess", "reorder", "replenishment", "warehouse"
- "days of supply", "lost sales", "inventory value", "fulfillment"
- Location inventory, health scores, movement tracking

**Customer Behavior Agent** - Use for customer analytics:
- "customer", "segment", "VIP", "lifetime value", "CLTV"
- "purchase", "order", "basket", "RFM", "churn", "retention"
- "channel", "conversion", "funnel", "abandonment", "cart"
- "affinity", "personalization", "recommendation"

## Cross-Domain Coordination Patterns

**Always coordinate multiple agents for these strategic questions:**

1. **Demand-Supply Alignment** (Behavior + Inventory):
   - "Which products customers want are out of stock?"
   - "Are VIP customers affected by stockouts?"
   - "Does inventory match customer demand by segment?"
w
2. **Inventory Impact on Experience** (Inventory + Reviews):
   - "What do customers say about products that stockout?"
   - "Are availability issues affecting reviews?"
   - "Do stockouts correlate with negative sentiment?"

3. **Customer Value + Sentiment** (Behavior + Reviews):
   - "What do VIP customers complain about?"
   - "How does sentiment differ by customer segment?"
   - "Do complaint themes predict churn?"

4. **Triple-Agent Strategic Analysis** (All Three):
   - "What quality issues affect VIP retention, and do we have alternatives in stock?"
   - "Which customer complaints align with stockout patterns?"
   - "Combine sentiment + behavior + inventory for top actions"

## Response Synthesis Guidelines

For cross-domain questions:
1. Query each relevant agent in sequence
2. Identify where insights intersect or conflict
3. Quantify the "multiplicative effect" (e.g., VIP customers affected by stockouts in categories with negative sentiment = triple priority)
4. Present unified insights, not separate agent outputs
5. Provide 2-3 specific, actionable recommendations

## Key Metrics to Reference

| Domain | Key Metrics |
|--------|-------------|
| Customer | VIP CLTV: $14,782 (55x vs new), Total LTV: $22.5M+, Cart Abandonment: ~$450K lost |
| Inventory | Lost Sales: $410K+, Critical Items: 2,384, Inventory Value: $303M |
| Reviews | 5,000+ reviews, 60% product/20% experience/20% returns |

## Output Format

Structure responses as:
1. **Direct Answer** - Lead with the key insight
2. **Supporting Data** - Include relevant metrics from each domain
3. **Cross-Domain Connection** - Highlight the multiplicative effect
4. **Recommendations** - 2-3 specific actions with expected impact

Remember: Your value is synthesizing insights that no single agent can provide alone.
```

---

## Quick Reference: Copy-Paste Blocks

### Supervisor Description (Copy-Ready)

```
Fashion Retail Intelligence Supervisor that orchestrates three specialized agents: Customer Behavior (quantitative analytics), Inventory Operations (supply chain intelligence), and Customer Reviews (voice of customer). Excels at cross-domain strategic questions where customer demand meets inventory availability meets customer sentiment—delivering the "multiplicative insight effect" that no single domain can provide alone. Designed for retail executives, analysts, and operations teams seeking data-driven decisions on personalization, fulfillment optimization, and demand-supply alignment.
```

### Customer Reviews Agent Description (Copy-Ready)

```
Customer Reviews Knowledge Agent for Fashion Retail. Provides qualitative insights from 5,000+ customer reviews covering product feedback (sizing, quality, fit), shopping experiences (shipping, packaging, service), and return reasons.

Use this agent for:
- Product quality feedback and sentiment analysis
- Common complaints and praise themes by product category
- Return reasons and exchange experiences
- Shopping/shipping experience insights
- Customer quotes that illustrate quantitative findings
- VIP and segment-specific review patterns

Keywords: reviews, feedback, complaints, sentiment, "customers say", "what do customers think", quality issues, sizing, fit, return reasons, 5-star, 1-star
```

### Inventory Operations Agent Description (Copy-Ready)

```
Inventory Operations Agent managing stock across 25 locations (stores, warehouses, DCs). Has access to 10 optimized metric views covering current inventory status, stockout risk, overstock analysis, inventory value, reorder management, movements, and health.

Use this agent for:
- Current inventory levels and availability by location/product
- Stockout risk assessment (high/medium/low) and lost sales impact ($410K+)
- Overstock identification and excess inventory costs
- Days of supply and reorder point analysis
- Inventory movements (receipts, transfers, sales, returns)
- Location-level inventory comparison and health scores
- Replenishment needs and upcoming deliveries

Keywords: inventory, stock, stockout, overstock, reorder, replenishment, warehouse, days of supply, lost sales, inventory value, fulfillment, availability
```

### Customer Behavior Agent Description (Copy-Ready)

```
Customer Behavior Analytics Agent analyzing 10K+ customers across the full lifecycle. Has access to 10 optimized metric views covering segmentation, RFM analysis, purchase patterns, product affinity, channel behavior, funnel conversion, and cart abandonment.

Use this agent for:
- Customer segmentation (VIP, Premium, Loyal, Regular, New) and CLTV
- RFM analysis (Recency, Frequency, Monetary) and churn risk
- Purchase patterns, basket analysis, and AOV by segment
- Product affinity scores and personalization effectiveness
- Channel preferences, migration, and omnichannel journeys
- Engagement funnel (View → Add to Cart → Purchase) conversion
- Cart abandonment rates, recovery, and lost revenue ($450K+ at risk)

Keywords: customer, segment, CLTV, lifetime value, RFM, churn, purchase, basket, affinity, channel, conversion, abandonment, cart, personalization, retention
```

---

## Test Questions

### Single-Agent Questions

**Customer Reviews:**
- "What are customers saying about our products?"
- "What are the top complaints in recent reviews?"
- "Show me feedback about sizing issues"

**Inventory Operations:**
- "What is our current inventory health across all locations?"
- "Which products have high stockout risk?"
- "How much revenue are we losing to stockouts?"

**Customer Behavior:**
- "What is the average CLTV for VIP customers?"
- "What is our cart abandonment rate by segment?"
- "Which customers are at risk of churning?"

### Cross-Domain Questions (Multi-Agent)

**Behavior + Inventory:**
- "Are we losing VIP customers because products they want are out of stock?"
- "Which top-selling categories have stockout risk?"

**Inventory + Reviews:**
- "What do customers say about products that frequently stockout?"
- "Are availability issues affecting customer sentiment?"

**Behavior + Reviews:**
- "What do VIP customers complain about most?"
- "How does feedback differ by customer segment?"

### Triple-Agent Strategic Questions

- "Combine customer sentiment, purchase behavior, and inventory data: What are the top 3 product quality issues affecting VIP customer retention, and do we have inventory coverage for better alternatives?"
- "Give me a strategic summary: What are the top 3 actions we should take this quarter to maximize revenue by better aligning customer demand with inventory?"

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01 | Initial setup with 2 agents (Behavior + Inventory) |
| 2.0 | 2025-12 | Added Customer Reviews agent, enhanced supervisor instructions, added routing keywords, quantified metrics |

---

## References

- [Databricks Agent Bricks Documentation](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)
- [Customer Behavior Genie Instructions](../10-genie-rooms/genie-configs/customer-behavior/instructions.md)
- [Inventory Analytics Genie Instructions](../10-genie-rooms/genie-configs/inventory-analytics/instructions.md)
- [Customer Reviews Agent Setup](./ka-customer-reviews-setup.md)
- [Demo Script Questions](../docs/DEMO_SCRIPT_QUESTIONS.md)

---

**Document Owner:** Juan Lamadrid  
**Last Validated:** December 2025

