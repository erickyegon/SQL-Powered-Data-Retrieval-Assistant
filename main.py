import streamlit as st
import pandas as pd
import time
import json
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

from config import DEFAULT_DB_HOST, DEFAULT_DB_PORT, DEFAULT_DB_NAME, DEFAULT_DB_USER, DEFAULT_DB_PASSWORD
from utils import (
    get_db_schema, call_groq_llm, execute_sql, create_db_engine, test_db_connection,
    clean_sql_response, analyze_query_performance, get_optimization_suggestions,
    parse_sql_complexity, create_auto_visualization, create_dashboard_charts,
    generate_business_report, create_pdf_report, init_session_state,
    add_to_history, add_to_favorites, get_query_history, get_favorite_queries,
    export_session_data
)

# Built-in prompt templates
PROMPT_TEMPLATES = {
    "basic": """You are an intelligent SQL assistant for a MySQL database.
Translate the following natural language query into a MySQL-compatible SQL query:

Database Schema:
{schema}

User Question:
{question}

IMPORTANT MySQL Guidelines:
- This is a MYSQL database, not PostgreSQL
- Use MySQL syntax and functions
- Respond with ONLY the SQL query
- Do NOT include any explanations, comments, or markdown formatting
- Do NOT use ``` code blocks
- Return ONLY the raw SQL statement that can be executed directly
- End with a semicolon

Generate ONLY the MySQL query:""",

    "production": """You are an expert MySQL database analyst. Your task is to convert natural language questions into precise, efficient, and secure MySQL queries.

## DATABASE SCHEMA:
{schema}

## USER QUERY:
{question}

## CRITICAL INSTRUCTIONS:
1. **Output Format**: Return ONLY the executable SQL query - no explanations, no markdown, no comments
2. **Database Type**: This is MySQL 8.0+ - use MySQL-specific syntax and functions
3. **Query Requirements**: Generate a syntactically correct, executable query
4. **Security**: Only SELECT queries unless explicitly requested otherwise

## MySQL Syntax Reminders:
- Date functions: DATE(), YEAR(), MONTH(), DAY(), DATE_FORMAT()
- String functions: CONCAT(), SUBSTRING(), LIKE, REGEXP
- Aggregations: COUNT(), SUM(), AVG(), MIN(), MAX() with GROUP BY
- Joins: Use proper MySQL JOIN syntax
- Limits: Use LIMIT for result limiting

## Business Logic Guidelines:
- For financial data: Consider decimal precision
- For date ranges: Include appropriate date comparisons
- For percentages: Assume stored as decimals (0.15 = 15%)
- For aggregations: Handle NULL values appropriately

RESPOND WITH ONLY THE SQL QUERY:""",

    "enterprise": """You are a senior database engineer with 15+ years of MySQL optimization experience.

## CONTEXT & SCHEMA:
Database: MySQL 8.0+ Business Analytics System
{schema}

## TASK:
Convert this business question into an optimal MySQL query: "{question}"

## DOMAIN EXPERTISE:
- fiscal_year: Business periods ('FY2023', '2023', etc.)
- product_code: Unique product identifiers
- customer_code: Unique customer identifiers  
- market: Geographic/business segments
- Percentages: Stored as decimals (0.15 = 15%)
- Financial amounts: DECIMAL precision

## OPTIMIZATION PATTERNS:
- Use LIMIT for top/bottom queries
- Prefer EXISTS over IN for large subqueries
- Use appropriate indexes (assume they exist)
- Consider MySQL-specific optimizations

## EXAMPLES:
"How many products?" → SELECT COUNT(DISTINCT product_code) FROM gross_price;
"Average cost by year" → SELECT cost_year, AVG(manufacturing_cost) FROM manufacturing_cost GROUP BY cost_year ORDER BY cost_year;

## CRITICAL: 
Return ONLY the executable MySQL query - no explanations, no formatting, no comments.

MySQL Query:"""
}


def get_prompt_template(template_type="production"):
    """Get prompt template by type"""
    return PROMPT_TEMPLATES.get(template_type, PROMPT_TEMPLATES["production"])


# Initialize session state
init_session_state()

