#!/usr/bin/env python3
"""
Build Enhanced Multi-Strategy Trading Bot Binary

Creates a standalone executable with all new strategies included.
"""

import PyInstaller.__main__
import sys
import os
from pathlib import Path

def build_binary():
    """Build the enhanced multi-strategy trading bot binary."""
    
    # Get the current directory
    current_dir = Path.cwd()
    
    # Define the main script
    main_script = "enhanced_multi_strategy_bot.py"
    
    if not Path(main_script).exists():
        print(f"Error: {main_script} not found!")
        return False
    
    # Define PyInstaller arguments
    args = [
        main_script,
        '--onefile',
        '--name=enhanced-multi-strategy-nifty-bot',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=.',
        '--clean',
        '--noconfirm',
        
        # Add data files
        '--add-data=nifty500_symbols.py:.',
        '--add-data=input:input',
        
        # Add source packages
        '--add-data=src:src',
        
        # Hidden imports for strategies
        '--hidden-import=src.strategies.ema_crossover_strategy',
        '--hidden-import=src.strategies.supertrend_strategy', 
        '--hidden-import=src.strategies.multi_strategy_scorer',
        '--hidden-import=src.notifications.email_service',
        '--hidden-import=src.analysis.ema_calculator',
        '--hidden-import=src.analysis.supertrend_calculator',
        '--hidden-import=src.models.data_models',
        '--hidden-import=src.models.exceptions',
        '--hidden-import=src.interfaces.strategy',
        '--hidden-import=src.interfaces.indicator',
        
        # Standard hidden imports
        '--hidden-import=yfinance',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=yaml',
        '--hidden-import=logging',
        '--hidden-import=datetime',
        '--hidden-import=pathlib',
        '--hidden-import=argparse',
        '--hidden-import=smtplib',
        '--hidden-import=email.mime.text',
        '--hidden-import=email.mime.multipart',
        
        # Console application
        '--console',
        
        # Optimization
        '--optimize=2',
    ]
    
    print("Building Enhanced Multi-Strategy NIFTY Trading Bot Binary...")
    print("=" * 60)
    print(f"Main script: {main_script}")
    print(f"Output directory: dist/")
    print(f"Build directory: build/")
    
    try:
        # Run PyInstaller
        PyInstaller.__main__.run(args)
        
        # Check if binary was created successfully
        binary_name = "enhanced-multi-strategy-nifty-bot"
        if sys.platform == "win32":
            binary_name += ".exe"
        
        binary_path = Path("dist") / binary_name
        
        if binary_path.exists():
            size_mb = binary_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ Binary created successfully!")
            print(f"📁 Location: {binary_path}")
            print(f"📊 Size: {size_mb:.1f} MB")
            
            # Test the binary
            print(f"\n🧪 Testing binary...")
            test_cmd = f'"{binary_path}" --help'
            print(f"Test command: {test_cmd}")
            
            return True
        else:
            print(f"\n❌ Binary creation failed!")
            print(f"Expected location: {binary_path}")
            return False
            
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        return False

def main():
    """Main function."""
    print("Enhanced Multi-Strategy NIFTY Trading Bot Binary Builder")
    print("=" * 60)
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found! Install with: pip install pyinstaller")
        return 1
    
    # Check if required files exist
    required_files = [
        "enhanced_multi_strategy_bot.py",
        "nifty500_symbols.py",
        "input/config_nifty50.yaml",
        "input/config_nifty100.yaml", 
        "input/config_nifty500.yaml",
        "src/strategies/ema_crossover_strategy.py",
        "src/strategies/supertrend_strategy.py",
        "src/strategies/multi_strategy_scorer.py",
        "src/notifications/email_service.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return 1
    
    print("✅ All required files found")
    
    # Build the binary
    if build_binary():
        print("\n🎉 Build completed successfully!")
        print("\nUsage examples:")
        print("  ./dist/enhanced-multi-strategy-nifty-bot --help")
        print("  ./dist/enhanced-multi-strategy-nifty-bot --test")
        print("  ./dist/enhanced-multi-strategy-nifty-bot --size nifty50")
        return 0
    else:
        print("\n💥 Build failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())