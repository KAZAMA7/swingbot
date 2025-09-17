"""
Database Management

Handles SQLite database operations for storing market data, indicators, and signals.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from ..models.data_models import OHLCV, Signal, IndicatorValue, SignalType
from ..models.exceptions import DatabaseError


class DatabaseManager:
    """Manages SQLite database operations."""
    
    def __init__(self, db_path: str = "trading_data.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as conn:
                self._create_tables(conn)
                
            self.logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection with automatic cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables."""
        
        # Price data table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timestamp)
            )
        """)
        
        # Indicators table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL NOT NULL,
                parameters TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timestamp, indicator_name)
            )
        """)
        
        # Signals table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                indicators TEXT,
                strategy_name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System log table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                component TEXT,
                details TEXT
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol_timestamp ON price_data(symbol, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_indicators_symbol_timestamp ON indicators(symbol, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON signals(symbol, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_system_log_timestamp ON system_log(timestamp)")
        
        conn.commit()
    
    def store_price_data(self, ohlcv_data: List[OHLCV]):
        """
        Store OHLCV price data.
        
        Args:
            ohlcv_data: List of OHLCV data objects
        """
        try:
            with self.get_connection() as conn:
                for data in ohlcv_data:
                    conn.execute("""
                        INSERT OR REPLACE INTO price_data 
                        (symbol, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data.symbol,
                        data.timestamp,
                        data.open,
                        data.high,
                        data.low,
                        data.close,
                        data.volume
                    ))
                conn.commit()
                
            self.logger.debug(f"Stored {len(ohlcv_data)} price data records")
            
        except Exception as e:
            raise DatabaseError(f"Failed to store price data: {e}")
    
    def store_indicator_values(self, indicator_values: List[IndicatorValue]):
        """
        Store technical indicator values.
        
        Args:
            indicator_values: List of IndicatorValue objects
        """
        try:
            with self.get_connection() as conn:
                for indicator in indicator_values:
                    conn.execute("""
                        INSERT OR REPLACE INTO indicators 
                        (symbol, timestamp, indicator_name, value, parameters)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        indicator.symbol,
                        indicator.timestamp,
                        indicator.indicator_name,
                        indicator.value,
                        str(indicator.parameters)
                    ))
                conn.commit()
                
            self.logger.debug(f"Stored {len(indicator_values)} indicator values")
            
        except Exception as e:
            raise DatabaseError(f"Failed to store indicator values: {e}")
    
    def store_signal(self, signal: Signal):
        """
        Store trading signal.
        
        Args:
            signal: Signal object
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO signals 
                    (symbol, timestamp, signal_type, confidence, indicators, strategy_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    signal.symbol,
                    signal.timestamp,
                    signal.signal_type.value,
                    signal.confidence,
                    str(signal.indicators),
                    signal.strategy_name
                ))
                conn.commit()
                
            self.logger.debug(f"Stored signal: {signal.signal_type.value} for {signal.symbol}")
            
        except Exception as e:
            raise DatabaseError(f"Failed to store signal: {e}")
    
    def get_price_data(self, symbol: str, limit: Optional[int] = None) -> List[OHLCV]:
        """
        Retrieve price data for a symbol.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of records to return
            
        Returns:
            List of OHLCV objects
        """
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT symbol, timestamp, open, high, low, close, volume
                    FROM price_data 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query, (symbol,))
                rows = cursor.fetchall()
                
                return [
                    OHLCV(
                        symbol=row['symbol'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    for row in rows
                ]
                
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve price data: {e}")
    
    def get_latest_signals(self, symbol: Optional[str] = None, limit: int = 100) -> List[Signal]:
        """
        Retrieve latest trading signals.
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum number of signals to return
            
        Returns:
            List of Signal objects
        """
        try:
            with self.get_connection() as conn:
                if symbol:
                    query = """
                        SELECT symbol, timestamp, signal_type, confidence, indicators, strategy_name
                        FROM signals 
                        WHERE symbol = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """
                    cursor = conn.execute(query, (symbol, limit))
                else:
                    query = """
                        SELECT symbol, timestamp, signal_type, confidence, indicators, strategy_name
                        FROM signals 
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """
                    cursor = conn.execute(query, (limit,))
                
                rows = cursor.fetchall()
                
                return [
                    Signal(
                        symbol=row['symbol'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        signal_type=SignalType(row['signal_type']),
                        confidence=row['confidence'],
                        indicators=eval(row['indicators']),  # Convert string back to dict
                        strategy_name=row['strategy_name']
                    )
                    for row in rows
                ]
                
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve signals: {e}")
    
    def log_system_event(self, level: str, message: str, component: str = None, details: str = None):
        """
        Log system event to database.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            component: Component name
            details: Additional details
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_log (level, message, component, details)
                    VALUES (?, ?, ?, ?)
                """, (level, message, component, details))
                conn.commit()
                
        except Exception as e:
            # Don't raise exception for logging failures to avoid infinite loops
            self.logger.error(f"Failed to log system event: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """
        Clean up old data to manage database size.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            with self.get_connection() as conn:
                cutoff_date = datetime.now().replace(day=1)  # Keep at least current month
                
                # Clean old price data
                conn.execute("""
                    DELETE FROM price_data 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                # Clean old indicators
                conn.execute("""
                    DELETE FROM indicators 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                # Clean old system logs
                conn.execute("""
                    DELETE FROM system_log 
                    WHERE timestamp < datetime('now', '-30 days')
                """)
                
                conn.commit()
                
            self.logger.info(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            raise DatabaseError(f"Failed to cleanup old data: {e}")