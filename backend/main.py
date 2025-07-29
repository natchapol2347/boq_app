#!/usr/bin/env python3
"""
Main application runner for the refactored BOQ processor.
This is the clean entry point that handles command-line arguments and starts the server.
"""

import os
import sys
import argparse
from pathlib import Path
import logging

def setup_logging():
    """Setup consistent logging format"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )

def reset_database_if_requested(args):
    """Reset database if --reset-db flag is provided"""
    if not args.reset_db:
        return
    
    app_root = Path(__file__).parent.parent.absolute()  # Go up to project root
    # Database in repo root data folder
    data_dir = app_root / 'data'
    os.makedirs(data_dir, exist_ok=True)
    db_path = str(data_dir / 'master_data.db')
    if db_path.exists():
        print(f"🔄 Resetting database at {db_path}")
        try:
            db_path.unlink()
            print("✅ Database reset successfully")
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            sys.exit(1)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='BOQ Processor - Refactored Version')
    parser.add_argument('--reset-db', action='store_true', help='Reset the database before running')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='localhost', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--add-sample-data', action='store_true', help='Add sample data to database')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Reset database if requested
    reset_database_if_requested(args)
    
    # Import and run the processor
    try:
        print("🚀 Starting BOQ Processor (Refactored Version)")
        print("=" * 60)
        print("📋 REFACTORING PHASE:")
        print("- Clean, organized code structure")
        print("- Same logic as original (no behavior changes)")
        print("- Easier debugging and maintenance")
        print("- Ready for step-by-step improvements")
        print("=" * 60)
        
        # Import the refactored processor
        from app import App
        
        # Create and configure processor
        processor = App()
        
        # Add sample data if requested
        if args.add_sample_data:
            print("📊 Adding sample data to all processors...")
            processor._add_sample_data()
            print("✅ Sample data added successfully")
        
        # Start the server
        print(f"🌐 Starting server on http://{args.host}:{args.port}")
        print("📝 Available API endpoints:")
        print("   POST /api/process-boq")
        print("   POST /api/generate-final-boq")
        print("   POST /api/apply-markup")
        print("   POST /api/pure-markup")
        print("   POST /api/cleanup-session")
        print("   GET  /api/config/inquiry")
        print("   POST /api/config/update")
        print("   GET  /api/download/<filename>")
        print("=" * 60)
        
        # Use 0.0.0.0 for Docker compatibility, localhost for local dev
        host = "0.0.0.0" if os.getenv('FLASK_ENV') == 'production' else args.host
        processor.run(host=host, port=args.port, debug=args.debug)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Make sure you have all required files:")
        required_files = [
            'app.py',
            'base_sheet_processor.py',
            'interior_sheet_processor.py',
            'electrical_sheet_processor.py',
            'ac_sheet_processor.py',
            'fp_sheet_processor.py',
        ]
        
        for file in required_files:
            if os.path.exists(file):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} - MISSING")
        
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error running processor: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()