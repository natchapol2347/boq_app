#!/usr/bin/env python3
"""
Main application runner for the BOQ processor with CRUD master data management.
No longer syncs from Excel - all data management is done through the API.
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
    
    app_root = Path(__file__).parent.parent.absolute()
    data_dir = app_root / 'data'
    db_path = data_dir / 'master_data.db'
    
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
    parser = argparse.ArgumentParser(description='BOQ Processor with CRUD Master Data Management')
    parser.add_argument('--reset-db', action='store_true', help='Reset the database before running')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='localhost', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Reset database if requested
    reset_database_if_requested(args)
    
    # Import and run the processor
    try:
        print("🚀 Starting BOQ Processor with CRUD Master Data Management")
        print("=" * 70)
        print("📋 NEW FEATURES:")
        print("- ❌ No more Excel master.xlsx sync")
        print("- ✅ Database-driven master data management") 
        print("- 🔧 Full CRUD API for master data")
        print("- 🌐 Streamlit admin interface for employees")
        print("- 📊 Real-time data updates")
        print("- 📤 Excel import/export capabilities")
        print("=" * 70)
        
        # Import the updated processor
        from app import App
        
        # Create and configure processor
        processor = App()
        
        # Start the server
        print(f"🌐 Starting server on http://{args.host}:{args.port}")
        print("📝 Available API endpoints:")
        print("   🔧 BOQ Processing:")
        print("      POST /api/process-boq")
        print("      POST /api/generate-final-boq")
        print("      POST /api/apply-markup")
        print("      POST /api/cleanup-session")
        print("")
        print("   📊 Master Data CRUD:")
        print("      GET    /api/master-data/list/<processor_type>")
        print("      GET    /api/master-data/get/<processor_type>/<item_id>")
        print("      POST   /api/master-data/create/<processor_type>")
        print("      PUT    /api/master-data/update/<processor_type>/<item_id>")
        print("      DELETE /api/master-data/delete/<processor_type>/<item_id>")
        print("      POST   /api/master-data/bulk-import/<processor_type>")
        print("      GET    /api/master-data/export/<processor_type>")
        print("")
        print("   ⚙️ Configuration:")
        print("      GET  /api/config/inquiry")
        print("      POST /api/config/update")
        print("      GET  /api/download/<filename>")
        print("")
        print("   🎯 Admin Interface:")
        print("      Run: streamlit run admin_master_data.py")
        print("=" * 70)
        
        # Use 0.0.0.0 for Docker compatibility, localhost for local dev
        host = "0.0.0.0" if os.getenv('FLASK_ENV') == 'production' else args.host
        processor.run(host=host, port=args.port, debug=args.debug)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Make sure you have all required files:")
        required_files = [
            'app.py',
            'src/processors/base_sheet_processor.py',
            'src/processors/interior_sheet_processor.py',
            'src/processors/electrical_sheet_processor.py',
            'src/processors/ac_sheet_processor.py',
            'src/processors/fp_sheet_processor.py',
            'src/config/config_manager.py',
            'models/config_models.py'
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