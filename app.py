"""
Advanced SQL Assistant - Enterprise AI-Powered Business Intelligence Platform
Professional Streamlit Application Entry Point

Author: AI Engineer & Data Scientist Portfolio Project
Demonstrates: LLM Integration, Query Optimization, Advanced Analytics, Enterprise Architecture
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from config import Config, GROQ_API_KEY, MODEL_NAME
from utils import (
    get_db_schema, call_groq_llm, execute_sql_with_error_recovery, 
    create_db_engine, test_db_connection, create_auto_visualization,
    init_session_state, add_to_history, add_to_favorites
)
from query_optimizer import QueryOptimizer, OptimizationLevel
from dashboard_builder import DashboardBuilder
from llm_guidance_system import LLMGuidanceSystem, QueryContext, BusinessDomain, QueryComplexity
from advanced_prompts import PromptTemplateManager

# Page configuration with professional settings
st.set_page_config(
    page_title="Advanced SQL Assistant | AI-Powered BI Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/advanced-sql-assistant',
        'Report a bug': 'https://github.com/yourusername/advanced-sql-assistant/issues',
        'About': """
        # Advanced SQL Assistant v2.0
        **Enterprise AI-Powered Business Intelligence Platform**
        
        Showcasing advanced AI Engineering and Data Science capabilities:
        - Multi-LLM orchestration with intelligent error recovery
        - Advanced query optimization and performance analysis  
        - Power BI-like dashboard creation with 15+ chart types
        - Statistical analysis and business intelligence features
        - Production-ready architecture with enterprise security
        
        Built with: Python, Streamlit, Groq AI, Advanced Analytics
        """
    }
)

def apply_professional_styling():
    """Apply professional CSS styling following data visualization best practices"""
    
    st.markdown("""
    <style>
    /* Professional color scheme and typography */
    .stApp {
        background-color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1f77b4 0%, #2e86ab 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(31, 119, 180, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 0.5rem;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        padding: 0px 24px;
        background-color: transparent;
        border-radius: 10px;
        color: #495057;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.4);
    }
    
    /* Metric cards with professional styling */
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1f77b4 0%, #2e86ab 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(31, 119, 180, 0.4);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #d1ecf1;
        border-color: #bee5eb;
        color: #0c5460;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #17a2b8;
    }
    
    .stError {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #dc3545;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
        border-right: 2px solid #e9ecef;
    }
    
    /* Chart containers */
    .chart-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    
    /* Hide Streamlit branding for professional appearance */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Professional spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Data table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    </style>
    """, unsafe_allow_html=True)

def render_professional_header():
    """Render professional header with branding"""
    
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Advanced SQL Assistant</h1>
        <p>Enterprise AI-Powered Business Intelligence Platform</p>
        <p style="font-size: 1rem; margin-top: 1rem;">
            <strong>Showcasing:</strong> AI Engineering • Data Science • Advanced Analytics • Enterprise Architecture
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_professional_sidebar():
    """Render professional sidebar with database connection"""
    
    with st.sidebar:
        st.markdown("### 🔗 Database Connection")
        
        # Database configuration
        db_type = st.selectbox("Database Type", ["MySQL", "PostgreSQL"], key="db_type")
        
        col1, col2 = st.columns(2)
        with col1:
            db_host = st.text_input("Host", value="localhost", key="db_host")
            db_name = st.text_input("Database", key="db_name")
        with col2:
            db_port = st.text_input("Port", value="3306" if db_type == "MySQL" else "5432", key="db_port")
            db_user = st.text_input("Username", key="db_user")
        
        db_password = st.text_input("Password", type="password", key="db_password")
        
        # Connection button
        if st.button("🔌 Connect to Database", use_container_width=True):
            if all([db_host, db_port, db_name, db_user, db_password]):
                try:
                    with st.spinner("Connecting to database..."):
                        engine = create_db_engine(db_type.lower(), db_host, int(db_port), db_name, db_user, db_password)
                        
                        if test_db_connection(engine):
                            st.session_state.engine = engine
                            st.session_state.db_connected = True
                            st.session_state.db_type = db_type.lower()
                            
                            # Load schema
                            schema = get_db_schema(engine, db_type.lower())
                            st.session_state.schema = schema
                            
                            st.success("✅ Connected successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Connection failed!")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all connection details")
        
        # Connection status
        if st.session_state.get('db_connected', False):
            st.success("🟢 Database Connected")
            
            # Schema info
            if 'schema' in st.session_state:
                schema = st.session_state.schema
                st.markdown("### 📊 Database Schema")
                st.info(f"**Tables:** {len(schema.get('tables', []))}")
                
                with st.expander("View Tables"):
                    for table in schema.get('tables', [])[:10]:  # Show first 10 tables
                        st.write(f"• {table}")
        else:
            st.warning("🔴 Not Connected")
        
        # API Configuration
        st.markdown("### 🤖 AI Configuration")
        if GROQ_API_KEY:
            st.success("✅ Groq API Key Configured")
            st.info(f"**Model:** {MODEL_NAME}")
        else:
            st.error("❌ Groq API Key Missing")
            st.info("Add GROQ_API_KEY to your .env file")

def main():
    """Main application entry point"""
    
    # Apply professional styling
    apply_professional_styling()
    
    # Initialize session state
    init_session_state()
    
    # Render professional header
    render_professional_header()
    
    # Render sidebar
    render_professional_sidebar()
    
    # Main content with professional tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🔍 Query Builder",
        "📊 Advanced Dashboard", 
        "⚡ Query Optimization",
        "🧠 AI Guidance",
        "📋 Business Reports",
        "📚 Query History",
        "⚙️ Settings"
    ])
    
    # Import and render tab content
    with tab1:
        from tabs.query_builder import render_query_builder_tab
        render_query_builder_tab()
    
    with tab2:
        from tabs.dashboard import render_dashboard_tab
        render_dashboard_tab()
    
    with tab3:
        from tabs.optimization import render_optimization_tab
        render_optimization_tab()
    
    with tab4:
        from tabs.ai_guidance import render_ai_guidance_tab
        render_ai_guidance_tab()
    
    with tab5:
        from tabs.reports import render_reports_tab
        render_reports_tab()
    
    with tab6:
        from tabs.history import render_history_tab
        render_history_tab()
    
    with tab7:
        from tabs.settings import render_settings_tab
        render_settings_tab()
    
    # Professional footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; padding: 2rem;">
        <p><strong>Advanced SQL Assistant v2.0</strong> | 
        AI Engineering & Data Science Portfolio Project | 
        Built with Python, Streamlit, Groq AI</p>
        <p>Demonstrating: LLM Integration • Query Optimization • Advanced Analytics • Enterprise Architecture</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
