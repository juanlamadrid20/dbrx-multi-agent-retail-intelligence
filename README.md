# DBRX Multi-Agent Retail Intelligence

A comprehensive fashion retail intelligence platform with inventory-aligned synthetic data generation, multi-agent analytics, and Databricks integration.

## 📁 Project Structure

| Folder | Description |
|--------|-------------|
| **[00-data/](00-data/)** | Synthetic data generation with inventory alignment. [📖 Full docs](00-data/README.md) |
| **[10-genie-rooms/](10-genie-rooms/)** | Databricks Genie spaces for customer behavior & inventory analytics |
| **[20-agent-brick/](20-agent-brick/)** | Agent Bricks: Knowledge Assistant + Multi-Agent Supervisor setup |
| **[30-mosaic-tool-calling-agent/](30-mosaic-tool-calling-agent/)** | Multi-tool calling agent using LangChain & GenieAgent |
| **[docs/](docs/)** | Demo scripts and presentation slides |
| **[src/](src/)** | Python package for fashion retail data generation |
| **[tests/](tests/)** | Contract and unit tests |

## 🚀 Quick Start

For complete setup instructions, data model details, scaling recommendations, and validation procedures, see the **[comprehensive documentation](00-data/README.md)**.

### Key Features

- **Inventory-Aligned Data Generation**: Sales respect real-time inventory constraints
- **Stockout Analytics**: Track lost sales and revenue impact
- **Multi-Agent Intelligence**: Customer behavior and inventory optimization agents
- **Multi-Tool Calling Agent**: Natural language queries across Genie spaces
- **Scalable Architecture**: From 10 customers to 2M+ enterprise scale
- **Databricks Integration**: Unity Catalog, Delta Lake, and Genie spaces

## 📊 Data Model

The platform generates a star schema with:
- **6 Dimension Tables** (customers, products, locations, dates, channels, time)
- **6 Fact Tables** (sales, inventory, customer events, cart abandonment, demand forecasts, stockout events)
- **Inventory-Aligned Features** for realistic business scenarios

## 🤖 Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Multi-Agent Supervisor                                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────┐ │
│  │  Customer Reviews   │  │ Customer Behavior   │  │  Inventory  │ │
│  │  Knowledge Agent    │  │ Genie Space         │  │ Genie Space │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

| Agent | Type | Domain |
|-------|------|--------|
| Customer Reviews | Knowledge Assistant | Qualitative voice of customer |
| Customer Behavior | Genie Space | Quantitative customer analytics |
| Inventory Operations | Genie Space | Supply chain intelligence |

## 🔧 Technologies

- **Databricks** - Data platform and compute
- **Delta Lake** - Data storage and versioning
- **Unity Catalog** - Data governance
- **Genie Spaces** - Natural language analytics
- **LangChain** - Agent orchestration
- **MLflow** - Model tracking and deployment
- **Python** - Data generation and processing
- **SQL** - Analytics and validation

## 📖 Documentation

| Resource | Description |
|----------|-------------|
| [00-data/README.md](00-data/README.md) | Complete data platform documentation |
| [20-agent-brick/README.md](20-agent-brick/README.md) | Agent Bricks deployment guides |
| [30-mosaic-tool-calling-agent/README.tool-calling-agent.md](30-mosaic-tool-calling-agent/README.tool-calling-agent.md) | Multi-tool agent architecture |
| [docs/DEMO_SCRIPT_QUESTIONS.md](docs/DEMO_SCRIPT_QUESTIONS.md) | Demo script and sample questions |

## 🏗️ Status

**✅ Production Ready** - All features implemented and validated

---

**Project Owner:** Juan Lamadrid  
**Last Updated:** 2025-12-29