# Set up the page
st.set_page_config(
    page_title="Advanced SQL Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 Advanced SQL Assistant with AI-Powered Analytics")
st.markdown(
    "*Enterprise-grade SQL generation, optimization, and business intelligence*")

# Create main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Query Builder",
    "📊 Dashboard",
    "⚡ Optimization",
    "📋 Reports",
    "📚 History"
])

# Sidebar for database configuration
st.sidebar.header("🗄️ Database Configuration")

# Prompt template selection
st.sidebar.subheader("🧠 AI Prompt Settings")
prompt_type = st.sidebar.selectbox(
    "Prompt Template Quality",
    options=["production", "enterprise", "basic"],
    index=0,
    help="Choose prompt complexity: Basic (fast), Production (balanced), Enterprise (advanced)"
)

# Display prompt info
if prompt_type == "basic":
    st.sidebar.info("🚀 **Basic**: Fast and simple queries")
elif prompt_type == "production":
    st.sidebar.info("⚡ **Production**: Optimized with best practices")
else:
    st.sidebar.info("🎯 **Enterprise**: Advanced with domain expertise")

# Database type selection
db_type = st.sidebar.selectbox(
    "Database Type",
    ["MySQL", "PostgreSQL"],
    index=0
)

# Database connection form
with st.sidebar.form("db_config"):
    st.subheader("Connection Details")

    db_host = st.text_input(
        "Host", value=DEFAULT_DB_HOST, placeholder="localhost")
    db_port = st.text_input("Port", value=str(
        DEFAULT_DB_PORT), placeholder="3306")
    db_name = st.text_input(
        "Database Name", value=DEFAULT_DB_NAME, placeholder="my_database")
    db_user = st.text_input(
        "Username", value=DEFAULT_DB_USER, placeholder="username")
    db_password = st.text_input(
        "Password", value=DEFAULT_DB_PASSWORD, type="password", placeholder="password")

    connect_button = st.form_submit_button("🔗 Connect to Database")

# Initialize session state for database connection
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
    st.session_state.engine = None
    st.session_state.schema = None

# Handle database connection
if connect_button:
    if not all([db_host, db_port, db_name, db_user, db_password]):
        st.sidebar.error("Please fill in all database connection fields.")
    else:
        try:
            with st.spinner("Connecting to database..."):
                engine = create_db_engine(
                    db_type, db_host, db_port, db_name, db_user, db_password)
                success, message = test_db_connection(engine)

                if success:
                    st.session_state.db_connected = True
                    st.session_state.engine = engine

                    # Get database schema
                    with st.spinner("Loading database schema..."):
                        # Download troubleshooting
                        with st.expander("🛠️ Download Troubleshooting", expanded=False):
                            st.markdown("""
                            **If downloads aren't working:**
                            
                            ✅ **Check Browser Settings:**
                            - Ensure pop-ups are allowed for this site
                            - Check if downloads are blocked by browser
                            - Try right-clicking download button → "Save link as"
                            
                            ✅ **Common Solutions:**
                            - Refresh the page and regenerate the report
                            - Try a different browser (Chrome, Firefox, Edge)
                            - Clear browser cache and cookies
                            - Disable browser extensions temporarily
                            
                            ✅ **Alternative Methods:**
                            - Use the quick CSV button in query results
                            - Copy data directly from the table view
                            - Generate smaller reports (use LIMIT in queries)
                            
                            ✅ **File Size Issues:**
                            - Large datasets may take time to prepare
                            - PDF generation requires more processing time
                            - Try CSV export first for large data
                            """)
                        st.session_state.schema = get_db_schema(engine)

                    st.sidebar.success("✅ Connected successfully!")
                    st.success(
                        "Database connected! You can now use all advanced features.")
                else:
                    st.sidebar.error(f"❌ Connection failed: {message}")
                    st.session_state.db_connected = False
        except Exception as e:
            st.sidebar.error(f"❌ Connection error: {str(e)}")
            st.session_state.db_connected = False

