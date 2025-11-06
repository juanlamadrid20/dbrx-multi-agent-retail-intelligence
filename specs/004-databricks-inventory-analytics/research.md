# Research: Inventory Analytics Genie Room Configuration

**Feature**: 004-databricks-inventory-analytics
**Date**: 2025-01-27
**Status**: Complete

## Research Questions

### 1. Genie Room Configuration Best Practices for Inventory Analytics

**Decision**: Configure Genie space with comprehensive instructions and sample queries, relying on automatic schema discovery

**Rationale**:
- **Improved Query Quality**: Clear instructions help Genie understand inventory domain context and generate better SQL
- **User Guidance**: Sample queries help users understand what inventory questions the Genie can answer
- **Domain Specialization**: Instructions guide Genie on inventory analytics patterns and terminology
- **Error Reduction**: Better context reduces ambiguous queries and improves response accuracy
- **Performance**: Well-configured Genie spaces generate more efficient SQL queries
- **Automatic Schema Discovery**: Tables with proper comments/descriptions enable Genie to understand data model without explicit documentation

**Alternatives Considered**:
- **No configuration**: Genie would work but with lower quality and less guidance
- **Minimal configuration**: Insufficient for domain-specific inventory analysis
- **Explicit data model documentation**: Clarification determined automatic schema discovery is sufficient (tables have proper comments)

**Configuration Components**:
1. **Instructions/System Prompt**: Domain-specific guidance for Genie on inventory analytics
2. **Sample Queries**: Representative examples covering all inventory use cases
3. **Automatic Schema Discovery**: Relies on table comments/descriptions (no explicit data model docs needed)

---

### 2. Sample Query Selection and Organization

**Decision**: Organize sample queries by analytical category aligned with functional requirements

**Rationale**:
- **Coverage**: Sample queries should cover all FR-001 through FR-024 capabilities
- **Categories**: Based on inventory analytics patterns:
  - Current Stock Status & Levels
  - Stockout Risk & Analysis
  - Overstock Identification & Analysis
  - Inventory Value & Financial Metrics
  - Days of Supply & Reorder Management
  - Inventory Movements & Replenishment
  - Inventory Turnover & Efficiency
  - Stockout Events & Lost Sales Impact
  - In-Transit Inventory
  - Location & Regional Comparisons
  - Historical Trends & Patterns
  - Inventory Health Metrics
- **Progressive Complexity**: Start with simple queries, include complex multi-step analyses
- **Real-World Examples**: Based on actual acceptance scenarios from spec

**Query Selection Criteria**:
- Represent each functional requirement (FR-001 to FR-024)
- Cover all acceptance scenarios (12 scenarios)
- Include edge cases (ambiguous queries, data quality issues, future dates)
- Demonstrate cross-category analysis (e.g., stockout risk + replenishment schedule)

**Implementation Notes**:
- Create structured sample query document organized by category
- Each query should include expected insights/response patterns
- Group by complexity: Simple, Medium, Complex
- Include queries that test multi-domain detection (should redirect)
- Focus on queries supported by available inventory tables (gold_inventory_fact, gold_stockout_events, gold_inventory_movement_fact)

---

### 3. Genie Instructions/System Prompt Structure

**Decision**: Create comprehensive instructions that guide Genie on inventory analytics domain

**Rationale**:
- **Domain Understanding**: Genie needs context on inventory management terminology and concepts
- **Query Interpretation**: Instructions help Genie understand ambiguous queries about inventory
- **Response Format**: Guide Genie on providing actionable insights vs raw data
- **Error Handling**: Instructions on how to provide specific error details and guidance (FR-022)
- **Multi-Domain Detection**: Instructions on detecting and redirecting multi-domain queries (FR-021)
- **Automatic Schema Discovery**: Instructions emphasize reliance on table comments/descriptions

**Instruction Components**:
1. **Domain Overview**: Inventory analytics context and key concepts
2. **Available Data**: Tables, schemas, key metrics (discovered automatically from table comments)
3. **Query Patterns**: Common inventory analytical patterns to recognize
4. **Response Guidelines**: How to structure answers with insights and recommendations
5. **Error Handling**: How to provide specific errors with actionable guidance
6. **Performance Guidelines**: Query optimization for medium-scale data (1-10M rows)
7. **Boundaries**: Multi-domain queries should be detected and redirected
8. **Forecasting**: Forecasting queries are out of scope (historical/current only)
9. **Language**: English-only queries

**Implementation Notes**:
- Instructions should be clear and concise (avoid overloading)
- Use examples within instructions to illustrate concepts
- Reference specific functional requirements to guide behavior
- Balance detail with readability
- Emphasize automatic schema discovery from table comments

---

### 4. Data Model Approach (Automatic Schema Discovery)

