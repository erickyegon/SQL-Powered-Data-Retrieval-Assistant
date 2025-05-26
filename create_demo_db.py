#!/usr/bin/env python3
"""
Quick script to create the demo database for testing
Run this to pre-create the demo database before deployment
"""

from sample_database import create_sample_database
import os

def main():
    """Create the demo database"""
    
    print("🚀 Creating demo database for Advanced SQL Assistant...")
    
    # Create the database
    db_path = create_sample_database()
    
    # Verify it was created
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path) / (1024 * 1024)  # Size in MB
        print(f"✅ Demo database created successfully!")
        print(f"📁 Location: {db_path}")
        print(f"📊 Size: {file_size:.2f} MB")
        print()
        print("🎯 Ready for portfolio demonstration!")
        print("   • 1000+ customers across multiple segments")
        print("   • 50+ products in various categories") 
        print("   • 10,000+ sales transactions over 3 years")
        print("   • Financial metrics and employee data")
        print()
        print("🚀 You can now run: streamlit run app.py")
        print("   Then enable Demo Mode in the sidebar!")
    else:
        print("❌ Failed to create demo database")

if __name__ == "__main__":
    main()
