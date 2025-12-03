# Sample Queries: Customer Behavior Genie

Sample queries organized by analytical category to help Genie learn query patterns and translate natural language to SQL.

Customer Segmentation & Value
Purchase Patterns & RFM Analysis
Product & Category Affinity
Channel Behavior & Migration
Engagement & Funnel Analysis
Abandonment & Recovery
Personalization & Affinity Impact
Stockout Risk Based on Customer Demand

NOTE: These queries were added to Genie room using playwright MCP to automate entry. 

---

## Customer Segmentation & Value

What are the key customer segments?
```sql
SELECT DISTINCT segment, COUNT(*) as customer_count
FROM juan_dev.retail.gold_customer_dim
WHERE is_current = TRUE
GROUP BY segment
ORDER BY customer_count DESC;
```

What is the average lifetime value by customer segment?
```sql
SELECT 
    segment,
    AVG(lifetime_value) as avg_cltv,
    COUNT(*) as customer_count
FROM juan_dev.retail.gold_customer_dim
WHERE is_current = TRUE
GROUP BY segment
ORDER BY avg_cltv DESC;
```

What are the key customer segments, and how do their lifetime values differ?
```sql
SELECT 
    segment,
    COUNT(*) as customer_count,
    AVG(lifetime_value) as avg_cltv,
    MIN(lifetime_value) as min_cltv,
    MAX(lifetime_value) as max_cltv,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lifetime_value) as median_cltv
FROM juan_dev.retail.gold_customer_dim
WHERE is_current = TRUE
GROUP BY segment
ORDER BY avg_cltv DESC;
```

Which segments have the highest average order value or frequency?
```sql
SELECT 
    c.segment,
    COUNT(DISTINCT s.transaction_id) / COUNT(DISTINCT c.customer_key) as avg_transactions_per_customer,
    AVG(s.net_sales_amount) as avg_order_value
FROM juan_dev.retail.gold_customer_dim c
JOIN juan_dev.retail.gold_sales_fact s ON c.customer_key = s.customer_key
WHERE c.is_current = TRUE
    AND s.is_return = FALSE
GROUP BY c.segment
ORDER BY avg_order_value DESC;
```

What is the distribution of customer lifetime value across segments over time?
```sql
SELECT 
    c.segment,
    d.month_name,
    d.year,
    COUNT(DISTINCT c.customer_key) as customer_count,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY c.lifetime_value) as p25_cltv,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY c.lifetime_value) as p50_cltv,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY c.lifetime_value) as p75_cltv,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY c.lifetime_value) as p90_cltv,
    AVG(c.lifetime_value) as avg_cltv
FROM juan_dev.retail.gold_customer_dim c
JOIN juan_dev.retail.gold_sales_fact s ON c.customer_key = s.customer_key
JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
WHERE c.is_current = TRUE
    AND s.is_return = FALSE
    AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 365)
GROUP BY c.segment, d.month_name, d.year
ORDER BY d.year, d.month_name, c.segment;
```

---

## Purchase Patterns & RFM Analysis

How frequently do customers make purchases?
```sql
SELECT 
    customer_key,
    COUNT(DISTINCT transaction_id) as purchase_frequency
FROM juan_dev.retail.gold_sales_fact
WHERE is_return = FALSE
GROUP BY customer_key
ORDER BY purchase_frequency DESC;
```

What is the average time between purchases for different segments?
```sql
WITH purchase_dates AS (
    SELECT 
        c.customer_key,
        c.segment,
        d.calendar_date,
        LAG(d.calendar_date) OVER (PARTITION BY c.customer_key ORDER BY d.calendar_date) as prev_purchase_date
    FROM juan_dev.retail.gold_sales_fact s
    JOIN juan_dev.retail.gold_customer_dim c ON s.customer_key = c.customer_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE c.is_current = TRUE
        AND s.is_return = FALSE
)
SELECT 
    segment,
    AVG(DATEDIFF(calendar_date, prev_purchase_date)) as avg_days_between_purchases
FROM purchase_dates
WHERE prev_purchase_date IS NOT NULL
GROUP BY segment
ORDER BY avg_days_between_purchases;
```

