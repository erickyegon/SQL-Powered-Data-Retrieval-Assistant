"""
Professional Streamlit UI for Advanced SQL Assistant
Follows data visualization best practices and enterprise UI standards
"""

import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.config import Config
from src.ui.components import (
    setup_page_config, 
    render_sidebar,
    render_header,
    render_query_builder,
    render_dashboard,
    render_optimization,
    render_ai_guidance,
    render_reports,
    render_history,
    render_settings
)

def main():
    """Main application entry point"""
    
    # Configure page with professional settings
    setup_page_config()
    
    # Apply custom CSS for professional appearance
    apply_custom_styling()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main header
    render_header()
    
    # Main content area with professional tabs
    render_main_content()

def apply_custom_styling():
    """Apply professional CSS styling following data visualization principles"""
    
    ui_config = Config.get_ui_config()
    
    st.markdown(f"""
    <style>
    /* Professional color scheme */
    .stApp {{
        background-color: {ui_config['theme']['background_color']};
    }}
    
    /* Header styling */
    .main-header {{
        background: linear-gradient(90deg, {ui_config['theme']['primary_color']}, #2e86ab);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {ui_config['theme']['secondary_background_color']};
        border-radius: 10px;
        padding: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        padding: 0px 24px;
        background-color: transparent;
        border-radius: 8px;
        color: {ui_config['theme']['text_color']};
        font-weight: 500;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {ui_config['theme']['primary_color']};
        color: white;
    }}
    
    /* Metric cards */
    .metric-card {{
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid {ui_config['theme']['primary_color']};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }}
    
    /* Success/Error messages */
    .stSuccess {{
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }}
    
    .stError {{
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }}
    
    /* Code blocks */
    .stCodeBlock {{
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 6px;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background-color: {ui_config['theme']['secondary_background_color']};
    }}
    
    /* Button styling */
    .stButton > button {{
        background-color: {ui_config['theme']['primary_color']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: #1565c0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    /* Data visualization containers */
    .chart-container {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }}
    
    /* Professional spacing */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Hide Streamlit branding for professional appearance */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Professional font */
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'favorite_queries' not in st.session_state:
        st.session_state.favorite_queries = []
    
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 'Query Builder'
    
    if 'dashboard_charts' not in st.session_state:
        st.session_state.dashboard_charts = []

def render_main_content():
    """Render main content with professional tab structure"""
    
    # Professional tab layout
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🔍 Query Builder",
        "📊 Advanced Dashboard", 
        "⚡ Query Optimization",
        "🧠 AI Guidance",
        "📋 Business Reports",
        "📚 Query History",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_query_builder()
    
    with tab2:
        render_dashboard()
    
    with tab3:
        render_optimization()
    
    with tab4:
        render_ai_guidance()
    
    with tab5:
        render_reports()
    
    with tab6:
        render_history()
    
    with tab7:
        render_settings()

if __name__ == "__main__":
    main()
