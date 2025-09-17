#!/usr/bin/env python3
"""
NIFTY Trading Bot

Enhanced trading bot specifically for NIFTY stocks with Indian market considerations.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
import yaml
from datetime import datetime, time
from pathlib import Path
import argparse
from nifty500_symbols import get_symbol_list, validate_symbols


def setup_logging(verbose=False):
    """Setup logging for NIFTY trading bot."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('nifty_trading_bot.log')
        ]
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
    """Generate trading signals for Indian market."""
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


def is_market_hours():
    """Check if Indian market is open (9:15 AM to 3:30 PM IST)."""
    now = datetime.now()
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Indian market hours: 9:15 AM to 3:30 PM IST
    market_open = time(9, 15)
    market_close = time(15, 30)
    current_time = now.time()
    
    return market_open <= current_time <= market_close


def analyze_symbol(symbol, logger, max_data_years=5):
    """Analyze a single NIFTY symbol."""
    try:
        logger.info(f"Analyzing {symbol}...")
        
        # Fetch comprehensive data for Indian stocks
        ticker = yf.Ticker(symbol)
        
        # Try different periods to get maximum data
        periods_to_try = [f"{max_data_years}y", "2y", "1y", "6mo"]
        data = None
        
        for period in periods_to_try:
            try:
                data = ticker.history(period=period)
                if not data.empty and len(data) > 100:
                    logger.debug(f"Fetched {len(data)} days of data for {symbol} (period: {period})")
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
        years_span = days_span / 365.25
        
        logger.info(f"{symbol}: {len(data)} records from {start_date} to {end_date} ({years_span:.1f} years)")
        
        # Calculate indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
        data['EMA'] = calculate_ema(data['Close'])
        
        # Generate signal
        signal = generate_signal(data)
        
        latest = data.iloc[-1]
        
        # Convert price to INR format
        current_price = latest['Close']
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'signal': signal,
            'price': current_price,
            'rsi': latest['RSI'],
            'bb_upper': latest['BB_Upper'],
            'bb_lower': latest['BB_Lower'],
            'ema': latest['EMA'],
            'data_years': years_span,
            'records': len(data)
        }
        
        logger.info(f"{symbol}: {signal} - Price: Rs.{current_price:.2f}, RSI: {latest['RSI']:.1f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None


def save_results(results, filename="nifty_signals.csv"):
    """Save results to CSV file with Indian formatting."""
    if not results:
        return
    
    df = pd.DataFrame(results)
    
    # Format for Indian market
    df['price_inr'] = df['price'].apply(lambda x: f"Rs.{x:.2f}")
    df['market_cap_category'] = df['symbol'].apply(classify_market_cap)
    
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")


def classify_market_cap(symbol):
    """Classify stocks by market cap based on NIFTY indices."""
    # This is a simplified classification
    large_cap = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS"]
    
    if symbol in large_cap:
        return "Large Cap"
    elif ".NS" in symbol:
        return "Mid/Small Cap"
    else:
        return "Unknown"


def main():
    """Main function for NIFTY trading bot."""
    parser = argparse.ArgumentParser(description="NIFTY Trading Bot")
    parser.add_argument("--size", choices=["nifty50", "nifty100", "nifty500"], 
                       default="nifty50", help="NIFTY index size")
    parser.add_argument("--config", type=str, help="Custom configuration file")
    parser.add_argument("--test", action="store_true", help="Test mode with limited symbols")
    parser.add_argument("--validate", action="store_true", help="Validate symbols only")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--market-hours-only", action="store_true", 
                       help="Only run during Indian market hours")
    
    args = parser.parse_args()
    
    logger = setup_logging(args.verbose)
    
    print("🇮🇳 NIFTY Stock Trading Bot")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Index: {args.size.upper()}")
    
    # Check market hours if requested
    if args.market_hours_only and not is_market_hours():
        print("⏰ Indian market is currently closed (9:15 AM - 3:30 PM IST, Mon-Fri)")
        print("   Use --market-hours-only=false to run anyway")
        return 0
    
    # Get symbol list
    symbols = get_symbol_list(args.size)
    
    if args.test:
        symbols = symbols[:10]  # Test with first 10 symbols
        print(f"🧪 Test mode: Using first 10 symbols")
    
    print(f"📈 Analyzing {len(symbols)} symbols...")
    
    # Validate symbols if requested
    if args.validate:
        print("\n🔍 Validating symbols...")
        validation_results = validate_symbols(symbols, min(len(symbols), 20))
        
        print(f"✅ Valid: {validation_results['valid']}")
        print(f"❌ Invalid: {validation_results['invalid']}")
        
        for symbol, details in validation_results['details'].items():
            if details['status'] == 'valid':
                print(f"  ✅ {symbol}: ₹{details['latest_price']:.2f}")
            else:
                print(f"  ❌ {symbol}: {details['status']}")
        
        return 0
    
    # Load configuration
    config_file = args.config or f"config_{args.size}.yaml"
    config = {}
    
    if Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    # Analyze symbols
    results = []
    signals_found = 0
    errors = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"Processing {symbol} ({i}/{len(symbols)})...", end=" ")
            
            result = analyze_symbol(symbol, logger)
            if result:
                results.append(result)
                if result['signal'] != 'NO_SIGNAL':
                    signals_found += 1
                print("✅")
            else:
                print("❌")
                errors += 1
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error with {symbol}: {e}")
            errors += 1
            print("❌")
    
    # Save results
    if results:
        output_file = f"{args.size}_signals.csv"
        save_results(results, output_file)
        
        print(f"\n📊 Analysis Complete!")
        print(f"   Processed: {len(results)} symbols")
        print(f"   Signals found: {signals_found}")
        print(f"   Errors: {errors}")
        
        # Show signals
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        
        if buy_signals:
            print(f"\n🟢 BUY Signals ({len(buy_signals)}):")
            for result in buy_signals:
                print(f"   📈 {result['symbol']}: Rs.{result['price']:.2f} (RSI: {result['rsi']:.1f})")
        
        if sell_signals:
            print(f"\n🔴 SELL Signals ({len(sell_signals)}):")
            for result in sell_signals:
                print(f"   📉 {result['symbol']}: Rs.{result['price']:.2f} (RSI: {result['rsi']:.1f})")
        
        if not buy_signals and not sell_signals:
            print("\n⚪ No trading signals found in current market conditions")
        
        # Summary statistics
        if results:
            avg_rsi = np.mean([r['rsi'] for r in results if not np.isnan(r['rsi'])])
            total_data_years = sum([r['data_years'] for r in results])
            
            print(f"\n📈 Market Summary:")
            print(f"   Average RSI: {avg_rsi:.1f}")
            print(f"   Total data analyzed: {total_data_years:.1f} years")
            print(f"   Market sentiment: {'Oversold' if avg_rsi < 40 else 'Overbought' if avg_rsi > 60 else 'Neutral'}")
    
    return 0


if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)