Which customers are at risk of churning, and which are the most loyal?
```sql
WITH customer_rfm AS (
    SELECT 
        c.customer_key,
        c.segment,
        DATEDIFF(CURRENT_DATE, MAX(d.calendar_date)) as recency_days,
        COUNT(DISTINCT s.transaction_id) as frequency,
        SUM(s.net_sales_amount) as monetary_value
    FROM juan_dev.retail.gold_customer_dim c
    JOIN juan_dev.retail.gold_sales_fact s ON c.customer_key = s.customer_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE c.is_current = TRUE
        AND s.is_return = FALSE
        AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 365)
    GROUP BY c.customer_key, c.segment
)
SELECT 
    customer_key,
    segment,
    recency_days,
    frequency,
    monetary_value,
    CASE 
        WHEN recency_days > 90 AND frequency < 3 THEN 'At Risk'
        WHEN recency_days <= 30 AND frequency >= 5 AND monetary_value > 1000 THEN 'Champion'
        WHEN recency_days <= 60 AND frequency >= 3 THEN 'Loyal'
        ELSE 'Regular'
    END as loyalty_status
FROM customer_rfm
ORDER BY 
    CASE loyalty_status
        WHEN 'At Risk' THEN 1
        WHEN 'Champion' THEN 2
        WHEN 'Loyal' THEN 3
        ELSE 4
    END,
    recency_days DESC;
```

Show me customers with low recency, high frequency, and high monetary value
```sql
WITH customer_rfm AS (
    SELECT 
        c.customer_key,
        c.customer_id,
        c.segment,
        DATEDIFF(CURRENT_DATE, MAX(d.calendar_date)) as recency,
        COUNT(DISTINCT s.transaction_id) as frequency,
        SUM(s.net_sales_amount) as monetary
    FROM juan_dev.retail.gold_customer_dim c
    JOIN juan_dev.retail.gold_sales_fact s ON c.customer_key = s.customer_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE c.is_current = TRUE
        AND s.is_return = FALSE
    GROUP BY c.customer_key, c.customer_id, c.segment
)
SELECT 
    customer_id,
    segment,
    recency,
    frequency,
    monetary
FROM customer_rfm
WHERE recency <= 30  -- Low recency (recent purchase)
    AND frequency >= 5  -- High frequency
    AND monetary >= 1000  -- High monetary value
ORDER BY monetary DESC;
```

Analyze RFM patterns across customer segments and identify migration trends
```sql
WITH customer_rfm_history AS (
    SELECT 
        c.customer_key,
        c.segment,
        d.year,
        d.quarter,
        DATEDIFF(CURRENT_DATE, MAX(d.calendar_date)) as recency,
        COUNT(DISTINCT s.transaction_id) as frequency,
        SUM(s.net_sales_amount) as monetary
    FROM juan_dev.retail.gold_customer_dim c
    JOIN juan_dev.retail.gold_sales_fact s ON c.customer_key = s.customer_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE c.is_current = TRUE
        AND s.is_return = FALSE
        AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 730)
    GROUP BY c.customer_key, c.segment, d.year, d.quarter
)
SELECT 
    segment,
    year,
    quarter,
    AVG(recency) as avg_recency,
    AVG(frequency) as avg_frequency,
    AVG(monetary) as avg_monetary,
    COUNT(DISTINCT customer_key) as customer_count
FROM customer_rfm_history
GROUP BY segment, year, quarter
ORDER BY year DESC, quarter DESC, segment;
```

---

## Product & Category Affinity

What products are trending?
```sql
SELECT 
    p.product_name,
    p.category_level_2,
    COUNT(DISTINCT s.transaction_id) as purchase_count,
    SUM(s.quantity_sold) as total_quantity,
    SUM(s.net_sales_amount) as total_revenue,
    COUNT(DISTINCT s.customer_key) as unique_customers
FROM juan_dev.retail.gold_sales_fact s
JOIN juan_dev.retail.gold_product_dim p ON s.product_key = p.product_key
JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
WHERE s.is_return = FALSE
    AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
    AND p.is_active = TRUE
GROUP BY p.product_name, p.category_level_2
ORDER BY purchase_count DESC
LIMIT 20;
```

