"""
Sample Database Creator for Advanced SQL Assistant
Creates a realistic business database with sample data for portfolio demonstration
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

class SampleDatabaseCreator:
    """Creates a comprehensive sample database for demonstration purposes"""
    
    def __init__(self, db_path="sample_business_data.db"):
        self.db_path = db_path
        self.conn = None
        
    def create_database(self):
        """Create the complete sample database with realistic business data"""
        
        print("🚀 Creating sample business database for portfolio demonstration...")
        
        # Create database connection
        self.conn = sqlite3.connect(self.db_path)
        
        # Create all tables
        self._create_tables()
        
        # Insert sample data
        self._insert_sample_data()
        
        # Create indexes for performance
        self._create_indexes()
        
        self.conn.close()
        
        print(f"✅ Sample database created successfully: {self.db_path}")
        print("📊 Database includes:")
        print("   • 1000+ customers across multiple segments")
        print("   • 50+ products in various categories")
        print("   • 10,000+ sales transactions over 3 years")
        print("   • Financial data with discounts and costs")
        print("   • Geographic and demographic data")
        print("   • Perfect for demonstrating AI query capabilities!")
        
    def _create_tables(self):
        """Create all database tables with proper schema"""
        
        # Customers table
        self.conn.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            customer_code TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            customer_segment TEXT,
            acquisition_date DATE,
            lifetime_value DECIMAL(10,2),
            credit_limit DECIMAL(10,2)
        )
        """)
        
        # Products table
        self.conn.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_code TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            subcategory TEXT,
            brand TEXT,
            unit_price DECIMAL(10,2),
            cost_price DECIMAL(10,2),
            launch_date DATE,
            status TEXT
        )
        """)
        
        # Sales transactions table
        self.conn.execute("""
        CREATE TABLE sales_transactions (
            transaction_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            transaction_date DATE,
            quantity INTEGER,
            unit_price DECIMAL(10,2),
            discount_percent DECIMAL(5,2),
            total_amount DECIMAL(10,2),
            sales_rep TEXT,
            region TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """)
        
        # Financial data table
        self.conn.execute("""
        CREATE TABLE financial_metrics (
            metric_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            fiscal_year INTEGER,
            fiscal_quarter INTEGER,
            revenue DECIMAL(12,2),
            cost_of_goods DECIMAL(12,2),
            gross_profit DECIMAL(12,2),
            marketing_spend DECIMAL(10,2),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """)
        
        # Employee performance table
        self.conn.execute("""
        CREATE TABLE employee_performance (
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            department TEXT,
            position TEXT,
            hire_date DATE,
            salary DECIMAL(10,2),
            performance_score DECIMAL(3,2),
            sales_target DECIMAL(12,2),
            sales_achieved DECIMAL(12,2),
            manager_id INTEGER
        )
        """)
        
        print("✅ Database tables created successfully")
    
    def _insert_sample_data(self):
        """Insert realistic sample data into all tables"""
        
        # Generate customers
        customers_data = self._generate_customers(1000)
        customers_df = pd.DataFrame(customers_data)
        customers_df.to_sql('customers', self.conn, if_exists='append', index=False)
        
        # Generate products
        products_data = self._generate_products(50)
        products_df = pd.DataFrame(products_data)
        products_df.to_sql('products', self.conn, if_exists='append', index=False)
        
        # Generate sales transactions
        sales_data = self._generate_sales_transactions(10000)
        sales_df = pd.DataFrame(sales_data)
        sales_df.to_sql('sales_transactions', self.conn, if_exists='append', index=False)
        
        # Generate financial metrics
        financial_data = self._generate_financial_metrics(5000)
        financial_df = pd.DataFrame(financial_data)
        financial_df.to_sql('financial_metrics', self.conn, if_exists='append', index=False)
        
        # Generate employee data
        employee_data = self._generate_employees(100)
        employee_df = pd.DataFrame(employee_data)
        employee_df.to_sql('employee_performance', self.conn, if_exists='append', index=False)
        
        print("✅ Sample data inserted successfully")
    
    def _generate_customers(self, count):
        """Generate realistic customer data"""
        
        segments = ['Enterprise', 'SMB', 'Startup', 'Government', 'Education']
        countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Australia', 'Japan']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Toronto', 'London', 'Berlin']
        
        customers = []
        for i in range(1, count + 1):
            customer = {
                'customer_id': i,
                'customer_name': f"Company {i:04d}",
                'customer_code': f"CUST{i:04d}",
                'email': f"contact{i}@company{i}.com",
                'phone': f"+1-555-{random.randint(1000, 9999)}",
                'address': f"{random.randint(100, 9999)} Business St",
                'city': random.choice(cities),
                'state': random.choice(['CA', 'NY', 'TX', 'FL', 'IL']),
                'country': random.choice(countries),
                'customer_segment': random.choice(segments),
                'acquisition_date': (datetime.now() - timedelta(days=random.randint(30, 1095))).date(),
                'lifetime_value': round(random.uniform(5000, 500000), 2),
                'credit_limit': round(random.uniform(10000, 1000000), 2)
            }
            customers.append(customer)
        
        return customers
    
    def _generate_products(self, count):
        """Generate realistic product data"""
        
        categories = ['Software', 'Hardware', 'Services', 'Consulting', 'Training']
        subcategories = {
            'Software': ['CRM', 'ERP', 'Analytics', 'Security'],
            'Hardware': ['Servers', 'Laptops', 'Networking', 'Storage'],
            'Services': ['Support', 'Implementation', 'Maintenance', 'Cloud'],
            'Consulting': ['Strategy', 'Technical', 'Business', 'Digital'],
            'Training': ['Online', 'Onsite', 'Certification', 'Workshop']
        }
        brands = ['TechCorp', 'DataSoft', 'CloudSys', 'SecureNet', 'InnovateLab']
        
        products = []
        for i in range(1, count + 1):
            category = random.choice(categories)
            product = {
                'product_id': i,
                'product_code': f"PROD{i:03d}",
                'product_name': f"{category} Solution {i}",
                'category': category,
                'subcategory': random.choice(subcategories[category]),
                'brand': random.choice(brands),
                'unit_price': round(random.uniform(100, 50000), 2),
                'cost_price': round(random.uniform(50, 25000), 2),
                'launch_date': (datetime.now() - timedelta(days=random.randint(30, 1095))).date(),
                'status': random.choice(['Active', 'Active', 'Active', 'Discontinued'])
            }
            products.append(product)
        
        return products
    
    def _generate_sales_transactions(self, count):
        """Generate realistic sales transaction data"""
        
        regions = ['North', 'South', 'East', 'West', 'Central']
        sales_reps = ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Wilson', 'David Brown']
        
        transactions = []
        for i in range(1, count + 1):
            customer_id = random.randint(1, 1000)
            product_id = random.randint(1, 50)
            quantity = random.randint(1, 100)
            unit_price = round(random.uniform(100, 10000), 2)
            discount = round(random.uniform(0, 25), 2)
            total = round(quantity * unit_price * (1 - discount/100), 2)
            
            transaction = {
                'transaction_id': i,
                'customer_id': customer_id,
                'product_id': product_id,
                'transaction_date': (datetime.now() - timedelta(days=random.randint(1, 1095))).date(),
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_percent': discount,
                'total_amount': total,
                'sales_rep': random.choice(sales_reps),
                'region': random.choice(regions)
            }
            transactions.append(transaction)
        
        return transactions
    
    def _generate_financial_metrics(self, count):
        """Generate financial metrics data"""
        
        metrics = []
        for i in range(1, count + 1):
            revenue = round(random.uniform(10000, 1000000), 2)
            cogs = round(revenue * random.uniform(0.3, 0.7), 2)
            
            metric = {
                'metric_id': i,
                'customer_id': random.randint(1, 1000),
                'product_id': random.randint(1, 50),
                'fiscal_year': random.choice([2022, 2023, 2024]),
                'fiscal_quarter': random.randint(1, 4),
                'revenue': revenue,
                'cost_of_goods': cogs,
                'gross_profit': revenue - cogs,
                'marketing_spend': round(revenue * random.uniform(0.05, 0.15), 2)
            }
            metrics.append(metric)
        
        return metrics
    
    def _generate_employees(self, count):
        """Generate employee performance data"""
        
        departments = ['Sales', 'Marketing', 'Engineering', 'Support', 'Finance']
        positions = ['Manager', 'Senior', 'Junior', 'Lead', 'Director']
        names = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Eva Brown']
        
        employees = []
        for i in range(1, count + 1):
            salary = round(random.uniform(50000, 200000), 2)
            target = round(random.uniform(100000, 2000000), 2)
            achieved = round(target * random.uniform(0.7, 1.3), 2)
            
            employee = {
                'employee_id': i,
                'employee_name': f"{random.choice(names)} {i}",
                'department': random.choice(departments),
                'position': random.choice(positions),
                'hire_date': (datetime.now() - timedelta(days=random.randint(30, 2000))).date(),
                'salary': salary,
                'performance_score': round(random.uniform(2.5, 5.0), 2),
                'sales_target': target,
                'sales_achieved': achieved,
                'manager_id': random.randint(1, 20) if i > 20 else None
            }
            employees.append(employee)
        
        return employees
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        
        indexes = [
            "CREATE INDEX idx_customers_segment ON customers(customer_segment)",
            "CREATE INDEX idx_customers_country ON customers(country)",
            "CREATE INDEX idx_products_category ON products(category)",
            "CREATE INDEX idx_sales_date ON sales_transactions(transaction_date)",
            "CREATE INDEX idx_sales_customer ON sales_transactions(customer_id)",
            "CREATE INDEX idx_sales_product ON sales_transactions(product_id)",
            "CREATE INDEX idx_financial_year ON financial_metrics(fiscal_year)",
            "CREATE INDEX idx_employee_dept ON employee_performance(department)"
        ]
        
        for index in indexes:
            self.conn.execute(index)
        
        print("✅ Database indexes created for optimal performance")

def create_sample_database():
    """Main function to create the sample database"""
    
    creator = SampleDatabaseCreator()
    creator.create_database()
    
    return creator.db_path

if __name__ == "__main__":
    create_sample_database()
