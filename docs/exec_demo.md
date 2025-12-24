# Executive Demo Questions for Multi-Agent Retail Intelligence

**Audience:** CEO and Key Executives  
**Demo Duration:** 15-20 minutes  
**Platform:** Databricks Agent Bricks Multi-Agent Supervisor

---

## Demo Context

This demo showcases a **Multi-Agent Supervisor** powered by Databricks Agent Bricks that orchestrates two specialized Genie rooms:

- **Customer Behavior Agent**: Customer segmentation, CLTV, cart abandonment, channel behavior, RFM analysis
- **Inventory Operations Agent**: Stockout risk, lost sales, inventory health, reorder management

The "multiplicative effect" of combining customer + inventory insights creates strategic value that neither domain can provide alone.

---

## Recommended Demo Flow

### Act 1: Setting the Stage (3-4 questions)

**Question 1 - Executive Overview:**
> "What is our current inventory health status across all locations, and how much revenue are we losing to stockouts?"

*Expected insight: 2,384 products in Critical status, $410K+ lost revenue from stockouts across locations*

**Question 2 - VIP Customer Focus:**
> "How many VIP customers do we have and what is their average lifetime value compared to other segments?"

*Expected insight: 500 VIP customers with $14,782 avg CLTV vs $270 for new customers (55x multiplier)*

**Question 3 - Cart Abandonment Problem:**
> "What is our cart abandonment rate and how much potential revenue are we leaving on the table?"

*Expected insight: ~97% abandonment rate, $450K+ in lost revenue across cart/shipping/payment stages*

---

### Act 2: Cross-Domain Intelligence (4-5 questions)

**Question 4 - The Big Picture (STAR QUESTION):**
> "Which of our top-selling product categories have stockout risk, and which customer segments are most affected?"

*Demonstrates multi-agent coordination: combines product affinity from customer agent with stockout risk from inventory agent*

**Question 5 - Demand-Supply Alignment:**
> "Are we losing VIP customers because products they want are out of stock? Show me the intersection of high-value customer demand and inventory gaps."

*Strategic insight: High CLTV customers may be churning due to stockouts in categories they prefer*

**Question 6 - Regional Opportunity:**
> "Compare inventory value and lost sales by region. Where should we prioritize inventory investment?"

*Expected insight: West region has $119M retail value but Central DC has highest lost sales ($355K)*

**Question 7 - Personalization + Availability:**
> "For products with high customer affinity scores, what is the current inventory availability? Are we missing personalization opportunities due to stockouts?"

*Shows the multiplicative effect: great recommendations mean nothing if product unavailable*

---

### Act 3: Actionable Insights (3-4 questions)

**Question 8 - Churn Risk Alert:**
> "Which customers are at risk of churning, and what can we do to retain them? Are there inventory issues affecting their experience?"

*Customer retention meets inventory operations*

**Question 9 - Urgent Actions:**
> "What products need immediate reordering across our flagship stores? Prioritize by lost sales impact."

*Expected insight: NYC, LA, Boston flagships all have 700+ apparel items with critical reorder status*

**Question 10 - Channel Optimization:**
> "How do our customers migrate between channels, and does our inventory allocation match their channel preferences?"

*Omnichannel strategy question that requires both agents*

---

### Act 4: Strategic Deep Dives (2-3 questions)

**Question 11 - Conversion Optimization:**
> "Where are customers dropping off in our purchase funnel, and is inventory availability a factor in cart abandonment?"

*Expected insight: low_inventory_trigger flag on cart abandonment events*

**Question 12 - Product Trends:**
> "What product categories are trending with our Loyal customers, and do we have adequate inventory coverage for the upcoming season?"

*Expected insight: Loyal segment drives 7,229 purchases in apparel - largest category with highest stockout risk*

**Question 13 (Closing Statement):**
> "Give me a strategic summary: What are the top 3 actions we should take this quarter to maximize revenue by better aligning customer demand with inventory?"

*Synthesizes all insights into executive action plan*

---

## Key Metrics to Highlight

| Domain | Metric | Value | Business Impact |
|--------|--------|-------|-----------------|
| Customer | VIP CLTV | $14,782 | 55x higher than new customers |
| Customer | Total Lifetime Value | $22.5M+ | Across all segments |
| Customer | Cart Abandonment | ~$450K lost | Recovery opportunity |
| Inventory | Lost Sales | $410K+ | From stockouts |
| Inventory | Critical Items | 2,384 products | Need immediate action |
| Inventory | Inventory Value | $303M retail | Capital optimization |
| Cross-Domain | Apparel at Risk | 10,687 SKUs | Top category by demand AND risk |

---

## Quick Reference: Copy-Paste Questions

### Single-Domain Questions (Customer Behavior)
```
How many VIP customers do we have and what is their average lifetime value compared to other segments?
```
```
What is our cart abandonment rate and how much potential revenue are we leaving on the table?
```
```
Which customers are at risk of churning, and what can we do to retain them?
```
```
Where are customers dropping off in our purchase funnel?
```

### Single-Domain Questions (Inventory Operations)
```
What is our current inventory health status across all locations, and how much revenue are we losing to stockouts?
```
```
What products need immediate reordering across our flagship stores? Prioritize by lost sales impact.
```
```
Compare inventory value and lost sales by region. Where should we prioritize inventory investment?
```

### Cross-Domain Questions (Multi-Agent Coordination)
```
Which of our top-selling product categories have stockout risk, and which customer segments are most affected?
```
```
Are we losing VIP customers because products they want are out of stock? Show me the intersection of high-value customer demand and inventory gaps.
```
```
For products with high customer affinity scores, what is the current inventory availability? Are we missing personalization opportunities due to stockouts?
```
```
How do our customers migrate between channels, and does our inventory allocation match their channel preferences?
```
```
What product categories are trending with our Loyal customers, and do we have adequate inventory coverage for the upcoming season?
```
```
Give me a strategic summary: What are the top 3 actions we should take this quarter to maximize revenue by better aligning customer demand with inventory?
```

---

## Demo Best Practices

1. **Start broad, go deep**: Begin with overview questions, then drill into specific areas executives show interest
2. **Let the AI tell the story**: The multi-agent supervisor will coordinate responses automatically
3. **Highlight the "multiplicative effect"**: Emphasize insights only possible by combining both domains
4. **End with actions**: Executive audiences want "what do we do about it?"
5. **Have backup questions ready**: If an area doesn't resonate, pivot to another domain

---

## Technical Details

### Data Schema
- **Catalog/Schema**: `juan_dev.retail`
- **Tables**: 12 dimension tables + 6 fact tables
- **Metric Views**: 20 pre-aggregated metric views for optimized queries

### Agent Configuration
- **Customer Behavior Genie**: 10 metric views covering segmentation, RFM, purchase patterns, affinity, channel behavior, funnel, abandonment
- **Inventory Operations Genie**: 10 metric views covering current status, stockout risk, overstock, value, reorder, movements, impact, location comparison, trends, health

### References
- Genie Room Instructions: `10-genie-rooms/genie-configs/customer-behavior/instructions.md`, `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
- Multi-Agent Setup: `20-agent-brick/mas-setup.md`

---

*Document generated: December 2025*  
*Last validated: All metrics verified against live data*

