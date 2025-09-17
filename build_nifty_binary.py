#!/usr/bin/env python3
"""
Build NIFTY Trading Bot Binary

Creates PyInstaller binaries specifically for NIFTY trading with Indian market support.
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


def create_nifty_spec_file():
    """Create PyInstaller spec file for NIFTY trading bot."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['nifty_trading_bot.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('nifty500_symbols.py', '.'),
        ('config_nifty50.yaml', '.'),
        ('config_nifty500.yaml', '.'),
    ],
    hiddenimports=[
        'yfinance',
        'pandas',
        'numpy',
        'ta',
        'matplotlib',
        'yaml',
        'apscheduler',
        'sqlite3',
        'pkg_resources.py2_warn',
        'nifty500_symbols'
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
    name='nifty-trading-bot',
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
    
    with open('nifty-trading-bot.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created NIFTY PyInstaller spec file: nifty-trading-bot.spec")


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies for NIFTY trading bot...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    
    return True


def build_nifty_binary():
    """Build the NIFTY trading bot binary using PyInstaller."""
    print("Building NIFTY trading bot binary...")
    
    try:
        # Create spec file
        create_nifty_spec_file()
        
        # Build with PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'nifty-trading-bot.spec'
        ]
        
        subprocess.check_call(cmd)
        
        # Get platform name for renaming
        platform_name = get_platform_name()
        
        # Find the built executable
        dist_dir = Path('dist')
        if platform.system() == "Windows":
            exe_name = 'nifty-trading-bot.exe'
            new_name = f'nifty-trading-bot-{platform_name}.exe'
        else:
            exe_name = 'nifty-trading-bot'
            new_name = f'nifty-trading-bot-{platform_name}'
        
        exe_path = dist_dir / exe_name
        new_path = dist_dir / new_name
        
        if exe_path.exists():
            exe_path.rename(new_path)
            print(f"NIFTY trading bot binary created successfully: {new_path}")
            print(f"Binary size: {new_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Test the binary
            print("\nTesting the binary...")
            test_cmd = [str(new_path), '--help']
            try:
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ Binary test successful!")
                else:
                    print(f"⚠️  Binary test returned code {result.returncode}")
                    print(f"Error: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("⚠️  Binary test timed out")
            except Exception as e:
                print(f"⚠️  Binary test failed: {e}")
            
            return True
        else:
            print("Binary not found in dist directory")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False


def create_usage_instructions():
    """Create usage instructions for the NIFTY trading bot."""
    platform_name = get_platform_name()
    
    if platform.system() == "Windows":
        binary_name = f'nifty-trading-bot-{platform_name}.exe'
    else:
        binary_name = f'nifty-trading-bot-{platform_name}'
    
    instructions = f"""
# NIFTY Trading Bot - Usage Instructions

## Binary Location
Your NIFTY trading bot binary is located at: `dist/{binary_name}`

## Basic Usage

### Test the bot (recommended first step)
```bash
.\\dist\\{binary_name} --test --verbose
```

### Analyze NIFTY 50 stocks
```bash
.\\dist\\{binary_name} --size nifty50
```

### Analyze NIFTY 500 stocks (takes longer)
```bash
.\\dist\\{binary_name} --size nifty500
```

### Validate symbols before analysis
```bash
.\\dist\\{binary_name} --validate --size nifty50
```

### Run only during Indian market hours
```bash
.\\dist\\{binary_name} --market-hours-only --size nifty50
```

## Configuration Files
- `config_nifty50.yaml` - Configuration for NIFTY 50 analysis
- `config_nifty500.yaml` - Configuration for NIFTY 500 analysis

## Output Files
- `nifty50_signals.csv` - Trading signals for NIFTY 50 stocks
- `nifty500_signals.csv` - Trading signals for NIFTY 500 stocks
- `nifty_trading_bot.log` - Application logs

## Indian Market Hours
The bot recognizes Indian market hours: 9:15 AM to 3:30 PM IST, Monday-Friday

## Features
✅ Comprehensive historical data (up to 5+ years per stock)
✅ Technical analysis (RSI, Bollinger Bands, EMA)
✅ Swing trading signals optimized for Indian markets
✅ Support for NIFTY 50, 100, and 500 stocks
✅ Indian Rupee (Rs.) price formatting
✅ Market hours awareness
✅ Configurable parameters

## Example Output
```
🇮🇳 NIFTY Stock Trading Bot
==================================================
📅 Date: 2025-09-17 18:04:32
📊 Index: NIFTY50
📈 Analyzing 50 symbols...

🟢 BUY Signals (2):
   📈 HINDUNILVR.NS: Rs.2569.70 (RSI: 29.7)
   📈 EXAMPLE.NS: Rs.1234.56 (RSI: 25.3)

📈 Market Summary:
   Average RSI: 62.6
   Market sentiment: Overbought
```

Enjoy trading with the NIFTY bot! 🇮🇳📈
"""
    
    with open('NIFTY_USAGE.md', 'w') as f:
        f.write(instructions)
    
    print(f"Created usage instructions: NIFTY_USAGE.md")


def main():
    """Main build function."""
    print("🇮🇳 NIFTY Trading Bot - Binary Builder")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # Check if we're in the right directory
    if not Path('nifty_trading_bot.py').exists():
        print("Error: nifty_trading_bot.py not found. Run this script from the project root.")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Build binary
    if not build_nifty_binary():
        return 1
    
    # Create usage instructions
    create_usage_instructions()
    
    print("\n🎉 NIFTY Trading Bot binary build completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Test the binary: .\\dist\\nifty-trading-bot-*.exe --test")
    print("2. Run NIFTY 50 analysis: .\\dist\\nifty-trading-bot-*.exe --size nifty50")
    print("3. Check NIFTY_USAGE.md for detailed instructions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())