Which product categories are most often purchased together?
```sql
WITH transaction_categories AS (
    SELECT DISTINCT
        s.transaction_id,
        p.category_level_2 as category
    FROM juan_dev.retail.gold_sales_fact s
    JOIN juan_dev.retail.gold_product_dim p ON s.product_key = p.product_key
    WHERE s.is_return = FALSE
)
SELECT 
    t1.category as category1,
    t2.category as category2,
    COUNT(DISTINCT t1.transaction_id) as co_occurrence_count
FROM transaction_categories t1
JOIN transaction_categories t2 ON t1.transaction_id = t2.transaction_id
WHERE t1.category < t2.category  -- Avoid duplicates and self-pairs
GROUP BY t1.category, t2.category
ORDER BY co_occurrence_count DESC
LIMIT 20;
```

What are the most common product pairings in a single transaction?
```sql
WITH transaction_products AS (
    SELECT 
        s.transaction_id,
        p.product_name as product1,
        LEAD(p.product_name) OVER (PARTITION BY s.transaction_id ORDER BY s.line_item_id) as product2
    FROM juan_dev.retail.gold_sales_fact s
    JOIN juan_dev.retail.gold_product_dim p ON s.product_key = p.product_key
    WHERE s.is_return = FALSE
)
SELECT 
    product1,
    product2,
    COUNT(*) as pair_count
FROM transaction_products
WHERE product2 IS NOT NULL
GROUP BY product1, product2
ORDER BY pair_count DESC
LIMIT 20;
```

Show me products with high customer affinity scores
```sql
SELECT 
    p.product_name,
    p.category_level_2,
    AVG(a.affinity_score) as avg_affinity_score,
    COUNT(DISTINCT a.customer_key) as customer_count,
    SUM(a.purchase_count) as total_purchases
FROM juan_dev.retail.gold_customer_product_affinity_agg a
JOIN juan_dev.retail.gold_product_dim p ON a.product_key = p.product_key
WHERE a.affinity_score > 0.05  -- High affinity threshold (top products based on actual data range)
    AND p.is_active = TRUE
GROUP BY p.product_name, p.category_level_2
ORDER BY avg_affinity_score DESC, total_purchases DESC
LIMIT 20;
```

Analyze product trends with customer segments driving the trends and growth patterns
```sql
WITH product_trends AS (
    SELECT 
        p.product_name,
        p.category_level_2,
        c.segment,
        d.month_name,
        d.year,
        COUNT(DISTINCT s.transaction_id) as transaction_count,
        SUM(s.quantity_sold) as total_quantity,
        SUM(s.net_sales_amount) as revenue
    FROM juan_dev.retail.gold_sales_fact s
    JOIN juan_dev.retail.gold_product_dim p ON s.product_key = p.product_key
    JOIN juan_dev.retail.gold_customer_dim c ON s.customer_key = c.customer_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE s.is_return = FALSE
        AND c.is_current = TRUE
        AND p.is_active = TRUE
        AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 180)
    GROUP BY p.product_name, p.category_level_2, c.segment, d.month_name, d.year
)
SELECT 
    product_name,
    category_level_2,
    segment,
    year,
    month_name,
    transaction_count,
    total_quantity,
    revenue,
    LAG(revenue) OVER (PARTITION BY product_name, segment ORDER BY year, month_name) as prev_revenue,
    (revenue - LAG(revenue) OVER (PARTITION BY product_name, segment ORDER BY year, month_name)) / 
        NULLIF(LAG(revenue) OVER (PARTITION BY product_name, segment ORDER BY year, month_name), 0) * 100 as growth_rate
FROM product_trends
ORDER BY product_name, segment, year DESC, month_name DESC;
```

How does category affinity differ by customer segment?
```sql
SELECT 
    c.segment,
    p.category_level_2,
    AVG(a.affinity_score) as avg_affinity_score,
    COUNT(DISTINCT a.customer_key) as customer_count,
    SUM(a.purchase_count) as total_purchases
FROM juan_dev.retail.gold_customer_product_affinity_agg a
JOIN juan_dev.retail.gold_customer_dim c ON a.customer_key = c.customer_key
JOIN juan_dev.retail.gold_product_dim p ON a.product_key = p.product_key
WHERE c.is_current = TRUE
    AND p.is_active = TRUE
GROUP BY c.segment, p.category_level_2
ORDER BY c.segment, avg_affinity_score DESC;
```