**Decision**: Rely on automatic schema discovery - no explicit data model documentation needed

**Rationale**:
- **Simplified Configuration**: Tables with proper comments/descriptions enable Genie to understand schema automatically
- **Reduced Maintenance**: No need to maintain separate data model documentation
- **Genie Capability**: Genie can discover relationships and metrics from table metadata
- **Consistency**: Table comments serve as single source of truth

**Key Requirements**:
- Tables must have proper comments and descriptions
- Column descriptions should explain purpose and relationships
- Table descriptions should explain grain and key metrics
- Genie will discover schema automatically when tables are added to space

**Implementation Notes**:
- Ensure inventory tables have comprehensive comments before adding to Genie space
- Table comments should describe:
  - Table purpose and grain
  - Key relationships (foreign keys)
  - Important metrics and calculations
  - Data quality notes

---

### 5. Genie Space Configuration Methods

**Decision**: Use Databricks Genie space configuration UI

**Rationale**:
- **UI Configuration**: Primary method for configuring Genie spaces (instructions, sample queries)
- **Documentation-Based**: Create configuration artifacts that can be applied via UI
- **Version Control**: Configuration documented in codebase for reproducibility
- **Automatic Schema Discovery**: Tables added to space with comments enable automatic discovery

**Alternatives Considered**:
- **UI-only**: Works but not version-controlled
- **API-only**: May not be available or fully supported
- **Hybrid**: Document in codebase, apply via UI (recommended)

**Implementation Notes**:
- Create configuration files (instructions, sample queries) in `10-genie-rooms/genie-configs/inventory-analytics/`
- Document configuration steps in quickstart guide
- Provide human-readable formats (Markdown)
- Include instructions for applying configuration via Databricks UI
- Ensure tables have proper comments before adding to space

---

### 6. Testing and Validation of Genie Configuration

**Decision**: Use existing test utilities to validate Genie space improvements

**Rationale**:
- **Existing Infrastructure**: `test_utils.py` already provides Genie testing capabilities
- **Validation**: Test that sample queries work correctly
- **Quality Metrics**: Measure improvement in query accuracy and response quality
- **Regression Testing**: Ensure configuration changes don't break existing functionality

**Test Approach**:
1. **Sample Query Validation**: Test all sample queries return valid responses
2. **Response Quality**: Verify responses include actionable insights and visualizations
3. **Error Handling**: Test error scenarios return specific guidance
4. **Multi-Domain Detection**: Verify multi-domain queries are detected and redirected
5. **Performance**: Verify queries meet performance targets (<10s simple, <60s complex)
6. **Forecasting Rejection**: Verify forecasting queries are handled appropriately
7. **Language Handling**: Verify non-English queries are handled appropriately

**Implementation Notes**:
- Extend existing test notebook with new test cases
- Create test suite for configuration validation
- Document expected responses for sample queries
- Track quality metrics before/after configuration improvements
- Test automatic schema discovery with properly commented tables

---

### 7. Inventory Analytics Domain Patterns

**Decision**: Identify common inventory analytics patterns for Genie instruction

**Rationale**:
- **Pattern Recognition**: Help Genie recognize common inventory question types
- **Query Optimization**: Understanding patterns helps generate efficient SQL
- **Response Quality**: Pattern-based responses improve consistency

**Key Patterns Identified**:
1. **Current Status Queries**: "What is...", "Show me...", "Which products..."
2. **Risk Assessment Queries**: "Which products are at risk...", "What is the risk of..."
3. **Trend Analysis Queries**: "How has... changed over time", "What are the trends..."
4. **Comparison Queries**: "Compare... across...", "Which locations have..."
5. **Action Queries**: "Which products need...", "What should we..."
6. **Impact Analysis Queries**: "What is the impact of...", "How much revenue was lost..."

**Implementation Notes**:
- Include pattern examples in instructions
- Guide Genie on recognizing these patterns
- Provide response templates for each pattern type

---

## Summary of Technical Decisions

1. **Configuration Approach**: Comprehensive instructions + sample queries + automatic schema discovery
2. **Sample Query Organization**: By analytical category, covering all functional requirements (FR-001 to FR-024)
3. **Instructions Structure**: Domain overview, query patterns, response guidelines, error handling, boundaries
4. **Data Model**: Automatic schema discovery from table comments/descriptions (no explicit docs needed)
5. **Configuration Method**: Documentation-based, applied via Databricks UI
6. **Testing**: Use existing test utilities to validate improvements
7. **Domain Patterns**: Common inventory analytics patterns identified for Genie guidance

All decisions focus on improving Genie room quality through configuration best practices, leveraging automatic schema discovery, and ensuring comprehensive coverage of inventory analytics capabilities.

