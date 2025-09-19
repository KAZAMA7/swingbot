#!/usr/bin/env python3
"""
Backtesting Runner for Enhanced Multi-Strategy NIFTY Trading Bot

Run comprehensive backtests to evaluate and tune strategy performance.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
import yaml
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List

# Import our modules
from nifty500_symbols import get_symbol_list
from src.strategies.ema_crossover_strategy import EMACrossoverStrategy
from src.strategies.supertrend_strategy import SuperTrendStrategy
from src.strategies.multi_strategy_scorer import MultiStrategyScorer
from src.backtesting.backtest_engine import BacktestEngine, BacktestConfig, save_backtest_results
from src.visualization.chart_generator import ChartGenerator

# Import indicator calculations from main bot
from enhanced_multi_strategy_bot import (
    calculate_multiple_rsi, calculate_multiple_ema, 
    calculate_bollinger_bands, calculate_macd, generate_legacy_signal
)


def setup_logging(verbose=False):
    """Setup logging for backtesting."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('backtest.log')
        ]
    )
    return logging.getLogger(__name__)


def load_backtest_config(config_file: str = None) -> Dict:
    """Load backtesting configuration."""
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    # Default configuration
    return {
        'backtest': {
            'initial_capital': 1000000.0,  # 10 Lakh INR
            'position_size_percent': 5.0,
            'max_positions': 20,
            'commission_percent': 0.1,
            'slippage_percent': 0.05,
            'stop_loss_percent': 5.0,
            'take_profit_percent': 15.0,
            'max_holding_days': 30,
            'min_signal_confidence': 0.3,
            'min_composite_score': 30.0
        },
        'data': {
            'symbols_limit': 50,  # Limit for faster backtesting
            'start_date': '2020-01-01',
            'end_date': None,  # Use current date
            'min_data_threshold': 200
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
        }
    }


