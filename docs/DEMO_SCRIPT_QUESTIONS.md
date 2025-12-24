# Executive Demo Questions for Multi-Agent Retail Intelligence

**Audience:** CEO and Key Executives  
**Demo Duration:** 15-20 minutes  
**Platform:** Databricks Agent Bricks Multi-Agent Supervisor

---

## Demo Context

This demo showcases a **Multi-Agent Supervisor** powered by Databricks Agent Bricks that orchestrates three specialized agents:

- **Customer Behavior Agent**: Customer segmentation, CLTV, cart abandonment, channel behavior, RFM analysis
- **Inventory Operations Agent**: Stockout risk, lost sales, inventory health, reorder management
- **Customer Reviews Agent** (Vector Search RAG): Sentiment analysis, product feedback, purchase experiences, return reasons

The "multiplicative effect" of combining customer behavior + inventory + voice of customer insights creates strategic value that no single domain can provide alone. This three-way coordination enables data-driven decisions that connect what customers *do*, what we *have*, and what customers *say*.

---

## Recommended Demo Flow

### Act 1: Setting the Stage (4-5 questions)

**Question 1 - Executive Overview:**
> "What is our current inventory health status across all locations, and how much revenue are we losing to stockouts?"

*Expected insight: 2,384 products in Critical status, $410K+ lost revenue from stockouts across locations*

**Question 2 - VIP Customer Focus:**
> "How many VIP customers do we have and what is their average lifetime value compared to other segments?"

*Expected insight: 500 VIP customers with $14,782 avg CLTV vs $270 for new customers (55x multiplier)*

**Question 3 - Cart Abandonment Problem:**
> "What is our cart abandonment rate and how much potential revenue are we leaving on the table?"

*Expected insight: ~97% abandonment rate, $450K+ in lost revenue across cart/shipping/payment stages*

**Question 4 - Voice of Customer Overview:**
> "What are customers saying about our products? Show me the key themes from recent reviews."

*Expected insight: Sentiment distribution across 5,000+ reviews - top praise themes (quality, fit) and top complaint themes (sizing, shipping)*

---

### Act 2: Cross-Domain Intelligence (5-6 questions)

**Question 5 - The Big Picture (STAR QUESTION):**
> "Which of our top-selling product categories have stockout risk, and which customer segments are most affected?"

*Demonstrates multi-agent coordination: combines product affinity from customer agent with stockout risk from inventory agent*

**Question 6 - Demand-Supply Alignment:**
> "Are we losing VIP customers because products they want are out of stock? Show me the intersection of high-value customer demand and inventory gaps."

*Strategic insight: High CLTV customers may be churning due to stockouts in categories they prefer*

**Question 7 - Reviews + Inventory (NEW):**
> "For products with frequent stockouts, what are customers saying in their reviews? Are we losing brand goodwill due to availability issues?"

*Connects inventory gaps to customer sentiment - shows downstream reputation impact of stockouts*

**Question 8 - Reviews + Customer Behavior (NEW):**
> "What do our VIP customers complain about most? Are these issues affecting their retention?"

*Links high-value customer complaints to churn risk - prioritizes fixes by customer value*

**Question 9 - Personalization + Availability:**
> "For products with high customer affinity scores, what is the current inventory availability? Are we missing personalization opportunities due to stockouts?"

*Shows the multiplicative effect: great recommendations mean nothing if product unavailable*

---

### Act 3: Actionable Insights (4-5 questions)

**Question 10 - Churn Risk Alert:**
> "Which customers are at risk of churning, and what can we do to retain them? Are there inventory issues affecting their experience?"

*Customer retention meets inventory operations*

**Question 11 - Return Feedback Analysis (NEW):**
> "What patterns do we see in return feedback? Which issues should we escalate to product teams?"

*Expected insight: Top return reasons by category - sizing issues in apparel, comfort in footwear, quality in accessories*

**Question 12 - Urgent Actions:**
> "What products need immediate reordering across our flagship stores? Prioritize by lost sales impact."

*Expected insight: NYC, LA, Boston flagships all have 700+ apparel items with critical reorder status*

**Question 13 - Channel Optimization:**
> "How do our customers migrate between channels, and does our inventory allocation match their channel preferences?"

