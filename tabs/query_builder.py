"""
Query Builder Tab - Professional AI-Powered SQL Generation
Demonstrates advanced prompt engineering and LLM integration
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils import (
    call_groq_llm, execute_sql_with_error_recovery, clean_sql_response,
    create_auto_visualization, add_to_history, add_to_favorites
)
from advanced_prompts import PromptTemplateManager

def render_query_builder_tab():
    """Render the professional query builder interface"""
    
    st.markdown("### 🔍 AI-Powered SQL Query Builder")
    st.markdown("Transform natural language questions into optimized SQL queries using advanced LLM technology.")
    
    if not st.session_state.get('db_connected', False):
        st.warning("⚠️ Please connect to your database first using the sidebar.")
        return
    
    # Professional layout with columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Natural language input
        st.markdown("#### 💬 Ask Your Question")
        nl_query = st.text_area(
            "Describe what you want to know about your data:",
            height=120,
            placeholder="Example: Show me the top 10 customers by revenue in the last quarter, including their growth rate compared to the previous quarter",
            help="Use natural language to describe your data question. The AI will convert it to optimized SQL."
        )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                prompt_template = st.selectbox(
                    "Prompt Template",
                    ["business_analyst", "data_scientist", "performance_optimizer"],
                    help="Choose the AI persona for query generation"
                )
                
                include_optimization = st.checkbox(
                    "Include Query Optimization",
                    value=True,
                    help="Add performance optimization hints"
                )
            
            with col_b:
                result_limit = st.number_input(
                    "Result Limit",
                    min_value=10,
                    max_value=10000,
                    value=1000,
                    help="Maximum number of rows to return"
                )
                
                explain_query = st.checkbox(
                    "Explain Query Logic",
                    value=False,
                    help="Include explanation of the generated SQL"
                )
    
    with col2:
        # Quick query templates
        st.markdown("#### ⚡ Quick Templates")
        
        quick_templates = {
            "📊 Revenue Analysis": "Show total revenue by month for the last 12 months",
            "👥 Customer Insights": "Show top 10 customers by total purchases",
            "📈 Growth Trends": "Show year-over-year growth by product category",
            "🎯 Performance KPIs": "Show key performance metrics for this quarter",
            "📋 Data Summary": "Show a summary of all tables and record counts"
        }
        
        for template_name, template_query in quick_templates.items():
            if st.button(template_name, use_container_width=True):
                st.session_state.template_query = template_query
                st.rerun()
        
        # Use template if selected
        if 'template_query' in st.session_state:
            nl_query = st.session_state.template_query
            del st.session_state.template_query
    
    # Generate SQL button
    if st.button("🚀 Generate SQL Query", type="primary", use_container_width=True):
        if nl_query.strip():
            generate_and_execute_query(nl_query, prompt_template, include_optimization, result_limit, explain_query)
        else:
            st.warning("⚠️ Please enter a question first.")

def generate_and_execute_query(nl_query, prompt_template, include_optimization, result_limit, explain_query):
    """Generate and execute SQL query with professional error handling"""
    
    try:
        # Initialize prompt manager
        prompt_manager = PromptTemplateManager()
        
        # Generate enhanced prompt
        with st.spinner("🧠 Generating optimized SQL query..."):
            start_time = time.time()
            
            # Get the appropriate prompt template
            enhanced_prompt = prompt_manager.get_template(
                prompt_template,
                db_type=st.session_state.get('db_type', 'mysql'),
                schema=str(st.session_state.get('schema', {})),
                question=nl_query
            )
            
            # Add optimization hints if requested
            if include_optimization:
                enhanced_prompt += f"\n\nOptimization Requirements:\n- Limit results to {result_limit} rows\n- Use appropriate indexes\n- Optimize for performance"
            
            # Add explanation request if needed
            if explain_query:
                enhanced_prompt += "\n\nPlease also provide a brief explanation of the query logic."
            
            # Call LLM
            raw_sql_query = call_groq_llm(enhanced_prompt)
            
            if not raw_sql_query:
                st.error("❌ Failed to generate SQL query. Please try rephrasing your question.")
                return
            
            # Clean the response
            sql_query = clean_sql_response(raw_sql_query)
            
            if not sql_query:
                st.error("❌ Generated query appears to be invalid. Please try again.")
                return
        
        # Display generated query
        st.markdown("### 📝 Generated SQL Query")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.code(sql_query, language="sql")
        
        with col2:
            if st.button("⭐ Save as Favorite"):
                add_to_favorites(nl_query, sql_query)
                st.success("✅ Saved to favorites!")
        
        with col3:
            if st.button("📋 Copy Query"):
                st.code(sql_query, language="sql")
                st.info("💡 Query displayed above for copying")
        
        # Execute query with error recovery
        st.markdown("### 📊 Query Results")
        
        try:
            with st.spinner("🔍 Executing query with intelligent error recovery..."):
                results, columns, final_query = execute_sql_with_error_recovery(
                    st.session_state.engine, sql_query, st.session_state.schema)
                execution_time = time.time() - start_time
                
                # Show if query was modified
                if final_query != sql_query:
                    st.success("🔧 Query was automatically optimized and executed successfully!")
                    with st.expander("📝 View Optimized Query"):
                        st.code(final_query, language="sql")
            
            if results:
                df = pd.DataFrame(results, columns=columns)
                
                # Store results for dashboard use
                st.session_state.query_results = df
                
                # Professional results display
                render_query_results(df, nl_query, final_query, execution_time)
                
                # Add to history
                add_to_history(nl_query, final_query, len(results), execution_time)
                
            else:
                st.info("✅ Query executed successfully, but no data was returned.")
                add_to_history(nl_query, final_query, 0, execution_time)
        
        except Exception as e:
            render_query_error(str(e), sql_query, raw_sql_query)
    
    except Exception as e:
        st.error(f"❌ Error generating query: {str(e)}")

def render_query_results(df, nl_query, sql_query, execution_time):
    """Render query results with professional styling and analytics"""
    
    # Results metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Rows Retrieved", f"{len(df):,}")
    
    with col2:
        st.metric("⚡ Execution Time", f"{execution_time:.2f}s")
    
    with col3:
        st.metric("📋 Columns", len(df.columns))
    
    with col4:
        # Quick export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="💾 Export CSV",
            data=csv_data,
            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Data preview with professional styling
    st.markdown("#### 📋 Data Preview")
    
    # Show data with pagination for large datasets
    if len(df) > 100:
        st.info(f"📊 Showing first 100 rows of {len(df):,} total rows")
        display_df = df.head(100)
    else:
        display_df = df
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )
    
    # Auto-visualization
    if len(df) > 0 and len(df.columns) >= 2:
        st.markdown("#### 📈 Intelligent Visualization")
        
        with st.container():
            viz_chart = create_auto_visualization(df)
            if viz_chart:
                st.plotly_chart(viz_chart, use_container_width=True, height=500)
            else:
                st.info("💡 No suitable visualization found for this data structure.")
    
    # Data insights
    if len(df) > 0:
        render_data_insights(df)

def render_data_insights(df):
    """Render professional data insights"""
    
    with st.expander("🔍 Data Insights & Statistics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Data Summary**")
            st.write(f"• **Total Records:** {len(df):,}")
            st.write(f"• **Columns:** {len(df.columns)}")
            
            # Data types
            numeric_cols = df.select_dtypes(include=['number']).columns
            text_cols = df.select_dtypes(include=['object']).columns
            date_cols = df.select_dtypes(include=['datetime']).columns
            
            st.write(f"• **Numeric Columns:** {len(numeric_cols)}")
            st.write(f"• **Text Columns:** {len(text_cols)}")
            st.write(f"• **Date Columns:** {len(date_cols)}")
        
        with col2:
            st.markdown("**📈 Quick Statistics**")
            
            if len(numeric_cols) > 0:
                # Show statistics for first numeric column
                first_numeric = numeric_cols[0]
                col_stats = df[first_numeric].describe()
                
                st.write(f"**{first_numeric}:**")
                st.write(f"• Mean: {col_stats['mean']:.2f}")
                st.write(f"• Median: {col_stats['50%']:.2f}")
                st.write(f"• Std Dev: {col_stats['std']:.2f}")
                st.write(f"• Range: {col_stats['min']:.2f} - {col_stats['max']:.2f}")

def render_query_error(error_str, sql_query, raw_sql_query):
    """Render professional error handling interface"""
    
    st.error(f"❌ Query Execution Error: {error_str}")
    
    # Provide helpful error analysis
    if "Unknown column" in error_str:
        st.warning("🔍 **Column Reference Error**: The query references a column that doesn't exist.")
        st.info("💡 **Suggestions:**\n- Check column names in your database schema\n- Verify table aliases are correct\n- Try rephrasing your question")
    elif "Table" in error_str and "doesn't exist" in error_str:
        st.warning("🔍 **Table Reference Error**: The query references a table that doesn't exist.")
        st.info("💡 **Suggestions:**\n- Check table names in your database\n- Verify database connection\n- Try asking about available tables first")
    elif "syntax error" in error_str.lower():
        st.warning("🔍 **SQL Syntax Error**: The generated query has syntax issues.")
        st.info("💡 **Suggestions:**\n- Try rephrasing your question more clearly\n- Use simpler language\n- Break complex requests into smaller parts")
    
    # Debug information
    with st.expander("🔧 Debug Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Raw LLM Response:**")
            st.code(raw_sql_query, language="sql")
        
        with col2:
            st.markdown("**Cleaned SQL:**")
            st.code(sql_query, language="sql")
        
        st.markdown("**Error Details:**")
        st.text(error_str)
    
    # Test connection button
    if st.button("🧪 Test Database Connection"):
        try:
            from utils import execute_sql
            test_results, test_columns = execute_sql(
                st.session_state.engine, 
                "SELECT 1 as test_connection"
            )
            st.success("✅ Database connection is working!")
        except Exception as test_e:
            st.error(f"❌ Database connection issue: {str(test_e)}")