def fetch_historical_data(symbols: List[str], start_date: str, end_date: str = None, 
                         min_threshold: int = 500) -> Dict[str, pd.DataFrame]:
    """Fetch historical data for backtesting."""
    logger = logging.getLogger(__name__)
    data_dict = {}
    
    logger.info(f"Fetching data for {len(symbols)} symbols from {start_date} to {end_date or 'present'}")
    
    for i, symbol in enumerate(symbols, 1):
        try:
            logger.info(f"Fetching {symbol} ({i}/{len(symbols)})...")
            
            ticker = yf.Ticker(symbol)
            
            # Determine period
            if end_date:
                data = ticker.history(start=start_date, end=end_date)
            else:
                # Calculate period from start_date to now
                start_dt = pd.to_datetime(start_date)
                days_diff = (datetime.now() - start_dt).days
                
                if days_diff > 365 * 5:
                    period = "max"
                elif days_diff > 365 * 2:
                    period = "5y"
                elif days_diff > 365:
                    period = "2y"
                else:
                    period = "1y"
                
                data = ticker.history(period=period)
            
            if data.empty or len(data) < min_threshold:
                logger.warning(f"Insufficient data for {symbol}: {len(data)} records")
                continue
            
            # Filter by date range if specified
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            if len(data) < min_threshold:
                logger.warning(f"Insufficient data after date filtering for {symbol}: {len(data)} records")
                continue
            
            # Calculate indicators
            data = add_indicators(data)
            
            data_dict[symbol] = data
            logger.debug(f"Loaded {symbol}: {len(data)} records from {data.index[0]} to {data.index[-1]}")
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            continue
    
    logger.info(f"Successfully loaded data for {len(data_dict)} symbols")
    return data_dict


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to price data."""
    # RSI
    rsi_values = calculate_multiple_rsi(data['Close'])
    for key, values in rsi_values.items():
        data[key] = values
    
    # EMA
    ema_values = calculate_multiple_ema(data['Close'])
    for key, values in ema_values.items():
        data[key] = values
    
    # Bollinger Bands
    data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
    
    # MACD
    data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = calculate_macd(data['Close'])
    
    return data


def create_signal_generator(strategies: Dict, strategy_weights: Dict):
    """Create signal generator function for backtesting."""
    
    def generate_signals(data: pd.DataFrame) -> Dict:
        """Generate trading signals for given data."""
        try:
            # Generate legacy signal
            legacy_signal, legacy_score = generate_legacy_signal(data)
            
            # Generate strategy signals
            strategy_signals = []
            
            for strategy_name, strategy_config in strategies.items():
                if not strategy_config.get('enabled', True):
                    continue
                
                try:
                    if strategy_name == 'ema_crossover':
                        strategy = EMACrossoverStrategy(
                            short_period=strategy_config.get('short_period', 50),
                            long_period=strategy_config.get('long_period', 200),
                            approach_threshold=strategy_config.get('approach_threshold', 0.02)
                        )
                    elif strategy_name == 'supertrend':
                        strategy = SuperTrendStrategy(
                            atr_period=strategy_config.get('atr_period', 10),
                            multiplier=strategy_config.get('multiplier', 3.0)
                        )
                    else:
                        continue
                    
                    signal = strategy.generate_signal(data, {})
                    strategy_signals.append(signal)
                    
                except Exception as e:
                    logging.getLogger(__name__).debug(f"Strategy {strategy_name} failed: {e}")
                    continue
            
            # Generate composite signal
            composite_signal = None
            if strategy_signals:
                scorer = MultiStrategyScorer(strategy_weights)
                composite_signal = scorer.calculate_composite_score(strategy_signals, "BACKTEST")
            
            return {
                'legacy_signal': legacy_signal,
                'legacy_score': legacy_score,
                'composite_signal': composite_signal.signal_type.value if composite_signal else 'NO_SIGNAL',
                'composite_score': composite_signal.composite_score if composite_signal else 0.0,
                'composite_confidence': composite_signal.confidence if composite_signal else 0.0,
                'strategy_signals': {signal.strategy_name: {
                    'signal': signal.signal_type.value,
                    'confidence': signal.confidence
                } for signal in strategy_signals}
            }
            
        except Exception as e:
            logging.getLogger(__name__).debug(f"Error generating signals: {e}")
            return {
                'legacy_signal': 'NO_SIGNAL',
                'legacy_score': 0,
                'composite_signal': 'NO_SIGNAL',
                'composite_score': 0.0,
                'composite_confidence': 0.0,
                'strategy_signals': {}
            }
    
    return generate_signals


def run_parameter_optimization(data_dict: Dict[str, pd.DataFrame], base_config: Dict) -> Dict:
    """Run parameter optimization to find best strategy settings."""
    logger = logging.getLogger(__name__)
    logger.info("Starting parameter optimization...")
    
    # Parameter ranges to test
    param_ranges = {
        'ema_crossover': {
            'short_period': [20, 50, 100],
            'long_period': [100, 200, 300],
            'approach_threshold': [0.01, 0.02, 0.05]
        },
        'supertrend': {
            'atr_period': [7, 10, 14],
            'multiplier': [2.0, 3.0, 4.0]
        },
        'backtest': {
            'stop_loss_percent': [3.0, 5.0, 8.0],
            'take_profit_percent': [10.0, 15.0, 20.0],
            'position_size_percent': [3.0, 5.0, 8.0]
        }
    }
    
    best_result = None
    best_params = None
    best_return = -float('inf')
    
    # Test different parameter combinations (simplified for demo)
    test_combinations = [
        # EMA periods
        {'ema_crossover': {'short_period': 50, 'long_period': 200}, 'supertrend': {'atr_period': 10, 'multiplier': 3.0}},
        {'ema_crossover': {'short_period': 20, 'long_period': 100}, 'supertrend': {'atr_period': 7, 'multiplier': 2.0}},
        {'ema_crossover': {'short_period': 100, 'long_period': 300}, 'supertrend': {'atr_period': 14, 'multiplier': 4.0}},
    ]
    
    for i, params in enumerate(test_combinations, 1):
        logger.info(f"Testing parameter set {i}/{len(test_combinations)}: {params}")
        
        try:
            # Update configuration
            test_config = base_config.copy()
            test_config['strategies'].update(params)
            
            # Create strategies
            strategies = {}
            strategy_weights = {}
            
            if test_config['strategies']['ema_crossover']['enabled']:
                ema_config = test_config['strategies']['ema_crossover']
                strategies['ema_crossover'] = EMACrossoverStrategy(
                    short_period=ema_config.get('short_period', 50),
                    long_period=ema_config.get('long_period', 200),
                    approach_threshold=ema_config.get('approach_threshold', 0.02)
                )
                strategy_weights['ema_crossover'] = ema_config.get('weight', 1.5)
            
            if test_config['strategies']['supertrend']['enabled']:
                st_config = test_config['strategies']['supertrend']
                strategies['supertrend'] = SuperTrendStrategy(
                    atr_period=st_config.get('atr_period', 10),
                    multiplier=st_config.get('multiplier', 3.0)
                )
                strategy_weights['supertrend'] = st_config.get('weight', 1.2)
            
            # Run backtest
            signal_generator = create_signal_generator(test_config['strategies'], strategy_weights)
            
            backtest_config = BacktestConfig(
                initial_capital=test_config['backtest']['initial_capital'],
                position_size_percent=test_config['backtest']['position_size_percent'],
                max_positions=test_config['backtest']['max_positions'],
                stop_loss_percent=test_config['backtest']['stop_loss_percent'],
                take_profit_percent=test_config['backtest']['take_profit_percent'],
                min_composite_score=test_config['backtest']['min_composite_score']
            )
            
            engine = BacktestEngine(backtest_config)
            result = engine.run_backtest(
                data_dict, 
                signal_generator,
                test_config['data']['start_date']
            )
            
            logger.info(f"Result: {result.total_return_percent:.2f}% return, "
                       f"{result.win_rate:.1f}% win rate, {result.total_trades} trades")
            
            # Check if this is the best result
            if result.total_return_percent > best_return:
                best_return = result.total_return_percent
                best_result = result
                best_params = params
                
        except Exception as e:
            logger.error(f"Error testing parameters {params}: {e}")
            continue
    
    logger.info(f"Best parameters found: {best_params}")
    logger.info(f"Best return: {best_return:.2f}%")
    
    return {
        'best_params': best_params,
        'best_result': best_result,
        'best_return': best_return
    }


def generate_backtest_report(results, output_dir: str = "output/backtests"):
    """Generate comprehensive backtest report."""
    logger = logging.getLogger(__name__)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    results_file = save_backtest_results(results, output_dir)
    
    # Generate performance charts
    chart_gen = ChartGenerator(output_path)
    
    try:
        # Equity curve chart
        import matplotlib.pyplot as plt
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Equity curve
        ax1.plot(results.equity_curve.index, results.equity_curve.values, 
                linewidth=2, color='blue', label='Portfolio Value')
        ax1.axhline(y=results.initial_capital, color='red', linestyle='--', 
                   alpha=0.7, label='Initial Capital')
        ax1.set_title("Equity Curve", fontsize=14, fontweight='bold')
        ax1.set_ylabel("Portfolio Value (₹)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        peak = results.equity_curve.expanding().max()
        drawdown = (results.equity_curve - peak) / peak * 100
        ax2.fill_between(drawdown.index, drawdown.values, 0, 
                        color='red', alpha=0.3, label='Drawdown')
        ax2.set_title("Drawdown", fontsize=14, fontweight='bold')
        ax2.set_ylabel("Drawdown (%)")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Monthly returns
        monthly_returns = results.equity_curve.resample('M').last().pct_change().dropna() * 100
        colors = ['green' if x > 0 else 'red' for x in monthly_returns]
        ax3.bar(range(len(monthly_returns)), monthly_returns.values, color=colors, alpha=0.7)
        ax3.set_title("Monthly Returns", fontsize=14, fontweight='bold')
        ax3.set_ylabel("Return (%)")
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax3.grid(True, alpha=0.3)
        
        # Trade distribution
        if results.trades:
            trade_returns = [t.pnl_percent for t in results.trades]
            ax4.hist(trade_returns, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7)
            ax4.set_title("Trade Return Distribution", fontsize=14, fontweight='bold')
            ax4.set_xlabel("Return (%)")
            ax4.set_ylabel("Frequency")
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        chart_file = output_path / f"backtest_performance_{timestamp}.png"
        plt.savefig(chart_file, dpi=100, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Performance chart saved: {chart_file}")
        
    except Exception as e:
        logger.error(f"Error generating performance charts: {e}")
    
    # Generate summary report
    report_file = output_path / f"backtest_summary_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("ENHANCED MULTI-STRATEGY NIFTY TRADING BOT - BACKTEST REPORT\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Backtest Period: {results.start_date} to {results.end_date}\n")
        f.write(f"Initial Capital: ₹{results.initial_capital:,.2f}\n")
        f.write(f"Final Capital: ₹{results.final_capital:,.2f}\n\n")
        
        f.write("PERFORMANCE METRICS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Return: ₹{results.total_return:,.2f} ({results.total_return_percent:.2f}%)\n")
        f.write(f"Annualized Return: {results.annualized_return:.2f}%\n")
        f.write(f"Maximum Drawdown: {results.max_drawdown:.2f}%\n")
        f.write(f"Sharpe Ratio: {results.sharpe_ratio:.2f}\n")
        f.write(f"Sortino Ratio: {results.sortino_ratio:.2f}\n\n")
        
        f.write("TRADE STATISTICS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Trades: {results.total_trades}\n")
        f.write(f"Winning Trades: {results.winning_trades}\n")
        f.write(f"Losing Trades: {results.losing_trades}\n")
        f.write(f"Win Rate: {results.win_rate:.1f}%\n")
        f.write(f"Profit Factor: {results.profit_factor:.2f}\n")
        f.write(f"Average Win: ₹{results.avg_win:.2f}\n")
        f.write(f"Average Loss: ₹{results.avg_loss:.2f}\n")
        f.write(f"Average Holding Days: {results.avg_holding_days:.1f}\n\n")
        
        if results.trades:
            f.write("TOP 10 BEST TRADES\n")
            f.write("-" * 30 + "\n")
            best_trades = sorted(results.trades, key=lambda x: x.pnl_percent, reverse=True)[:10]
            for i, trade in enumerate(best_trades, 1):
                f.write(f"{i:2d}. {trade.symbol:12s} {trade.entry_date.strftime('%Y-%m-%d')} "
                       f"₹{trade.pnl:8.2f} ({trade.pnl_percent:6.2f}%) {trade.holding_days:3d} days\n")
            
            f.write("\nTOP 10 WORST TRADES\n")
            f.write("-" * 30 + "\n")
            worst_trades = sorted(results.trades, key=lambda x: x.pnl_percent)[:10]
            for i, trade in enumerate(worst_trades, 1):
                f.write(f"{i:2d}. {trade.symbol:12s} {trade.entry_date.strftime('%Y-%m-%d')} "
                       f"₹{trade.pnl:8.2f} ({trade.pnl_percent:6.2f}%) {trade.holding_days:3d} days\n")
    
    logger.info(f"Backtest report saved: {report_file}")
    
    return {
        'results_file': results_file,
        'chart_file': str(chart_file) if 'chart_file' in locals() else None,
        'report_file': str(report_file)
    }


def main():
    """Main backtesting function."""
    parser = argparse.ArgumentParser(description="Enhanced Multi-Strategy NIFTY Trading Bot Backtester")
    parser.add_argument("--config", type=str, help="Configuration file")
    parser.add_argument("--symbols", type=int, default=50, help="Number of symbols to test (default: 50)")
    parser.add_argument("--start-date", type=str, default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--optimize", action="store_true", help="Run parameter optimization")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--size", choices=["nifty50", "nifty100", "nifty500"], 
                       default="nifty50", help="NIFTY index size")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    print("Enhanced Multi-Strategy NIFTY Trading Bot - Backtester")
    print("=" * 60)
    print(f"Start Date: {args.start_date}")
    print(f"End Date: {args.end_date or 'Present'}")
    print(f"Symbols: {args.symbols} from {args.size.upper()}")
    
    # Load configuration
    config = load_backtest_config(args.config)
    config['data']['start_date'] = args.start_date
    if args.end_date:
        config['data']['end_date'] = args.end_date
    
    # Get symbols
    all_symbols = get_symbol_list(args.size)
    symbols = all_symbols[:args.symbols]
    
    print(f"Selected symbols: {len(symbols)}")
    
    # Fetch data
    logger.info("Fetching historical data...")
    data_dict = fetch_historical_data(
        symbols, 
        config['data']['start_date'], 
        config['data'].get('end_date'),
        config['data']['min_data_threshold']
    )
    
    if len(data_dict) < 3:
        logger.error("Insufficient data loaded. Need at least 3 symbols for backtesting.")
        return 1
    
    print(f"Data loaded for {len(data_dict)} symbols")
    
    # Run optimization if requested
    if args.optimize:
        logger.info("Running parameter optimization...")
        optimization_results = run_parameter_optimization(data_dict, config)
        
        if optimization_results['best_params']:
            config['strategies'].update(optimization_results['best_params'])
            logger.info(f"Using optimized parameters: {optimization_results['best_params']}")
    
    # Setup strategies
    strategies = {}
    strategy_weights = {}
    
    if config['strategies']['ema_crossover']['enabled']:
        ema_config = config['strategies']['ema_crossover']
        strategies['ema_crossover'] = EMACrossoverStrategy(
            short_period=ema_config.get('short_period', 50),
            long_period=ema_config.get('long_period', 200),
            approach_threshold=ema_config.get('approach_threshold', 0.02)
        )
        strategy_weights['ema_crossover'] = ema_config.get('weight', 1.5)
    
    if config['strategies']['supertrend']['enabled']:
        st_config = config['strategies']['supertrend']
        strategies['supertrend'] = SuperTrendStrategy(
            atr_period=st_config.get('atr_period', 10),
            multiplier=st_config.get('multiplier', 3.0)
        )
        strategy_weights['supertrend'] = st_config.get('weight', 1.2)
    
    print(f"Enabled strategies: {list(strategies.keys())}")
    
    # Create signal generator
    signal_generator = create_signal_generator(config['strategies'], strategy_weights)
    
    # Setup backtest engine
    backtest_config = BacktestConfig(
        initial_capital=config['backtest']['initial_capital'],
        position_size_percent=config['backtest']['position_size_percent'],
        max_positions=config['backtest']['max_positions'],
        commission_percent=config['backtest']['commission_percent'],
        slippage_percent=config['backtest']['slippage_percent'],
        stop_loss_percent=config['backtest']['stop_loss_percent'],
        take_profit_percent=config['backtest']['take_profit_percent'],
        max_holding_days=config['backtest']['max_holding_days'],
        min_signal_confidence=config['backtest']['min_signal_confidence'],
        min_composite_score=config['backtest']['min_composite_score']
    )
    
    # Run backtest
    logger.info("Starting backtest...")
    engine = BacktestEngine(backtest_config)
    
    results = engine.run_backtest(
        data_dict, 
        signal_generator,
        config['data']['start_date'],
        config['data'].get('end_date')
    )
    
    # Generate report
    logger.info("Generating backtest report...")
    report_files = generate_backtest_report(results)
    
    # Print summary
    print("\nBACKTEST RESULTS SUMMARY")
    print("=" * 40)
    print(f"Total Return: ₹{results.total_return:,.2f} ({results.total_return_percent:.2f}%)")
    print(f"Annualized Return: {results.annualized_return:.2f}%")
    print(f"Maximum Drawdown: {results.max_drawdown:.2f}%")
    print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
    print(f"Win Rate: {results.win_rate:.1f}%")
    print(f"Total Trades: {results.total_trades}")
    print(f"Profit Factor: {results.profit_factor:.2f}")
    
    print(f"\nReports saved:")
    for file_type, file_path in report_files.items():
        if file_path:
            print(f"  {file_type}: {file_path}")
    
    return 0


if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nBacktest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)