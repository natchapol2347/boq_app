#!/usr/bin/env python3
# Run script for the hard-coded BOQ processor

import os
import argparse
from pathlib import Path
import sqlite3
import sys

def main():
    parser = argparse.ArgumentParser(description='Run the hard-coded BOQ processor')
    parser.add_argument('--reset-db', action='store_true', help='Reset the database before running')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='localhost', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--add-sample-costs', action='store_true', help='Add sample costs to the database')
    
    args = parser.parse_args()
    
    # Reset database if requested
    if args.reset_db:
        db_path = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor' / 'master_data.db'
        if os.path.exists(db_path):
            print(f"Resetting database at {db_path}")
            try:
                os.remove(db_path)
                print("Database reset successfully")
            except Exception as e:
                print(f"Error resetting database: {e}")
                sys.exit(1)
    
    # Add sample costs if requested
    if args.add_sample_costs:
        db_path = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor' / 'master_data.db'
        if os.path.exists(db_path):
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get all tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    for table in tables:
                        if table.startswith('sqlite_'):
                            continue
                            
                        # Update with sample costs
                        cursor.execute(f"UPDATE {table} SET material_cost = 500, labor_cost = 300, total_cost = 800")
                        conn.commit()
                        
                        # Check if update worked
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE material_cost > 0")
                        count = cursor.fetchone()[0]
                        print(f"Added sample costs to {count} items in table {table}")
                
                print("Sample costs added successfully")
            except Exception as e:
                print(f"Error adding sample costs: {e}")
                sys.exit(1)
    
    # Import and run the processor
    try:
        from hard_coded_boq import HardCodedBOQProcessor
        
        print(f"Starting BOQ processor on {args.host}:{args.port} (debug={args.debug})")
        processor = HardCodedBOQProcessor()
        processor.run(host=args.host, port=args.port, debug=args.debug)
        
    except Exception as e:
        print(f"Error running processor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()