"""
Advanced prompt templates and AI interaction utilities for SQL Assistant
Provides specialized prompts for different use cases and AI-powered insights
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re


class PromptTemplateManager:
    """Manage and customize AI prompt templates"""

    def __init__(self):
        self.templates = self._load_default_templates()
        self.custom_templates = {}

    def _load_default_templates(self) -> Dict[str, str]:
        """Load default prompt templates"""
        return {
            "basic_sql": """You are an intelligent SQL assistant for a {db_type} database.
Translate the following natural language query into a {db_type}-compatible SQL query:

Database Schema:
{schema}

User Question:
{question}

IMPORTANT Guidelines:
- This is a {db_type} database
- Use {db_type} syntax and functions
- Respond with ONLY the SQL query
- Do NOT use markdown formatting
- Return only the raw SQL statement

Generate the {db_type} query:""",

            "business_analyst": """You are a senior business analyst with expertise in {db_type} databases and business intelligence.

## CONTEXT:
Database: {db_type} Business Analytics System
Schema: {schema}

## BUSINESS QUESTION:
{question}

## YOUR EXPERTISE:
- 10+ years in business intelligence and data analytics
- Expert in SQL optimization and business metrics
- Deep understanding of business processes and KPIs

## TASK:
Create an optimal {db_type} query that answers the business question accurately and efficiently.

## BUSINESS INTELLIGENCE PATTERNS:
- Revenue Analysis: Focus on time-based trends, segmentation, and growth metrics
- Customer Analytics: Segmentation, lifetime value, retention, and behavior patterns  
- Product Performance: Sales velocity, profit margins, inventory turnover
- Operational Metrics: Efficiency ratios, quality metrics, resource utilization
- Financial Reporting: P&L components, budget variance, cash flow analysis

## QUERY OPTIMIZATION:
- Use appropriate indexes (assume standard business database indexes exist)
- Optimize for common business reporting patterns
- Consider data volume and query performance
- Use CTEs for complex business logic
- Apply proper aggregation and grouping for business metrics

## OUTPUT REQUIREMENTS:
- Generate ONE executable {db_type} query
- No explanations or markdown
- Ensure business accuracy and data integrity
- Use meaningful aliases for business readability

Generate the business-focused {db_type} query:""",

            "data_scientist": """You are a data scientist with deep expertise in {db_type} databases and statistical analysis.

## DATABASE CONTEXT:
Type: {db_type}
Schema: {schema}

## DATA SCIENCE REQUEST:
{question}

## YOUR EXPERTISE:
- Advanced statistical analysis and machine learning
- Expert in SQL for data science workflows
- Statistical modeling and predictive analytics
- Data preprocessing and feature engineering

## ANALYTICAL APPROACH:
1. **Statistical Foundations**: Apply proper statistical methods
2. **Data Quality**: Consider missing values, outliers, and data distribution
3. **Feature Engineering**: Create meaningful derived metrics
4. **Temporal Analysis**: Understand time-series patterns and seasonality
5. **Cohort Analysis**: Group-based behavioral analysis
6. **Correlation Analysis**: Identify relationships between variables

## ADVANCED SQL PATTERNS:
- Window functions for time-series analysis
- Statistical functions (percentiles, standard deviation, correlation)
- Cohort analysis with self-joins and date arithmetic
- Data sampling and stratification
- Outlier detection using statistical methods
- Moving averages and trend analysis

## DATA SCIENCE CALCULATIONS:
- Retention rates and churn analysis
- Customer lifetime value (CLV)
- Statistical significance testing
- A/B test analysis
- Seasonality and trend decomposition
- Correlation and regression analysis

Generate an analytically rigorous {db_type} query:""",

            "performance_optimizer": """You are a database performance expert specializing in {db_type} optimization.

## DATABASE ENVIRONMENT:
Type: {db_type}
Schema: {schema}

## OPTIMIZATION REQUEST:
{question}

## YOUR EXPERTISE:
- 15+ years in database performance tuning
- Expert in {db_type} query execution plans and optimization
- Index design and query rewriting specialist
- Performance monitoring and bottleneck identification

