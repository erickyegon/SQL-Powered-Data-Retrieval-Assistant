import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlparse
import re
from sqlalchemy import text, MetaData, create_engine
from datetime import datetime, timedelta
import streamlit as st
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import base64

from config import GROQ_API_KEY, GROQ_API_URL, MODEL_NAME

# ============ DATABASE FUNCTIONS ============


def build_connection_string(db_type, host, port, database, username, password):
    if db_type.lower() == 'mysql':
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    elif db_type.lower() == 'postgresql':
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def create_db_engine(db_type, host, port, database, username, password):
    connection_string = build_connection_string(
        db_type, host, port, database, username, password)
    return create_engine(connection_string)


def get_db_schema(engine):
    meta = MetaData()
    meta.reflect(bind=engine)
    schema = ""
    for table in meta.tables.values():
        schema += f"\nTable: {table.name}\nColumns: " + ", ".join(
            [f"{col.name} ({col.type})" for col in table.columns]
        ) + "\n"
    return schema.strip()


def test_db_connection(engine):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


def execute_sql(engine, query):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return result.fetchall(), result.keys()

# ============ LLM FUNCTIONS ============


def validate_extracted_sql(sql_query):
    """Validate that the extracted string is actually SQL"""
    if not sql_query:
        return False, "Empty query"

    # Remove comments and whitespace
    cleaned = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    if not cleaned:
        return False, "Query is empty after cleaning"

    # Check for SQL keywords
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE',
                    'DELETE', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN']
    if not any(keyword in cleaned.upper() for keyword in sql_keywords):
        return False, "No valid SQL keywords found"

    # Check for obvious non-SQL content
    non_sql_indicators = [
        'however', 'to calculate', 'this query', 'note that', 'explanation',
        'assuming', 'the following', 'we can use', 'here is', 'you can use',
        'to address', 'the issue', 'the problem'
    ]

    for indicator in non_sql_indicators:
        if indicator in cleaned.lower():
            return False, f"Contains explanatory text: '{indicator}'"

    # Check for balanced parentheses
    if cleaned.count('(') != cleaned.count(')'):
        return False, "Unbalanced parentheses"

    # Check for proper SQL structure
    cleaned_upper = cleaned.upper()
    if cleaned_upper.startswith('SELECT'):
        if 'FROM' not in cleaned_upper:
            return False, "SELECT query missing FROM clause"

    return True, "Valid SQL"


