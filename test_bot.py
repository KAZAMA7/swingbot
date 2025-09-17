#!/usr/bin/env python3
"""
Simple test script for the trading bot
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Test basic imports
    import yfinance as yf
    import pandas as pd
    import numpy as np
    print("✓ Core dependencies imported successfully")
    
    # Test yfinance connection
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(period="1d")
    if not hist.empty:
        print("✓ Yahoo Finance connection working")
    else:
        print("✗ Yahoo Finance connection failed")
    
    print("\nBasic functionality test passed!")
    print("You can now run the trading bot with: python src/main.py --test")
    
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)