## OPTIMIZATION PRINCIPLES:
1. **Index Utilization**: Design queries to leverage existing indexes
2. **Join Optimization**: Use efficient join strategies and order
3. **Predicate Pushdown**: Apply filters as early as possible
4. **Cardinality Estimation**: Consider table sizes and selectivity
5. **Execution Plan**: Optimize for minimal I/O and CPU usage

## PERFORMANCE PATTERNS:
- Use covering indexes when possible
- Prefer EXISTS over IN for subqueries with large datasets
- Use appropriate join hints for complex queries
- Minimize function usage in WHERE clauses
- Use LIMIT/TOP for large result sets
- Consider query plan caching

## {db_type} SPECIFIC OPTIMIZATIONS:
""" + ("""
### MySQL Optimizations:
- Use proper storage engines (InnoDB for transactions)
- Leverage MySQL-specific functions and syntax
- Consider partition pruning for large tables
- Use MySQL's query cache effectively
- Optimize for MySQL's nested loop joins
""" if "{db_type}" == "MySQL" else """
### PostgreSQL Optimizations:
- Leverage PostgreSQL's advanced indexing (BTREE, GIN, GIST)
- Use PostgreSQL's advanced SQL features efficiently
- Consider partial indexes and expression indexes
- Optimize for PostgreSQL's hash and merge joins
- Use PostgreSQL's query planner hints when necessary
""") + """

## OUTPUT REQUIREMENTS:
- Generate a performance-optimized {db_type} query
- Focus on execution efficiency over readability
- Use query patterns that minimize resource usage
- Ensure scalability for large datasets

Generate the performance-optimized {db_type} query:""",

            "security_auditor": """You are a database security specialist with expertise in {db_type} security and compliance.

## SECURITY CONTEXT:
Database: {db_type}
Schema: {schema}

## SECURITY REQUEST:
{question}

## YOUR EXPERTISE:
- Database security hardening and compliance
- SQL injection prevention and query validation
- Data privacy and access control patterns
- Audit trail and monitoring query design

## SECURITY PRINCIPLES:
1. **Principle of Least Privilege**: Query only necessary data
2. **Data Sanitization**: Ensure no sensitive data exposure
3. **Audit Compliance**: Include audit-friendly patterns
4. **Access Patterns**: Design for role-based access control
5. **Data Masking**: Consider data privacy requirements

## SECURE QUERY PATTERNS:
- Avoid dynamic SQL construction
- Use parameterized query patterns
- Implement row-level security concepts
- Add audit trail fields when relevant
- Consider data classification levels
- Implement data retention compliance

## COMPLIANCE CONSIDERATIONS:
- GDPR: Right to be forgotten, data minimization
- SOX: Financial data accuracy and auditability
- HIPAA: Protected health information safeguards
- PCI-DSS: Payment card data protection

Generate a security-compliant {db_type} query:""",

            "report_generator": """You are a business intelligence report developer specializing in {db_type} reporting queries.

## REPORTING CONTEXT:
Database: {db_type}
Schema: {schema}

## REPORT REQUEST:
{question}

## YOUR EXPERTISE:
- Executive dashboard and KPI reporting
- Financial and operational reporting standards
- Data visualization and chart-ready query design
- Report automation and scheduling optimization

## REPORTING STANDARDS:
1. **Executive Readiness**: Clear, actionable business metrics
2. **Drill-down Capability**: Hierarchical data organization
3. **Time Intelligence**: Period comparisons and trending
4. **Exception Reporting**: Highlight outliers and anomalies
5. **Data Governance**: Consistent metric definitions

## REPORT QUERY PATTERNS:
- Hierarchical grouping for drill-down reports
- Time-based comparisons (YoY, MoM, QoQ)
- Ranking and top/bottom analyses
- Variance analysis (actual vs. budget/forecast)
- Exception highlighting with conditional logic
- Summary and detail level aggregations

## BUSINESS METRICS:
- Financial: Revenue, margins, costs, variances
- Sales: Conversion rates, pipeline, quotas
- Operations: Efficiency, quality, utilization
- Customer: Acquisition, retention, satisfaction
- Product: Performance, profitability, lifecycle

## CHART-READY OUTPUT:
- Design for visualization tools
- Consistent naming conventions
- Appropriate data types for charting
- Logical sort orders
- Meaningful labels and descriptions

