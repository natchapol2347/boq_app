#!/usr/bin/env python3
"""
PyInstaller build script for BOQ Processor
Alternative to cx_Free
ze with different packaging approach
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import shutil

def create_pyinstaller_spec():
    """Create PyInstaller spec file for cross-platform builds"""
    
    current_dir = Path(__file__).parent
    platform_name = platform.system().lower()
    
    # Determine executable name and icon
    if platform_name == "windows":
        exe_name = "BOQ_Processor.exe"
        icon_file = "icon.ico"
        console = False
    elif platform_name == "darwin":
        exe_name = "BOQ_Processor"
        icon_file = "icon.icns"
        console = False
    else:  # Linux
        exe_name = "BOQ_Processor"
        icon_file = "icon.png"
        console = False
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BOQ Processor
Auto-generated for {platform_name}
"""

import os
import sys
from pathlib import Path

# Get current directory
current_dir = Path(SPECPATH)

# Data files to include (repo root structure)
datas = [
    (str(current_dir / 'models'), 'models'),
    (str(current_dir / 'master_data'), 'master_data'),
    (str(current_dir / 'samples'), 'samples'),
    (str(current_dir / 'streamlit_frontend.py'), '.'),
    (str(current_dir / 'main.py'), '.'),
    (str(current_dir / 'refactored_boq_processor.py'), '.'),
    (str(current_dir / 'base_sheet_processor.py'), '.'),
    (str(current_dir / 'interior_sheet_processor.py'), '.'),
    (str(current_dir / 'electrical_sheet_processor.py'), '.'),
    (str(current_dir / 'ac_sheet_processor.py'), '.'),
    (str(current_dir / 'fp_sheet_processor.py'), '.'),
    (str(current_dir / 'config_manager.py'), '.'),
]

# Add optional files if they exist
optional_files = [
    ('requirements.txt', '.'),
    ('CLAUDE.md', '.'),
    ('{icon_file}', '.'),
]

for src, dst in optional_files:
    src_path = current_dir / src
    if src_path.exists():
        datas.append((str(src_path), dst))

# Create empty directories
empty_dirs = ['uploads', 'output', 'temp', 'logs', 'data', 'config']
for dir_name in empty_dirs:
    dir_path = current_dir / dir_name
    dir_path.mkdir(exist_ok=True)
    # Create a placeholder file to ensure directory is included
    placeholder = dir_path / '.keep'
    placeholder.touch()
    datas.append((str(dir_path), dir_name))

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'pandas',
    'openpyxl',
    'flask',
    'flask_cors',
    'streamlit',
    'pydantic',
    'fuzzywuzzy',
    'PIL',
    'sqlite3',
    'tkinter',
    'models.config_models',
    'streamlit.components.v1',
    'altair',
    'numpy',
    'pyarrow',
    'click',
    'tornado',
    'watchdog',
    'validators',
    'protobuf',
    'gitpython',
    'pillow',
    'pympler',
    'rich',
    'toml',
    'tzlocal',
    'blinker',
    'werkzeug.security',
    'werkzeug.utils',
]

# Analysis
a = Analysis(
    ['boq_launcher.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'jupyter', 'IPython', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicates
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(console)},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(current_dir / '{icon_file}') if (current_dir / '{icon_file}').exists() else None,
)

# macOS app bundle (optional)
{"app = BUNDLE(exe, name='BOQ_Processor.app', icon=str(current_dir / 'icon.icns'), bundle_identifier='com.woodman.boqprocessor')" if platform_name == "darwin" else "# No app bundle for non-macOS"}
'''
    
    return spec_content

def build_with_pyinstaller():
    """Build executable using PyInstaller"""
    
    print(f"🔨 Building BOQ Processor with PyInstaller on {platform.system()}...")
    
    # Create spec file
    spec_content = create_pyinstaller_spec()
    spec_file = Path("boq_processor.spec")
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ Created spec file: {spec_file}")
    
    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")
    
    if dist_dir.exists():
        print("🧹 Cleaning previous dist directory...")
        shutil.rmtree(dist_dir)
    
    if build_dir.exists():
        print("🧹 Cleaning previous build directory...")
        shutil.rmtree(build_dir)
    
    # Build with PyInstaller
    print("🚀 Starting PyInstaller build...")
    
    try:
        # Run PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ PyInstaller build completed successfully!")
        print(f"📁 Executable created in: {dist_dir.absolute()}")
        
        # List contents of dist directory
        if dist_dir.exists():
            print("\\n📋 Build contents:")
            for item in dist_dir.rglob("*"):
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    print(f"   {item.relative_to(dist_dir)} ({size_mb:.1f} MB)")
        
        # Platform-specific instructions
        platform_name = platform.system()
        if platform_name == "Windows":
            exe_path = dist_dir / "BOQ_Processor.exe"
            print(f"\\n🪟 Windows executable: {exe_path}")
            print("   Double-click to run!")
        elif platform_name == "Darwin":
            exe_path = dist_dir / "BOQ_Processor"
            app_path = dist_dir / "BOQ_Processor.app"
            if app_path.exists():
                print(f"\\n🍎 macOS app bundle: {app_path}")
                print("   Drag to Applications folder and double-click!")
            else:
                print(f"\\n🍎 macOS executable: {exe_path}")
                print("   Run from terminal or double-click!")
        else:
            exe_path = dist_dir / "BOQ_Processor"
            print(f"\\n🐧 Linux executable: {exe_path}")
            print("   Make executable with: chmod +x BOQ_Processor")
            print("   Then run: ./BOQ_Processor")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed!")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during build: {e}")
        return False

def main():
    """Main build function"""
    print("🎯 BOQ Processor - PyInstaller Build Script")
    print("="*50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Check if required files exist
    required_files = ['boq_launcher.py', 'main.py', 'streamlit_frontend.py']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    # Start build
    success = build_with_pyinstaller()
    
    if success:
        print("\\n" + "="*50)
        print("🎉 BUILD SUCCESSFUL!")
        print("✅ Your BOQ Processor executable is ready!")
        print("✅ All paths are contained within the app directory")
        print("✅ No external dependencies required")
        print("✅ Portable - works on any compatible system")
        print("="*50)
    else:
        print("\\n" + "="*50)
        print("❌ BUILD FAILED!")
        print("Check the error messages above for details.")
        print("="*50)
    
    return success

if __name__ == "__main__":
    main()