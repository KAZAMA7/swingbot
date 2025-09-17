#!/usr/bin/env python3
"""
Simple Trading Bot - Standalone Version

A simplified version of the trading bot that can be run directly.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
import yaml
from datetime import datetime
from pathlib import Path


def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator."""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    avg_gains = gains.ewm(span=period).mean()
    avg_losses = losses.ewm(span=period).mean()
    
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.fillna(50)


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band


def calculate_ema(prices, period=20):
    """Calculate Exponential Moving Average."""
    return prices.ewm(span=period).mean()


def generate_signal(data, rsi_oversold=30, rsi_overbought=70):
    """Generate trading signals."""
    latest = data.iloc[-1]
    
    # BUY: RSI < 30 AND price < BB_lower AND price > EMA
    if (latest['RSI'] < rsi_oversold and 
        latest['Close'] < latest['BB_Lower'] and 
        latest['Close'] > latest['EMA']):
        return 'BUY'
    
    # SELL: RSI > 70 AND price > BB_upper AND price < EMA
    elif (latest['RSI'] > rsi_overbought and 
          latest['Close'] > latest['BB_Upper'] and 
          latest['Close'] < latest['EMA']):
        return 'SELL'
    
    return 'NO_SIGNAL'


def analyze_symbol(symbol, logger):
    """Analyze a single symbol."""
    try:
        logger.info(f"Analyzing {symbol}...")
        
        # Fetch comprehensive data (try to get maximum available)
        ticker = yf.Ticker(symbol)
        
        # Try different periods to get maximum data
        periods_to_try = ["max", "10y", "5y", "2y", "1y"]
        data = None
        
        for period in periods_to_try:
            try:
                data = ticker.history(period=period)
                if not data.empty and len(data) > 100:  # Ensure we have sufficient data
                    logger.debug(f"Successfully fetched {len(data)} days of data for {symbol} (period: {period})")
                    break
            except Exception as e:
                logger.debug(f"Failed to fetch {period} data for {symbol}: {e}")
                continue
        
        if data is None or data.empty:
            logger.warning(f"No data available for {symbol}")
            return None
        
        # Show data summary
        start_date = data.index.min().strftime('%Y-%m-%d')
        end_date = data.index.max().strftime('%Y-%m-%d')
        days_span = (data.index.max() - data.index.min()).days
        logger.info(f"{symbol}: {len(data)} records from {start_date} to {end_date} ({days_span} days, {days_span/365.25:.1f} years)")
        
        # Calculate indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
        data['EMA'] = calculate_ema(data['Close'])
        
        # Generate signal
        signal = generate_signal(data)
        
        latest = data.iloc[-1]
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'signal': signal,
            'price': latest['Close'],
            'rsi': latest['RSI'],
            'bb_upper': latest['BB_Upper'],
            'bb_lower': latest['BB_Lower'],
            'ema': latest['EMA']
        }
        
        logger.info(f"{symbol}: {signal} - Price: ${latest['Close']:.2f}, RSI: {latest['RSI']:.1f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None


def save_results(results, filename="signals.csv"):
    """Save results to CSV file."""
    if not results:
        return
    
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")


def main():
    """Main function."""
    logger = setup_logging()
    
    print("Simple Stock Trading Bot")
    print("=" * 40)
    
    # Default watchlist - NIFTY 50 stocks
    watchlist = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
        'ICICIBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS'
    ]
    
    # Load config if exists
    config_file = Path('config.yaml')
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                watchlist = config.get('watchlist', watchlist)
                logger.info(f"Loaded config with {len(watchlist)} symbols")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    else:
        # Create default config
        default_config = {
            'watchlist': watchlist,
            'indicators': {
                'rsi': {'period': 14},
                'bollinger_bands': {'period': 20, 'std_dev': 2},
                'ema': {'period': 20}
            },
            'strategy': {
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
        }
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logger.info(f"Created default config: {config_file}")
        except Exception as e:
            logger.warning(f"Could not create config: {e}")
    
    # Analyze symbols
    results = []
    signals_found = 0
    
    for symbol in watchlist:
        result = analyze_symbol(symbol, logger)
        if result:
            results.append(result)
            if result['signal'] != 'NO_SIGNAL':
                signals_found += 1
    
    # Save results
    if results:
        save_results(results)
        
        print(f"\nAnalysis Complete!")
        print(f"Processed: {len(results)} symbols")
        print(f"Signals found: {signals_found}")
        
        # Show signals
        for result in results:
            if result['signal'] != 'NO_SIGNAL':
                print(f"🚨 {result['signal']} signal for {result['symbol']} at ${result['price']:.2f}")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\nShutting down...")
        exit(0)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)