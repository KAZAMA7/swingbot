#!/usr/bin/env python3
"""
Database Update Script for Enhanced Multi-Strategy NIFTY Trading Bot

Updates the database schema and populates it with enhanced multi-strategy data.
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import yfinance as yf
from typing import Dict, List, Optional

# Import our modules
from nifty500_symbols import get_symbol_list
from src.strategies.ema_crossover_strategy import EMACrossoverStrategy
from src.strategies.supertrend_strategy import SuperTrendStrategy
from src.strategies.multi_strategy_scorer import MultiStrategyScorer
from enhanced_multi_strategy_bot import (
    calculate_multiple_rsi, calculate_multiple_ema, 
    calculate_bollinger_bands, calculate_macd, generate_legacy_signal
)


def setup_logging():
    """Setup logging for database update."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('database_update.log')
        ]
    )
    return logging.getLogger(__name__)


class DatabaseUpdater:
    """Updates the trading database with enhanced multi-strategy data."""
    
    def __init__(self, db_path: str = "DBs/nifty500_trading_data.db"):
        """Initialize database updater."""
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategies
        self.ema_strategy = EMACrossoverStrategy(short_period=50, long_period=200)
        self.supertrend_strategy = SuperTrendStrategy(atr_period=10, multiplier=3.0)
        self.scorer = MultiStrategyScorer({
            'ema_crossover': 1.5,
            'supertrend': 1.2,
            'legacy': 1.0
        })
    
    def update_database_schema(self):
        """Update database schema with new tables for enhanced strategies."""
        self.logger.info("Updating database schema...")
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Add new tables for enhanced strategies
                
                # Enhanced signals table with more detailed information
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS enhanced_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        composite_signal TEXT NOT NULL,
                        composite_score REAL NOT NULL,
                        composite_confidence REAL NOT NULL,
                        legacy_signal TEXT,
                        legacy_score INTEGER,
                        strategy_signals TEXT,  -- JSON of individual strategy signals
                        price REAL NOT NULL,
                        price_change REAL,
                        price_change_percent REAL,
                        data_quality TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Strategy performance tracking
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS strategy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_name TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        signal_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        entry_price REAL,
                        exit_price REAL,
                        pnl REAL,
                        pnl_percent REAL,
                        holding_days INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Enhanced indicators with strategy-specific data
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS enhanced_indicators (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        ema_50 REAL,
                        ema_200 REAL,
                        ema_crossover_signal TEXT,
                        ema_crossover_confidence REAL,
                        supertrend_value REAL,
                        supertrend_direction INTEGER,
                        supertrend_signal TEXT,
                        supertrend_confidence REAL,
                        rsi_14 REAL,
                        rsi_21 REAL,
                        rsi_50 REAL,
                        bb_upper REAL,
                        bb_middle REAL,
                        bb_lower REAL,
                        macd REAL,
                        macd_signal REAL,
                        macd_histogram REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timestamp)
                    )
                """)
                
                # Backtest results storage
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backtest_name TEXT NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        initial_capital REAL NOT NULL,
                        final_capital REAL NOT NULL,
                        total_return REAL NOT NULL,
                        total_return_percent REAL NOT NULL,
                        annualized_return REAL NOT NULL,
                        max_drawdown REAL NOT NULL,
                        sharpe_ratio REAL NOT NULL,
                        win_rate REAL NOT NULL,
                        total_trades INTEGER NOT NULL,
                        strategy_config TEXT,  -- JSON of strategy configuration
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_signals_symbol_timestamp ON enhanced_signals(symbol, timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_performance_symbol_timestamp ON strategy_performance(symbol, timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_indicators_symbol_timestamp ON enhanced_indicators(symbol, timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_results_name ON backtest_results(backtest_name)")
                
                conn.commit()
                
            self.logger.info("Database schema updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update database schema: {e}")
            raise
    
    def populate_enhanced_indicators(self, symbols: List[str], limit_per_symbol: int = 1000):
        """Populate enhanced indicators for given symbols."""
        self.logger.info(f"Populating enhanced indicators for {len(symbols)} symbols...")
        
        total_processed = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.logger.info(f"Processing {symbol} ({i}/{len(symbols)})...")
                
                # Get existing price data from database
                price_data = self._get_price_data_from_db(symbol, limit_per_symbol)
                
                if len(price_data) < 200:  # Need enough data for indicators
                    self.logger.warning(f"Insufficient data for {symbol}: {len(price_data)} records")
                    continue
                
                # Calculate all indicators
                indicators_data = self._calculate_all_indicators(symbol, price_data)
                
                # Store enhanced indicators
                self._store_enhanced_indicators(symbol, indicators_data)
                
                total_processed += 1
                
                if total_processed % 10 == 0:
                    self.logger.info(f"Processed {total_processed} symbols so far...")
                    
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
        
        self.logger.info(f"Enhanced indicators populated for {total_processed} symbols")
    
    def populate_enhanced_signals(self, symbols: List[str]):
        """Generate and store enhanced multi-strategy signals."""
        self.logger.info(f"Generating enhanced signals for {len(symbols)} symbols...")
        
        signals_generated = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.logger.info(f"Generating signals for {symbol} ({i}/{len(symbols)})...")
                
                # Get recent price data
                price_data = self._get_price_data_from_db(symbol, 500)
                
                if len(price_data) < 200:
                    self.logger.warning(f"Insufficient data for {symbol}")
                    continue
                
                # Generate signals using our enhanced strategies
                signal_data = self._generate_enhanced_signals(symbol, price_data)
                
                if signal_data:
                    self._store_enhanced_signal(signal_data)
                    signals_generated += 1
                
            except Exception as e:
                self.logger.error(f"Error generating signals for {symbol}: {e}")
                continue
        
        self.logger.info(f"Generated {signals_generated} enhanced signals")
    
    def _get_price_data_from_db(self, symbol: str, limit: int) -> pd.DataFrame:
        """Get price data from database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                query = """
                    SELECT timestamp, open, high, low, close, volume
                    FROM price_data 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(symbol, limit))
                
                if df.empty:
                    return df
                
                # Convert timestamp and set as index
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)  # Sort chronologically
                
                # Rename columns to match yfinance format
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting price data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _calculate_all_indicators(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Calculate all technical indicators for the data."""
        try:
            # Calculate RSI
            rsi_values = calculate_multiple_rsi(data['Close'])
            
            # Calculate EMAs
            ema_values = calculate_multiple_ema(data['Close'])
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(data['Close'])
            
            # Calculate MACD
            macd, macd_signal, macd_histogram = calculate_macd(data['Close'])
            
            # Generate strategy signals
            ema_signal = self.ema_strategy.generate_signal(data, {})
            supertrend_signal = self.supertrend_strategy.generate_signal(data, {})
            
            # Get the latest values
            latest_idx = data.index[-1]
            
            return {
                'timestamp': latest_idx,
                'ema_50': ema_values.get('EMA_50', pd.Series()).iloc[-1] if not ema_values.get('EMA_50', pd.Series()).empty else None,
                'ema_200': ema_values.get('EMA_200', pd.Series()).iloc[-1] if not ema_values.get('EMA_200', pd.Series()).empty else None,
                'ema_crossover_signal': ema_signal.signal_type.value if ema_signal else 'NO_SIGNAL',
                'ema_crossover_confidence': ema_signal.confidence if ema_signal else 0.0,
                'supertrend_signal': supertrend_signal.signal_type.value if supertrend_signal else 'NO_SIGNAL',
                'supertrend_confidence': supertrend_signal.confidence if supertrend_signal else 0.0,
                'rsi_14': rsi_values.get('RSI_14', pd.Series()).iloc[-1] if not rsi_values.get('RSI_14', pd.Series()).empty else None,
                'rsi_21': rsi_values.get('RSI_21', pd.Series()).iloc[-1] if not rsi_values.get('RSI_21', pd.Series()).empty else None,
                'rsi_50': rsi_values.get('RSI_50', pd.Series()).iloc[-1] if not rsi_values.get('RSI_50', pd.Series()).empty else None,
                'bb_upper': bb_upper.iloc[-1] if not bb_upper.empty else None,
                'bb_middle': bb_middle.iloc[-1] if not bb_middle.empty else None,
                'bb_lower': bb_lower.iloc[-1] if not bb_lower.empty else None,
                'macd': macd.iloc[-1] if not macd.empty else None,
                'macd_signal': macd_signal.iloc[-1] if not macd_signal.empty else None,
                'macd_histogram': macd_histogram.iloc[-1] if not macd_histogram.empty else None,
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")
            return {}
    
    def _generate_enhanced_signals(self, symbol: str, data: pd.DataFrame) -> Optional[Dict]:
        """Generate enhanced multi-strategy signals."""
        try:
            # Generate legacy signal
            legacy_signal, legacy_score = generate_legacy_signal(data)
            
            # Generate strategy signals
            strategy_signals = []
            
            ema_signal = self.ema_strategy.generate_signal(data, {})
            if ema_signal:
                strategy_signals.append(ema_signal)
            
            supertrend_signal = self.supertrend_strategy.generate_signal(data, {})
            if supertrend_signal:
                strategy_signals.append(supertrend_signal)
            
            # Generate composite signal
            composite_signal = None
            if strategy_signals:
                composite_signal = self.scorer.calculate_composite_score(strategy_signals, symbol)
            
            if not composite_signal:
                return None
            
            # Get current price info
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            price_change = current_price - prev_price
            price_change_percent = (price_change / prev_price * 100) if prev_price != 0 else 0
            
            return {
                'symbol': symbol,
                'timestamp': data.index[-1],
                'composite_signal': composite_signal.signal_type.value,
                'composite_score': composite_signal.composite_score,
                'composite_confidence': composite_signal.confidence,
                'legacy_signal': legacy_signal,
                'legacy_score': legacy_score,
                'strategy_signals': json.dumps({
                    signal.strategy_name: {
                        'signal': signal.signal_type.value,
                        'confidence': signal.confidence
                    } for signal in strategy_signals
                }),
                'price': current_price,
                'price_change': price_change,
                'price_change_percent': price_change_percent,
                'data_quality': f"{len(data)} records"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            return None
    
    def _store_enhanced_indicators(self, symbol: str, indicators_data: Dict):
        """Store enhanced indicators in database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO enhanced_indicators 
                    (symbol, timestamp, ema_50, ema_200, ema_crossover_signal, ema_crossover_confidence,
                     supertrend_signal, supertrend_confidence, rsi_14, rsi_21, rsi_50,
                     bb_upper, bb_middle, bb_lower, macd, macd_signal, macd_histogram)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    indicators_data['timestamp'].isoformat(),
                    indicators_data.get('ema_50'),
                    indicators_data.get('ema_200'),
                    indicators_data.get('ema_crossover_signal'),
                    indicators_data.get('ema_crossover_confidence'),
                    indicators_data.get('supertrend_signal'),
                    indicators_data.get('supertrend_confidence'),
                    indicators_data.get('rsi_14'),
                    indicators_data.get('rsi_21'),
                    indicators_data.get('rsi_50'),
                    indicators_data.get('bb_upper'),
                    indicators_data.get('bb_middle'),
                    indicators_data.get('bb_lower'),
                    indicators_data.get('macd'),
                    indicators_data.get('macd_signal'),
                    indicators_data.get('macd_histogram')
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing indicators for {symbol}: {e}")
    
    def _store_enhanced_signal(self, signal_data: Dict):
        """Store enhanced signal in database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO enhanced_signals 
                    (symbol, timestamp, composite_signal, composite_score, composite_confidence,
                     legacy_signal, legacy_score, strategy_signals, price, price_change, 
                     price_change_percent, data_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_data['symbol'],
                    signal_data['timestamp'].isoformat(),
                    signal_data['composite_signal'],
                    signal_data['composite_score'],
                    signal_data['composite_confidence'],
                    signal_data['legacy_signal'],
                    signal_data['legacy_score'],
                    signal_data['strategy_signals'],
                    signal_data['price'],
                    signal_data['price_change'],
                    signal_data['price_change_percent'],
                    signal_data['data_quality']
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing signal for {signal_data['symbol']}: {e}")
    
    def get_database_stats(self):
        """Get current database statistics."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                stats = {}
                
                # Get table counts
                tables = ['price_data', 'signals', 'indicators', 'enhanced_signals', 
                         'enhanced_indicators', 'strategy_performance', 'backtest_results']
                
                for table in tables:
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = cursor.fetchone()[0]
                    except sqlite3.OperationalError:
                        stats[table] = 0  # Table doesn't exist yet
                
                # Get unique symbols
                cursor = conn.execute("SELECT COUNT(DISTINCT symbol) FROM price_data")
                stats['unique_symbols'] = cursor.fetchone()[0]
                
                # Get date range
                cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_data")
                date_range = cursor.fetchone()
                stats['date_range'] = f"{date_range[0]} to {date_range[1]}"
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_signals(self, days_to_keep: int = 30):
        """Clean up old signals to prevent database bloat."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Keep only recent enhanced signals
                conn.execute("""
                    DELETE FROM enhanced_signals 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                # Keep only recent regular signals
                conn.execute("""
                    DELETE FROM signals 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                conn.commit()
                
            self.logger.info(f"Cleaned up signals older than {days_to_keep} days")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old signals: {e}")


def main():
    """Main function to update the database."""
    logger = setup_logging()
    
    print("Enhanced Multi-Strategy NIFTY Trading Bot - Database Update")
    print("=" * 60)
    
    # Initialize database updater
    updater = DatabaseUpdater()
    
    # Show current database stats
    print("\nCurrent Database Statistics:")
    stats = updater.get_database_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Update database schema
    print("\n1. Updating database schema...")
    updater.update_database_schema()
    
    # Get symbols to process
    print("\n2. Getting symbols to process...")
    all_symbols = get_symbol_list("nifty500")
    
    # Ask user what to update
    print(f"\nFound {len(all_symbols)} symbols in NIFTY 500")
    print("\nWhat would you like to update?")
    print("1. Update indicators for all symbols (recommended)")
    print("2. Update indicators for top 50 symbols (faster)")
    print("3. Generate new signals only")
    print("4. Full update (indicators + signals)")
    print("5. Show database stats only")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        print("\n3. Updating indicators for all symbols...")
        updater.populate_enhanced_indicators(all_symbols)
        
    elif choice == "2":
        print("\n3. Updating indicators for top 50 symbols...")
        updater.populate_enhanced_indicators(all_symbols[:50])
        
    elif choice == "3":
        print("\n3. Generating new signals...")
        updater.populate_enhanced_signals(all_symbols[:100])  # Limit for performance
        
    elif choice == "4":
        print("\n3. Full update - updating indicators...")
        updater.populate_enhanced_indicators(all_symbols[:100])  # Limit for performance
        print("\n4. Generating signals...")
        updater.populate_enhanced_signals(all_symbols[:100])
        
    elif choice == "5":
        print("\nDatabase statistics shown above.")
        
    else:
        print("Invalid choice. Exiting.")
        return
    
    # Clean up old data
    if choice in ["1", "2", "3", "4"]:
        print("\n5. Cleaning up old signals...")
        updater.cleanup_old_signals(30)
    
    # Show updated stats
    print("\nUpdated Database Statistics:")
    stats = updater.get_database_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Database update completed successfully!")
    print(f"📊 Database location: {updater.db_path}")
    print("📈 Ready for enhanced multi-strategy analysis!")


if __name__ == "__main__":
    main()