# Display connection status
if st.session_state.db_connected:
    st.sidebar.success("✅ Database Connected")

    # Session info
    st.sidebar.subheader("📊 Session Info")
    st.sidebar.metric(
        "Queries Run", st.session_state.current_session["query_count"])
    st.sidebar.metric("Session Time",
                      str(datetime.now() - st.session_state.current_session["started_at"]).split('.')[0])

    # Show schema information (collapsible)
    with st.sidebar.expander("📋 Database Schema", expanded=False):
        if st.session_state.schema:
            st.text(st.session_state.schema)
else:
    st.sidebar.warning("⚠️ Database Not Connected")

# ============ TAB 1: QUERY BUILDER ============
with tab1:
    st.header("💬 Intelligent Query Builder")

    if not st.session_state.db_connected:
        st.info(
            "👆 Please configure and connect to your database using the sidebar first.")
        st.markdown("""
        ### How to get started:
        1. **Configure Database**: Use the sidebar to enter your database connection details
        2. **Choose Prompt Quality**: Select the AI prompt template that fits your needs
        3. **Connect**: Click the "Connect to Database" button
        4. **Ask Questions**: Once connected, ask questions about your data in natural language
        
        ### Example Questions for Your Business Data:
        #### 📊 **Basic Analytics**
        - "How many products do we have?"
        - "Show me all markets"
        - "What are the available fiscal years?"
        
        #### 💰 **Financial Analysis** 
        - "What's the average gross price by fiscal year?"
        - "Show me products with highest manufacturing costs"
        - "Which customers have the highest pre-invoice discounts?"
        
        #### 📈 **Business Intelligence**
        - "Calculate profit margins for each product"
        - "Show freight costs by market"
        - "Find products with manufacturing cost above $100"
        - "Compare gross prices between 2022 and 2023"
        """)
    else:
        # Favorite queries section
        col1, col2 = st.columns([3, 1])

        with col1:
            # User input
            nl_query = st.text_input(
                "Enter your question in natural language:",
                placeholder="e.g., Show me all customers from New York",
                help="Ask questions about your data in plain English. The AI will convert it to SQL."
            )

        with col2:
            st.markdown("**Quick Actions**")
            if st.button("📋 Use Favorite"):
                favorites = get_favorite_queries()
                if favorites:
                    selected_fav = st.selectbox("Select favorite",
                                                [f"{fav['name']}: {fav['nl_query'][:50]}..." for fav in favorites])
                    if selected_fav:
                        fav_index = int(selected_fav.split(':')
                                        [0].split()[-1]) - 1
                        nl_query = favorites[fav_index]['nl_query']

        if nl_query:
            start_time = time.time()

            # Check if we need to retry with basic prompt
            retry_with_basic = st.session_state.get('retry_with_basic', False)
            if retry_with_basic:
                st.session_state['retry_with_basic'] = False
                current_prompt_type = "basic"
                st.info("🔄 Retrying with Basic prompt template...")
            else:
                current_prompt_type = prompt_type

            # Get the selected prompt template
            template = get_prompt_template(current_prompt_type)
            prompt = template.format(
                schema=st.session_state.schema, question=nl_query)

            # Generate SQL using Groq LLM
            with st.spinner("🤖 Generating SQL using Groq LLM..."):
                raw_sql_query = call_groq_llm(prompt)

            if raw_sql_query:
                sql_query = clean_sql_response(raw_sql_query)

                if not sql_query:
                    st.error(
                        "❌ Failed to extract valid SQL from the AI response.")

                    # Try automatic retry with basic prompt if not already tried
                    if current_prompt_type != "basic" and not retry_with_basic:
                        st.info(
                            "🔄 Attempting automatic retry with Basic prompt...")

                        basic_template = get_prompt_template("basic")
                        basic_prompt = basic_template.format(
                            schema=st.session_state.schema, question=nl_query)

                        with st.spinner("🤖 Retrying with simplified prompt..."):
                            retry_raw_sql = call_groq_llm(basic_prompt)

                        if retry_raw_sql:
                            sql_query = clean_sql_response(retry_raw_sql)
                            if sql_query:
                                st.success(
                                    "✅ Retry successful with Basic prompt!")
                                raw_sql_query = retry_raw_sql  # Update for debugging display

                    if not sql_query:
                        with st.expander("🔧 Debugging Information", expanded=True):
                            st.subheader("Raw AI Response:")
                            st.text_area("Full response from AI:",
                                         raw_sql_query, height=200)

                            st.subheader("Troubleshooting Tips:")
                            st.markdown("""
                            **Common Issues & Solutions:**
                            1. **AI returned explanations instead of SQL:**
                               - Try rephrasing: "Generate only the SQL query for..."
                               - Use simpler language
                               - Be more specific about table names
                            
                            2. **Complex query causing issues:**
                               - Break down into simpler parts
                               - Ask for basic query first, then refine
                            
                            3. **Schema confusion:**
                               - Verify table and column names exist
                               - Check the schema in the sidebar
                            
                            4. **Try different approaches:**
                               - "Show me data from [table_name]"
                               - "Count records in [table_name]"
                               - "List columns in [table_name]"
                            """)
                else:
                    # Display generated SQL
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.subheader("📝 Generated SQL Query")
                    with col2:
                        if st.button("⭐ Add to Favorites"):
                            fav_name = st.text_input(
                                "Favorite name:", value=f"Query {len(get_favorite_queries()) + 1}")
                            add_to_favorites(nl_query, sql_query, fav_name)
                            st.success("Added to favorites!")
                    with col3:
                        complexity = parse_sql_complexity(sql_query)
                        st.metric("Complexity Score", sum(
                            complexity.values()) if isinstance(complexity, dict) else 0)

                    st.code(sql_query, language="sql")

                    # Store SQL query for later export
                    st.session_state['last_sql_query'] = sql_query
                    st.session_state['last_nl_query'] = nl_query

                    # Execute SQL and display results
                    st.subheader("📊 Query Results")
                    try:
                        with st.spinner("🔍 Executing query..."):
                            results, columns = execute_sql(
                                st.session_state.engine, sql_query)
                            execution_time = time.time() - start_time

                        if results:
                            df = pd.DataFrame(results, columns=columns)

                            # Display data
                            st.dataframe(df, use_container_width=True)

                            # Add to history
                            add_to_history(nl_query, sql_query,
                                           len(results), execution_time)

                            # Show result summary
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Rows Retrieved", len(results))
                            with col2:
                                st.metric("Execution Time",
                                          f"{execution_time:.2f}s")
                            with col3:
                                st.metric("Columns", len(columns))
                            with col4:
                                # Quick CSV download
                                csv_data = df.to_csv(index=False)
                                st.download_button(
                                    label="💾 CSV",
                                    data=csv_data,
                                    file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    help="Quick CSV download"
                                )

                            # Quick visualization
                            if len(df) > 0:
                                st.subheader("📈 Quick Visualization")
                                viz_chart = create_auto_visualization(df)
                                if viz_chart:
                                    st.plotly_chart(
                                        viz_chart, use_container_width=True)
                        else:
                            st.info(
                                "✅ Query executed successfully, but no data was returned.")
                            add_to_history(nl_query, sql_query,
                                           0, execution_time)

                    except Exception as e:
                        st.error(f"❌ Error executing query: {str(e)}")
                        st.info(
                            "💡 Try rephrasing your question or check if the table/column names are correct.")

                        with st.expander("🔧 Debug Information"):
                            st.text(f"Raw LLM response: {raw_sql_query}")
                            st.text(f"Cleaned SQL: {sql_query}")
            else:
                st.error(
                    "❌ Failed to generate SQL query. Please check your Groq API key and try again.")

