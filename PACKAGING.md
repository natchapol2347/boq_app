# BOQ Processor - Packaging Guide

## 🎯 Overview

This guide explains how to package the BOQ Processor into standalone executables for Windows and Mac. All files and data are contained within the application directory (no AppData or system dependencies).

## 🏗️ Repository Structure (After Packaging Updates)

```
boq_app/
├── boq_launcher.py          # Cross-platform GUI launcher
├── generate_icons.py        # Icon generator for all platforms
├── setup_cx_freeze.py       # cx_Freeze packaging script
├── build_pyinstaller.py     # PyInstaller packaging script
├── build_all.py            # Universal build script
├── icon.ico/.icns/.png     # Platform-specific icons
├── 
├── main.py                 # Flask backend (updated paths)
├── streamlit_frontend.py   # Streamlit UI (updated paths)
├── refactored_boq_processor.py  # Main processor (updated paths)
├── config_manager.py       # Config management (updated paths)
├── *_sheet_processor.py    # Sheet processors
├── models/                 # Pydantic models
├── master_data/           # Excel master files
├── samples/               # Sample files
├── 
├── data/                  # SQLite database (created at runtime)
├── config/                # Settings (created at runtime)
├── uploads/               # File uploads (created at runtime)
├── output/                # Generated files (created at runtime)
├── temp/                  # Temporary files (created at runtime)
└── logs/                  # Log files (created at runtime)
```

## 🔧 Key Changes Made

### 1. Path Structure Update
- **Before**: Used `Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor'`
- **After**: Uses repo root with `Path(__file__).parent.absolute()`
- **Result**: Everything contained in one portable folder

### 2. Files Updated
- `refactored_boq_processor.py` - Updated to use repo root paths
- `config_manager.py` - Updated to use repo root paths  
- `streamlit_frontend.py` - Updated to use repo root paths

### 3. Environment Variable Support
The launcher sets these environment variables for packaged apps:
- `BOQ_APP_ROOT` - Application root directory
- `BOQ_DATA_DIR` - Database directory
- `BOQ_CONFIG_DIR` - Configuration directory
- `BOQ_OUTPUT_DIR` - Output directory
- `BOQ_UPLOADS_DIR` - Upload directory

## 🚀 Quick Start - Build Everything

```bash
# 1. Generate icons (optional - will auto-generate if missing)
python generate_icons.py

# 2. Build with both cx_Freeze and PyInstaller
python build_all.py
```

This creates:
- `dist_cx_freeze/BOQ_Processor.exe` (cx_Freeze build)
- `dist/BOQ_Processor.exe` (PyInstaller build)

## 🛠️ Manual Build Options

### Option 1: cx_Freeze (Recommended)

```bash
# Install cx_Freeze
pip install cx_Freeze

# Build
python setup_cx_freeze.py build

# Output: dist_cx_freeze/BOQ_Processor.exe
```

**Advantages:**
- Smaller file size
- Better for simple GUI apps
- More reliable for Tkinter

### Option 2: PyInstaller (Alternative)

```bash
# Install PyInstaller
pip install PyInstaller

# Build
python build_pyinstaller.py

# Output: dist/BOQ_Processor.exe
```

**Advantages:**
- Better for complex dependencies
- More mature tool
- Better Streamlit support

## 🎨 Icon Generation

Icons are automatically generated for all platforms:

```bash
python generate_icons.py
```

Creates:
- `icon.ico` (Windows)
- `icon.icns` (macOS)
- `icon.png` (Linux)

## 🖥️ Cross-Platform Support

### Windows
- **Executable**: `BOQ_Processor.exe`
- **GUI**: Native tkinter with Windows styling
- **Icon**: `.ico` format
- **Installation**: Just run the .exe

### macOS
- **Executable**: `BOQ_Processor` (or `BOQ_Processor.app`)
- **GUI**: Native tkinter with macOS styling
- **Icon**: `.icns` format
- **Installation**: Drag to Applications

### Linux
- **Executable**: `BOQ_Processor`
- **GUI**: Native tkinter with Linux styling
- **Icon**: `.png` format
- **Installation**: Make executable and run

## 📁 Portable Structure

After packaging, users get a single folder containing everything:

```
BOQ_Processor/
├── BOQ_Processor.exe       # Main executable
├── master_data/           # Your Excel files
├── models/                # Python models
├── uploads/               # Upload area (empty initially)
├── output/                # Results area (empty initially)
├── data/                  # Database (created on first run)
├── config/                # Settings (created on first run)
└── lib/                   # Python dependencies
```

**Benefits:**
✅ No installation required  
✅ No system dependencies  
✅ No registry changes  
✅ No AppData pollution  
✅ Easy backup (copy folder)  
✅ Easy uninstall (delete folder)  
✅ Works on any compatible system  

## 🔍 Testing

### Test the Launcher
```bash
python boq_launcher.py
```

### Test Individual Components
```bash
# Test backend
python main.py

# Test frontend (in another terminal)
streamlit run streamlit_frontend.py
```

## 🐛 Troubleshooting

### Common Issues

**1. Missing Dependencies**
```bash
# Install all required packages
pip install -r requirements.txt
pip install cx_Freeze PyInstaller Pillow
```

**2. Icon Generation Fails**
```bash
# Install Pillow
pip install Pillow
```

**3. Path Issues**
- Check that all Python files use the updated path structure
- Verify environment variables are set correctly by launcher

**4. Build Fails**
```bash
# Clean previous builds
rm -rf build/ dist/ dist_cx_freeze/
rm -f *.spec

# Try again
python build_all.py
```

### Platform-Specific Issues

**Windows:**
- Use `setup_cx_freeze.py` for better Windows integration
- Ensure antivirus doesn't block the build

**macOS:**
- Use `build_pyinstaller.py` for app bundle creation
- May need to sign the app for distribution

**Linux:**
- Ensure all GUI dependencies are installed
- Use `chmod +x BOQ_Processor` to make executable

## 📦 Distribution

### For End Users
1. Build the executable using your preferred method
2. Copy the entire output folder (e.g., `dist_cx_freeze/`)
3. Zip the folder for distribution
4. Users just extract and double-click the executable

### For Developers
1. Clone the repository
2. Run `python build_all.py`
3. Test both builds on target platform
4. Distribute the most stable build

## 🎉 Success Criteria

After packaging, you should have:
- ✅ Single executable that launches both backend and frontend
- ✅ GUI launcher with status indicators
- ✅ All files contained in app directory
- ✅ No external dependencies
- ✅ Cross-platform compatibility
- ✅ Professional icons for all platforms
- ✅ Easy distribution and installation

The end result is a professional, portable application that non-technical users can easily run on Windows or Mac without any setup!