def clean_sql_response(sql_response):
    """Clean SQL response by extracting only the SQL query from verbose AI responses"""
    if not sql_response:
        return None

    sql_response = sql_response.strip()

    # Method 1: Extract from markdown code blocks
    # Look for SQL code blocks with ```sql or ```
    sql_blocks = re.findall(r'```(?:sql)?\s*\n?(.*?)\n?```',
                            sql_response, re.DOTALL | re.IGNORECASE)

    if sql_blocks:
        # Get the first SQL block that looks like a complete query
        for block in sql_blocks:
            cleaned_block = block.strip()
            is_valid, _ = validate_extracted_sql(cleaned_block)
            if is_valid:
                return cleaned_block

    # Method 2: Extract SQL from mixed content
    # Look for lines that start with SQL keywords
    lines = sql_response.split('\n')
    sql_lines = []
    in_sql_block = False

    for line in lines:
        line_upper = line.strip().upper()

        # Start capturing if we see SQL keywords
        if (line_upper.startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'SHOW', 'DESCRIBE', 'EXPLAIN'))):
            in_sql_block = True
            sql_lines.append(line.strip())
        elif in_sql_block:
            # Continue capturing if we're in a SQL block
            if line.strip() and not line.strip().startswith(('--', '#', '//')):
                # Stop if we hit explanatory text
                if any(phrase in line.lower() for phrase in ['however', 'this query', 'note that', 'explanation', 'to address']):
                    break
                sql_lines.append(line.strip())
            elif line.strip().endswith(';'):
                sql_lines.append(line.strip())
                break
            elif not line.strip():
                # Empty line - might be end of SQL
                if sql_lines and sql_lines[-1].endswith(';'):
                    break

    if sql_lines:
        potential_sql = '\n'.join(sql_lines).strip()
        is_valid, _ = validate_extracted_sql(potential_sql)
        if is_valid:
            return potential_sql

    # Method 3: Look for a single line SQL query
    single_line_sql = None
    for line in lines:
        line_stripped = line.strip()
        if (line_stripped.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE', 'EXPLAIN')) and
                line_stripped.endswith(';')):
            is_valid, _ = validate_extracted_sql(line_stripped)
            if is_valid:
                single_line_sql = line_stripped
                break

    if single_line_sql:
        return single_line_sql

    # Method 4: Last resort - try to clean the entire response
    # Remove common explanation phrases and extract just SQL
    explanation_phrases = [
        r'to calculate.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'however.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'this query.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'note that.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'explanation.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'to address.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'assuming.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'the following query.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'we can use.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'here is.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'here\'s.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'the query would be.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'you can use.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)'
    ]

    cleaned = sql_response
    for phrase_pattern in explanation_phrases:
        cleaned = re.sub(phrase_pattern, '', cleaned,
                         flags=re.IGNORECASE | re.DOTALL)

    # Remove markdown formatting
    cleaned = re.sub(r'```(?:sql)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'```', '', cleaned)
    cleaned = cleaned.strip()

    # Try to extract SQL from what remains
    sql_match = re.search(
        r'((?:SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|DESCRIBE|EXPLAIN).*?;)', cleaned, re.IGNORECASE | re.DOTALL)
    if sql_match:
        potential_sql = sql_match.group(1).strip()
        is_valid, _ = validate_extracted_sql(potential_sql)
        if is_valid:
            return potential_sql

    return None


def call_groq_llm(prompt):
    """Call Groq LLM with error handling"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in environment variables")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 400:
            print(f"❌ 400 Bad Request Error: {response.text}")
            return None

        response.raise_for_status()
        response_json = response.json()

        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"].strip()
        else:
            print("❌ Unexpected response structure:", response_json)
            return None

    except Exception as err:
        print(f"❌ An error occurred: {err}")
        return None

# ============ QUERY OPTIMIZATION ============


def analyze_query_performance(engine, query, db_type="mysql"):
    """Analyze query performance and provide optimization suggestions"""
    try:
        if db_type.lower() == "mysql":
            explain_query = f"EXPLAIN FORMAT=JSON {query}"
        else:  # PostgreSQL
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"

        with engine.connect() as conn:
            result = conn.execute(text(explain_query))
            explain_result = result.fetchone()[0]

        return explain_result
    except Exception as e:
        return f"Error analyzing query: {str(e)}"


def get_optimization_suggestions(query, explain_result, schema):
    """Get AI-powered optimization suggestions"""
    optimization_prompt = f"""
You are a database performance expert. Analyze this SQL query and its execution plan to provide optimization suggestions.

Query:
{query}

Execution Plan:
{explain_result}

Database Schema:
{schema}

Provide specific, actionable optimization suggestions including:
1. Index recommendations
2. Query rewrite suggestions
3. Performance bottlenecks
4. Best practices violations

Format as a bulleted list with clear, implementable recommendations.
"""

    return call_groq_llm(optimization_prompt)


def parse_sql_complexity(query):
    """Parse SQL query to determine complexity metrics"""
    try:
        parsed = sqlparse.parse(query)[0]

        complexity = {
            "tables": 0,
            "joins": 0,
            "subqueries": 0,
            "aggregations": 0,
            "conditions": 0
        }

        query_upper = query.upper()

        # Count tables (rough estimate)
        if "FROM" in query_upper:
            complexity["tables"] = query_upper.count(
                "FROM") + query_upper.count("JOIN")

        # Count joins
        complexity["joins"] = query_upper.count("JOIN")

        # Count subqueries
        complexity["subqueries"] = query_upper.count("SELECT") - 1

        # Count aggregations
        agg_functions = ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", "GROUP BY"]
        complexity["aggregations"] = sum(
            query_upper.count(func) for func in agg_functions)

        # Count conditions
        complexity["conditions"] = query_upper.count(
            "WHERE") + query_upper.count("AND") + query_upper.count("OR")

        return complexity
    except:
        return {"error": "Could not parse query complexity"}

# ============ DATA VISUALIZATION ============


def create_auto_visualization(df, chart_type="auto"):
    """Create automatic visualizations based on data characteristics"""
    if df.empty:
        return None

    # Determine best chart type if auto
    if chart_type == "auto":
        chart_type = suggest_chart_type(df)

    try:
        if chart_type == "bar":
            return create_bar_chart(df)
        elif chart_type == "line":
            return create_line_chart(df)
        elif chart_type == "pie":
            return create_pie_chart(df)
        elif chart_type == "scatter":
            return create_scatter_plot(df)
        elif chart_type == "histogram":
            return create_histogram(df)
        else:
            return create_bar_chart(df)  # Default fallback
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        return None


def suggest_chart_type(df):
    """Suggest appropriate chart type based on data characteristics"""
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns

    if len(numeric_cols) >= 2:
        return "scatter"
    elif len(categorical_cols) == 1 and len(numeric_cols) == 1:
        if len(df) <= 10:
            return "pie"
        else:
            return "bar"
    elif len(categorical_cols) >= 1:
        return "bar"
    elif len(numeric_cols) == 1:
        return "histogram"
    else:
        return "bar"


def create_bar_chart(df):
    """Create bar chart from dataframe"""
    if len(df.columns) < 2:
        return None

    x_col = df.columns[0]
    y_col = df.columns[1]

    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
    fig.update_layout(height=500)
    return fig


def create_line_chart(df):
    """Create line chart from dataframe"""
    if len(df.columns) < 2:
        return None

    x_col = df.columns[0]
    y_col = df.columns[1]

    fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
    fig.update_layout(height=500)
    return fig


def create_pie_chart(df):
    """Create pie chart from dataframe"""
    if len(df.columns) < 2:
        return None

    labels_col = df.columns[0]
    values_col = df.columns[1]

    fig = px.pie(df, names=labels_col, values=values_col,
                 title=f"Distribution of {values_col}")
    return fig


def create_scatter_plot(df):
    """Create scatter plot from dataframe"""
    numeric_cols = df.select_dtypes(include=['number']).columns

    if len(numeric_cols) < 2:
        return None

    x_col = numeric_cols[0]
    y_col = numeric_cols[1]

    fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
    fig.update_layout(height=500)
    return fig


def create_histogram(df):
    """Create histogram from dataframe"""
    numeric_cols = df.select_dtypes(include=['number']).columns

    if len(numeric_cols) == 0:
        return None

    col = numeric_cols[0]
    fig = px.histogram(df, x=col, title=f"Distribution of {col}")
    fig.update_layout(height=500)
    return fig


def create_dashboard_charts(df):
    """Create multiple charts for dashboard view"""
    charts = []

    # Summary statistics
    if not df.empty:
        summary_fig = create_summary_table(df)
        charts.append(("Summary Statistics", summary_fig))

    # Auto visualization
    auto_chart = create_auto_visualization(df)
    if auto_chart:
        charts.append(("Data Visualization", auto_chart))

    return charts


def create_summary_table(df):
    """Create summary statistics table"""
    try:
        summary = df.describe()

        fig = go.Figure(data=[go.Table(
            header=dict(values=['Statistic'] + list(summary.columns),
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[summary.index] + [summary[col] for col in summary.columns],
                       fill_color='lavender',
                       align='left'))
        ])

        fig.update_layout(title="Summary Statistics", height=400)
        return fig
    except:
        return None

# ============ REPORT GENERATION ============


def generate_business_report(df, query, analysis_results=None):
    """Generate comprehensive business intelligence report"""
    report_data = {
        "title": "Business Intelligence Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "data_summary": get_data_summary(df),
        "analysis": analysis_results or {},
        "insights": generate_ai_insights(df, query),
        "recommendations": get_business_recommendations(df, query)
    }

    return report_data


def get_data_summary(df):
    """Get comprehensive data summary"""
    if df.empty:
        return {"error": "No data to summarize"}

    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "column_types": {col: str(df[col].dtype) for col in df.columns},
        "missing_values": df.isnull().sum().to_dict(),
        "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    }

    # Add statistical summary for numeric columns
    numeric_summary = df.describe().to_dict() if not df.select_dtypes(
        include=['number']).empty else {}
    summary["statistics"] = numeric_summary

    return summary


def generate_ai_insights(df, query):
    """Generate AI-powered insights from data"""
    insights_prompt = f"""
Analyze this business data and query to provide key insights:

Query: {query}
Data Summary:
- Rows: {len(df)}
- Columns: {list(df.columns)}

Sample Data:
{df.head().to_string()}

Statistical Summary:
{df.describe().to_string() if not df.select_dtypes(include=['number']).empty else "No numeric data"}

Provide 3-5 key business insights and trends from this data. Focus on:
1. Notable patterns or outliers
2. Business implications
3. Data quality observations
4. Actionable findings

Keep insights concise and business-focused.
"""

    return call_groq_llm(insights_prompt)


def get_business_recommendations(df, query):
    """Get AI-powered business recommendations"""
    recommendations_prompt = f"""
Based on this business query and data analysis, provide strategic recommendations:

Query: {query}
Data Points: {len(df)} rows

Key Metrics:
{df.head().to_string()}

Provide 3-5 actionable business recommendations including:
1. Strategic actions based on the data
2. Areas for further investigation  
3. Risk mitigation strategies
4. Opportunities for optimization

Format as numbered recommendations with clear action items.
"""

    return call_groq_llm(recommendations_prompt)


def create_pdf_report(report_data, df):
    """Create PDF report from report data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        spaceAfter=30
    )
    story.append(Paragraph(report_data["title"], title_style))
    story.append(Spacer(1, 12))

    # Metadata
    story.append(Paragraph(
        f"<b>Generated:</b> {report_data['generated_at']}", styles['Normal']))
    story.append(
        Paragraph(f"<b>Query:</b> {report_data['query'][:100]}...", styles['Normal']))
    story.append(Spacer(1, 20))

    # Data Summary
    story.append(Paragraph("Data Summary", styles['Heading2']))
    summary = report_data["data_summary"]
    story.append(
        Paragraph(f"Total Rows: {summary.get('total_rows', 'N/A')}", styles['Normal']))
    story.append(Paragraph(
        f"Total Columns: {summary.get('total_columns', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Sample data table
    if not df.empty and len(df) > 0:
        story.append(Paragraph("Sample Data", styles['Heading2']))

        # Create table data
        sample_df = df.head(10)
        table_data = [list(sample_df.columns)]
        for _, row in sample_df.iterrows():
            table_data.append(
                [str(val)[:20] + "..." if len(str(val)) > 20 else str(val) for val in row])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

    # Insights
    if report_data.get("insights"):
        story.append(Paragraph("Key Insights", styles['Heading2']))
        story.append(Paragraph(report_data["insights"], styles['Normal']))
        story.append(Spacer(1, 20))

    # Recommendations
    if report_data.get("recommendations"):
        story.append(Paragraph("Business Recommendations", styles['Heading2']))
        story.append(
            Paragraph(report_data["recommendations"], styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ============ SESSION MANAGEMENT ============


def init_session_state():
    """Initialize session state for query history and favorites"""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []

    if 'favorite_queries' not in st.session_state:
        st.session_state.favorite_queries = []

    if 'current_session' not in st.session_state:
        st.session_state.current_session = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "started_at": datetime.now(),
            "query_count": 0
        }


def add_to_history(nl_query, sql_query, results_count, execution_time=None):
    """Add query to history"""
    history_item = {
        "timestamp": datetime.now(),
        "nl_query": nl_query,
        "sql_query": sql_query,
        "results_count": results_count,
        "execution_time": execution_time,
        "session_id": st.session_state.current_session["id"]
    }

    st.session_state.query_history.append(history_item)
    st.session_state.current_session["query_count"] += 1

    # Keep only last 50 queries
    if len(st.session_state.query_history) > 50:
        st.session_state.query_history = st.session_state.query_history[-50:]


def add_to_favorites(nl_query, sql_query, name=None):
    """Add query to favorites"""
    favorite_item = {
        "id": len(st.session_state.favorite_queries) + 1,
        "name": name or f"Query {len(st.session_state.favorite_queries) + 1}",
        "nl_query": nl_query,
        "sql_query": sql_query,
        "created_at": datetime.now()
    }

    st.session_state.favorite_queries.append(favorite_item)


def get_query_history():
    """Get formatted query history"""
    return st.session_state.query_history


def get_favorite_queries():
    """Get favorite queries"""
    return st.session_state.favorite_queries


def export_session_data():
    """Export session data as JSON"""
    session_data = {
        "session_info": st.session_state.current_session,
        "query_history": [
            {
                **item,
                "timestamp": item["timestamp"].isoformat()
            }
            for item in st.session_state.query_history
        ],
        "favorite_queries": [
            {
                **item,
                "created_at": item["created_at"].isoformat()
            }
            for item in st.session_state.favorite_queries
        ],
        "exported_at": datetime.now().isoformat()
    }

    return json.dumps(session_data, indent=2)
