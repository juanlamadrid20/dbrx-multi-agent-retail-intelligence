# Research: Customer Behavior Genie Room Configuration

**Feature**: 003-cutomer-behavior-genie
**Date**: 2025-11-04
**Status**: Complete

## Research Questions

### 1. Genie Room Configuration Best Practices

**Decision**: Configure Genie space with comprehensive instructions, sample queries, and data model documentation

**Rationale**:
- **Improved Query Quality**: Clear instructions help Genie understand domain context and generate better SQL
- **User Guidance**: Sample queries help users understand what questions the Genie can answer
- **Domain Specialization**: Instructions guide Genie on customer behavior analysis patterns and terminology
- **Error Reduction**: Better context reduces ambiguous queries and improves response accuracy
- **Performance**: Well-configured Genie spaces generate more efficient SQL queries

**Alternatives Considered**:
- **No configuration**: Genie would work but with lower quality and less guidance
- **Minimal configuration**: Insufficient for domain-specific customer behavior analysis
- **Over-configuration**: Too much detail could confuse Genie - balance needed

**Configuration Components**:
1. **Instructions/System Prompt**: Domain-specific guidance for Genie
2. **Sample Queries**: Representative examples covering all use cases
3. **Data Model Documentation**: Schema information, table relationships, key metrics
4. **Query Patterns**: Common analytical patterns and best practices
5. **Error Handling Guidance**: How to handle edge cases and provide actionable guidance

---

### 2. Sample Query Selection and Organization

**Decision**: Organize sample queries by analytical category aligned with functional requirements

**Rationale**:
- **Coverage**: Sample queries should cover all FR-001 through FR-011 capabilities
- **Categories**: Match the structure in README.genie.customer-behavior.md:
  - Customer Segmentation & Value
  - Purchase Patterns & RFM Analysis
  - Product & Category Affinity
  - Channel Behavior & Migration
  - Engagement & Funnel Analysis
  - Abandonment & Recovery
  - Personalization & Affinity Impact
- **Progressive Complexity**: Start with simple queries, include complex multi-step analyses
- **Real-World Examples**: Based on actual acceptance scenarios from spec

**Query Selection Criteria**:
- Represent each functional requirement (FR-001 to FR-011)
- Cover all acceptance scenarios (12 scenarios)
- Include edge cases (ambiguous queries, data quality issues)
- Demonstrate cross-category analysis (e.g., segmentation + channel behavior)

**Implementation Notes**:
- Create structured sample query document organized by category
- Each query should include expected insights/response patterns
- Group by complexity: Simple, Medium, Complex
- Include queries that test multi-domain detection (should redirect)

---

### 3. Genie Instructions/System Prompt Structure

**Decision**: Create comprehensive instructions that guide Genie on customer behavior domain

**Rationale**:
- **Domain Understanding**: Genie needs context on customer behavior terminology and concepts
- **Query Interpretation**: Instructions help Genie understand ambiguous queries
- **Response Format**: Guide Genie on providing actionable insights vs raw data
- **Error Handling**: Instructions on how to provide specific error details and guidance (FR-022)
- **Multi-Domain Detection**: Instructions on detecting and redirecting multi-domain queries (FR-021)

**Instruction Components**:
1. **Domain Overview**: Customer behavior analysis context
2. **Available Data**: Tables, schemas, key metrics available
3. **Query Patterns**: Common analytical patterns to recognize
4. **Response Guidelines**: How to structure answers with insights and recommendations
5. **Error Handling**: How to provide specific errors with actionable guidance
6. **Performance Guidelines**: Query optimization for medium-scale data (1-10M rows)
7. **Boundaries**: Multi-domain queries should be detected and redirected

**Implementation Notes**:
- Instructions should be clear and concise (avoid overloading)
- Use examples within instructions to illustrate concepts
- Reference specific functional requirements to guide behavior
- Balance detail with readability

---

### 4. Data Model Documentation for Genie

**Decision**: Document customer behavior data model for Genie understanding

**Rationale**:
- **Schema Awareness**: Genie needs to understand available tables and relationships
- **Metric Definitions**: Clear definitions of calculated metrics (CLTV, abandonment rate, etc.)
- **Query Optimization**: Understanding relationships helps generate efficient SQL
- **Data Quality**: Knowledge of data structure helps identify quality issues

**Documentation Components**:
1. **Table Schema**: Key tables and their columns
2. **Relationships**: How tables relate (foreign keys, joins)
3. **Metric Definitions**: Formulas and calculation methods
4. **Time Periods**: Available date ranges and temporal granularity
5. **Data Quality Notes**: Known issues or constraints

**Implementation Notes**:
- Reference existing data model from `00-data/` if available
- Focus on tables relevant to customer behavior analysis
- Include examples of how to join tables correctly
- Document calculated metrics (not just raw data)

---

### 5. Genie Space Configuration Methods

**Decision**: Use Databricks Genie space configuration UI and API (if available)

**Rationale**:
- **UI Configuration**: Primary method for configuring Genie spaces (instructions, sample queries)
- **Documentation-Based**: Create configuration artifacts that can be applied via UI
- **Version Control**: Configuration documented in codebase for reproducibility
- **API Support**: If Genie API supports configuration updates, use for automation

**Alternatives Considered**:
- **UI-only**: Works but not version-controlled
- **API-only**: May not be available or fully supported
- **Hybrid**: Document in codebase, apply via UI (recommended)

**Implementation Notes**:
- Create configuration files (instructions, sample queries) in `10-genie-rooms/`
- Document configuration steps in quickstart guide
- Provide both human-readable and machine-readable formats
- Include instructions for applying configuration via Databricks UI

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
2. **Response Quality**: Verify responses include actionable insights
3. **Error Handling**: Test error scenarios return specific guidance
4. **Multi-Domain Detection**: Verify multi-domain queries are detected
5. **Performance**: Verify queries meet performance targets (<10s simple, <60s complex)

**Implementation Notes**:
- Extend existing test notebook with new test cases
- Create test suite for configuration validation
- Document expected responses for sample queries
- Track quality metrics before/after configuration improvements

---

## Summary of Technical Decisions

1. **Configuration Approach**: Comprehensive instructions + sample queries + data model documentation
2. **Sample Query Organization**: By analytical category, covering all functional requirements
3. **Instructions Structure**: Domain overview, query patterns, response guidelines, error handling
4. **Data Model Documentation**: Schema, relationships, metrics, data quality notes
5. **Configuration Method**: Documentation-based, applied via Databricks UI
6. **Testing**: Use existing test utilities to validate improvements

All decisions focus on improving Genie room quality through configuration best practices, not creating wrapper functions.