# ============ TAB 2: DASHBOARD ============
with tab2:
    st.header("📊 Interactive Dashboard")

    if not st.session_state.db_connected:
        st.info("Connect to your database to access dashboard features.")
    else:
        # Dashboard controls
        col1, col2, col3 = st.columns(3)

        with col1:
            dashboard_query = st.selectbox(
                "Quick Dashboard Queries",
                [
                    "SELECT * FROM information_schema.tables WHERE table_schema = DATABASE()",
                    "SHOW TABLE STATUS",
                    "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = DATABASE()",
                    "Custom Query..."
                ]
            )

        with col2:
            chart_type = st.selectbox(
                "Chart Type",
                ["auto", "bar", "line", "pie", "scatter", "histogram"]
            )

        with col3:
            refresh_dashboard = st.button("🔄 Refresh Dashboard")

        if dashboard_query == "Custom Query...":
            custom_query = st.text_area("Enter custom SQL query:", height=100)
            if custom_query and st.button("Execute Dashboard Query"):
                try:
                    results, columns = execute_sql(
                        st.session_state.engine, custom_query)
                    if results:
                        df = pd.DataFrame(results, columns=columns)

                        # Create dashboard charts
                        charts = create_dashboard_charts(df)

                        # Display charts
                        for chart_title, chart in charts:
                            st.subheader(chart_title)
                            if chart:
                                st.plotly_chart(
                                    chart, use_container_width=True)

                        # Data table
                        st.subheader("📋 Data Table")
                        st.dataframe(df, use_container_width=True)

                except Exception as e:
                    st.error(f"Dashboard error: {str(e)}")

        elif dashboard_query and dashboard_query != "Custom Query...":
            try:
                results, columns = execute_sql(
                    st.session_state.engine, dashboard_query)
                if results:
                    df = pd.DataFrame(results, columns=columns)

                    # Create visualization
                    if chart_type == "auto":
                        viz_chart = create_auto_visualization(df)
                    else:
                        viz_chart = create_auto_visualization(df, chart_type)

                    if viz_chart:
                        st.plotly_chart(viz_chart, use_container_width=True)

                    st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Dashboard error: {str(e)}")