Generate a comprehensive reporting {db_type} query:""",

            "troubleshooting": """You are a database troubleshooting expert for {db_type} systems.

## TROUBLESHOOTING CONTEXT:
Database: {db_type}
Schema: {schema}

## ISSUE TO INVESTIGATE:
{question}

## YOUR EXPERTISE:
- Database performance diagnosis and resolution
- Query optimization and execution plan analysis
- Data quality assessment and anomaly detection
- System health monitoring and alerting

## DIAGNOSTIC APPROACH:
1. **Root Cause Analysis**: Identify underlying issues
2. **Data Validation**: Check for data quality problems
3. **Performance Analysis**: Identify bottlenecks and inefficiencies
4. **System Health**: Monitor resource usage and constraints
5. **Error Pattern Detection**: Find recurring issues

## TROUBLESHOOTING QUERIES:
- Data quality checks (nulls, duplicates, outliers)
- Performance monitoring (slow queries, blocking)
- Constraint violations and referential integrity
- Storage and growth analysis
- Index usage and effectiveness
- Query plan analysis and optimization

## DIAGNOSTIC PATTERNS:
- Statistical analysis for anomaly detection
- Time-based analysis for trend identification
- Resource utilization monitoring
- Error log analysis and pattern recognition
- Data lineage and dependency checking

Generate a diagnostic {db_type} query to investigate the issue:"""
        }

    def get_template(self, template_name: str, **kwargs) -> str:
        """Get formatted template"""
        if template_name in self.custom_templates:
            template = self.custom_templates[template_name]
        elif template_name in self.templates:
            template = self.templates[template_name]
        else:
            template = self.templates["basic_sql"]  # Fallback

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter for template: {e}")

    def add_custom_template(self, name: str, template: str):
        """Add custom template"""
        self.custom_templates[name] = template

    def list_templates(self) -> List[str]:
        """List available templates"""
        return list(self.templates.keys()) + list(self.custom_templates.keys())

    def get_template_description(self, template_name: str) -> str:
        """Get template description"""
        descriptions = {
            "basic_sql": "Simple SQL generation for basic queries",
            "business_analyst": "Business-focused queries with KPI and reporting emphasis",
            "data_scientist": "Advanced analytics with statistical functions",
            "performance_optimizer": "Performance-optimized queries for large datasets",
            "security_auditor": "Security-compliant queries with audit considerations",
            "report_generator": "Report-ready queries for dashboards and BI",
            "troubleshooting": "Diagnostic queries for system investigation"
        }
        return descriptions.get(template_name, "Custom template")


class InsightGenerator:
    """Generate AI-powered insights from data and queries"""

    @staticmethod
    def generate_data_insights_prompt(df_summary: Dict, query: str) -> str:
        """Generate prompt for data insights"""
        return f"""You are a senior data analyst providing business insights from query results.

## QUERY EXECUTED:
{query}

## DATA SUMMARY:
- Total Records: {df_summary.get('total_rows', 'Unknown')}
- Columns: {df_summary.get('total_columns', 'Unknown')}
- Data Types: {df_summary.get('column_types', {})}

## SAMPLE STATISTICS:
{json.dumps(df_summary.get('statistics', {}), indent=2)}

## YOUR TASK:
Analyze this data and provide 3-5 key business insights. Focus on:

1. **Patterns & Trends**: What patterns emerge from the data?
2. **Business Implications**: What do these numbers mean for the business?
3. **Actionable Findings**: What specific actions should be considered?
4. **Data Quality**: Any notable data quality observations?
5. **Follow-up Questions**: What additional analysis would be valuable?

## OUTPUT FORMAT:
Provide clear, concise insights in business language. Each insight should be:
- Specific and measurable
- Actionable for business stakeholders
- Supported by the data evidence
- Free of technical jargon

Generate the business insights:"""

    @staticmethod
    def generate_optimization_prompt(query: str, execution_plan: str, schema: str) -> str:
        """Generate prompt for query optimization"""
        return f"""You are a database performance expert analyzing a query for optimization opportunities.

## QUERY TO OPTIMIZE:
{query}

## EXECUTION PLAN:
{execution_plan}

## DATABASE SCHEMA:
{schema}

## YOUR EXPERTISE:
- Query execution plan analysis
- Index design and optimization
- Query rewriting for performance
- Database-specific optimization techniques

