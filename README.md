# DBRX Multi-Agent Retail Intelligence

This project provides a comprehensive fashion retail intelligence platform with inventory-aligned synthetic data generation, multi-agent analytics, and Databricks integration.

## 📁 Project Structure

- **[00-data/](00-data/)** - Synthetic data generation with inventory alignment
  - **[README.md](00-data/README.md)** - 📖 **Complete documentation, data model, and scaling guide**
- **[10-genie-rooms/](10-genie-rooms/)** - Databricks Genie spaces for customer behavior and inventory analytics
- **[20-agent-brick/](20-agent-brick/)** - Multi-agent system setup and orchestration
- **[50-analysis/](50-analysis/)** - Cross-domain analysis notebooks
- **[specs/](specs/)** - Feature specifications and implementation plans
- **[src/](src/)** - Python package for fashion retail data generation
- **[tests/](tests/)** - Contract and unit tests

## 🚀 Quick Start

For complete setup instructions, data model details, scaling recommendations, and validation procedures, see the **[comprehensive documentation](00-data/README.md)**.

### Key Features

- **Inventory-Aligned Data Generation**: Sales respect real-time inventory constraints
- **Stockout Analytics**: Track lost sales and revenue impact
- **Multi-Agent Intelligence**: Customer behavior and inventory optimization agents
- **Scalable Architecture**: From 10 customers to 2M+ enterprise scale
- **Databricks Integration**: Unity Catalog, Delta Lake, and Genie spaces

## 📊 Data Model

The platform generates a star schema with:
- **6 Dimension Tables** (customers, products, locations, dates, channels, time)
- **6 Fact Tables** (sales, inventory, customer events, cart abandonment, demand forecasts, stockout events)
- **Inventory-Aligned Features** for realistic business scenarios

## 🔧 Technologies

- **Databricks** - Data platform and compute
- **Delta Lake** - Data storage and versioning
- **Unity Catalog** - Data governance
- **Genie Spaces** - Natural language analytics
- **Python** - Data generation and processing
- **SQL** - Analytics and validation

## 📖 Documentation

**👉 [Start here: Complete Documentation](00-data/README.md)**

The unified documentation includes:
- Installation and quick start guide
- Complete data model with ERD
- Scaling from test to enterprise volumes
- Validation tests and procedures
- Performance optimization
- Use cases and example queries
- Troubleshooting guide

## 🏗️ Status

**✅ Production Ready** - All features implemented and validated

---

**Project Owner:** Juan Lamadrid  
**Last Updated:** 2025-01-27
