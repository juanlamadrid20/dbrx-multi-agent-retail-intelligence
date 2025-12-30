# Agent Bricks - Fashion Retail Intelligence

This folder contains configuration guides for deploying the Fashion Retail Intelligence Agent Bricks.

---

## Setup Guides

| Guide | Description |
|-------|-------------|
| [Knowledge Assistant](./README.knowledge-assistant.md) | Customer Reviews agent using Vector Search |
| [Multi-Agent Supervisor](./README.multi-agent-supervisor.md) | Orchestrates 3 agents for cross-domain insights |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Multi-Agent Supervisor: multi-agent-retail-intelligence           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────┐ │
│  │  Customer Reviews   │  │ Customer Behavior   │  │  Inventory  │ │
│  │  Knowledge Agent    │  │ Genie Space         │  │ Genie Space │ │
│  │                     │  │                     │  │             │ │
│  │  (Agent Endpoint)   │  │  (Genie Space Ref)  │  │(Genie Space)│ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Summary

| Agent | Type | Domain |
|-------|------|--------|
| Customer Reviews | Knowledge Assistant | Qualitative voice of customer |
| Customer Behavior | Genie Space | Quantitative customer analytics |
| Inventory Operations | Genie Space | Supply chain intelligence |

---

## Deployment Order

1. **Deploy Genie Spaces** (if not already done)
   - Customer Behavior Genie with metric views
   - Inventory Operations Genie with metric views

2. **Deploy Knowledge Assistant** → [README.knowledge-assistant.md](./README.knowledge-assistant.md)
   - Creates the Customer Reviews agent
   - Note the Agent Endpoint after deployment

3. **Deploy Multi-Agent Supervisor** → [README.multi-agent-supervisor.md](./README.multi-agent-supervisor.md)
   - References the Knowledge Assistant via Agent Endpoint
   - References Genie Spaces directly

---

## The "Multiplicative Effect"

Combining all three agents creates strategic value that no single domain can provide alone:

| Pattern | Agents | Example Question |
|---------|--------|------------------|
| Demand-Supply Alignment | Behavior + Inventory | "Are VIP customers affected by stockouts?" |
| Inventory Impact on Experience | Inventory + Reviews | "What do customers say about products that stockout?" |
| Customer Value + Sentiment | Behavior + Reviews | "What do VIP customers complain about?" |
| **Triple-Agent Strategic** | All Three | "What quality issues affect VIP retention, and do we have alternatives in stock?" |

---

## References

- [Databricks Agent Bricks Documentation](https://docs.databricks.com/aws/en/generative-ai/agent-bricks)
- [Customer Behavior Genie](../10-genie-rooms/customer-behavior/)
- [Inventory Analytics Genie](../10-genie-rooms/inventory-analytics/)
