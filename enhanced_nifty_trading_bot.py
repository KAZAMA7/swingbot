#!/usr/bin/env python3
"""
Enhanced NIFTY Trading Bot with Multiple RSIs and EMAs

Advanced trading bot with multiple timeframe analysis for better opportunity detection.
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
            logging.FileHandler('enhanced_nifty_trading_bot.log')
        ]
    )
    return logging.getLogger(__name__)


def calculate_multiple_rsi(prices, periods=[14, 21, 50]):
    """Calculate RSI for multiple periods."""
    rsi_values = {}
    
    for period in periods:
        delta = prices.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        avg_gains = gains.ewm(span=period).mean()
        avg_losses = losses.ewm(span=period).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        rsi_values[f'RSI_{period}'] = rsi.fillna(50)
    
    return rsi_values


def calculate_multiple_ema(prices, periods=[9, 21, 50, 200]):
    """Calculate EMA for multiple periods."""
    ema_values = {}
    
    for period in periods:
        ema_values[f'EMA_{period}'] = prices.ewm(span=period).mean()
    
    return ema_values


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def generate_enhanced_signal(data):
    """
    Generate enhanced trading signals using multiple indicators.
    
    Enhanced Strategy:
    - Multiple RSI confirmation (14, 21, 50 periods)
    - Multiple EMA trend analysis (9, 21, 50, 200 periods)
    - Bollinger Bands for volatility
    - MACD for momentum
    """
    latest = data.iloc[-1]
    
    # RSI Analysis
    rsi_14 = latest['RSI_14']
    rsi_21 = latest['RSI_21']
    rsi_50 = latest['RSI_50']
    
    # EMA Analysis
    ema_9 = latest['EMA_9']
    ema_21 = latest['EMA_21']
    ema_50 = latest['EMA_50']
    ema_200 = latest['EMA_200']
    
    # Price and other indicators
    price = latest['Close']
    bb_upper = latest['BB_Upper']
    bb_lower = latest['BB_Lower']
    macd = latest['MACD']
    macd_signal = latest['MACD_Signal']
    
    # Signal strength scoring
    buy_score = 0
    sell_score = 0
    
    # RSI Scoring (Multiple timeframes)
    if rsi_14 < 30:
        buy_score += 3  # Strong oversold
    elif rsi_14 < 40:
        buy_score += 1  # Mild oversold
    elif rsi_14 > 70:
        sell_score += 3  # Strong overbought
    elif rsi_14 > 60:
        sell_score += 1  # Mild overbought
    
    if rsi_21 < 35:
        buy_score += 2
    elif rsi_21 > 65:
        sell_score += 2
    
    if rsi_50 < 40:
        buy_score += 1
    elif rsi_50 > 60:
        sell_score += 1
    
    # EMA Trend Analysis
    if price > ema_9 > ema_21 > ema_50:
        buy_score += 3  # Strong uptrend
    elif price < ema_9 < ema_21 < ema_50:
        sell_score += 3  # Strong downtrend
    
    if price > ema_200:
        buy_score += 2  # Above long-term trend
    elif price < ema_200:
        sell_score += 2  # Below long-term trend
    
    # Bollinger Bands
    if price < bb_lower:
        buy_score += 2  # Oversold by volatility
    elif price > bb_upper:
        sell_score += 2  # Overbought by volatility
    
    # MACD Momentum
    if macd > macd_signal and macd > 0:
        buy_score += 2  # Bullish momentum
    elif macd < macd_signal and macd < 0:
        sell_score += 2  # Bearish momentum
    
    # Generate signal based on scores
    if buy_score >= 6 and buy_score > sell_score:
        return 'STRONG_BUY', buy_score
    elif buy_score >= 4 and buy_score > sell_score:
        return 'BUY', buy_score
    elif sell_score >= 6 and sell_score > buy_score:
        return 'STRONG_SELL', sell_score
    elif sell_score >= 4 and sell_score > buy_score:
        return 'SELL', sell_score
    else:
        return 'NO_SIGNAL', max(buy_score, sell_score)


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


def analyze_symbol_enhanced(symbol, logger, max_data_years=None, config=None):
    """Analyze a single NIFTY symbol with enhanced indicators."""
    try:
        logger.info(f"Analyzing {symbol}...")
        
        # Fetch comprehensive data for Indian stocks
        ticker = yf.Ticker(symbol)
        
        # Get data fetching configuration
        if config and 'data_fetching' in config:
            data_config = config['data_fetching']
            max_period = data_config.get('max_data_period', 'max')
            fallback_periods = data_config.get('fallback_periods', ["max", "10y", "5y", "2y", "1y", "6mo"])
            min_threshold = data_config.get('min_data_threshold', 200)
        else:
            # Default configuration prioritizing maximum data
            max_period = max_data_years and f"{max_data_years}y" or "max"
            fallback_periods = ["max", "10y", "5y", "2y", "1y", "6mo"]
            min_threshold = 200
        
        # Try different periods to get maximum data, starting with "max"
        periods_to_try = fallback_periods if max_period == "max" else [max_period] + [p for p in fallback_periods if p != max_period]
        data = None
        
        period_used = None
        for period in periods_to_try:
            try:
                logger.debug(f"Attempting to fetch {period} data for {symbol}...")
                data = ticker.history(period=period)
                if not data.empty and len(data) >= min_threshold:  # Use configurable threshold
                    period_used = period
                    logger.debug(f"Successfully fetched {len(data)} days of data for {symbol} (period: {period})")
                    break
                else:
                    logger.debug(f"Insufficient data with {period} period for {symbol}: {len(data) if data is not None and not data.empty else 0} days")
            except Exception as e:
                logger.debug(f"Failed to fetch {period} data for {symbol}: {e}")
                continue
        
        if data is None or data.empty or len(data) < min_threshold:
            logger.warning(f"Insufficient data for {symbol} (need {min_threshold}+ days for analysis, got {len(data) if data is not None and not data.empty else 0})")
            return None
        
        # Show enhanced data summary
        start_date = data.index.min().strftime('%Y-%m-%d')
        end_date = data.index.max().strftime('%Y-%m-%d')
        days_span = (data.index.max() - data.index.min()).days
        years_span = days_span / 365.25
        
        # Enhanced logging with period used and data quality info
        logger.info(f"{symbol}: {len(data)} records from {start_date} to {end_date} ({years_span:.1f} years) [Period: {period_used}]")
        
        # Warn if data span is less than expected
        if years_span < 1.0:
            logger.warning(f"{symbol}: Limited historical data ({years_span:.1f} years) - signals may be less reliable")
        
        # Calculate multiple RSI indicators
        rsi_values = calculate_multiple_rsi(data['Close'])
        for key, values in rsi_values.items():
            data[key] = values
        
        # Calculate multiple EMA indicators
        ema_values = calculate_multiple_ema(data['Close'])
        for key, values in ema_values.items():
            data[key] = values
        
        # Calculate Bollinger Bands
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
        
        # Calculate MACD
        data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = calculate_macd(data['Close'])
        
        # Generate enhanced signal
        signal, score = generate_enhanced_signal(data)
        
        latest = data.iloc[-1]
        current_price = latest['Close']
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'signal': signal,
            'signal_score': score,
            'price': current_price,
            
            # Multiple RSI values
            'rsi_14': latest['RSI_14'],
            'rsi_21': latest['RSI_21'],
            'rsi_50': latest['RSI_50'],
            
            # Multiple EMA values
            'ema_9': latest['EMA_9'],
            'ema_21': latest['EMA_21'],
            'ema_50': latest['EMA_50'],
            'ema_200': latest['EMA_200'],
            
            # Other indicators
            'bb_upper': latest['BB_Upper'],
            'bb_lower': latest['BB_Lower'],
            'macd': latest['MACD'],
            'macd_signal': latest['MACD_Signal'],
            
            # Trend analysis
            'short_trend': 'UP' if current_price > latest['EMA_21'] else 'DOWN',
            'long_trend': 'UP' if current_price > latest['EMA_200'] else 'DOWN',
            
            # Enhanced data information
            'data_start_date': start_date,
            'data_end_date': end_date,
            'data_years': years_span,
            'data_records': len(data),
            'data_period_used': period_used,
        }
        
        # Enhanced logging with multiple indicators (Unicode-safe)
        trend_text = "UP" if result['short_trend'] == 'UP' else "DOWN"
        signal_text = {"STRONG_BUY": "STRONG_BUY", "BUY": "BUY", "STRONG_SELL": "STRONG_SELL", "SELL": "SELL", "NO_SIGNAL": "NO_SIGNAL"}
        
        logger.info(f"{symbol}: {signal_text.get(signal, 'NO_SIGNAL')} (Score: {score}) - "
                   f"Price: Rs.{current_price:.2f} [{trend_text}] | "
                   f"RSI(14/21/50): {latest['RSI_14']:.1f}/{latest['RSI_21']:.1f}/{latest['RSI_50']:.1f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None


def save_enhanced_results(results, filename="enhanced_nifty_signals.csv"):
    """Save enhanced results to CSV file with detailed analysis including data range information."""
    if not results:
        return
    
    df = pd.DataFrame(results)
    
    # Format for Indian market
    df['price_inr'] = df['price'].apply(lambda x: f"Rs.{x:.2f}")
    df['market_cap_category'] = df['symbol'].apply(classify_market_cap)
    
    # Add trend analysis
    df['trend_alignment'] = df.apply(lambda row: 
        'BULLISH' if row['short_trend'] == 'UP' and row['long_trend'] == 'UP'
        else 'BEARISH' if row['short_trend'] == 'DOWN' and row['long_trend'] == 'DOWN'
        else 'MIXED', axis=1)
    
    # Add data quality indicators
    df['data_quality'] = df['data_years'].apply(lambda x: 
        'EXCELLENT' if x >= 5 
        else 'GOOD' if x >= 2 
        else 'LIMITED' if x >= 1 
        else 'POOR')
    
    # Format data range for display
    df['data_range'] = df.apply(lambda row: 
        f"{row['data_start_date']} to {row['data_end_date']} ({row['data_years']:.1f}y)", axis=1)
    
    # Sort by signal strength, then by data quality
    signal_order = {'STRONG_BUY': 5, 'BUY': 4, 'NO_SIGNAL': 3, 'SELL': 2, 'STRONG_SELL': 1}
    quality_order = {'EXCELLENT': 4, 'GOOD': 3, 'LIMITED': 2, 'POOR': 1}
    df['signal_rank'] = df['signal'].map(signal_order)
    df['quality_rank'] = df['data_quality'].map(quality_order)
    df = df.sort_values(['signal_rank', 'signal_score', 'quality_rank'], ascending=[False, False, False])
    
    df.to_csv(filename, index=False)
    print(f"Enhanced results with data range information saved to {filename}")
    
    # Print data quality summary
    quality_counts = df['data_quality'].value_counts()
    print(f"Data Quality Summary:")
    for quality, count in quality_counts.items():
        print(f"  {quality}: {count} symbols")


def classify_market_cap(symbol):
    """Classify stocks by market cap based on NIFTY indices."""
    # Large cap stocks (typically NIFTY 50)
    large_cap = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
        "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
        "ASIANPAINT.NS", "LT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS"
    ]
    
    if symbol in large_cap:
        return "Large Cap"
    elif ".NS" in symbol:
        return "Mid/Small Cap"
    else:
        return "Unknown"


def load_config(config_file=None):
    """Load and validate configuration from YAML file."""
    if config_file and Path(config_file).exists():
        config_path = config_file
    else:
        # Default config file
        config_path = "config_enhanced_nifty.yaml"
    
    try:
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return validate_config(config)
        else:
            print(f"Warning: Config file {config_path} not found, using defaults")
            return get_default_config()
    except Exception as e:
        print(f"Warning: Error loading config file {config_path}: {e}")
        return get_default_config()


def get_default_config():
    """Get default configuration with data fetching settings."""
    return {
        'data_fetching': {
            'max_data_period': 'max',
            'fallback_periods': ['max', '10y', '5y', '2y', '1y', '6mo'],
            'min_data_threshold': 200,
            'timeout_per_symbol': 60,
            'show_data_summary': True
        },
        'data_sources': {
            'yahoo_finance': {
                'enabled': True,
                'rate_limit': 1,
                'timeout': 30
            }
        }
    }


def validate_config(config):
    """Validate and set defaults for configuration."""
    if not config:
        return get_default_config()
    
    # Ensure data_fetching section exists
    if 'data_fetching' not in config:
        config['data_fetching'] = get_default_config()['data_fetching']
    else:
        # Validate and set defaults for data_fetching options
        data_config = config['data_fetching']
        defaults = get_default_config()['data_fetching']
        
        for key, default_value in defaults.items():
            if key not in data_config:
                data_config[key] = default_value
        
        # Validate fallback_periods is a list
        if not isinstance(data_config['fallback_periods'], list):
            print("Warning: fallback_periods must be a list, using defaults")
            data_config['fallback_periods'] = defaults['fallback_periods']
        
        # Validate min_data_threshold is positive integer
        if not isinstance(data_config['min_data_threshold'], int) or data_config['min_data_threshold'] <= 0:
            print("Warning: min_data_threshold must be positive integer, using default")
            data_config['min_data_threshold'] = defaults['min_data_threshold']
        
        # Validate timeout_per_symbol is positive
        if not isinstance(data_config['timeout_per_symbol'], (int, float)) or data_config['timeout_per_symbol'] <= 0:
            print("Warning: timeout_per_symbol must be positive number, using default")
            data_config['timeout_per_symbol'] = defaults['timeout_per_symbol']
    
    return config


def main():
    """Main function for Enhanced NIFTY trading bot."""
    parser = argparse.ArgumentParser(description="Enhanced NIFTY Trading Bot with Multiple RSIs and EMAs")
    parser.add_argument("--size", choices=["nifty50", "nifty100", "nifty500"], 
                       default="nifty500", help="NIFTY index size (default: nifty500)")
    parser.add_argument("--config", type=str, help="Custom configuration file")
    parser.add_argument("--test", action="store_true", help="Test mode with limited symbols")
    parser.add_argument("--validate", action="store_true", help="Validate symbols only")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--market-hours-only", action="store_true", 
                       help="Only run during Indian market hours")
    parser.add_argument("--min-score", type=int, default=4, 
                       help="Minimum signal score to display (default: 4)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    logger = setup_logging(args.verbose)
    
    print("Enhanced NIFTY Stock Trading Bot (India)")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Index: {args.size.upper()}")
    print(f"Min Signal Score: {args.min_score}")
    print(f"Indicators: Multiple RSI (14,21,50) + Multiple EMA (9,21,50,200) + BB + MACD")
    
    # Check market hours if requested
    if args.market_hours_only and not is_market_hours():
        print("Indian market is currently closed (9:15 AM - 3:30 PM IST, Mon-Fri)")
        print("Use --market-hours-only=false to run anyway")
        return 0
    
    # Get symbol list
    symbols = get_symbol_list(args.size)
    
    if args.test:
        symbols = symbols[:20]  # Test with first 20 symbols
        print(f"Test mode: Using first 20 symbols")
    
    print(f"Analyzing {len(symbols)} symbols...")
    
    # Validate symbols if requested
    if args.validate:
        print("\nValidating symbols...")
        validation_results = validate_symbols(symbols, min(len(symbols), 20))
        
        print(f"Valid: {validation_results['valid']}")
        print(f"Invalid: {validation_results['invalid']}")
        
        for symbol, details in validation_results['details'].items():
            if details['status'] == 'valid':
                print(f"  [OK] {symbol}: Rs.{details['latest_price']:.2f}")
            else:
                print(f"  [ERR] {symbol}: {details['status']}")
        
        return 0
    
    # Analyze symbols
    results = []
    signals_found = 0
    errors = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"Processing {symbol} ({i}/{len(symbols)})...", end=" ")
            
            result = analyze_symbol_enhanced(symbol, logger, config=config)
            if result:
                results.append(result)
                if result['signal'] != 'NO_SIGNAL' and result['signal_score'] >= args.min_score:
                    signals_found += 1
                print("[OK]")
            else:
                print("[ERR]")
                errors += 1
                
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error with {symbol}: {e}")
            errors += 1
            print("❌")
    
    # Save results
    if results:
        output_file = f"enhanced_{args.size}_signals.csv"
        save_enhanced_results(results, output_file)
        
        print(f"\nEnhanced Analysis Complete!")
        print(f"Processed: {len(results)} symbols")
        print(f"Quality signals found: {signals_found}")
        print(f"Errors: {errors}")
        
        # Show high-quality signals
        strong_buy = [r for r in results if r['signal'] == 'STRONG_BUY']
        buy_signals = [r for r in results if r['signal'] == 'BUY' and r['signal_score'] >= args.min_score]
        strong_sell = [r for r in results if r['signal'] == 'STRONG_SELL']
        sell_signals = [r for r in results if r['signal'] == 'SELL' and r['signal_score'] >= args.min_score]
        
        if strong_buy:
            print(f"\n** STRONG BUY Signals ({len(strong_buy)}):")
            for result in strong_buy:
                print(f"   [BUY++] {result['symbol']}: Rs.{result['price']:.2f} (Score: {result['signal_score']}) "
                     f"RSI: {result['rsi_14']:.1f} | Trend: {result['short_trend']}/{result['long_trend']} | "
                     f"Data: {result['data_years']:.1f}y [{result['data_period_used']}]")
        
        if buy_signals:
            print(f"\n* BUY Signals ({len(buy_signals)}):")
            for result in buy_signals:
                print(f"   [BUY] {result['symbol']}: Rs.{result['price']:.2f} (Score: {result['signal_score']}) "
                     f"RSI: {result['rsi_14']:.1f} | Trend: {result['short_trend']}/{result['long_trend']} | "
                     f"Data: {result['data_years']:.1f}y [{result['data_period_used']}]")
        
        if strong_sell:
            print(f"\n** STRONG SELL Signals ({len(strong_sell)}):")
            for result in strong_sell:
                print(f"   [SELL++] {result['symbol']}: Rs.{result['price']:.2f} (Score: {result['signal_score']}) "
                     f"RSI: {result['rsi_14']:.1f} | Trend: {result['short_trend']}/{result['long_trend']} | "
                     f"Data: {result['data_years']:.1f}y [{result['data_period_used']}]")
        
        if sell_signals:
            print(f"\n* SELL Signals ({len(sell_signals)}):")
            for result in sell_signals:
                print(f"   [SELL] {result['symbol']}: Rs.{result['price']:.2f} (Score: {result['signal_score']}) "
                     f"RSI: {result['rsi_14']:.1f} | Trend: {result['short_trend']}/{result['long_trend']} | "
                     f"Data: {result['data_years']:.1f}y [{result['data_period_used']}]")
        
        if not any([strong_buy, buy_signals, strong_sell, sell_signals]):
            print(f"\nNo high-quality trading signals found (min score: {args.min_score})")
            print("Try lowering --min-score or check market conditions")
        
        # Enhanced summary statistics with data quality information
        if results:
            avg_rsi_14 = np.mean([r['rsi_14'] for r in results if not np.isnan(r['rsi_14'])])
            avg_rsi_50 = np.mean([r['rsi_50'] for r in results if not np.isnan(r['rsi_50'])])
            total_data_years = sum([r['data_years'] for r in results])
            avg_data_years = np.mean([r['data_years'] for r in results])
            
            bullish_trends = len([r for r in results if r['short_trend'] == 'UP' and r['long_trend'] == 'UP'])
            bearish_trends = len([r for r in results if r['short_trend'] == 'DOWN' and r['long_trend'] == 'DOWN'])
            
            # Data quality statistics
            excellent_data = len([r for r in results if r['data_years'] >= 5])
            good_data = len([r for r in results if 2 <= r['data_years'] < 5])
            limited_data = len([r for r in results if 1 <= r['data_years'] < 2])
            poor_data = len([r for r in results if r['data_years'] < 1])
            
            # Period usage statistics
            period_usage = {}
            for result in results:
                period = result['data_period_used']
                period_usage[period] = period_usage.get(period, 0) + 1
            
            print(f"\nEnhanced Market Summary:")
            print(f"Average RSI (14-day): {avg_rsi_14:.1f}")
            print(f"Average RSI (50-day): {avg_rsi_50:.1f}")
            print(f"Bullish trends: {bullish_trends}/{len(results)} ({bullish_trends/len(results)*100:.1f}%)")
            print(f"Bearish trends: {bearish_trends}/{len(results)} ({bearish_trends/len(results)*100:.1f}%)")
            print(f"Total data analyzed: {total_data_years:.1f} years")
            print(f"Average data per symbol: {avg_data_years:.1f} years")
            print(f"Market sentiment: {'Oversold' if avg_rsi_14 < 40 else 'Overbought' if avg_rsi_14 > 60 else 'Neutral'}")
            
            print(f"\nData Quality Distribution:")
            print(f"Excellent (5+ years): {excellent_data} symbols ({excellent_data/len(results)*100:.1f}%)")
            print(f"Good (2-5 years): {good_data} symbols ({good_data/len(results)*100:.1f}%)")
            print(f"Limited (1-2 years): {limited_data} symbols ({limited_data/len(results)*100:.1f}%)")
            print(f"Poor (<1 year): {poor_data} symbols ({poor_data/len(results)*100:.1f}%)")
            
            print(f"\nPeriod Usage Statistics:")
            for period, count in sorted(period_usage.items(), key=lambda x: x[1], reverse=True):
                print(f"{period}: {count} symbols ({count/len(results)*100:.1f}%)")
    
    return 0


if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)