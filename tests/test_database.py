"""
Tests for Database Manager
"""

import unittest
import tempfile
from datetime import datetime
from pathlib import Path

from src.data.database import DatabaseManager
from src.models.data_models import OHLCV, Signal, SignalType, IndicatorValue


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.db_manager = DatabaseManager(str(self.db_path))
    
    def test_store_and_retrieve_price_data(self):
        """Test storing and retrieving price data."""
        test_data = [
            OHLCV(
                symbol='AAPL',
                timestamp=datetime(2023, 1, 1, 9, 30),
                open=150.0,
                high=155.0,
                low=149.0,
                close=154.0,
                volume=1000000
            )
        ]
        
        # Store data
        self.db_manager.store_price_data(test_data)
        
        # Retrieve data
        retrieved = self.db_manager.get_price_data('AAPL')
        
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].symbol, 'AAPL')
        self.assertEqual(retrieved[0].close, 154.0)
    
    def test_store_signal(self):
        """Test storing trading signals."""
        signal = Signal(
            symbol='AAPL',
            timestamp=datetime.now(),
            signal_type=SignalType.BUY,
            confidence=0.8,
            indicators={'rsi': 25.0, 'bb_lower': 148.0},
            strategy_name='swing_trading'
        )
        
        # Store signal
        self.db_manager.store_signal(signal)
        
        # Retrieve signals
        signals = self.db_manager.get_latest_signals('AAPL')
        
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, SignalType.BUY)
        self.assertEqual(signals[0].confidence, 0.8)


if __name__ == '__main__':
    unittest.main()