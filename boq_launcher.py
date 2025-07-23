#!/usr/bin/env python3
"""
Cross-platform BOQ Processor Launcher
Supports Windows, Mac, and Linux with repo-contained paths
"""

import sys
import os
import time
import subprocess
import threading
import webbrowser
import socket
import platform
from pathlib import Path

# Platform-specific imports
try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    print("⚠️  tkinter not available - running in console mode")
    GUI_AVAILABLE = False

class CrossPlatformBOQLauncher:
    """Cross-platform BOQ launcher with repo-contained paths"""
    
    def __init__(self):
        self.platform = platform.system()
        self.backend_process = None
        self.frontend_process = None
        self.backend_port = 5000
        self.frontend_port = 8501
        self.is_running = False
        
        # Setup repo-contained paths
        self.setup_repo_paths()
        
        if GUI_AVAILABLE:
            self.setup_gui()
        else:
            self.run_console_mode()
    
    def setup_repo_paths(self):
        """Setup all paths within the repo root directory"""
        # Get app root directory (works for both development and packaged)
        if getattr(sys, 'frozen', False):
            # Running as packaged executable
            self.app_root = Path(sys.executable).parent
        else:
            # Running as Python script
            self.app_root = Path(__file__).parent.absolute()
        
        # Create all necessary directories within repo
        self.data_dir = self.app_root / "data"
        self.config_dir = self.app_root / "config"
        self.uploads_dir = self.app_root / "uploads"
        self.output_dir = self.app_root / "output"
        self.temp_dir = self.app_root / "temp"
        self.logs_dir = self.app_root / "logs"
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.config_dir, self.uploads_dir, 
                         self.output_dir, self.temp_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)
        
        print(f"🖥️  Platform: {self.platform}")
        print(f"📁 App root: {self.app_root}")
        print(f"📊 Data: {self.data_dir}")
        print(f"⚙️  Config: {self.config_dir}")
        print(f"📥 Output: {self.output_dir}")
    
    def setup_gui(self):
        """Setup GUI with platform-specific adaptations"""
        self.root = tk.Tk()
        
        # Platform-specific window setup
        title = "ระบบประมาณราคา BOQ - BOQ Processor"
        self.root.title(title)
        
        if self.platform == "Darwin":  # macOS
            self.root.configure(bg='#f0f0f0')
        elif self.platform == "Linux":
            self.root.configure(bg='#ffffff')
        else:  # Windows
            self.root.configure(bg='#f0f0f0')
        
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Try to set icon (platform-specific)
        self.set_platform_icon()
        
        # Create GUI elements
        self.create_gui_elements()
        
        # Platform-specific window behavior
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def set_platform_icon(self):
        """Set platform-specific icon"""
        try:
            if self.platform == "Windows":
                icon_path = self.app_root / "icon.ico"
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
            elif self.platform == "Darwin":  # macOS
                icon_path = self.app_root / "icon.icns"
                if icon_path.exists():
                    # macOS iconphoto with icns
                    pass
            else:  # Linux
                icon_path = self.app_root / "icon.png"
                if icon_path.exists():
                    img = tk.PhotoImage(file=str(icon_path))
                    self.root.iconphoto(False, img)
        except Exception as e:
            print(f"⚠️  Could not set icon: {e}")
    
    def create_gui_elements(self):
        """Create cross-platform GUI elements"""
        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title with platform-appropriate font
        title_font = self.get_platform_font("title")
        title = tk.Label(
            main_frame, 
            text="📊 ระบบประมาณราคา BOQ",
            font=title_font
        )
        title.pack(pady=(0, 10))
        
        subtitle_font = self.get_platform_font("subtitle")
        subtitle = tk.Label(
            main_frame,
            text="BOQ Processor - ระบบคำนวณต้นทุนอัตโนมัติ",
            font=subtitle_font
        )
        subtitle.pack(pady=(0, 20))
        
        # Path info frame
        path_frame = tk.Frame(main_frame)
        path_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(path_frame, text="📁 ตำแหน่งไฟล์:", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(path_frame, text=f"App Root: {self.app_root}", font=("Arial", 8), fg="gray").pack(anchor="w")
        tk.Label(path_frame, text=f"Database: {self.data_dir}/master_data.db", font=("Arial", 8), fg="gray").pack(anchor="w")
        tk.Label(path_frame, text=f"Output: {self.output_dir}", font=("Arial", 8), fg="gray").pack(anchor="w")
        
        # Status frame
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))
        
        status_font = self.get_platform_font("normal")
        tk.Label(status_frame, text="สถานะระบบ:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.backend_status = tk.Label(status_frame, text="🔴 Backend: ไม่ทำงาน", font=status_font)
        self.backend_status.pack(anchor="w")
        
        self.frontend_status = tk.Label(status_frame, text="🔴 Frontend: ไม่ทำงาน", font=status_font)
        self.frontend_status.pack(anchor="w")
        
        self.browser_status = tk.Label(status_frame, text="🔴 Browser: ยังไม่เปิด", font=status_font)
        self.browser_status.pack(anchor="w")
        
        # Buttons with platform-appropriate styling
        self.create_platform_buttons(main_frame)
        
        # Log area
        tk.Label(main_frame, text="บันทึกการทำงาน (System Log):", font=("Arial", 10, "bold")).pack(anchor="w")
        
        log_font = self.get_platform_font("monospace")
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, font=log_font)
        self.log_text.pack(fill="both", expand=True, pady=(5, 10))
        
        # Instructions
        instructions = tk.Label(
            main_frame,
            text="คำแนะนำ: กดปุ่ม 'เริ่มระบบ' เพื่อเริ่มใช้งาน โปรแกรมจะเปิดเว็บไซต์โดยอัตโนมัติ\nไฟล์ทั้งหมดจะถูกเก็บไว้ในโฟลเดอร์เดียวกับโปรแกรม (ไม่ใช้ AppData)",
            font=("Arial", 8),
            fg="gray",
            wraplength=650,
            justify="left"
        )
        instructions.pack(pady=(5, 0))
    
    def get_platform_font(self, font_type):
        """Get platform-appropriate fonts"""
        if self.platform == "Darwin":  # macOS
            fonts = {
                "title": ("Helvetica", 16, "bold"),
                "subtitle": ("Helvetica", 10),
                "normal": ("Helvetica", 9),
                "monospace": ("Monaco", 8)
            }
        elif self.platform == "Linux":
            fonts = {
                "title": ("DejaVu Sans", 16, "bold"),
                "subtitle": ("DejaVu Sans", 10),
                "normal": ("DejaVu Sans", 9),
                "monospace": ("DejaVu Sans Mono", 8)
            }
        else:  # Windows
            fonts = {
                "title": ("Arial", 16, "bold"),
                "subtitle": ("Arial", 10),
                "normal": ("Arial", 9),
                "monospace": ("Consolas", 8)
            }
        
        return fonts.get(font_type, ("Arial", 10))
    
    def create_platform_buttons(self, parent):
        """Create platform-specific button styling"""
        button_frame = tk.Frame(parent)
        button_frame.pack(fill="x", pady=10)
        
        # Platform-specific button colors
        if self.platform == "Darwin":  # macOS
            start_color = "#007AFF"  # macOS blue
            stop_color = "#FF3B30"   # macOS red
        elif self.platform == "Linux":
            start_color = "#4CAF50"  # Material green
            stop_color = "#F44336"   # Material red
        else:  # Windows
            start_color = "#0078D4"  # Windows blue
            stop_color = "#D13438"   # Windows red
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 เริ่มระบบ (Start System)",
            command=self.start_system,
            bg=start_color,
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        )
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_button = tk.Button(
            button_frame,
            text="⏹️ หยุดระบบ (Stop System)",
            command=self.stop_system,
            bg=stop_color,
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            state="disabled"
        )
        self.stop_button.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Browser button
        self.browser_button = tk.Button(
            parent,
            text="🌐 เปิดเว็บไซต์ (Open Website)",
            command=self.open_browser,
            font=("Arial", 10),
            state="disabled"
        )
        self.browser_button.pack(fill="x", pady=(5, 10))
        
        # Open output folder button
        self.folder_button = tk.Button(
            parent,
            text="📁 เปิดโฟลเดอร์ผลลัพธ์ (Open Output Folder)",
            command=self.open_output_folder,
            font=("Arial", 9)
        )
        self.folder_button.pack(fill="x", pady=(5, 0))
    
    def start_system(self):
        """Start both backend and frontend servers"""
        if self.is_running:
            self.log("⚠️ ระบบกำลังทำงานอยู่แล้ว")
            return
        
        self.log("🚀 เริ่มระบบ BOQ Processor...")
        
        # Start backend
        self.start_backend()
        time.sleep(2)
        
        # Start frontend
        self.start_frontend()
        time.sleep(3)
        
        # Update UI
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.browser_button.config(state="normal")
        
        # Auto-open browser
        self.open_browser()
    
    def start_backend(self):
        """Start Flask backend server"""
        try:
            python_cmd = sys.executable
            
            # Debug: Log execution environment
            self.log(f"🔍 Debug: sys.frozen = {getattr(sys, 'frozen', False)}")
            self.log(f"🔍 Debug: python_cmd = {python_cmd}")
            
            # Handle PyInstaller packaging - files are in _MEIPASS temp directory
            if getattr(sys, 'frozen', False):
                # Running as packaged executable
                self.log(f"🔍 Debug: sys._MEIPASS = {getattr(sys, '_MEIPASS', 'NOT_FOUND')}")
                backend_script = Path(sys._MEIPASS) / "main.py"
                # List contents of _MEIPASS for debugging
                if hasattr(sys, '_MEIPASS'):
                    meipass_files = list(Path(sys._MEIPASS).glob("*.py"))
                    self.log(f"🔍 Debug: Python files in _MEIPASS: {[f.name for f in meipass_files]}")
            else:
                # Running as Python script
                backend_script = self.app_root / "main.py"
            
            self.log(f"🔍 Debug: Looking for backend script at: {backend_script}")
            
            if not backend_script.exists():
                self.log(f"❌ ไม่พบไฟล์ main.py ที่ {backend_script}")
                # List what IS available in the directory
                parent_dir = backend_script.parent
                if parent_dir.exists():
                    available_files = list(parent_dir.glob("*"))
                    self.log(f"🔍 Debug: Available files in {parent_dir}: {[f.name for f in available_files[:10]]}")
                return
            
            # Set environment variables for repo paths
            env = os.environ.copy()
            env['BOQ_APP_ROOT'] = str(self.app_root)
            env['BOQ_DATA_DIR'] = str(self.data_dir)
            env['BOQ_CONFIG_DIR'] = str(self.config_dir)
            env['BOQ_OUTPUT_DIR'] = str(self.output_dir)
            env['BOQ_UPLOADS_DIR'] = str(self.uploads_dir)
            
            self.backend_process = subprocess.Popen(
                [python_cmd, str(backend_script)],
                cwd=str(self.app_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if self.platform == "Windows" else 0
            )
            
            self.log("✅ Backend เริ่มทำงานแล้ว (Port 5000)")
            self.backend_status.config(text="🟢 Backend: ทำงาน", fg="green")
            
        except Exception as e:
            self.log(f"❌ ไม่สามารถเริ่ม Backend ได้: {e}")
    
    def start_frontend(self):
        """Start Streamlit frontend"""
        try:
            python_cmd = sys.executable
            
            # Handle PyInstaller packaging - files are in _MEIPASS temp directory
            if getattr(sys, 'frozen', False):
                # Running as packaged executable
                frontend_script = Path(sys._MEIPASS) / "streamlit_frontend.py"
            else:
                # Running as Python script
                frontend_script = self.app_root / "streamlit_frontend.py"
            
            if not frontend_script.exists():
                self.log(f"❌ ไม่พบไฟล์ streamlit_frontend.py ที่ {frontend_script}")
                return
            
            # Set environment variables for repo paths
            env = os.environ.copy()
            env['BOQ_APP_ROOT'] = str(self.app_root)
            env['BOQ_DATA_DIR'] = str(self.data_dir)
            env['BOQ_CONFIG_DIR'] = str(self.config_dir)
            env['BOQ_OUTPUT_DIR'] = str(self.output_dir)
            env['BOQ_UPLOADS_DIR'] = str(self.uploads_dir)
            
            self.frontend_process = subprocess.Popen(
                [python_cmd, "-m", "streamlit", "run", str(frontend_script), 
                 "--server.port", str(self.frontend_port), 
                 "--server.headless", "true",
                 "--browser.gatherUsageStats", "false"],
                cwd=str(self.app_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if self.platform == "Windows" else 0
            )
            
            self.log("✅ Frontend เริ่มทำงานแล้ว (Port 8501)")
            self.frontend_status.config(text="🟢 Frontend: ทำงาน", fg="green")
            
        except Exception as e:
            self.log(f"❌ ไม่สามารถเริ่ม Frontend ได้: {e}")
    
    def stop_system(self):
        """Stop both servers"""
        self.log("⏹️ หยุดระบบ...")
        
        # Stop processes
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
            self.backend_status.config(text="🔴 Backend: หยุดทำงาน", fg="red")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process = None
            self.frontend_status.config(text="🔴 Frontend: หยุดทำงาน", fg="red")
        
        # Update UI
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.browser_button.config(state="disabled")
        self.browser_status.config(text="🔴 Browser: ปิดแล้ว", fg="red")
        
        self.log("✅ ระบบหยุดทำงานแล้ว")
    
    def open_browser(self):
        """Platform-specific browser opening"""
        try:
            url = f"http://localhost:{self.frontend_port}"
            self.log(f"🌐 เปิดเว็บไซต์: {url}")
            
            # Platform-specific browser opening
            if self.platform == "Darwin":  # macOS
                subprocess.run(["open", url])
            elif self.platform == "Linux":
                subprocess.run(["xdg-open", url])
            else:  # Windows
                webbrowser.open(url)
            
            self.browser_status.config(text="🟢 Browser: เปิดแล้ว", fg="green")
            
        except Exception as e:
            self.log(f"❌ ไม่สามารถเปิด browser ได้: {e}")
    
    def open_output_folder(self):
        """Open output folder in file manager"""
        try:
            if self.platform == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_dir)])
            elif self.platform == "Linux":
                subprocess.run(["xdg-open", str(self.output_dir)])
            else:  # Windows
                subprocess.run(["explorer", str(self.output_dir)])
            
            self.log(f"📁 เปิดโฟลเดอร์: {self.output_dir}")
            
        except Exception as e:
            self.log(f"❌ ไม่สามารถเปิดโฟลเดอร์ได้: {e}")
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        if GUI_AVAILABLE and hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        else:
            print(log_message.strip())
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_system()
        self.root.destroy()
    
    def run_console_mode(self):
        """Run in console mode if GUI is not available"""
        print("\n" + "="*60)
        print("    BOQ PROCESSOR - CONSOLE MODE")
        print("    ระบบประมาณราคา BOQ (ไม่มี GUI)")
        print("="*60)
        print(f"📁 App Root: {self.app_root}")
        print(f"📊 Database: {self.data_dir}/master_data.db")
        print(f"📥 Output: {self.output_dir}")
        print("="*60)
        
        while True:
            print("\nเลือกคำสั่ง:")
            print("1. เริ่มระบบ (Start System)")
            print("2. หยุดระบบ (Stop System)")
            print("3. เปิดเว็บไซต์ (Open Browser)")
            print("4. ออกจากโปรแกรม (Exit)")
            
            choice = input("\nพิมพ์หมายเลข (1-4): ").strip()
            
            if choice == "1":
                self.start_system()
            elif choice == "2":
                self.stop_system()
            elif choice == "3":
                self.open_browser()
            elif choice == "4":
                if self.is_running:
                    self.stop_system()
                print("👋 ออกจากโปรแกรม")
                break
            else:
                print("❌ กรุณาเลือก 1-4")
    
    def run(self):
        """Run the launcher"""
        if GUI_AVAILABLE:
            self.root.mainloop()
        # Console mode runs automatically if GUI not available

def main():
    """Main entry point"""
    launcher = CrossPlatformBOQLauncher()
    launcher.run()

if __name__ == "__main__":
    main()