---

## Channel Behavior & Migration

Through which channels do customers prefer to shop?
```sql
SELECT 
    ch.channel_name,
    COUNT(DISTINCT s.customer_key) as unique_customers,
    COUNT(DISTINCT s.transaction_id) as transaction_count,
    SUM(s.net_sales_amount) as total_revenue,
    AVG(s.net_sales_amount) as avg_order_value
FROM juan_dev.retail.gold_sales_fact s
JOIN juan_dev.retail.gold_channel_dim ch ON s.channel_key = ch.channel_key
JOIN juan_dev.retail.gold_customer_dim c ON s.customer_key = c.customer_key
WHERE s.is_return = FALSE
    AND c.is_current = TRUE
GROUP BY ch.channel_name
ORDER BY total_revenue DESC;
```

How do customers migrate between acquisition and preferred channels over time?
```sql
SELECT 
    c.acquisition_channel,
    c.preferred_channel,
    COUNT(*) as customer_count,
    AVG(c.lifetime_value) as avg_cltv
FROM juan_dev.retail.gold_customer_dim c
WHERE c.is_current = TRUE
    AND c.acquisition_channel IS NOT NULL
    AND c.preferred_channel IS NOT NULL
GROUP BY c.acquisition_channel, c.preferred_channel
ORDER BY customer_count DESC;
```

What is the impact of channel on purchase frequency and value?
```sql
SELECT 
    ch.channel_name,
    COUNT(DISTINCT s.customer_key) as unique_customers,
    COUNT(DISTINCT s.transaction_id) / COUNT(DISTINCT s.customer_key) as avg_transactions_per_customer,
    AVG(s.net_sales_amount) as avg_order_value,
    SUM(s.net_sales_amount) as total_revenue
FROM juan_dev.retail.gold_sales_fact s
JOIN juan_dev.retail.gold_channel_dim ch ON s.channel_key = ch.channel_key
JOIN juan_dev.retail.gold_customer_dim c ON s.customer_key = c.customer_key
WHERE s.is_return = FALSE
    AND c.is_current = TRUE
GROUP BY ch.channel_name
ORDER BY avg_order_value DESC;
```

Analyze multi-channel customer behavior and channel migration patterns by segment
```sql
WITH customer_channels AS (
    SELECT 
        c.customer_key,
        c.segment,
        ch.channel_name,
        COUNT(DISTINCT s.transaction_id) as transaction_count,
        COUNT(DISTINCT d.calendar_date) as days_active
    FROM juan_dev.retail.gold_sales_fact s
    JOIN juan_dev.retail.gold_customer_dim c ON s.customer_key = c.customer_key
    JOIN juan_dev.retail.gold_channel_dim ch ON s.channel_key = ch.channel_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE s.is_return = FALSE
        AND c.is_current = TRUE
        AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 365)
    GROUP BY c.customer_key, c.segment, ch.channel_name
),
multi_channel_customers AS (
    SELECT 
        customer_key,
        segment,
        COUNT(DISTINCT channel_name) as channel_count
    FROM customer_channels
    GROUP BY customer_key, segment
    HAVING COUNT(DISTINCT channel_name) > 1
)
SELECT 
    m.segment,
    m.channel_count,
    COUNT(DISTINCT m.customer_key) as customer_count,
    AVG(m.channel_count) as avg_channels_per_customer
FROM multi_channel_customers m
GROUP BY m.segment, m.channel_count
ORDER BY m.segment, m.channel_count DESC;
```

---

## Engagement & Funnel Analysis

What are the conversion rates at each stage of the engagement funnel?
```sql
WITH funnel_metrics AS (
    SELECT 
        COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.session_id END) as views,
        COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) as add_to_cart,
        COUNT(DISTINCT CASE WHEN s.transaction_id IS NOT NULL THEN e.session_id END) as purchases
    FROM juan_dev.retail.gold_customer_event_fact e
    LEFT JOIN juan_dev.retail.gold_sales_fact s ON e.customer_key = s.customer_key 
        AND e.date_key = s.date_key
    JOIN juan_dev.retail.gold_date_dim d ON e.date_key = d.date_key
    WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
)
SELECT 
    views,
    add_to_cart,
    purchases,
    (add_to_cart::DOUBLE / NULLIF(views, 0)) * 100 as cart_conversion_rate,
    (purchases::DOUBLE / NULLIF(add_to_cart, 0)) * 100 as purchase_conversion_rate,
    (purchases::DOUBLE / NULLIF(views, 0)) * 100 as overall_conversion_rate
FROM funnel_metrics;
```

