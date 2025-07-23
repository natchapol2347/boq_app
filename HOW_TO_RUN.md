# 🚀 BOQ Processor - How to Run

## For End Users (Non-Technical)

### 📱 **Option 1: Use the Packaged Executable (Recommended)**

1. **Get the packaged app** from your developer
2. **Double-click to run:**
   - **Windows**: `BOQ_Processor.exe`
   - **Mac**: `BOQ_Processor.app`
   - **Linux**: `BOQ_Processor`

3. **The app will:**
   - Show a GUI launcher window
   - Automatically start both backend and frontend servers
   - Open your web browser to the BOQ interface
   - All files saved in the same folder as the app

4. **To use:**
   - Upload your Excel BOQ file
   - Process and download results
   - All output files go to the `output/` folder next to the app

**That's it! No installation, no setup, no technical knowledge needed.**

---

## For Developers

### 🛠️ **Option 2: Run from Source Code**

#### Prerequisites
```bash
# Install Python 3.9+ and dependencies
pip install -r requirements.txt
```

#### Quick Start (GUI Launcher)
```bash
# Run the cross-platform launcher
python boq_launcher.py
```
This gives you the same GUI as the packaged version.

#### Manual Start (Separate Terminals)
```bash
# Terminal 1: Start backend
python main.py

# Terminal 2: Start frontend  
streamlit run streamlit_frontend.py
```

#### Test Individual Components
```bash
# Test backend only
python main.py
# Visit: http://localhost:5000

# Test frontend only (backend must be running)
streamlit run streamlit_frontend.py
# Visit: http://localhost:8501
```

### 📦 **Building Executables**

#### Build for Current Platform
```bash
# Generate icons (if not already done)
python generate_icons.py

# Build executable with PyInstaller
python build_pyinstaller.py
```

Output:
- **Mac**: `dist/BOQ_Processor.app` and `dist/BOQ_Processor`
- **Windows**: `dist/BOQ_Processor.exe` (when run on Windows)

#### Alternative Build Tools
```bash
# cx_Freeze (backup option)
python setup_cx_freeze.py build

# Universal build script (tries both)
python build_all.py
```

---

## 🔧 Configuration

### Environment Variables (Optional)
The launcher automatically sets these, but you can override:

```bash
export BOQ_APP_ROOT="/path/to/app"
export BOQ_DATA_DIR="/path/to/data"
export BOQ_CONFIG_DIR="/path/to/config"
export BOQ_OUTPUT_DIR="/path/to/output"
export BOQ_UPLOADS_DIR="/path/to/uploads"
```

### File Structure
```
BOQ_Processor/
├── BOQ_Processor.app/          # Mac app (packaged)
├── BOQ_Processor               # Executable (packaged)
├── master_data/               # Your Excel master files
├── samples/                   # Example files
├── uploads/                   # File upload area
├── output/                    # Generated BOQ files
├── data/                      # SQLite database
├── config/                    # App settings
├── temp/                      # Temporary files
└── logs/                      # Log files
```

---

## 🐛 Troubleshooting

### Common Issues

**🔴 "Backend not working"**
- Check if port 5000 is already in use
- Try restarting the launcher
- Check `logs/` folder for error messages

**🔴 "Frontend not loading"**
- Wait a few seconds after starting
- Check if port 8501 is available
- Manually visit http://localhost:8501

**🔴 "Permission denied" (Mac)**
```bash
# Make executable
chmod +x BOQ_Processor

# Or run from source
python boq_launcher.py
```

**🔴 "App won't open" (Mac)**
- Right-click → Open (bypass Gatekeeper)
- Or: System Preferences → Security → Allow anyway

**🔴 "Missing files" (Development)**
```bash
# Make sure all directories exist
mkdir -p uploads output data config temp logs

# Install missing dependencies
pip install -r requirements.txt
```

### Getting Help

1. **Check logs**: Look in `logs/` folder or console output
2. **Try source code**: If executable fails, try `python boq_launcher.py`
3. **Check ports**: Make sure 5000 and 8501 are free
4. **File permissions**: Ensure app can write to its directory

---

## 📋 Quick Reference

### For Users
| Task | Command |
|------|---------|
| Run app | Double-click `BOQ_Processor.app` |
| Find outputs | Check `output/` folder next to app |
| Reset app | Delete `data/` and `config/` folders |

### For Developers  
| Task | Command |
|------|---------|
| Run GUI launcher | `python boq_launcher.py` |
| Run backend only | `python main.py` |
| Run frontend only | `streamlit run streamlit_frontend.py` |
| Build executable | `python build_pyinstaller.py` |
| Generate icons | `python generate_icons.py` |
| Test build | `python test_build.py build` |

### URLs
- **Backend API**: http://localhost:5000
- **Frontend UI**: http://localhost:8501
- **Health Check**: http://localhost:5000/health

---

## 🎯 Success Criteria

✅ **App launches without errors**  
✅ **Both servers start automatically**  
✅ **Browser opens to BOQ interface**  
✅ **Can upload and process Excel files**  
✅ **Output files appear in output/ folder**  
✅ **All paths contained in app directory**  

If all these work, your BOQ Processor is ready to use! 🎉