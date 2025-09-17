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
    """Create PyInstaller spec file for NIFTY trading bot with proper CLI support."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['enhanced_nifty_trading_bot.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('nifty500_symbols.py', '.'),
        ('config_nifty50.yaml', '.'),
        ('config_nifty500.yaml', '.'),
        ('config_enhanced_nifty.yaml', '.'),
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
        'nifty500_symbols',
        'argparse',
        'sys',
        'os'
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
    name='enhanced-nifty-trading-bot',
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
    
    with open('enhanced-nifty-trading-bot.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created Enhanced NIFTY PyInstaller spec file: enhanced-nifty-trading-bot.spec")


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
    """Build the Enhanced NIFTY trading bot binary using PyInstaller."""
    print("Building Enhanced NIFTY trading bot binary...")
    
    try:
        # Create spec file
        create_nifty_spec_file()
        
        # Build with PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'enhanced-nifty-trading-bot.spec'
        ]
        
        subprocess.check_call(cmd)
        
        # Get platform name for renaming
        platform_name = get_platform_name()
        
        # Find the built executable
        dist_dir = Path('dist')
        if platform.system() == "Windows":
            exe_name = 'enhanced-nifty-trading-bot.exe'
            new_name = f'enhanced-nifty-trading-bot-{platform_name}.exe'
        else:
            exe_name = 'enhanced-nifty-trading-bot'
            new_name = f'enhanced-nifty-trading-bot-{platform_name}'
        
        exe_path = dist_dir / exe_name
        new_path = dist_dir / new_name
        
        if exe_path.exists():
            exe_path.rename(new_path)
            print(f"Enhanced NIFTY trading bot binary created successfully: {new_path}")
            print(f"Binary size: {new_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Test the binary with multiple command line options
            print("\nTesting the binary...")
            test_commands = [
                [str(new_path), '--help'],
                [str(new_path), '--test', '--verbose'],
                [str(new_path), '--size', 'nifty50', '--min-score', '5']
            ]
            
            for i, test_cmd in enumerate(test_commands, 1):
                try:
                    print(f"Test {i}: {' '.join(test_cmd[1:])}")
                    result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        print(f"✅ Test {i} successful!")
                    else:
                        print(f"⚠️  Test {i} returned code {result.returncode}")
                        if result.stderr:
                            print(f"Error: {result.stderr[:200]}...")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Test {i} timed out")
                except Exception as e:
                    print(f"⚠️  Test {i} failed: {e}")
            
            return True
        else:
            print("Binary not found in dist directory")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False


def create_usage_instructions():
    """Create usage instructions for the Enhanced NIFTY trading bot."""
    platform_name = get_platform_name()
    
    if platform.system() == "Windows":
        binary_name = f'enhanced-nifty-trading-bot-{platform_name}.exe'
    else:
        binary_name = f'enhanced-nifty-trading-bot-{platform_name}'
    
    instructions = f"""
# Enhanced NIFTY Trading Bot - Usage Instructions

## Binary Location
Your Enhanced NIFTY trading bot binary is located at: `dist/{binary_name}`

## Key Enhancements
🚀 **Maximum Historical Data**: Fetches stock data from inception using "max" period
📊 **Enhanced Data Reporting**: Shows actual data ranges and quality for each stock
⚙️ **Fixed CLI Arguments**: All command line options now work properly in binary
🔧 **Configurable Data Fetching**: Control data periods and thresholds via config files

## Basic Usage

### Test the bot (recommended first step)
```bash
.\\dist\\{binary_name} --test --verbose
```

### Analyze NIFTY 50 stocks with maximum historical data
```bash
.\\dist\\{binary_name} --size nifty50
```

### Analyze NIFTY 500 stocks (comprehensive analysis)
```bash
.\\dist\\{binary_name} --size nifty500
```

### Validate symbols before analysis
```bash
.\\dist\\{binary_name} --validate --size nifty50
```

### Run with custom minimum signal score
```bash
.\\dist\\{binary_name} --size nifty50 --min-score 6
```

### Use custom configuration file
```bash
.\\dist\\{binary_name} --config config_enhanced_nifty.yaml --test
```

### Run only during Indian market hours
```bash
.\\dist\\{binary_name} --market-hours-only --size nifty50
```

## Configuration Files
- `config_enhanced_nifty.yaml` - Enhanced configuration with maximum data settings
- `config_nifty50.yaml` - Configuration for NIFTY 50 analysis
- `config_nifty500.yaml` - Configuration for NIFTY 500 analysis

### Data Fetching Configuration
```yaml
data_fetching:
  max_data_period: "max"  # Fetch from inception
  fallback_periods: ["max", "10y", "5y", "2y", "1y", "6mo"]
  min_data_threshold: 200  # Minimum days required
  timeout_per_symbol: 60   # Timeout in seconds
  show_data_summary: true  # Show data range info
```