Which channels drive the most engagement and conversions?
```sql
SELECT 
    ch.channel_name,
    COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.event_id END) as views,
    COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END) as add_to_cart,
    COUNT(DISTINCT CASE WHEN s.transaction_id IS NOT NULL THEN s.transaction_id END) as purchases,
    (COUNT(DISTINCT CASE WHEN s.transaction_id IS NOT NULL THEN s.transaction_id END)::DOUBLE / 
     NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.event_id END), 0)) * 100 as conversion_rate
FROM juan_dev.retail.gold_customer_event_fact e
JOIN juan_dev.retail.gold_channel_dim ch ON e.channel_key = ch.channel_key
LEFT JOIN juan_dev.retail.gold_sales_fact s ON e.customer_key = s.customer_key
    AND e.date_key = s.date_key
    AND s.is_return = FALSE
JOIN juan_dev.retail.gold_date_dim d ON e.date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
GROUP BY ch.channel_name
ORDER BY conversion_rate DESC;
```

Where are customers dropping off in the purchase funnel?
```sql
WITH funnel_stages AS (
    SELECT 
        COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.session_id END) as stage1_views,
        COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) as stage2_cart,
        COUNT(DISTINCT CASE WHEN s.transaction_id IS NOT NULL THEN e.session_id END) as stage3_purchase
    FROM juan_dev.retail.gold_customer_event_fact e
    LEFT JOIN juan_dev.retail.gold_sales_fact s ON e.customer_key = s.customer_key 
        AND e.date_key = s.date_key
        AND s.is_return = FALSE
    JOIN juan_dev.retail.gold_date_dim d ON e.date_key = d.date_key
    WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
)
SELECT 
    stage1_views,
    stage2_cart,
    stage3_purchase,
    (stage1_views - stage2_cart) as drop_off_views_to_cart,
    (stage2_cart - stage3_purchase) as drop_off_cart_to_purchase,
    ((stage1_views - stage2_cart)::DOUBLE / NULLIF(stage1_views, 0)) * 100 as drop_off_rate_views_to_cart,
    ((stage2_cart - stage3_purchase)::DOUBLE / NULLIF(stage2_cart, 0)) * 100 as drop_off_rate_cart_to_purchase
FROM funnel_stages;
```

Analyze engagement funnel by customer segment with drop-off analysis
```sql
WITH segment_funnel AS (
    SELECT 
        c.segment,
        COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.session_id END) as views,
        COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) as add_to_cart,
        COUNT(DISTINCT CASE WHEN s.transaction_id IS NOT NULL THEN e.session_id END) as purchases
    FROM juan_dev.retail.gold_customer_event_fact e
    JOIN juan_dev.retail.gold_customer_dim c ON e.customer_key = c.customer_key
    LEFT JOIN juan_dev.retail.gold_sales_fact s ON e.customer_key = s.customer_key 
        AND e.date_key = s.date_key
        AND s.is_return = FALSE
    JOIN juan_dev.retail.gold_date_dim d ON e.date_key = d.date_key
    WHERE c.is_current = TRUE
        AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
    GROUP BY c.segment
)
SELECT 
    segment,
    views,
    add_to_cart,
    purchases,
    (add_to_cart::DOUBLE / NULLIF(views, 0)) * 100 as cart_conversion_rate,
    (purchases::DOUBLE / NULLIF(add_to_cart, 0)) * 100 as purchase_conversion_rate,
    ((views - add_to_cart)::DOUBLE / NULLIF(views, 0)) * 100 as drop_off_rate_views_to_cart,
    ((add_to_cart - purchases)::DOUBLE / NULLIF(add_to_cart, 0)) * 100 as drop_off_rate_cart_to_purchase
FROM segment_funnel
ORDER BY purchases DESC;
```