# ============ TAB 3: OPTIMIZATION ============
with tab3:
    st.header("⚡ Query Optimization Center")

    if not st.session_state.db_connected:
        st.info("Connect to your database to access optimization features.")
    else:
        st.subheader("🔍 Analyze Query Performance")

        # Query input for optimization
        optimize_query = st.text_area(
            "Enter SQL query to optimize:",
            height=150,
            placeholder="SELECT * FROM your_table WHERE conditions..."
        )

        col1, col2 = st.columns(2)

        with col1:
            analyze_button = st.button("📊 Analyze Performance")

        with col2:
            suggest_button = st.button("💡 Get AI Suggestions")

        if optimize_query and analyze_button:
            try:
                with st.spinner("Analyzing query performance..."):
                    # Parse query complexity
                    complexity = parse_sql_complexity(optimize_query)

                    # Display complexity metrics
                    st.subheader("📈 Query Complexity Analysis")

                    if isinstance(complexity, dict) and "error" not in complexity:
                        col1, col2, col3, col4, col5 = st.columns(5)

                        with col1:
                            st.metric("Tables", complexity.get("tables", 0))
                        with col2:
                            st.metric("Joins", complexity.get("joins", 0))
                        with col3:
                            st.metric("Subqueries", complexity.get(
                                "subqueries", 0))
                        with col4:
                            st.metric("Aggregations", complexity.get(
                                "aggregations", 0))
                        with col5:
                            st.metric("Conditions", complexity.get(
                                "conditions", 0))

                    # Get execution plan
                    explain_result = analyze_query_performance(
                        st.session_state.engine, optimize_query, db_type.lower()
                    )

                    if explain_result and not isinstance(explain_result, str):
                        st.subheader("🔧 Execution Plan")
                        st.json(explain_result)
                    elif isinstance(explain_result, str):
                        st.warning(f"Could not analyze: {explain_result}")

            except Exception as e:
                st.error(f"Analysis error: {str(e)}")

        if optimize_query and suggest_button:
            try:
                with st.spinner("Generating AI optimization suggestions..."):
                    # Get optimization suggestions
                    suggestions = get_optimization_suggestions(
                        optimize_query,
                        "Query analysis in progress...",
                        st.session_state.schema
                    )

                    if suggestions:
                        st.subheader("💡 AI-Powered Optimization Suggestions")
                        st.markdown(suggestions)
                    else:
                        st.warning(
                            "Could not generate optimization suggestions.")

            except Exception as e:
                st.error(f"Suggestion error: {str(e)}")

        # Performance tips
        st.subheader("🎯 General Performance Tips")
        with st.expander("Click to view optimization best practices"):
            st.markdown("""
            ### Query Optimization Best Practices:
            
            **Indexing:**
            - Add indexes on frequently queried columns
            - Use composite indexes for multi-column WHERE clauses
            - Avoid over-indexing (impacts INSERT/UPDATE performance)
            
            **Query Structure:**
            - Use LIMIT for large result sets
            - Prefer EXISTS over IN for subqueries
            - Use appropriate JOIN types
            - Avoid SELECT * when possible
            
            **WHERE Clauses:**
            - Place most selective conditions first
            - Use indexed columns in WHERE clauses
            - Avoid functions in WHERE conditions
            
            **Performance Monitoring:**
            - Use EXPLAIN to understand execution plans
            - Monitor slow query logs
            - Regular database maintenance (ANALYZE TABLE)
            """)