## OPTIMIZATION ANALYSIS:
Please analyze this query and provide specific optimization recommendations:

1. **Execution Plan Analysis**:
   - Identify expensive operations (table scans, sorts, joins)
   - Highlight performance bottlenecks
   - Estimate relative costs of operations

2. **Index Recommendations**:
   - Suggest specific indexes that would improve performance
   - Explain how each index would be utilized
   - Consider composite index opportunities

3. **Query Rewrite Suggestions**:
   - Alternative query structures for better performance
   - More efficient join strategies
   - Optimization of WHERE clauses and predicates

4. **Best Practices**:
   - SQL patterns that could be improved
   - Database-specific optimization opportunities
   - Scalability considerations

## OUTPUT FORMAT:
Provide actionable recommendations with:
- Specific SQL index creation statements
- Rewritten query examples where beneficial
- Expected performance impact
- Implementation priority (High/Medium/Low)

Generate the optimization recommendations:"""

    @staticmethod
    def generate_business_recommendations_prompt(df_summary: Dict, query: str, business_context: str = None) -> str:
        """Generate prompt for business recommendations"""
        return f"""You are a senior business consultant providing strategic recommendations based on data analysis.

## BUSINESS CONTEXT:
{business_context or 'General business analysis'}

## QUERY ANALYZED:
{query}

## DATA INSIGHTS:
- Dataset Size: {df_summary.get('total_rows', 'Unknown')} records
- Key Metrics Available: {list(df_summary.get('column_types', {}).keys())}
- Data Completeness: {df_summary.get('missing_values', {})}

## STATISTICAL OVERVIEW:
{json.dumps(df_summary.get('statistics', {}), indent=2)}

## YOUR MANDATE:
As a business consultant, provide strategic recommendations based on this data analysis.

## RECOMMENDATION FRAMEWORK:
1. **Strategic Priorities**: What should be the immediate focus areas?
2. **Operational Improvements**: What processes can be optimized?
3. **Risk Mitigation**: What risks does the data reveal?
4. **Growth Opportunities**: Where are the expansion possibilities?
5. **Resource Allocation**: How should resources be prioritized?

## BUSINESS CONSIDERATIONS:
- Market competitiveness and positioning
- Customer satisfaction and retention
- Operational efficiency and cost management
- Revenue growth and profitability
- Risk management and compliance

## OUTPUT REQUIREMENTS:
Provide 3-5 strategic recommendations that are:
- Specific and actionable
- Quantifiable where possible
- Aligned with business objectives
- Implementable within reasonable timeframes
- Supported by data evidence

Generate the business recommendations:"""


class QueryEnhancer:
    """Enhance and optimize user queries"""

    @staticmethod
    def enhance_natural_language_query(user_query: str, schema_context: str) -> str:
        """Enhance user's natural language query with more context"""
        enhancement_patterns = [
            {
                'pattern': r'\b(sales|revenue|income)\b',
                'enhancement': 'Include time period analysis and trend identification'
            },
            {
                'pattern': r'\b(customer|client|user)\b',
                'enhancement': 'Consider customer segmentation and behavioral analysis'
            },
            {
                'pattern': r'\b(top|best|highest|most)\b',
                'enhancement': 'Include ranking criteria and statistical significance'
            },
            {
                'pattern': r'\b(compare|comparison|versus|vs)\b',
                'enhancement': 'Include statistical comparison methods and variance analysis'
            },
            {
                'pattern': r'\b(trend|trending|growth|decline)\b',
                'enhancement': 'Include time-series analysis and seasonality considerations'
            }
        ]

        enhanced_query = user_query
        suggestions = []

        for pattern in enhancement_patterns:
            if re.search(pattern['pattern'], user_query, re.IGNORECASE):
                suggestions.append(pattern['enhancement'])

        if suggestions:
            enhanced_query += f"\n\nAdditional analysis considerations: {'; '.join(suggestions)}"

        return enhanced_query

    @staticmethod
    def suggest_follow_up_queries(original_query: str, results_summary: Dict) -> List[str]:
        """Suggest follow-up queries based on results"""
        suggestions = []

        # Time-based follow-ups
        if 'date' in original_query.lower() or 'time' in original_query.lower():
            suggestions.extend([
                "Show the same analysis for the previous period for comparison",
                "Break down the results by quarter or month",
                "Identify seasonal patterns or trends"
            ])

        # Volume-based follow-ups
        row_count = results_summary.get('total_rows', 0)
        if row_count > 100:
            suggestions.extend([
                "Show top 10 results only",
                "Add percentage distribution analysis",
                "Identify outliers or anomalies"
            ])
        elif row_count < 10:
            suggestions.extend([
                "Expand date range or criteria",
                "Check for data availability issues",
                "Analyze broader category or segment"
            ])

        # Aggregation follow-ups
        if 'sum' in original_query.lower() or 'count' in original_query.lower():
            suggestions.extend([
                "Break down by subcategories",
                "Show percentage contribution of each component",
                "Compare with historical averages"
            ])

        # Filtering follow-ups
        if 'where' in original_query.lower():
            suggestions.extend([
                "Remove filters to see complete picture",
                "Apply different filter criteria",
                "Compare filtered vs. unfiltered results"
            ])

        return suggestions[:5]  # Limit to 5 suggestions


