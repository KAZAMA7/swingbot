"""
Tests for Trading Strategy
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime

from src.strategies.swing_trading_strategy import SwingTradingStrategy
from src.models.data_models import SignalType
from src.models.exceptions import StrategyError


class TestSwingTradingStrategy(unittest.TestCase):
    """Test cases for SwingTradingStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = SwingTradingStrategy()
        
        # Create test data
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        self.test_data = pd.DataFrame({
            'Open': np.random.uniform(95, 105, 50),
            'High': np.random.uniform(100, 110, 50),
            'Low': np.random.uniform(90, 100, 50),
            'Close': np.random.uniform(95, 105, 50),
            'Volume': np.random.randint(1000000, 5000000, 50)
        }, index=dates)
    
    def test_buy_signal_generation(self):
        """Test BUY signal generation."""
        # Create indicators that should trigger a BUY signal
        indicators = {
            'rsi': pd.Series([25.0] * 50, index=self.test_data.index),  # Oversold
            'bollinger_bands': pd.DataFrame({
                'upper_band': [110.0] * 50,
                'lower_band': [90.0] * 50,
                'middle_band': [100.0] * 50
            }, index=self.test_data.index),
            'ema': pd.Series([85.0] * 50, index=self.test_data.index)  # EMA below current price
        }

        # Set current price below BB lower band but above EMA
        self.test_data.loc[self.test_data.index[-1], 'Close'] = 89.0
        
        signal = self.strategy.generate_signal(self.test_data, indicators)
        
        self.assertEqual(signal.signal_type, SignalType.BUY)
        self.assertGreater(signal.confidence, 0)
        self.assertEqual(signal.strategy_name, 'swing_trading')
    
    def test_sell_signal_generation(self):
        """Test SELL signal generation."""
        # Create indicators that should trigger a SELL signal
        indicators = {
            'rsi': pd.Series([75.0] * 50, index=self.test_data.index),  # Overbought
            'bollinger_bands': pd.DataFrame({
                'upper_band': [110.0] * 50,
                'lower_band': [90.0] * 50,
                'middle_band': [100.0] * 50
            }, index=self.test_data.index),
            'ema': pd.Series([115.0] * 50, index=self.test_data.index)  # Above current price
        }
        
        # Set current price above BB upper band but below EMA
        self.test_data.loc[self.test_data.index[-1], 'Close'] = 111.0
        
        signal = self.strategy.generate_signal(self.test_data, indicators)
        
        self.assertEqual(signal.signal_type, SignalType.SELL)
        self.assertGreater(signal.confidence, 0)
    
    def test_no_signal_generation(self):
        """Test NO_SIGNAL generation."""
        # Create neutral indicators
        indicators = {
            'rsi': pd.Series([50.0] * 50, index=self.test_data.index),  # Neutral
            'bollinger_bands': pd.DataFrame({
                'upper_band': [110.0] * 50,
                'lower_band': [90.0] * 50,
                'middle_band': [100.0] * 50
            }, index=self.test_data.index),
            'ema': pd.Series([100.0] * 50, index=self.test_data.index)
        }
        
        signal = self.strategy.generate_signal(self.test_data, indicators)
        
        self.assertEqual(signal.signal_type, SignalType.NO_SIGNAL)
        self.assertEqual(signal.confidence, 0.0)
    
    def test_missing_indicators(self):
        """Test handling of missing indicators."""
        incomplete_indicators = {
            'rsi': pd.Series([25.0] * 50, index=self.test_data.index)
            # Missing bollinger_bands and ema
        }
        
        with self.assertRaises(StrategyError):
            self.strategy.generate_signal(self.test_data, incomplete_indicators)
    
    def test_required_indicators(self):
        """Test required indicators list."""
        required = self.strategy.get_required_indicators()
        
        self.assertIn('rsi', required)
        self.assertIn('bollinger_bands', required)
        self.assertIn('ema', required)
    
    def test_strategy_parameters(self):
        """Test strategy parameters."""
        params = self.strategy.get_strategy_params()
        
        self.assertIn('rsi_oversold', params)
        self.assertIn('rsi_overbought', params)
        self.assertEqual(params['rsi_oversold'], 30)
        self.assertEqual(params['rsi_overbought'], 70)
    
    def test_condition_validation(self):
        """Test condition validation."""
        valid_conditions = {
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        
        invalid_conditions = {
            'rsi_oversold': 80,  # Should be less than overbought
            'rsi_overbought': 70
        }
        
        self.assertTrue(self.strategy.validate_conditions(valid_conditions))
        self.assertFalse(self.strategy.validate_conditions(invalid_conditions))
    
    def test_signal_strength(self):
        """Test signal strength calculation."""
        indicators = {
            'rsi': pd.Series([25.0] * 50, index=self.test_data.index),
            'bollinger_bands': pd.DataFrame({
                'upper_band': [110.0] * 50,
                'lower_band': [90.0] * 50,
                'middle_band': [100.0] * 50
            }, index=self.test_data.index),
            'ema': pd.Series([95.0] * 50, index=self.test_data.index)
        }
        
        strength = self.strategy.get_signal_strength(self.test_data, indicators)
        
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)


if __name__ == '__main__':
    unittest.main()