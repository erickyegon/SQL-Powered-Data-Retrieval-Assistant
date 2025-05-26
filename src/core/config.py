"""
Configuration Management for Advanced SQL Assistant
Centralized configuration with environment variable support
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    # Groq API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_NAME = "llama-3.3-70b-versatile"
    
    # Database Configuration
    DEFAULT_DB_HOST = os.getenv("DB_HOST", "localhost")
    DEFAULT_DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DEFAULT_DB_NAME = os.getenv("DB_NAME", "")
    DEFAULT_DB_USER = os.getenv("DB_USER", "")
    DEFAULT_DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Application Configuration
    MAX_QUERY_HISTORY = int(os.getenv("MAX_QUERY_HISTORY", "100"))
    MAX_FAVORITES = int(os.getenv("MAX_FAVORITES", "50"))
    QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", "300"))
    
    # LLM Configuration
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    
    # Security Configuration
    ENABLE_SQL_VALIDATION = os.getenv("ENABLE_SQL_VALIDATION", "true").lower() == "true"
    ALLOW_MODIFICATION_QUERIES = os.getenv("ALLOW_MODIFICATION_QUERIES", "false").lower() == "true"
    
    # Professional UI Theme
    UI_THEME = {
        'primary_color': '#1f77b4',
        'background_color': '#ffffff',
        'secondary_background_color': '#f0f2f6',
        'text_color': '#262730',
        'font': 'sans serif'
    }
    
    # Data Visualization Standards (following best practices)
    CHART_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    # Visualization Configuration
    ENABLE_INTERACTIVE_CHARTS = os.getenv("ENABLE_INTERACTIVE_CHARTS", "true").lower() == "true"
    MAX_VISUALIZATION_ROWS = int(os.getenv("MAX_VISUALIZATION_ROWS", "10000"))
    DEFAULT_CHART_HEIGHT = int(os.getenv("DEFAULT_CHART_HEIGHT", "500"))
    
    # Export Configuration
    ENABLE_CSV_EXPORT = os.getenv("ENABLE_CSV_EXPORT", "true").lower() == "true"
    ENABLE_JSON_EXPORT = os.getenv("ENABLE_JSON_EXPORT", "true").lower() == "true"
    ENABLE_EXCEL_EXPORT = os.getenv("ENABLE_EXCEL_EXPORT", "true").lower() == "true"
    MAX_EXPORT_ROWS = int(os.getenv("MAX_EXPORT_ROWS", "100000"))
    
    # Session Configuration
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_QUERIES = os.getenv("LOG_QUERIES", "true").lower() == "true"
    LOG_PERFORMANCE = os.getenv("LOG_PERFORMANCE", "true").lower() == "true"
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Get database configuration as dictionary"""
        return {
            'host': cls.DEFAULT_DB_HOST,
            'port': cls.DEFAULT_DB_PORT,
            'database': cls.DEFAULT_DB_NAME,
            'user': cls.DEFAULT_DB_USER,
            'password': cls.DEFAULT_DB_PASSWORD
        }
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration as dictionary"""
        return {
            'api_key': cls.GROQ_API_KEY,
            'api_url': cls.GROQ_API_URL,
            'model_name': cls.MODEL_NAME,
            'temperature': cls.LLM_TEMPERATURE,
            'max_tokens': cls.LLM_MAX_TOKENS
        }
    
    @classmethod
    def get_ui_config(cls) -> Dict[str, Any]:
        """Get UI configuration for professional styling"""
        return {
            'theme': cls.UI_THEME,
            'chart_colors': cls.CHART_COLORS,
            'chart_height': cls.DEFAULT_CHART_HEIGHT,
            'interactive_charts': cls.ENABLE_INTERACTIVE_CHARTS
        }