class PromptOptimizer:
    """Optimize prompts for better AI responses"""

    @staticmethod
    def optimize_prompt_for_context(base_prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt based on context"""
        optimized_prompt = base_prompt

        # Add database-specific optimizations
        db_type = context.get('db_type', '').lower()
        if db_type == 'mysql':
            optimized_prompt += "\n\n## MySQL-Specific Considerations:\n"
            optimized_prompt += "- Use MySQL date functions (DATE_FORMAT, YEAR, MONTH)\n"
            optimized_prompt += "- Consider MySQL's LIMIT syntax\n"
            optimized_prompt += "- Use MySQL string functions (CONCAT, SUBSTRING)\n"
        elif db_type == 'postgresql':
            optimized_prompt += "\n\n## PostgreSQL-Specific Considerations:\n"
            optimized_prompt += "- Use PostgreSQL date functions (DATE_TRUNC, EXTRACT)\n"
            optimized_prompt += "- Consider PostgreSQL's LIMIT/OFFSET syntax\n"
            optimized_prompt += "- Use PostgreSQL string functions (CONCAT, SUBSTR)\n"

        # Add schema complexity considerations
        schema = context.get('schema', '')
        table_count = schema.count('Table:') if schema else 0
        if table_count > 10:
            optimized_prompt += "\n\n## Complex Schema Considerations:\n"
            optimized_prompt += "- This database has many tables - ensure correct table selection\n"
            optimized_prompt += "- Pay attention to table relationships and foreign keys\n"
            optimized_prompt += "- Consider query performance with multiple table joins\n"

        # Add user expertise level considerations
        user_level = context.get('user_level', 'intermediate')
        if user_level == 'beginner':
            optimized_prompt += "\n\n## Beginner-Friendly Approach:\n"
            optimized_prompt += "- Generate simple, readable queries\n"
            optimized_prompt += "- Avoid complex subqueries unless necessary\n"
            optimized_prompt += "- Use clear table and column aliases\n"
        elif user_level == 'advanced':
            optimized_prompt += "\n\n## Advanced Features:\n"
            optimized_prompt += "- Use advanced SQL features when beneficial\n"
            optimized_prompt += "- Optimize for performance and efficiency\n"
            optimized_prompt += "- Consider using CTEs and window functions\n"

        return optimized_prompt

# Factory functions


def create_prompt_manager() -> PromptTemplateManager:
    """Create prompt template manager"""
    return PromptTemplateManager()


def create_insight_generator() -> InsightGenerator:
    """Create insight generator"""
    return InsightGenerator()


def create_query_enhancer() -> QueryEnhancer:
    """Create query enhancer"""
    return QueryEnhancer()


# Example usage
if __name__ == "__main__":
    # Example usage
    prompt_manager = create_prompt_manager()

    # List available templates
    print("Available templates:", prompt_manager.list_templates())

    # Get a template
    template = prompt_manager.get_template(
        "business_analyst",
        db_type="MySQL",
        schema="Sample schema...",
        question="What are our top customers?"
    )

    print("Generated prompt length:", len(template))
    print("Advanced prompts module loaded successfully")