---

## Abandonment & Recovery

What is the rate of cart abandonment?
```sql
SELECT 
    COUNT(*) as total_carts,
    SUM(CASE WHEN is_recovered = FALSE THEN 1 ELSE 0 END) as abandoned_carts,
    (SUM(CASE WHEN is_recovered = FALSE THEN 1 ELSE 0 END)::DOUBLE / COUNT(*)) * 100 as abandonment_rate
FROM juan_dev.retail.gold_cart_abandonment_fact;
```

Which stages of the funnel have the highest abandonment rates?
```sql
SELECT 
    abandonment_stage,
    COUNT(*) as total_abandonments,
    SUM(CASE WHEN is_recovered = TRUE THEN 1 ELSE 0 END) as recovered,
    (SUM(CASE WHEN is_recovered = FALSE THEN 1 ELSE 0 END)::DOUBLE / COUNT(*)) * 100 as abandonment_rate
FROM juan_dev.retail.gold_cart_abandonment_fact
GROUP BY abandonment_stage
ORDER BY abandonment_rate DESC;
```

What is the rate of cart abandonment, and how effective are recovery campaigns?
```sql
SELECT 
    COUNT(*) as total_abandonments,
    SUM(CASE WHEN recovery_email_sent = TRUE THEN 1 ELSE 0 END) as recovery_emails_sent,
    SUM(CASE WHEN is_recovered = TRUE THEN 1 ELSE 0 END) as recovery_conversions,
    (SUM(CASE WHEN is_recovered = FALSE THEN 1 ELSE 0 END)::DOUBLE / COUNT(*)) * 100 as abandonment_rate,
    (SUM(CASE WHEN is_recovered = TRUE THEN 1 ELSE 0 END)::DOUBLE / 
     NULLIF(SUM(CASE WHEN recovery_email_sent = TRUE THEN 1 ELSE 0 END), 0)) * 100 as recovery_conversion_rate
FROM juan_dev.retail.gold_cart_abandonment_fact;
```

Which products have the highest cart abandonment rates?
```sql
-- Note: Cart abandonment is tracked at cart level, not product level
-- This query shows abandonment by cart characteristics
SELECT 
    abandonment_stage,
    COUNT(*) as abandonment_count,
    AVG(cart_value) as avg_cart_value,
    AVG(items_count) as avg_items_per_cart,
    SUM(CASE WHEN is_recovered = TRUE THEN 1 ELSE 0 END) as recovered_count
FROM juan_dev.retail.gold_cart_abandonment_fact
GROUP BY abandonment_stage
ORDER BY abandonment_count DESC;
```

Show me cart abandonment rates by customer segment
```sql
SELECT 
    c.segment,
    COUNT(*) as total_abandonments,
    SUM(CASE WHEN ca.is_recovered = FALSE THEN 1 ELSE 0 END) as abandoned_carts,
    (SUM(CASE WHEN ca.is_recovered = FALSE THEN 1 ELSE 0 END)::DOUBLE / COUNT(*)) * 100 as abandonment_rate,
    AVG(ca.cart_value) as avg_cart_value
FROM juan_dev.retail.gold_cart_abandonment_fact ca
JOIN juan_dev.retail.gold_customer_dim c ON ca.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.segment
ORDER BY abandonment_rate DESC;
```

Analyze cart abandonment patterns by segment and abandonment stage with recovery effectiveness
```sql
SELECT 
    c.segment,
    ca.abandonment_stage,
    COUNT(*) as abandonment_count,
    AVG(ca.cart_value) as avg_cart_value,
    AVG(ca.items_count) as avg_items_per_cart,
    SUM(CASE WHEN ca.recovery_email_sent = TRUE THEN 1 ELSE 0 END) as recovery_emails_sent,
    SUM(CASE WHEN ca.is_recovered = TRUE THEN 1 ELSE 0 END) as recovery_conversions,
    (SUM(CASE WHEN ca.is_recovered THEN 1 ELSE 0 END)::DOUBLE / 
     NULLIF(SUM(CASE WHEN ca.recovery_email_sent = TRUE THEN 1 ELSE 0 END), 0)) * 100 as recovery_rate
FROM juan_dev.retail.gold_cart_abandonment_fact ca
JOIN juan_dev.retail.gold_customer_dim c ON ca.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.segment, ca.abandonment_stage
ORDER BY abandonment_count DESC
LIMIT 30;
```

