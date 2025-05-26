"""
Demo Database Manager for Advanced SQL Assistant
Manages the sample database for portfolio demonstrations and Streamlit deployment
"""

import sqlite3
import os
from pathlib import Path
import streamlit as st
from sample_database import create_sample_database

class DemoDatabaseManager:
    """Manages the demo database for portfolio showcase"""
    
    def __init__(self):
        self.db_path = "sample_business_data.db"
        self.demo_queries = self._get_demo_queries()
    
    def ensure_demo_database_exists(self):
        """Ensure the demo database exists, create if not"""
        
        if not os.path.exists(self.db_path):
            st.info("🔄 Creating sample database for demonstration...")
            create_sample_database()
            st.success("✅ Sample database created successfully!")
        
        return self.db_path
    
    def get_demo_connection_config(self):
        """Get connection configuration for the demo database"""
        
        # Ensure database exists
        db_path = self.ensure_demo_database_exists()
        
        return {
            'db_type': 'sqlite',
            'db_path': db_path,
            'host': None,
            'port': None,
            'database': db_path,
            'user': None,
            'password': None
        }
    
    def create_demo_engine(self):
        """Create SQLAlchemy engine for the demo database"""
        
        from sqlalchemy import create_engine
        
        db_path = self.ensure_demo_database_exists()
        engine = create_engine(f'sqlite:///{db_path}')
        
        return engine
    
    def get_demo_schema(self):
        """Get schema information for the demo database"""
        
        schema = {
            'tables': [
                'customers',
                'products', 
                'sales_transactions',
                'financial_metrics',
                'employee_performance'
            ],
            'table_info': {
                'customers': {
                    'columns': ['customer_id', 'customer_name', 'customer_code', 'email', 'city', 'country', 'customer_segment', 'lifetime_value'],
                    'description': 'Customer information including demographics and business metrics'
                },
                'products': {
                    'columns': ['product_id', 'product_code', 'product_name', 'category', 'subcategory', 'brand', 'unit_price', 'cost_price'],
                    'description': 'Product catalog with pricing and categorization'
                },
                'sales_transactions': {
                    'columns': ['transaction_id', 'customer_id', 'product_id', 'transaction_date', 'quantity', 'unit_price', 'discount_percent', 'total_amount', 'region'],
                    'description': 'Sales transaction records with customer and product details'
                },
                'financial_metrics': {
                    'columns': ['metric_id', 'customer_id', 'product_id', 'fiscal_year', 'fiscal_quarter', 'revenue', 'cost_of_goods', 'gross_profit', 'marketing_spend'],
                    'description': 'Financial performance metrics by customer and product'
                },
                'employee_performance': {
                    'columns': ['employee_id', 'employee_name', 'department', 'position', 'salary', 'performance_score', 'sales_target', 'sales_achieved'],
                    'description': 'Employee performance and compensation data'
                }
            }
        }
        
        return schema
    
    def _get_demo_queries(self):
        """Get sample queries that showcase AI capabilities"""
        
        return {
            "📊 Revenue Analysis": {
                "question": "Show me total revenue by customer segment for the last year with growth rates",
                "complexity": "Medium",
                "showcases": ["Aggregation", "Date filtering", "Business metrics"]
            },
            "🏆 Top Performers": {
                "question": "Who are the top 10 customers by lifetime value and their recent purchase patterns?",
                "complexity": "Medium", 
                "showcases": ["Ranking", "Customer analysis", "Purchase behavior"]
            },
            "📈 Sales Trends": {
                "question": "Analyze monthly sales trends by product category with seasonal patterns",
                "complexity": "High",
                "showcases": ["Time series", "Trend analysis", "Seasonal patterns"]
            },
            "💰 Profitability Analysis": {
                "question": "Calculate profit margins by product and identify the most profitable combinations",
                "complexity": "High",
                "showcases": ["Financial calculations", "Profitability analysis", "Product optimization"]
            },
            "🎯 Sales Performance": {
                "question": "Compare sales rep performance against targets by region with variance analysis",
                "complexity": "High",
                "showcases": ["Performance metrics", "Variance analysis", "Regional comparison"]
            },
            "🔍 Customer Segmentation": {
                "question": "Segment customers by purchase frequency and average order value for targeted marketing",
                "complexity": "High",
                "showcases": ["Customer segmentation", "RFM analysis", "Marketing insights"]
            },
            "📋 Executive Dashboard": {
                "question": "Create an executive summary with key KPIs: revenue, growth, top customers, and performance metrics",
                "complexity": "Very High",
                "showcases": ["Executive reporting", "KPI dashboard", "Multi-metric analysis"]
            },
            "🔄 Cohort Analysis": {
                "question": "Perform customer cohort analysis showing retention rates and revenue per cohort over time",
                "complexity": "Very High", 
                "showcases": ["Cohort analysis", "Retention metrics", "Advanced analytics"]
            }
        }
    
    def get_sample_questions(self):
        """Get sample questions for demo purposes"""
        
        return list(self.demo_queries.keys())
    
    def get_question_details(self, question_key):
        """Get details about a specific demo question"""
        
        return self.demo_queries.get(question_key, {})
    
    def render_demo_info(self):
        """Render demo database information in Streamlit"""
        
        st.markdown("### 🎯 **Portfolio Demo Database**")
        st.info("""
        **Perfect for showcasing AI capabilities to recruiters!**
        
        This sample database contains realistic business data:
        • **1,000+ customers** across multiple segments and regions
        • **50+ products** in various categories with pricing data  
        • **10,000+ sales transactions** spanning 3 years
        • **Financial metrics** with revenue, costs, and profitability
        • **Employee performance** data with targets and achievements
        """)
        
        # Database statistics
        try:
            conn = sqlite3.connect(self.db_path)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                customers_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                st.metric("👥 Customers", f"{customers_count:,}")
            
            with col2:
                products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                st.metric("📦 Products", f"{products_count:,}")
            
            with col3:
                transactions_count = conn.execute("SELECT COUNT(*) FROM sales_transactions").fetchone()[0]
                st.metric("💳 Transactions", f"{transactions_count:,}")
            
            with col4:
                total_revenue = conn.execute("SELECT SUM(total_amount) FROM sales_transactions").fetchone()[0]
                st.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
            
            conn.close()
            
        except Exception as e:
            st.warning(f"Could not load database statistics: {str(e)}")
    
    def render_sample_questions(self):
        """Render sample questions for demo"""
        
        st.markdown("### 🚀 **Try These Impressive Demo Questions**")
        st.markdown("*Click any question to automatically fill the query builder:*")
        
        for question_key, details in self.demo_queries.items():
            with st.expander(f"{question_key} - {details['complexity']} Complexity"):
                st.markdown(f"**Question:** {details['question']}")
                st.markdown(f"**Showcases:** {', '.join(details['showcases'])}")
                
                if st.button(f"Use This Question", key=f"use_{question_key}"):
                    st.session_state.demo_question = details['question']
                    st.success("✅ Question loaded! Go to the Query Builder tab to see it in action.")
    
    def get_demo_database_info(self):
        """Get comprehensive database information for AI context"""
        
        schema = self.get_demo_schema()
        
        info = f"""
        DEMO DATABASE SCHEMA INFORMATION:
        
        This is a comprehensive business database with the following tables:
        
        1. CUSTOMERS TABLE:
           - Contains customer information, demographics, and business metrics
           - Key columns: customer_id, customer_name, customer_segment, country, lifetime_value
           - 1000+ records across Enterprise, SMB, Startup, Government, Education segments
        
        2. PRODUCTS TABLE:
           - Product catalog with categories and pricing
           - Key columns: product_id, product_name, category, subcategory, unit_price, cost_price
           - 50+ products across Software, Hardware, Services, Consulting, Training categories
        
        3. SALES_TRANSACTIONS TABLE:
           - Detailed sales transaction records
           - Key columns: transaction_id, customer_id, product_id, transaction_date, quantity, total_amount, region
           - 10,000+ transactions over 3 years with regional and temporal data
        
        4. FINANCIAL_METRICS TABLE:
           - Financial performance data by customer and product
           - Key columns: customer_id, product_id, fiscal_year, revenue, cost_of_goods, gross_profit
           - Quarterly financial data for comprehensive analysis
        
        5. EMPLOYEE_PERFORMANCE TABLE:
           - Employee performance and compensation data
           - Key columns: employee_name, department, salary, performance_score, sales_target, sales_achieved
           - 100+ employees across Sales, Marketing, Engineering, Support, Finance departments
        
        BUSINESS CONTEXT:
        - Multi-year data (2022-2024) for trend analysis
        - Global customer base across USA, Canada, UK, Germany, France, Australia, Japan
        - Comprehensive financial metrics for profitability analysis
        - Employee performance data for HR analytics
        - Rich dimensional data for advanced business intelligence queries
        """
        
        return info

# Global instance for easy access
demo_db_manager = DemoDatabaseManager()