# ============ TAB 4: REPORTS ============
with tab4:
    st.header("📋 Business Intelligence Reports")

    if not st.session_state.db_connected:
        st.info("Connect to your database to generate reports.")
    else:
        st.subheader("📊 Generate Comprehensive Report")

        # Report configuration
        col1, col2 = st.columns(2)

        with col1:
            report_query = st.text_area(
                "Query for Report Data:",
                height=100,
                placeholder="SELECT * FROM your_main_table LIMIT 100"
            )

        with col2:
            report_type = st.selectbox(
                "Report Type",
                ["Business Intelligence", "Data Summary", "Performance Analysis"]
            )

            include_charts = st.checkbox("Include Visualizations", value=True)
            include_insights = st.checkbox("Include AI Insights", value=True)

        if st.button("📈 Generate Report") and report_query:
            try:
                with st.spinner("Generating comprehensive report..."):
                    # Execute query
                    results, columns = execute_sql(
                        st.session_state.engine, report_query)

                    if results:
                        df = pd.DataFrame(results, columns=columns)

                        # Generate report data
                        report_data = generate_business_report(
                            df,
                            report_query,
                            {"type": report_type, "charts_included": include_charts}
                        )

                        # Display report
                        st.subheader(f"📋 {report_data['title']}")
                        st.caption(f"Generated: {report_data['generated_at']}")

                        # Report sections
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("📊 Data Summary")
                            summary = report_data["data_summary"]
                            st.metric("Total Rows", summary.get(
                                "total_rows", 0))
                            st.metric("Total Columns", summary.get(
                                "total_columns", 0))
                            st.metric("Memory Usage", summary.get(
                                "memory_usage", "N/A"))

                        with col2:
                            if include_charts:
                                st.subheader("📈 Data Visualization")
                                viz_chart = create_auto_visualization(df)
                                if viz_chart:
                                    st.plotly_chart(
                                        viz_chart, use_container_width=True)

                        # AI Insights
                        if include_insights and report_data.get("insights"):
                            st.subheader("🧠 AI-Generated Insights")
                            st.markdown(report_data["insights"])

                        # Business Recommendations
                        if report_data.get("recommendations"):
                            st.subheader("💼 Business Recommendations")
                            st.markdown(report_data["recommendations"])

                        # Data table
                        st.subheader("📋 Raw Data")
                        st.dataframe(df, use_container_width=True)

                        # Export options
                        st.subheader("📤 Export Options")

                        # Prepare download data
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                        # Prepare CSV data
                        try:
                            csv_data = df.to_csv(index=False)
                        except Exception as e:
                            st.error(f"Error preparing CSV: {e}")
                            csv_data = None

                        # Prepare PDF data
                        pdf_data = None
                        try:
                            with st.spinner("Generating PDF report..."):
                                pdf_buffer = create_pdf_report(report_data, df)
                                if pdf_buffer:
                                    pdf_data = pdf_buffer.getvalue()
                                    st.success(
                                        "✅ PDF report generated successfully!")
                                else:
                                    st.warning(
                                        "⚠️ PDF generation returned empty buffer")
                        except ImportError as e:
                            st.error(
                                f"❌ PDF generation requires additional packages. Install: pip install reportlab")
                        except Exception as e:
                            st.error(f"❌ Error generating PDF: {e}")
                            st.info(
                                "💡 Try generating CSV or JSON export instead")

                        # Prepare JSON data
                        try:
                            report_json = json.dumps(
                                report_data, default=str, indent=2)
                        except Exception as e:
                            st.error(f"Error preparing JSON: {e}")
                            report_json = None

                        # Download buttons
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if csv_data:
                                st.download_button(
                                    label="💾 Download CSV",
                                    data=csv_data,
                                    file_name=f"report_{timestamp}.csv",
                                    mime="text/csv",
                                    help="Download raw data as CSV file"
                                )
                            else:
                                st.button("💾 CSV Unavailable", disabled=True)

                        with col2:
                            if pdf_data:
                                st.download_button(
                                    label="📄 Download PDF",
                                    data=pdf_data,
                                    file_name=f"report_{timestamp}.pdf",
                                    mime="application/pdf",
                                    help="Download formatted PDF report"
                                )
                            else:
                                st.button("📄 PDF Unavailable", disabled=True)

                        with col3:
                            if report_json:
                                st.download_button(
                                    label="📊 Download JSON",
                                    data=report_json,
                                    file_name=f"report_{timestamp}.json",
                                    mime="application/json",
                                    help="Download structured data as JSON"
                                )
                            else:
                                st.button("📊 JSON Unavailable", disabled=True)

                        # Additional export options
                        st.markdown("---")
                        st.subheader("🔄 Additional Export Options")

                        col1, col2 = st.columns(2)

                        with col1:
                            # Excel export
                            try:
                                excel_buffer = io.BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    df.to_excel(
                                        writer, sheet_name='Data', index=False)

                                    # Add summary sheet if we have insights
                                    if report_data.get("insights"):
                                        summary_df = pd.DataFrame({
                                            'Metric': ['Total Rows', 'Total Columns', 'Generated At'],
                                            'Value': [
                                                report_data["data_summary"].get(
                                                    "total_rows", "N/A"),
                                                report_data["data_summary"].get(
                                                    "total_columns", "N/A"),
                                                report_data["generated_at"]
                                            ]
                                        })
                                        summary_df.to_excel(
                                            writer, sheet_name='Summary', index=False)

                                excel_data = excel_buffer.getvalue()

                                st.download_button(
                                    label="📊 Download Excel",
                                    data=excel_data,
                                    file_name=f"report_{timestamp}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    help="Download data as Excel workbook with multiple sheets"
                                )
                            except ImportError:
                                st.info(
                                    "📊 Excel export requires: `pip install openpyxl`")
                            except Exception as e:
                                st.warning(
                                    f"📊 Excel export unavailable: {str(e)[:50]}...")
                                # Fallback to CSV
                                if csv_data:
                                    st.download_button(
                                        label="💾 Download CSV (Fallback)",
                                        data=csv_data,
                                        file_name=f"report_{timestamp}_fallback.csv",
                                        mime="text/csv",
                                        help="Fallback CSV download"
                                    )

                        with col2:
                            # SQL query export
                            if st.session_state.get('last_sql_query'):
                                last_nl_query = st.session_state.get(
                                    'last_nl_query', 'N/A')
                                last_sql_query = st.session_state.get(
                                    'last_sql_query', '')

                                sql_content = f"""-- Generated SQL Query
-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Original Question: {last_nl_query}

{last_sql_query}
"""
                                st.download_button(
                                    label="🗂️ Download SQL",
                                    data=sql_content,
                                    file_name=f"query_{timestamp}.sql",
                                    mime="text/plain",
                                    help="Download the generated SQL query"
                                )
                            else:
                                st.info("🗂️ No SQL query available for export")
                                st.caption(
                                    "Generate a query first to enable SQL export")
                    else:
                        st.warning("No data returned from query.")

            except Exception as e:
                st.error(f"Report generation error: {str(e)}")

