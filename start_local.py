#!/usr/bin/env python3
"""
Local development startup script
Starts both backend and frontend for development
"""

import subprocess
import sys
import time
import os
from pathlib import Path
import signal
import threading

class LocalDevServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Shutting down servers...")
        self.stop_servers()
        sys.exit(0)
    
    def start_backend(self):
        """Start Flask backend"""
        print("🚀 Starting Flask backend...")
        self.backend_process = subprocess.Popen(
            [sys.executable, "backend/main.py", "--port", "5000"],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Monitor backend output in a thread
        def monitor_backend():
            for line in iter(self.backend_process.stdout.readline, ''):
                if line.strip():
                    print(f"[Backend] {line.strip()}")
                if self.backend_process.poll() is not None:
                    break
        
        threading.Thread(target=monitor_backend, daemon=True).start()
        time.sleep(3)  # Give backend time to start
        
    def start_frontend(self):
        """Start Streamlit frontend"""
        print("🌐 Starting Streamlit frontend...")
        self.frontend_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "frontend/frontend.py",
             "--server.port", "8501",
             "--server.address", "localhost"],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Monitor frontend output in a thread
        def monitor_frontend():
            for line in iter(self.frontend_process.stdout.readline, ''):
                if line.strip():
                    print(f"[Frontend] {line.strip()}")
                if self.frontend_process.poll() is not None:
                    break
        
        threading.Thread(target=monitor_frontend, daemon=True).start()
        
    def stop_servers(self):
        """Stop both servers"""
        if self.backend_process:
            print("⏹️  Stopping backend...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                
        if self.frontend_process:
            print("⏹️  Stopping frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
    
    def run(self):
        """Run both servers"""
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("🎯 BOQ Processor - Local Development Server")
        print("=" * 50)
        
        try:
            # Start backend
            self.start_backend()
            
            # Start frontend
            self.start_frontend()
            
            self.running = True
            print("\n✅ Both servers started successfully!")
            print("🌐 Frontend: http://localhost:8501")
            print("🔧 Backend API: http://localhost:5000")
            print("\n📝 Press Ctrl+C to stop both servers")
            print("=" * 50)
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend process died")
                    break
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend process died") 
                    break
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stop_servers()

if __name__ == "__main__":
    server = LocalDevServer()
    server.run()