What is the revenue recovery rate from abandoned carts?
```sql
SELECT 
    COUNT(*) as total_abandonments,
    SUM(cart_value) as total_abandoned_value,
    SUM(CASE WHEN is_recovered = TRUE THEN cart_value ELSE 0 END) as recovered_revenue,
    (SUM(CASE WHEN is_recovered = TRUE THEN cart_value ELSE 0 END)::DOUBLE / 
     NULLIF(SUM(cart_value), 0)) * 100 as revenue_recovery_rate
FROM juan_dev.retail.gold_cart_abandonment_fact;
```

---

## Personalization & Affinity Impact

Which segments respond best to personalization?
```sql
SELECT 
    c.segment,
    AVG(a.affinity_score) as avg_affinity_score,
    COUNT(DISTINCT a.customer_key) as customers_with_affinity,
    SUM(a.purchase_count) as total_purchases,
    AVG(a.predicted_cltv_impact) as avg_predicted_cltv_impact
FROM juan_dev.retail.gold_customer_product_affinity_agg a
JOIN juan_dev.retail.gold_customer_dim c ON a.customer_key = c.customer_key
WHERE c.is_current = TRUE
    AND a.affinity_score > 0.05  -- High affinity threshold (top products based on actual data)
GROUP BY c.segment
ORDER BY avg_affinity_score DESC;
```

How effective are personalized recommendations in driving purchases?
```sql
SELECT 
    CASE 
        WHEN a.affinity_score >= 0.08 THEN 'High Affinity'
        WHEN a.affinity_score >= 0.06 THEN 'Medium Affinity'
        ELSE 'Low Affinity'
    END as affinity_level,
    COUNT(DISTINCT a.customer_key) as customer_count,
    SUM(a.purchase_count) as total_purchases,
    AVG(a.purchase_count) as avg_purchases_per_customer,
    AVG(a.predicted_cltv_impact) as avg_cltv_impact
FROM juan_dev.retail.gold_customer_product_affinity_agg a
JOIN juan_dev.retail.gold_customer_dim c ON a.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY affinity_level
ORDER BY avg_cltv_impact DESC;
```

What is the predicted impact of affinity-based targeting on CLTV?
```sql
SELECT 
    c.segment,
    COUNT(DISTINCT a.customer_key) as targeted_customers,
    SUM(a.predicted_cltv_impact) as total_predicted_cltv_impact,
    AVG(a.predicted_cltv_impact) as avg_predicted_cltv_impact,
    AVG(c.lifetime_value) as current_avg_cltv
FROM juan_dev.retail.gold_customer_product_affinity_agg a
JOIN juan_dev.retail.gold_customer_dim c ON a.customer_key = c.customer_key
WHERE c.is_current = TRUE
    AND a.affinity_score > 0.05  -- High affinity threshold (top products based on actual data)
GROUP BY c.segment
ORDER BY total_predicted_cltv_impact DESC;
```

Analyze personalization effectiveness by segment with affinity impact and CLTV predictions
```sql
SELECT 
    c.segment,
    COUNT(DISTINCT a.customer_key) as customers_with_affinity,
    AVG(a.affinity_score) as avg_affinity_score,
    SUM(a.purchase_count) as total_purchases_from_affinity,
    AVG(a.predicted_cltv_impact) as avg_predicted_cltv_impact,
    SUM(a.predicted_cltv_impact) as total_predicted_cltv_impact,
    AVG(c.lifetime_value) as current_avg_cltv
FROM juan_dev.retail.gold_customer_product_affinity_agg a
JOIN juan_dev.retail.gold_customer_dim c ON a.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.segment
ORDER BY avg_predicted_cltv_impact DESC;
```

---

## Stockout Risk Based on Customer Demand