*Omnichannel strategy question that requires both agents*

---

### Act 4: Strategic Deep Dives (3-4 questions)

**Question 14 - Conversion Optimization:**
> "Where are customers dropping off in our purchase funnel, and is inventory availability a factor in cart abandonment?"

*Expected insight: low_inventory_trigger flag on cart abandonment events*

**Question 15 - Product Trends:**
> "What product categories are trending with our Loyal customers, and do we have adequate inventory coverage for the upcoming season?"

*Expected insight: Loyal segment drives 7,229 purchases in apparel - largest category with highest stockout risk*

**Question 16 - Triple-Agent Strategic Question (NEW STAR QUESTION):**
> "Combine customer sentiment, purchase behavior, and inventory data: What are the top 3 product quality issues affecting VIP customer retention, and do we have inventory coverage for better alternatives?"

*The ultimate cross-domain question: connects reviews (what they say) + behavior (what they do) + inventory (what we have)*

**Question 17 (Closing Statement):**
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
| Reviews | Total Reviews | ~5,000 | Voice of customer data |
| Reviews | Avg Rating | ~3.8 stars | Product satisfaction baseline |
| Reviews | Return Feedback | 20% of reviews | Quality improvement signals |
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

### Single-Domain Questions (Voice of Customer)
```
What are customers saying about our products? Show me the key themes from recent reviews.
```
```
What patterns do we see in return feedback? Which issues should we escalate to product teams?
```
```
What do customers love most about our brand? What themes emerge from 5-star reviews?
```
```
Are there any emerging quality issues in recent customer feedback we should address?
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

### Triple-Agent Questions (Reviews + Behavior + Inventory)
```
For products with frequent stockouts, what are customers saying in their reviews? Are we losing brand goodwill due to availability issues?
```
```
What do our VIP customers complain about most? Are these issues affecting their retention?
```
```
Combine customer sentiment, purchase behavior, and inventory data: What are the top 3 product quality issues affecting VIP customer retention, and do we have inventory coverage for better alternatives?
```
```
Give me a strategic summary: What are the top 3 actions we should take this quarter to maximize revenue by better aligning customer demand with inventory?
```

---

## Demo Best Practices

1. **Start broad, go deep**: Begin with overview questions, then drill into specific areas executives show interest
2. **Let the AI tell the story**: The multi-agent supervisor will coordinate responses automatically
3. **Highlight the "multiplicative effect"**: Emphasize insights only possible by combining all three domains
4. **Use Voice of Customer for emotional impact**: Customer quotes resonate with executives
5. **End with actions**: Executive audiences want "what do we do about it?"
6. **Have backup questions ready**: If an area doesn't resonate, pivot to another domain

---

## Technical Details

### Data Schema
- **Catalog/Schema**: `juan_dev.retail`
- **Tables**: 12 dimension tables + 7 fact tables (including customer reviews)
- **Metric Views**: 20 pre-aggregated metric views for optimized queries
- **Vector Search**: Enabled on `gold_customer_reviews` for semantic search

### Agent Configuration
- **Customer Behavior Genie**: 10 metric views covering segmentation, RFM, purchase patterns, affinity, channel behavior, funnel, abandonment
- **Inventory Operations Genie**: 10 metric views covering current status, stockout risk, overstock, value, reorder, movements, impact, location comparison, trends, health
- **Customer Reviews Agent**: Vector Search RAG over `gold_customer_reviews` (~5,000 reviews) with semantic search on review content

### Customer Reviews Data
- **Table**: `juan_dev.retail.gold_customer_reviews`
- **Volume**: ~5,000 reviews
- **Types**: Product reviews (60%), Purchase experiences (20%), Return feedback (20%)
- **Linked to**: `gold_customer_dim` (customer_key), `gold_product_dim` (product_key)
- **Vector Search**: Embeddings on `review_text` column for semantic queries

### References
- Genie Room Instructions: `10-genie-rooms/genie-configs/customer-behavior/instructions.md`, `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
- Multi-Agent Setup: `20-agent-brick/mas-setup.md`
- Reviews Generation: `00-data/01-generate-reviews.ipynb`

---

*Document generated: December 2025*  
*Last validated: All metrics verified against live data*