# ============ TAB 5: HISTORY ============
with tab5:
    st.header("📚 Query History & Favorites")

    # Create subtabs for history and favorites
    hist_tab1, hist_tab2, hist_tab3 = st.tabs(
        ["🕒 Recent Queries", "⭐ Favorites", "📊 Session Data"])

    with hist_tab1:
        st.subheader("🕒 Query History")

        history = get_query_history()

        if history:
            # Display recent queries
            for i, item in enumerate(reversed(history[-10:])):
                with st.expander(f"Query {len(history)-i}: {item['nl_query'][:60]}..."):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(
                            f"**Natural Language:** {item['nl_query']}")
                        st.code(item['sql_query'], language="sql")
                        st.caption(
                            f"Executed: {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

                    with col2:
                        st.metric("Results", item['results_count'])
                        if item.get('execution_time'):
                            st.metric("Time", f"{item['execution_time']:.2f}s")

                        if st.button(f"🔄 Re-run", key=f"rerun_{i}"):
                            st.info(
                                "Paste the SQL above into the Query Builder tab to re-run")
        else:
            st.info("No query history yet. Run some queries to see them here.")

    with hist_tab2:
        st.subheader("⭐ Favorite Queries")

        favorites = get_favorite_queries()

        if favorites:
            for fav in favorites:
                with st.expander(f"⭐ {fav['name']}"):
                    st.markdown(f"**Question:** {fav['nl_query']}")
                    st.code(fav['sql_query'], language="sql")
                    st.caption(
                        f"Saved: {fav['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔄 Use Query", key=f"use_{fav['id']}"):
                            st.info(
                                "Copy the SQL above to the Query Builder tab")
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{fav['id']}"):
                            st.session_state.favorite_queries = [
                                f for f in st.session_state.favorite_queries if f['id'] != fav['id']
                            ]
                            st.experimental_rerun()
        else:
            st.info("No favorite queries yet. Add some from the Query Builder tab.")

    with hist_tab3:
        st.subheader("📊 Session Analytics")

        session_info = st.session_state.current_session

        # Session metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Session Duration",
                str(datetime.now() - session_info["started_at"]).split('.')[0]
            )

        with col2:
            st.metric("Total Queries", session_info["query_count"])

        with col3:
            st.metric("Favorites Saved", len(get_favorite_queries()))

        # Export session data
        if st.button("📤 Export Session Data"):
            session_json = export_session_data()
            st.download_button(
                label="Download Session Data",
                data=session_json,
                file_name=f"session_{session_info['id']}.json",
                mime="application/json"
            )

        # Clear session option
        if st.button("🗑️ Clear Session Data", type="secondary"):
            if st.checkbox("I understand this will clear all history and favorites"):
                st.session_state.query_history = []
                st.session_state.favorite_queries = []
                st.session_state.current_session["query_count"] = 0
                st.success("Session data cleared!")
                st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown(
    "🔧 **Advanced SQL Assistant** | Powered by Groq AI | Enhanced with Business Intelligence")

