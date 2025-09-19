#!/usr/bin/env python3
"""
Enhanced Multi-Strategy NIFTY Trading Bot

Advanced trading bot with EMA Crossover, SuperTrend, and Multi-Strategy scoring.
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

# Import new strategies
from src.strategies.ema_crossover_strategy import EMACrossoverStrategy
from src.strategies.supertrend_strategy import SuperTrendStrategy
from src.strategies.multi_strategy_scorer import MultiStrategyScorer
from src.notifications.email_service import EmailNotificationService
from src.visualization.chart_generator import ChartGenerator


def setup_logging(verbose=False, output_config=None):
    """Setup logging for NIFTY trading bot."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create output directories if they don't exist
    if output_config:
        base_dir = output_config.get('base_directory', 'output')
        logs_dir = output_config.get('logs_directory', 'logs')
        log_path = Path(base_dir) / logs_dir
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / 'enhanced_multi_strategy_bot.log'
    else:
        log_file = 'enhanced_multi_strategy_bot.log'
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
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


def generate_legacy_signal(data):
    """
    Generate legacy trading signals using multiple indicators.
    
    Legacy Strategy:
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


def analyze_symbol_multi_strategy(symbol, logger, config=None, strategies=None, 
                                email_service=None, scorer=None, chart_generator=None):
    """Analyze a single NIFTY symbol with multiple strategies."""
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
            max_period = "max"
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
                if not data.empty and len(data) >= min_threshold:
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
        
        # Calculate legacy indicators
        rsi_values = calculate_multiple_rsi(data['Close'])
        for key, values in rsi_values.items():
            data[key] = values
        
        ema_values = calculate_multiple_ema(data['Close'])
        for key, values in ema_values.items():
            data[key] = values
        
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
        data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = calculate_macd(data['Close'])
        
        # Generate legacy signal
        legacy_signal, legacy_score = generate_legacy_signal(data)
        
        # Generate new strategy signals
        strategy_signals = []
        
        if strategies:
            for strategy_name, strategy in strategies.items():
                try:
                    signal = strategy.generate_signal(data, {})
                    strategy_signals.append(signal)
                    logger.debug(f"{symbol} - {strategy_name}: {signal.signal_type.value} (confidence: {signal.confidence:.2f})")
                except Exception as e:
                    logger.error(f"Strategy {strategy_name} failed for {symbol}: {e}")
        
        # Generate composite signal if we have multiple strategies
        composite_signal = None
        if strategy_signals and scorer:
            try:
                composite_signal = scorer.calculate_composite_score(strategy_signals, symbol)
                logger.debug(f"{symbol} - Composite: {composite_signal.signal_type.value} (score: {composite_signal.composite_score:.1f})")
            except Exception as e:
                logger.error(f"Composite scoring failed for {symbol}: {e}")
        
        # Send email notification if configured
        if email_service and composite_signal:
            try:
                email_service.send_signal_notification(composite_signal, symbol)
            except Exception as e:
                logger.error(f"Email notification failed for {symbol}: {e}")
        
        # Generate chart if configured and signal is strong enough
        chart_path = None
        if (chart_generator and composite_signal and 
            abs(composite_signal.composite_score) >= 30.0):
            try:
                chart_path = chart_generator.generate_comprehensive_chart(
                    symbol, data, {
                        'composite_signal': composite_signal.signal_type.value,
                        'composite_score': composite_signal.composite_score,
                        'composite_confidence': composite_signal.confidence,
                        'legacy_signal': legacy_signal,
                        'legacy_score': legacy_score
                    }, {signal.strategy_name: {
                        'signal': signal.signal_type.value,
                        'confidence': signal.confidence
                    } for signal in strategy_signals}
                )
                if chart_path:
                    logger.info(f"Chart generated for {symbol}: {chart_path}")
            except Exception as e:
                logger.error(f"Chart generation failed for {symbol}: {e}")
        
        latest = data.iloc[-1]
        current_price = latest['Close']
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            
            # Legacy signal
            'legacy_signal': legacy_signal,
            'legacy_score': legacy_score,
            
            # Composite signal
            'composite_signal': composite_signal.signal_type.value if composite_signal else 'NO_SIGNAL',
            'composite_score': composite_signal.composite_score if composite_signal else 0.0,
            'composite_confidence': composite_signal.confidence if composite_signal else 0.0,
            
            # Individual strategy signals
            'strategy_signals': {signal.strategy_name: {
                'signal': signal.signal_type.value,
                'confidence': signal.confidence
            } for signal in strategy_signals},
            
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
            'chart_path': chart_path,
        }
        
        # Enhanced logging with multiple strategies
        trend_text = "UP" if result['short_trend'] == 'UP' else "DOWN"
        
        if composite_signal:
            logger.info(f"{symbol}: COMPOSITE={composite_signal.signal_type.value} (Score: {composite_signal.composite_score:.1f}) | "
                       f"LEGACY={legacy_signal} (Score: {legacy_score}) | "
                       f"Price: Rs.{current_price:.2f} [{trend_text}] | "
                       f"Strategies: {len(strategy_signals)}")
        else:
            logger.info(f"{symbol}: LEGACY={legacy_signal} (Score: {legacy_score}) | "
                       f"Price: Rs.{current_price:.2f} [{trend_text}] | "
                       f"RSI(14/21/50): {latest['RSI_14']:.1f}/{latest['RSI_21']:.1f}/{latest['RSI_50']:.1f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None


def load_enhanced_config(config_file=None, size="nifty500"):
    """Load enhanced configuration with strategy settings."""
    if config_file and Path(config_file).exists():
        config_path = config_file
    else:
        # Auto-select config based on size parameter
        config_mapping = {
            "nifty50": "input/config_nifty50.yaml",
            "nifty100": "input/config_nifty100.yaml", 
            "nifty500": "input/config_nifty500.yaml"
        }
        config_path = config_mapping.get(size, "input/config_enhanced_multi_strategy.yaml")
    
    try:
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return validate_enhanced_config(config)
        else:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return get_default_enhanced_config()
    except Exception as e:
        logger.warning(f"Error loading config file {config_path}: {e}")
        return get_default_enhanced_config()


def get_default_enhanced_config():
    """Get default enhanced configuration."""
    return {
        'data_fetching': {
            'max_data_period': 'max',
            'fallback_periods': ['max', '10y', '5y', '2y', '1y', '6mo'],
            'min_data_threshold': 200,
            'timeout_per_symbol': 60,
            'show_data_summary': True
        },
        'strategies': {
            'ema_crossover': {
                'enabled': True,
                'short_period': 50,
                'long_period': 200,
                'approach_threshold': 0.02,
                'weight': 1.5
            },
            'supertrend': {
                'enabled': True,
                'atr_period': 10,
                'multiplier': 3.0,
                'weight': 1.2
            },
            'legacy': {
                'enabled': True,
                'weight': 1.0
            }
        },
        'multi_strategy': {
            'enabled': True,
            'strong_buy_threshold': 60.0,
            'buy_threshold': 30.0,
            'sell_threshold': -30.0,
            'strong_sell_threshold': -60.0
        },
        'email_notifications': {
            'enabled': False,
            'smtp_host': '',
            'smtp_port': 587,
            'use_tls': True,
            'username': '',
            'password': '',
            'recipients': [],
            'send_on_strong_signals_only': True
        },
        'output': {
            'base_directory': 'output',
            'signals_directory': 'signals',
            'logs_directory': 'logs',
            'charts_directory': 'charts'
        },
        'charts': {
            'enabled': True,
            'generate_for_signals': True,
            'min_score_threshold': 30.0,
            'save_all_symbols': False
        }
    }


def validate_enhanced_config(config):
    """Validate enhanced configuration."""
    if not config:
        return get_default_enhanced_config()
    
    defaults = get_default_enhanced_config()
    
    # Ensure all sections exist
    for section in ['data_fetching', 'strategies', 'multi_strategy', 'email_notifications']:
        if section not in config:
            config[section] = defaults[section]
    
    return config


def initialize_strategies(config):
    """Initialize trading strategies based on configuration."""
    strategies = {}
    strategy_weights = {}
    
    strategy_config = config.get('strategies', {})
    
    # EMA Crossover Strategy
    if strategy_config.get('ema_crossover', {}).get('enabled', True):
        ema_config = strategy_config['ema_crossover']
        strategies['ema_crossover'] = EMACrossoverStrategy(
            short_period=ema_config.get('short_period', 50),
            long_period=ema_config.get('long_period', 200),
            approach_threshold=ema_config.get('approach_threshold', 0.02)
        )
        strategy_weights['ema_crossover'] = ema_config.get('weight', 1.5)
    
    # SuperTrend Strategy
    if strategy_config.get('supertrend', {}).get('enabled', True):
        st_config = strategy_config['supertrend']
        strategies['supertrend'] = SuperTrendStrategy(
            atr_period=st_config.get('atr_period', 10),
            multiplier=st_config.get('multiplier', 3.0)
        )
        strategy_weights['supertrend'] = st_config.get('weight', 1.2)
    
    return strategies, strategy_weights


def initialize_email_service(config):
    """Initialize email notification service."""
    email_config = config.get('email_notifications', {})
    
    if not email_config.get('enabled', False):
        return None
    
    try:
        return EmailNotificationService(email_config)
    except Exception as e:
        logger.warning(f"Failed to initialize email service: {e}")
        return None


def save_enhanced_results(results, filename="enhanced_multi_strategy_signals.csv", output_config=None):
    """Save enhanced results with multi-strategy information."""
    if not results:
        return
    
    # Create output directory structure
    if output_config:
        base_dir = output_config.get('base_directory', 'output')
        signals_dir = output_config.get('signals_directory', 'signals')
        output_path = Path(base_dir) / signals_dir
        output_path.mkdir(parents=True, exist_ok=True)
        full_filename = output_path / filename
    else:
        full_filename = filename
    
    df = pd.DataFrame(results)
    
    # Format for Indian market
    df['price_inr'] = df['price'].apply(lambda x: f"Rs.{x:.2f}")
    
    # Add signal comparison
    df['signal_agreement'] = df.apply(lambda row: 
        'AGREE' if row['legacy_signal'] != 'NO_SIGNAL' and row['composite_signal'] != 'NO_SIGNAL' and 
                  ((row['legacy_signal'] in ['BUY', 'STRONG_BUY'] and row['composite_signal'] == 'BUY') or
                   (row['legacy_signal'] in ['SELL', 'STRONG_SELL'] and row['composite_signal'] == 'SELL'))
        else 'DISAGREE' if row['legacy_signal'] != 'NO_SIGNAL' and row['composite_signal'] != 'NO_SIGNAL'
        else 'PARTIAL', axis=1)
    
    # Sort by composite score, then legacy score
    df = df.sort_values(['composite_score', 'legacy_score'], ascending=[False, False])
    
    df.to_csv(full_filename, index=False)
    print(f"Enhanced multi-strategy results saved to {full_filename}")


def main():
    """Main function for Enhanced Multi-Strategy NIFTY trading bot."""
    parser = argparse.ArgumentParser(description="Enhanced Multi-Strategy NIFTY Trading Bot")
    parser.add_argument("--size", choices=["nifty50", "nifty100", "nifty500"], 
                       default="nifty500", help="NIFTY index size (default: nifty500)")
    parser.add_argument("--config", type=str, help="Custom configuration file")
    parser.add_argument("--test", action="store_true", help="Test mode with limited symbols")
    parser.add_argument("--validate", action="store_true", help="Validate symbols only")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--market-hours-only", action="store_true", 
                       help="Only run during Indian market hours")
    parser.add_argument("--min-composite-score", type=float, default=30.0, 
                       help="Minimum composite score to display (default: 30.0)")
    parser.add_argument("--email-test", action="store_true", help="Send test email")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_enhanced_config(args.config, args.size)
    
    global logger
    logger = setup_logging(args.verbose, config.get('output'))
    
    print("Enhanced Multi-Strategy NIFTY Trading Bot")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Index: {args.size.upper()}")
    print(f"Min Composite Score: {args.min_composite_score}")
    print(f"Strategies: EMA Crossover + SuperTrend + Legacy Multi-Indicator")
    
    # Check market hours if requested
    if args.market_hours_only and not is_market_hours():
        print("Indian market is currently closed (9:15 AM - 3:30 PM IST, Mon-Fri)")
        return 0
    
    # Initialize strategies
    strategies, strategy_weights = initialize_strategies(config)
    print(f"Enabled Strategies: {list(strategies.keys())}")
    
    # Initialize multi-strategy scorer
    scorer = MultiStrategyScorer(strategy_weights) if strategies else None
    
    # Initialize email service
    email_service = initialize_email_service(config)
    if email_service:
        print("Email notifications: ENABLED")
        if args.email_test:
            print("Sending test email...")
            if email_service.send_test_email():
                print("✅ Test email sent successfully!")
            else:
                print("❌ Test email failed!")
            return 0
    else:
        print("Email notifications: DISABLED")
    
    # Initialize chart generator
    chart_generator = None
    chart_config = config.get('charts', {})
    if chart_config.get('enabled', True):
        output_config = config.get('output', {})
        charts_dir = Path(output_config.get('base_directory', 'output')) / output_config.get('charts_directory', 'charts')
        chart_generator = ChartGenerator(str(charts_dir))
        print("Chart generation: ENABLED")
    else:
        print("Chart generation: DISABLED")
    
    # Get symbol list
    symbols = get_symbol_list(args.size)
    
    if args.test:
        symbols = symbols[:10]  # Test with first 10 symbols
        print(f"Test mode: Using first 10 symbols")
    
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
            
            result = analyze_symbol_multi_strategy(
                symbol, logger, config, strategies, email_service, scorer, chart_generator
            )
            if result:
                results.append(result)
                if (result['composite_signal'] != 'NO_SIGNAL' and 
                    abs(result['composite_score']) >= args.min_composite_score):
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"enhanced_multi_strategy_{args.size}_signals_{timestamp}.csv"
        save_enhanced_results(results, output_file, config.get('output'))
        
        print(f"\nEnhanced Multi-Strategy Analysis Complete!")
        print(f"Processed: {len(results)} symbols")
        print(f"Quality signals found: {signals_found}")
        print(f"Errors: {errors}")
        
        # Show high-quality composite signals
        strong_buy = [r for r in results if r['composite_signal'] == 'BUY' and r['composite_score'] >= 60]
        buy_signals = [r for r in results if r['composite_signal'] == 'BUY' and 30 <= r['composite_score'] < 60]
        strong_sell = [r for r in results if r['composite_signal'] == 'SELL' and r['composite_score'] <= -60]
        sell_signals = [r for r in results if r['composite_signal'] == 'SELL' and -60 < r['composite_score'] <= -30]
        
        if strong_buy:
            print(f"\n🟢 STRONG BUY Signals ({len(strong_buy)}):")
            for result in strong_buy[:5]:  # Show top 5
                print(f"   {result['symbol']}: Score={result['composite_score']:.1f}, "
                     f"Confidence={result['composite_confidence']:.1%}, "
                     f"Price=Rs.{result['price']:.2f}")
        
        if buy_signals:
            print(f"\n🟡 BUY Signals ({len(buy_signals)}):")
            for result in buy_signals[:5]:  # Show top 5
                print(f"   {result['symbol']}: Score={result['composite_score']:.1f}, "
                     f"Confidence={result['composite_confidence']:.1%}, "
                     f"Price=Rs.{result['price']:.2f}")
        
        if strong_sell:
            print(f"\n🔴 STRONG SELL Signals ({len(strong_sell)}):")
            for result in strong_sell[:5]:  # Show top 5
                print(f"   {result['symbol']}: Score={result['composite_score']:.1f}, "
                     f"Confidence={result['composite_confidence']:.1%}, "
                     f"Price=Rs.{result['price']:.2f}")
        
        if sell_signals:
            print(f"\n🟠 SELL Signals ({len(sell_signals)}):")
            for result in sell_signals[:5]:  # Show top 5
                print(f"   {result['symbol']}: Score={result['composite_score']:.1f}, "
                     f"Confidence={result['composite_confidence']:.1%}, "
                     f"Price=Rs.{result['price']:.2f}")
        
        if not any([strong_buy, buy_signals, strong_sell, sell_signals]):
            print(f"\nNo high-quality composite signals found (min score: {args.min_composite_score})")
        
        # Strategy performance summary
        if results and strategies:
            print(f"\n📊 Strategy Performance Summary:")
            strategy_stats = {}
            
            for result in results:
                for strategy_name, strategy_data in result.get('strategy_signals', {}).items():
                    if strategy_name not in strategy_stats:
                        strategy_stats[strategy_name] = {'signals': 0, 'avg_confidence': 0.0}
                    
                    if strategy_data['signal'] != 'NO_SIGNAL':
                        strategy_stats[strategy_name]['signals'] += 1
                        strategy_stats[strategy_name]['avg_confidence'] += strategy_data['confidence']
            
            for strategy_name, stats in strategy_stats.items():
                if stats['signals'] > 0:
                    avg_conf = stats['avg_confidence'] / stats['signals']
                    print(f"  {strategy_name.upper()}: {stats['signals']} signals, "
                         f"Avg Confidence: {avg_conf:.1%}")
    
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