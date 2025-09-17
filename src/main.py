#!/usr/bin/env python3
"""
Stock Trading Bot - Main Entry Point

A cross-platform stock swing trading bot that fetches market data,
performs technical analysis, and generates trading signals.
"""

import argparse
import sys
import logging
from pathlib import Path

from config.config_manager import ConfigManager
from data.database import DatabaseManager
from data.data_manager import DataManager
from data.yahoo_finance_fetcher import YahooFinanceFetcher
from analysis.analysis_engine import AnalysisEngine
from signals.signal_generator import SignalGenerator
from scheduler.scheduler import TradingScheduler
from models.exceptions import TradingBotError


class TradingBot:
    """Main trading bot application."""
    
    def __init__(self, config_path: str = None, verbose: bool = False):
        """
        Initialize trading bot.
        
        Args:
            config_path: Path to configuration file
            verbose: Enable verbose logging
        """
        self.setup_logging(verbose)
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize configuration
            self.config_manager = ConfigManager(config_path)
            self.config = self.config_manager.load_config()
            
            # Initialize database
            db_path = self.config.get('output', {}).get('database', 'trading_data.db')
            self.db_manager = DatabaseManager(db_path)
            
            # Initialize data manager (handles comprehensive data operations)
            self.data_manager = DataManager(self.config, self.db_manager)
            
            # Keep data fetcher for backward compatibility
            rate_limit = self.config.get('data_sources', {}).get('yahoo_finance', {}).get('rate_limit', 5)
            self.data_fetcher = YahooFinanceFetcher(rate_limit)
            
            # Initialize analysis engine
            self.analysis_engine = AnalysisEngine(self.config)
            
            # Initialize signal generator
            self.signal_generator = SignalGenerator(self.config, self.db_manager)
            
            # Initialize scheduler
            self.scheduler = TradingScheduler(self.config)
            self.scheduler.set_update_callback(self.update_all_symbols)
            
            self.logger.info("Trading bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize trading bot: {e}")
            raise TradingBotError(f"Initialization failed: {e}")
    
    def setup_logging(self, verbose: bool = False):
        """Setup logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('trading_bot.log')
            ]
        )
    
    def update_all_symbols(self):
        """Update all symbols in watchlist."""
        try:
            watchlist = self.config_manager.get_watchlist()
            self.logger.info(f"Processing {len(watchlist)} symbols: {watchlist}")
            
            results = {
                'processed_symbols': 0,
                'signals_generated': 0,
                'errors': 0
            }
            
            for symbol in watchlist:
                try:
                    # Use enhanced data manager for comprehensive data handling
                    self.logger.debug(f"Initializing comprehensive data for {symbol}")
                    historical_data = self.data_manager.initialize_symbol_data(symbol)
                    
                    if historical_data.empty:
                        self.logger.warning(f"No data available for {symbol}")
                        continue
                    
                    # Log data summary
                    summary = self.data_manager.get_data_summary(symbol)
                    self.logger.info(f"{symbol}: {summary['records']} records from {summary.get('date_range', {}).get('start', 'N/A')} to {summary.get('date_range', {}).get('end', 'N/A')}")
                    
                    # Perform technical analysis
                    self.logger.debug(f"Analyzing {symbol}")
                    indicators = self.analysis_engine.analyze_symbol(symbol, historical_data)
                    
                    if not indicators:
                        self.logger.warning(f"No indicators calculated for {symbol}")
                        continue
                    
                    # Generate signal
                    self.logger.debug(f"Generating signal for {symbol}")
                    signal = self.signal_generator.process_symbol(symbol, historical_data, indicators)
                    
                    results['processed_symbols'] += 1
                    if signal.signal_type.value != 'NO_SIGNAL':
                        results['signals_generated'] += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}")
                    results['errors'] += 1
                    continue
            
            self.logger.info(f"Update completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return {'error': str(e)}
    
    def run_manual_update(self):
        """Run manual update."""
        try:
            self.logger.info("Starting manual update...")
            result = self.update_all_symbols()
            self.logger.info("Manual update completed")
            return result
        except Exception as e:
            self.logger.error(f"Manual update failed: {e}")
            raise
    
    def run_scheduled_mode(self):
        """Run in scheduled mode."""
        try:
            self.logger.info("Starting scheduled mode...")
            self.scheduler.start_scheduled_mode()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.scheduler.stop()
        except Exception as e:
            self.logger.error(f"Scheduled mode failed: {e}")
            raise
    
    def test_connection(self):
        """Test connection to data source."""
        try:
            self.logger.info("Testing connection to Yahoo Finance...")
            if self.data_fetcher.test_connection():
                self.logger.info("Connection test successful")
                return True
            else:
                self.logger.error("Connection test failed")
                return False
        except Exception as e:
            self.logger.error(f"Connection test error: {e}")
            return False
    
    def check_data_availability(self, symbols: List[str] = None):
        """
        Check data availability for symbols.
        
        Args:
            symbols: List of symbols to check (uses watchlist if None)
        """
        try:
            if symbols is None:
                symbols = self.config_manager.get_watchlist()
            
            self.logger.info("Checking data availability...")
            
            for symbol in symbols:
                self.logger.info(f"Checking {symbol}...")
                
                # Check what's available from Yahoo Finance
                availability = self.data_manager.check_data_availability(symbol)
                
                if 'error' in availability:
                    self.logger.error(f"{symbol}: {availability['error']}")
                    continue
                
                # Check existing data
                summary = self.data_manager.get_data_summary(symbol)
                
                print(f"\n{symbol} Data Availability:")
                print(f"  Max available records: {availability['max_records']}")
                print(f"  Recommended period: {availability['recommended_period']}")
                
                if availability['available_periods'].get('max'):
                    max_data = availability['available_periods']['max']
                    print(f"  Full history: {max_data['records']} records ({max_data['start_date']} to {max_data['end_date']})")
                
                if summary['status'] == 'data_available':
                    print(f"  Local database: {summary['records']} records ({summary['date_range']['start']} to {summary['date_range']['end']})")
                    print(f"  Last update: {summary['last_update']}")
                else:
                    print(f"  Local database: No data stored")
                
        except Exception as e:
            self.logger.error(f"Data availability check failed: {e}")
    
    def initialize_all_data(self, force_refresh: bool = False):
        """
        Initialize comprehensive data for all watchlist symbols.
        
        Args:
            force_refresh: Force complete data refresh
        """
        try:
            watchlist = self.config_manager.get_watchlist()
            self.logger.info(f"Initializing comprehensive data for {len(watchlist)} symbols...")
            
            results = self.data_manager.bulk_initialize(watchlist, force_refresh)
            
            print(f"\nData Initialization Results:")
            print(f"  Initialized: {results['initialized']} symbols")
            print(f"  Updated: {results['updated']} symbols") 
            print(f"  Errors: {results['errors']} symbols")
            
            # Show details for each symbol
            for symbol, details in results['details'].items():
                if details['status'] == 'data_available':
                    print(f"  {symbol}: {details['records']} records ({details['date_range']['start']} to {details['date_range']['end']})")
                elif details['status'] == 'error':
                    print(f"  {symbol}: ERROR - {details['error']}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Data initialization failed: {e}")
            raise


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Stock Trading Bot - Automated swing trading signals"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--manual", 
        action="store_true",
        help="Run manual update instead of scheduled mode"
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test connection and exit"
    )
    parser.add_argument(
        "--check-data", 
        action="store_true",
        help="Check data availability for all symbols"
    )
    parser.add_argument(
        "--init-data", 
        action="store_true",
        help="Initialize comprehensive historical data for all symbols"
    )
    parser.add_argument(
        "--force-refresh", 
        action="store_true",
        help="Force complete data refresh (use with --init-data)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main application entry point."""
    try:
        args = parse_arguments()
        
        print("Stock Trading Bot starting...")
        print(f"Configuration file: {args.config}")
        print(f"Manual mode: {args.manual}")
        print(f"Test mode: {args.test}")
        print(f"Verbose logging: {args.verbose}")
        
        # Initialize trading bot
        bot = TradingBot(args.config, args.verbose)
        
        # Test connection if requested
        if args.test:
            if bot.test_connection():
                print("Connection test passed!")
                return 0
            else:
                print("Connection test failed!")
                return 1
        
        # Check data availability if requested
        if args.check_data:
            bot.check_data_availability()
            return 0
        
        # Initialize data if requested
        if args.init_data:
            bot.initialize_all_data(args.force_refresh)
            return 0
        
        # Run in appropriate mode
        if args.manual:
            result = bot.run_manual_update()
            print(f"Manual update completed: {result}")
        else:
            bot.run_scheduled_mode()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())