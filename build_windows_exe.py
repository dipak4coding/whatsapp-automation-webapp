#!/usr/bin/env python3
"""
Windows Executable Builder for WhatsApp Message Automation
This script should be run on a Windows machine to create the executable

Run this on Windows:
1. Install Python 3.8+ on Windows
2. pip install pyinstaller flask pandas selenium webdriver-manager openpyxl
3. python build_windows_exe.py
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def check_windows():
    """Check if running on Windows"""
    if platform.system() != 'Windows':
        print("⚠️  This script should be run on Windows to create a Windows executable")
        print("   Current platform:", platform.system())
        print("\nFor Windows executable:")
        print("1. Copy this folder to a Windows machine")
        print("2. Install Python 3.8+ on Windows")
        print("3. Run: pip install pyinstaller flask pandas selenium webdriver-manager openpyxl")
        print("4. Run: python build_windows_exe.py")
        return False
    return True

def install_dependencies():
    """Install required packages"""
    packages = [
        'pyinstaller',
        'flask', 
        'pandas',
        'selenium',
        'webdriver-manager', 
        'openpyxl'
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False
    return True

def create_pyinstaller_spec():
    """Create PyInstaller spec file for Windows"""
    spec_content = '''# WhatsApp Message Automation - Windows PyInstaller Spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('templates/*.html', 'templates'),
    ('default_templates/*.txt', 'default_templates'),
    ('default_config.json', '.'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'pandas',
        'selenium',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'openpyxl',
        'jinja2',
        'werkzeug',
        'urllib3',
        'requests',
        'threading',
        'json',
        'logging',
        'datetime',
        'time',
        'os',
        'sys',
        'shutil',
        'sqlite3'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhatsAppAutomation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='icon.ico' if os.path.exists('icon.ico') else None
)
'''
    
    with open('app_windows.spec', 'w') as f:
        f.write(spec_content)
    print("✓ Created PyInstaller spec file for Windows")

def create_version_info():
    """Create version info for Windows executable"""
    version_info = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'WhatsApp Legal Automation'),
            StringStruct('FileDescription', 'WhatsApp Message Automation Tool'),
            StringStruct('FileVersion', '1.0.0.0'),
            StringStruct('InternalName', 'WhatsAppAutomation'),
            StringStruct('LegalCopyright', 'Copyright (c) 2025'),
            StringStruct('OriginalFilename', 'WhatsAppAutomation.exe'),
            StringStruct('ProductName', 'WhatsApp Message Automation'),
            StringStruct('ProductVersion', '1.0.0.0')
          ])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w') as f:
        f.write(version_info)
    print("✓ Created version info file")

def build_executable():
    """Build the Windows executable"""
    print("Building Windows executable...")
    print("This will take 5-10 minutes...")
    
    try:
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'app_windows.spec']
        subprocess.check_call(cmd)
        
        # Check if executable was created
        exe_path = Path("dist/WhatsAppAutomation.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✓ Windows executable created: {size_mb:.1f} MB")
            return True
        else:
            print("✗ Executable not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build executable: {e}")
        return False

def create_deployment_package():
    """Create deployment package for Windows"""
    deploy_dir = Path("WhatsApp-Automation-Windows-Standalone")
    
    # Remove existing deployment directory
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    
    # Create deployment directory
    deploy_dir.mkdir()
    print(f"✓ Created deployment directory: {deploy_dir}")
    
    # Copy executable
    exe_path = Path("dist/WhatsAppAutomation.exe")
    if exe_path.exists():
        shutil.copy2(exe_path, deploy_dir / "WhatsAppAutomation.exe")
        print("✓ Copied executable")
    else:
        print("✗ Executable not found")
        return False
    
    # Copy essential files
    essential_files = {
        'default_config.json': 'Configuration defaults',
        'sample_clients.csv': 'Sample CSV file' if Path('sample_clients.csv').exists() else None
    }
    
    for file_name, description in essential_files.items():
        if description and Path(file_name).exists():
            shutil.copy2(file_name, deploy_dir / file_name)
            print(f"✓ Copied {description}")
    
    # Copy template directories
    template_dirs = ['default_templates']
    for dir_name in template_dirs:
        if Path(dir_name).exists():
            shutil.copytree(dir_name, deploy_dir / dir_name)
            print(f"✓ Copied {dir_name}")
    
    # Create startup batch file
    startup_bat = deploy_dir / "Start_WhatsApp_Automation.bat"
    startup_content = '''@echo off
title WhatsApp Message Automation - Standalone Version
color 0A

echo.
echo ===================================================
echo    WhatsApp Message Automation - Standalone
echo ===================================================
echo.
echo ✓ NO Python installation required!
echo ✓ All dependencies included
echo.
echo Starting application...
echo.
echo The web interface will open at: http://localhost:8080
echo.
echo FIRST TIME USERS:
echo - Make sure Chrome browser is installed
echo - You'll scan WhatsApp QR code on first message send
echo - Check QUICK_START.txt for detailed instructions
echo.
echo To STOP: Close this window or press Ctrl+C
echo.

REM Create necessary directories
if not exist "uploads" mkdir uploads >nul 2>&1
if not exist "logs" mkdir logs >nul 2>&1
if not exist "templates" mkdir templates >nul 2>&1

REM Start the application
echo Starting WhatsApp Automation...
WhatsAppAutomation.exe

echo.
echo Application stopped.
pause
'''
    
    with open(startup_bat, 'w') as f:
        f.write(startup_content)
    print("✓ Created startup batch file")
    
    # Create comprehensive quick start guide
    quick_start = deploy_dir / "QUICK_START.txt"
    quick_start_content = '''
🚀 WhatsApp Message Automation - STANDALONE VERSION
=================================================

✅ NO PYTHON INSTALLATION NEEDED!
✅ NO TECHNICAL SETUP REQUIRED!

SYSTEM REQUIREMENTS:
• Windows 10 or Windows 11
• Google Chrome browser (download from google.com/chrome)
• Internet connection
• Administrator privileges (recommended)

FIRST TIME SETUP (2 minutes):
1. Extract this ZIP file to any folder (e.g., Desktop)
2. Double-click "Start_WhatsApp_Automation.bat"
3. Wait 30-60 seconds for startup (first time is slower)
4. Your web browser will open to: http://localhost:8080

DAILY USAGE:
1. Double-click "Start_WhatsApp_Automation.bat"
2. Upload your CSV file in the web interface
3. Configure message templates (pre-filled by default)
4. Click "Start Messaging"
5. Scan WhatsApp QR code when browser opens (first time only)
6. Monitor progress in the dashboard

CSV FILE FORMAT:
Your CSV must have these exact columns:
• Client (client name)
• Contact (phone with country code like +919876543210)
• NextHearingDate (date as YYYY-MM-DD)
• Category (Active, Inactive, or NoClientsInstruction)
• TypRnRy (case type)
• Parties (case details)

IMPORTANT NOTES:
• Keep Chrome updated and set as default browser
• First message sending requires WhatsApp QR scan
• Application creates: uploads/, logs/, templates/ folders
• Close the black command window to stop the application
• Works offline after initial setup

TROUBLESHOOTING:
• If port 8080 busy: Wait and try again, or restart computer
• If Chrome issues: Update Chrome browser
• If WhatsApp issues: Clear browser cache, log out WhatsApp Web
• If executable won't run: Right-click → "Run as administrator"

CUSTOMIZATION:
• Update phone numbers in Configuration page
• Edit message templates through web interface
• Default templates are professional and ready to use

DEFAULT MESSAGE TEMPLATES:
• Active clients: Hearing reminders
• Inactive clients: Re-engagement messages  
• No instructions: Urgent instruction requests

SUPPORT:
• Check logs/ folder for error details
• Ensure Chrome is installed and updated
• Make sure CSV format matches requirements

VERSION: 1.0 Standalone
BUILD DATE: {build_date}

NO PYTHON • NO SETUP • JUST RUN! 🚀
'''.replace('{build_date}', str(Path().cwd()))
    
    with open(quick_start, 'w') as f:
        f.write(quick_start_content)
    print("✓ Created quick start guide")
    
    # Create sample CSV if it doesn't exist
    if not (deploy_dir / "sample_clients.csv").exists():
        sample_csv = deploy_dir / "sample_clients.csv"
        sample_content = '''Client,Contact,NextHearingDate,Category,TypRnRy,Parties
John Doe,+919876543210,2025-01-15,Active,Civil,John Doe vs. ABC Company Ltd
Jane Smith,+918765432109,2025-01-16,Active,Criminal,State vs. Jane Smith
Bob Johnson,+917654321098,2025-01-17,NoClientsInstruction,Family,Bob Johnson vs. Mary Johnson
Alice Brown,+916543210987,2025-01-18,Active,Commercial,Alice Brown vs. XYZ Corporation
Michael Davis,+915432109876,2025-01-20,Inactive,Property,Michael Davis vs. City Council'''
        
        with open(sample_csv, 'w') as f:
            f.write(sample_content)
        print("✓ Created sample CSV file")
    
    return True

def create_zip_package():
    """Create final ZIP package"""
    try:
        zip_name = "WhatsApp-Automation-Windows-Standalone"
        shutil.make_archive(zip_name, 'zip', zip_name)
        
        zip_path = Path(f"{zip_name}.zip")
        if zip_path.exists():
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"✓ Created deployment ZIP: {zip_path} ({size_mb:.1f} MB)")
            return True
        else:
            print("✗ Failed to create ZIP file")
            return False
            
    except Exception as e:
        print(f"✗ Error creating ZIP: {e}")
        return False

def main():
    """Main build process"""
    print("WhatsApp Message Automation - Windows Standalone Builder")
    print("=" * 60)
    
    # Check platform
    if not check_windows():
        return False
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("✗ app.py not found. Run this script from the webapp directory.")
        return False
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("✗ Failed to install dependencies")
        return False
    
    # Create build files
    print("\n🔧 Creating build configuration...")
    create_version_info()
    create_pyinstaller_spec()
    
    # Build executable
    print("\n🏗️ Building executable...")
    if not build_executable():
        return False
    
    # Create deployment package
    print("\n📁 Creating deployment package...")
    if not create_deployment_package():
        return False
    
    # Create ZIP
    print("\n📦 Creating ZIP package...")
    if not create_zip_package():
        return False
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Windows standalone package created!")
    print("\nFiles created:")
    print("• WhatsApp-Automation-Windows-Standalone/ (folder)")
    print("• WhatsApp-Automation-Windows-Standalone.zip (send this to users)")
    print("\n🚀 DEPLOYMENT INSTRUCTIONS:")
    print("1. Send the ZIP file to Windows users")
    print("2. Users extract and run Start_WhatsApp_Automation.bat")
    print("3. No Python installation required!")
    print("4. Works on any Windows 10/11 machine")
    
    print(f"\n📊 Package size: {Path('WhatsApp-Automation-Windows-Standalone.zip').stat().st_size / (1024*1024):.1f} MB")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\nPress Enter to exit...")
            sys.exit(1)
        else:
            input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