# Help section
with st.expander("ℹ️ Help & Documentation"):
    st.markdown("""
    ## 🚀 Advanced Features Guide
    
    ### 🔍 Query Builder
    - **Smart SQL Generation**: Convert natural language to optimized SQL
    - **Prompt Templates**: Choose from Basic, Production, or Enterprise prompts
    - **Quick Visualization**: Automatic chart generation for results
    - **Favorites System**: Save and reuse successful queries
    
    ### 📊 Dashboard
    - **Interactive Charts**: Multiple chart types with auto-detection
    - **Custom Queries**: Run any SQL for dashboard visualization
    - **Real-time Refresh**: Update dashboard data instantly
    
    ### ⚡ Optimization
    - **Performance Analysis**: EXPLAIN query execution plans
    - **AI Suggestions**: Get optimization recommendations
    - **Complexity Scoring**: Understand query complexity metrics
    
    ### 📋 Reports
    - **Business Intelligence**: Comprehensive data analysis reports
    - **AI Insights**: Automated pattern detection and recommendations
    - **Export Options**: PDF, CSV, and JSON export capabilities
    
    ### 📚 History & Sessions
    - **Query History**: Track all executed queries with metadata
    - **Session Management**: Persistent session data and analytics
    - **Export/Import**: Backup and restore query collections
    
    ## 🛠️ Setup Requirements
    - Groq API key in `.env` file as `GROQ_API_KEY`
    - Database connection (MySQL or PostgreSQL)
    - All required Python packages installed
    """)