## Output Files
- `enhanced_nifty50_signals.csv` - Enhanced trading signals for NIFTY 50
- `enhanced_nifty500_signals.csv` - Enhanced trading signals for NIFTY 500
- `enhanced_nifty_trading_bot.log` - Detailed application logs

## Enhanced Output Features
✅ **Data Range Information**: Shows actual start/end dates and years of data
✅ **Data Quality Indicators**: EXCELLENT (5+ years), GOOD (2-5 years), LIMITED (1-2 years), POOR (<1 year)
✅ **Period Usage Statistics**: Shows which data periods were successfully used
✅ **Enhanced CSV Output**: Includes data quality and range columns

## Indian Market Hours
The bot recognizes Indian market hours: 9:15 AM to 3:30 PM IST, Monday-Friday

## Enhanced Features
✅ Maximum historical data from stock inception
✅ Multiple RSI periods (14, 21, 50) for comprehensive analysis
✅ Multiple EMA periods (9, 21, 50, 200) for trend analysis
✅ Bollinger Bands and MACD for momentum analysis
✅ Enhanced data quality reporting and validation
✅ Configurable data fetching with fallback periods
✅ Improved error handling and timeout management
✅ Support for NIFTY 50, 100, and 500 stocks
✅ Indian Rupee (Rs.) price formatting
✅ Market hours awareness
✅ Comprehensive logging and progress indicators

## Example Enhanced Output
```
🇮🇳 Enhanced NIFTY Stock Trading Bot
==================================================
📅 Date: 2025-09-17 18:04:32
📊 Index: NIFTY50
🎯 Min Signal Score: 4
📈 Indicators: Multiple RSI (14,21,50) + Multiple EMA (9,21,50,200) + BB + MACD

🟢🟢 STRONG BUY Signals (2):
   💎 HINDUNILVR.NS: Rs.2569.70 (Score: 7) RSI: 29.7 | Trend: UP/UP | Data: 15.2y [max]
   💎 RELIANCE.NS: Rs.2845.30 (Score: 6) RSI: 32.1 | Trend: UP/UP | Data: 12.8y [max]

📈 Enhanced Market Summary:
   Average RSI (14-day): 52.3
   Average RSI (50-day): 48.7
   Bullish trends: 28/50 (56.0%)
   Bearish trends: 15/50 (30.0%)
   Total data analyzed: 487.3 years
   Average data per symbol: 9.7 years
   Market sentiment: Neutral

📊 Data Quality Distribution:
   Excellent (5+ years): 42 symbols (84.0%)
   Good (2-5 years): 6 symbols (12.0%)
   Limited (1-2 years): 2 symbols (4.0%)
   Poor (<1 year): 0 symbols (0.0%)

⏱️  Period Usage Statistics:
   max: 45 symbols (90.0%)
   10y: 3 symbols (6.0%)
   5y: 2 symbols (4.0%)
```

## Troubleshooting

### Command Line Arguments Not Working
- Ensure you're using the enhanced binary (enhanced-nifty-trading-bot-*)
- Try running with --help to verify CLI functionality
- Check that you're using the correct binary for your platform

### Data Fetching Issues
- Check internet connection for Yahoo Finance API access
- Verify symbol format (should end with .NS for Indian stocks)
- Review configuration file for correct data fetching settings
- Check logs for detailed error information

### Performance Optimization
- Use --test flag for quick testing with limited symbols
- Adjust min_data_threshold in config for faster processing
- Use specific NIFTY size (nifty50 vs nifty500) based on needs

Enjoy enhanced trading analysis with maximum historical data! 🇮🇳📈📊
"""
    
    with open('ENHANCED_NIFTY_USAGE.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"Created enhanced usage instructions: ENHANCED_NIFTY_USAGE.md")


def main():
    """Main build function."""
    print("🇮🇳 NIFTY Trading Bot - Binary Builder")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # Check if we're in the right directory
    if not Path('enhanced_nifty_trading_bot.py').exists():
        print("Error: enhanced_nifty_trading_bot.py not found. Run this script from the project root.")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Build binary
    if not build_nifty_binary():
        return 1
    
    # Create usage instructions
    create_usage_instructions()
    
    print("\n🎉 Enhanced NIFTY Trading Bot binary build completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Test the binary: .\\dist\\enhanced-nifty-trading-bot-*.exe --test")
    print("2. Run NIFTY 50 analysis: .\\dist\\enhanced-nifty-trading-bot-*.exe --size nifty50")
    print("3. Check ENHANCED_NIFTY_USAGE.md for detailed instructions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())