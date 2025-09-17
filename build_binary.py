#!/usr/bin/env python3
"""
Build script for creating PyInstaller binaries
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def get_platform_name():
    """Get platform-specific name for binary."""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == "windows":
        return f"windows-{arch}"
    elif system == "darwin":
        return f"macos-{arch}"
    elif system == "linux":
        return f"linux-{arch}"
    else:
        return f"{system}-{arch}"


def create_spec_file():
    """Create PyInstaller spec file."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'yfinance',
        'pandas',
        'numpy',
        'ta',
        'matplotlib',
        'yaml',
        'apscheduler',
        'sqlite3',
        'pkg_resources.py2_warn'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='trading-bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('trading-bot.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file: trading-bot.spec")


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    
    return True


def build_binary():
    """Build the binary using PyInstaller."""
    print("Building binary...")
    
    try:
        # Create spec file
        create_spec_file()
        
        # Build with PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'trading-bot.spec'
        ]
        
        subprocess.check_call(cmd)
        
        # Get platform name for renaming
        platform_name = get_platform_name()
        
        # Find the built executable
        dist_dir = Path('dist')
        if platform.system() == "Windows":
            exe_name = 'trading-bot.exe'
            new_name = f'trading-bot-{platform_name}.exe'
        else:
            exe_name = 'trading-bot'
            new_name = f'trading-bot-{platform_name}'
        
        exe_path = dist_dir / exe_name
        new_path = dist_dir / new_name
        
        if exe_path.exists():
            exe_path.rename(new_path)
            print(f"Binary created successfully: {new_path}")
            print(f"Binary size: {new_path.stat().st_size / (1024*1024):.1f} MB")
            return True
        else:
            print("Binary not found in dist directory")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False


def main():
    """Main build function."""
    print("Stock Trading Bot - Binary Builder")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # Check if we're in the right directory
    if not Path('src/main.py').exists():
        print("Error: src/main.py not found. Run this script from the project root.")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Build binary
    if not build_binary():
        return 1
    
    print("\nBuild completed successfully!")
    print("You can find the binary in the 'dist' directory.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())