Which products or categories are at risk of stockout or overstock based on customer demand patterns?
```sql
WITH demand_signals AS (
    SELECT 
        p.product_key,
        p.product_name,
        p.category_level_2,
        COUNT(DISTINCT s.transaction_id) as recent_purchase_count,
        SUM(s.quantity_sold) as recent_demand,
        -- Count cart abandonments with low inventory trigger for this product's category
        (SELECT COUNT(*) 
         FROM juan_dev.retail.gold_cart_abandonment_fact ca2
         JOIN juan_dev.retail.gold_customer_dim c2 ON ca2.customer_key = c2.customer_key
         WHERE ca2.low_inventory_trigger = TRUE
           AND c2.preferred_category = p.category_level_2) as low_inventory_abandonments
    FROM juan_dev.retail.gold_sales_fact s
    JOIN juan_dev.retail.gold_product_dim p ON s.product_key = p.product_key
    JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
    WHERE s.is_return = FALSE
        AND p.is_active = TRUE
        AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
    GROUP BY p.product_key, p.product_name, p.category_level_2
)
SELECT 
    product_name,
    category_level_2,
    recent_purchase_count,
    recent_demand,
    low_inventory_abandonments,
    CASE 
        WHEN low_inventory_abandonments > 10 AND recent_demand > 100 THEN 'Stockout Risk'
        WHEN recent_demand < 10 THEN 'Overstock Risk'
        ELSE 'Normal'
    END as risk_level
FROM demand_signals
WHERE low_inventory_abandonments > 0 OR recent_demand < 10
ORDER BY low_inventory_abandonments DESC, recent_demand DESC;
```

---

## Error Handling Examples

These queries demonstrate error scenarios that Genie should handle gracefully:

Show me customer purchase data from schema X (permission error example)
```sql
-- This query would fail if user lacks permissions
-- Genie should detect and provide actionable guidance
SELECT * FROM unauthorized_schema.customer_data;
```

Show me customer data (ambiguous query example)
```sql
-- This query is too ambiguous - could mean segments, purchases, or engagement
-- Genie should ask for clarification or provide multiple interpretations
SELECT * FROM juan_dev.retail.gold_customer_dim WHERE is_current = TRUE LIMIT 100;
```

Show me sales data from 2020 to 2025 (data quality error example)
```sql
-- This query may return no results if data doesn't exist for that range
-- Genie should indicate available data range
SELECT 
    d.calendar_date,
    SUM(s.net_sales_amount) as total_sales
FROM juan_dev.retail.gold_sales_fact s
JOIN juan_dev.retail.gold_date_dim d ON s.date_key = d.date_key
WHERE d.calendar_date >= '2020-01-01'
    AND d.calendar_date <= '2025-12-31'
    AND s.is_return = FALSE
GROUP BY d.calendar_date
ORDER BY d.calendar_date;
```

---

## Multi-Domain Detection Examples

These queries should be detected as multi-domain and redirected:

Which products are frequently abandoned in carts and do we have inventory issues with those items?
```sql
-- This query requires inventory data (multi-domain)
-- Genie should detect keywords like "inventory issues" and redirect
-- Customer behavior portion: shows cart abandonment by stage
SELECT 
    abandonment_stage,
    COUNT(*) as abandonment_count,
    SUM(CASE WHEN low_inventory_trigger = TRUE THEN 1 ELSE 0 END) as low_inventory_abandonments
FROM juan_dev.retail.gold_cart_abandonment_fact
GROUP BY abandonment_stage
ORDER BY abandonment_count DESC;
-- Note: This query only shows abandonment characteristics, not specific products or inventory levels
-- For product-level abandonment and inventory data, use multi-domain agent
```

Show me products with high cart abandonment and their current stock levels
```sql
-- This query requires inventory data (multi-domain)
-- Genie should detect "stock levels" and redirect
-- Customer behavior portion: shows cart abandonment characteristics
SELECT 
    abandonment_stage,
    COUNT(*) as abandonment_count,
    AVG(cart_value) as avg_cart_value,
    SUM(CASE WHEN low_inventory_trigger = TRUE THEN 1 ELSE 0 END) as low_inventory_abandonments
FROM juan_dev.retail.gold_cart_abandonment_fact
GROUP BY abandonment_stage
ORDER BY abandonment_count DESC;
-- Note: Stock levels require inventory data - use multi-domain agent
-- This query only shows abandonment metrics, not product-specific data or inventory levels
```
