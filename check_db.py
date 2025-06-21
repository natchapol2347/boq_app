"""
Simple script to check the database contents
"""
import sqlite3
import os
from pathlib import Path

def check_database():
    """Check the database contents"""
    db_path = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor' / 'master_data.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check table structure
            cursor.execute("PRAGMA table_info(master_items)")
            columns = cursor.fetchall()
            print("Database structure:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Check item count
            cursor.execute("SELECT COUNT(*) FROM master_items")
            count = cursor.fetchone()[0]
            print(f"\nTotal items in database: {count}")
            
            # Check items with costs
            cursor.execute("SELECT COUNT(*) FROM master_items WHERE material_cost > 0 OR labor_cost > 0")
            count_with_costs = cursor.fetchone()[0]
            print(f"Items with non-zero costs: {count_with_costs}")
            
            # Show some sample items with costs
            if count_with_costs > 0:
                cursor.execute(
                    "SELECT name, material_cost, labor_cost, total_cost FROM master_items WHERE material_cost > 0 OR labor_cost > 0 LIMIT 10"
                )
                items = cursor.fetchall()
                print("\nSample items with costs:")
                for item in items:
                    print(f"  - {item[0]}: Material={item[1]}, Labor={item[2]}, Total={item[3]}")
            
            # Show some sample items without costs
            cursor.execute(
                "SELECT name, material_cost, labor_cost, total_cost FROM master_items WHERE material_cost = 0 AND labor_cost = 0 LIMIT 10"
            )
            items = cursor.fetchall()
            print("\nSample items without costs:")
            for item in items:
                print(f"  - {item[0]}: Material={item[1]}, Labor={item[2]}, Total={item[3]}")
            
            return True
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database()