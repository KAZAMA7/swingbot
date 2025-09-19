"""
Tests for Trading Strategy
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime

from src.strategies.swing_trading_strategy import SwingTradingStrategy
from src.strategies.ema_crossover_strategy import EMACrossoverStrategy
from src.strategies.supertrend_strategy import SuperTrendStrategy
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


class TestEMACrossoverStrategy(unittest.TestCase):
    """Test cases for EMACrossoverStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = EMACrossoverStrategy(short_period=20, long_period=50)
        
        # Create test data with trend
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # Generate trending price data
        prices = []
        price = 100.0
        for i in range(100):
            # Create uptrend in first half, downtrend in second half
            if i < 50:
                change = np.random.normal(0.5, 1)  # Slight upward bias
            else:
                change = np.random.normal(-0.5, 1)  # Slight downward bias
            price += change
            prices.append(max(price, 1))
        
        self.test_data = pd.DataFrame({
            'Open': [p * 0.99 for p in prices],
            'High': [p * 1.02 for p in prices],
            'Low': [p * 0.98 for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)
    
    def test_ema_crossover_signal_generation(self):
        """Test EMA crossover signal generation."""
        signal = self.strategy.generate_signal(self.test_data, {})
        
        # Should generate a valid signal
        self.assertIn(signal.signal_type, [SignalType.BUY, SignalType.SELL, SignalType.NO_SIGNAL])
        self.assertGreaterEqual(signal.confidence, 0.0)
        self.assertLessEqual(signal.confidence, 1.0)
        self.assertEqual(signal.strategy_name, 'ema_crossover')
    
    def test_ema_crossover_parameters(self):
        """Test EMA crossover parameters."""
        params = self.strategy.get_strategy_params()
        
        self.assertEqual(params['short_period'], 50)
        self.assertEqual(params['long_period'], 200)
        self.assertEqual(params['approach_threshold'], 0.02)
    
    def test_ema_crossover_validation(self):
        """Test parameter validation."""
        valid_conditions = {
            'short_period': 20,
            'long_period': 50,
            'approach_threshold': 0.02
        }
        
        invalid_conditions = {
            'short_period': 50,  # Should be less than long_period
            'long_period': 20,
            'approach_threshold': 0.02
        }
        
        self.assertTrue(self.strategy.validate_conditions(valid_conditions))
        self.assertFalse(self.strategy.validate_conditions(invalid_conditions))
    
    def test_crossover_type_detection(self):
        """Test crossover type detection."""
        crossover_type = self.strategy.detect_crossover_type(self.test_data)
        
        valid_types = ['none', 'bullish', 'bearish', 'approaching_bullish', 'approaching_bearish']
        self.assertIn(crossover_type, valid_types)
    
    def test_ema_values_retrieval(self):
        """Test EMA values retrieval."""
        ema_values = self.strategy.get_ema_values(self.test_data)
        
        self.assertIn('short_ema', ema_values)
        self.assertIn('long_ema', ema_values)
        self.assertIn('convergence_pct', ema_values)
        self.assertEqual(ema_values['short_period'], 20)
        self.assertEqual(ema_values['long_period'], 50)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        small_data = self.test_data.head(10)  # Not enough for 50-period EMA
        
        with self.assertRaises(StrategyError):
            self.strategy.generate_signal(small_data, {})


class TestSuperTrendStrategy(unittest.TestCase):
    """Test cases for SuperTrendStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = SuperTrendStrategy(atr_period=10, multiplier=3.0)
        
        # Create test data with volatility
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        np.random.seed(42)
        
        # Generate realistic OHLC data
        prices = []
        price = 100.0
        for _ in range(50):
            change = np.random.normal(0, 2)
            price += change
            prices.append(max(price, 1))
        
        self.test_data = pd.DataFrame({
            'Open': [p * np.random.uniform(0.98, 1.02) for p in prices],
            'High': [p * np.random.uniform(1.01, 1.05) for p in prices],
            'Low': [p * np.random.uniform(0.95, 0.99) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 50)
        }, index=dates)
    
    def test_supertrend_signal_generation(self):
        """Test SuperTrend signal generation."""
        signal = self.strategy.generate_signal(self.test_data, {})
        
        # Should generate a valid signal
        self.assertIn(signal.signal_type, [SignalType.BUY, SignalType.SELL, SignalType.NO_SIGNAL])
        self.assertGreaterEqual(signal.confidence, 0.0)
        self.assertLessEqual(signal.confidence, 1.0)
        self.assertEqual(signal.strategy_name, 'supertrend')
    
    def test_supertrend_parameters(self):
        """Test SuperTrend parameters."""
        params = self.strategy.get_strategy_params()
        
        self.assertEqual(params['atr_period'], 10)
        self.assertEqual(params['multiplier'], 3.0)
    
    def test_supertrend_validation(self):
        """Test parameter validation."""
        valid_conditions = {
            'atr_period': 10,
            'multiplier': 3.0
        }
        
        invalid_conditions = {
            'atr_period': 0,  # Should be positive
            'multiplier': -1.0  # Should be positive
        }
        
        self.assertTrue(self.strategy.validate_conditions(valid_conditions))
        self.assertFalse(self.strategy.validate_conditions(invalid_conditions))
    
    def test_trend_change_detection(self):
        """Test trend change detection."""
        trend_info = self.strategy.detect_trend_change(self.test_data)
        
        self.assertIn('current_trend', trend_info)
        self.assertIn('trend_reversal', trend_info)
        self.assertIn('reversal_type', trend_info)
        self.assertIn(trend_info['current_trend'], ['bullish', 'bearish'])
        self.assertIsInstance(trend_info['trend_reversal'], bool)
    
    def test_supertrend_values_retrieval(self):
        """Test SuperTrend values retrieval."""
        st_values = self.strategy.get_supertrend_values(self.test_data)
        
        self.assertIn('supertrend_value', st_values)
        self.assertIn('trend_direction', st_values)
        self.assertIn('atr_value', st_values)
        self.assertEqual(st_values['atr_period'], 10)
        self.assertEqual(st_values['multiplier'], 3.0)
    
    def test_price_vs_supertrend(self):
        """Test price vs SuperTrend comparison."""
        is_above = self.strategy.is_price_above_supertrend(self.test_data)
        
        self.assertIsInstance(is_above, bool)
    
    def test_trend_strength_score(self):
        """Test trend strength score calculation."""
        strength_score = self.strategy.calculate_trend_strength_score(self.test_data)
        
        self.assertIsInstance(strength_score, float)
        self.assertGreaterEqual(strength_score, -1.0)
        self.assertLessEqual(strength_score, 1.0)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        small_data = self.test_data.head(5)  # Not enough for ATR calculation
        
        with self.assertRaises(StrategyError):
            self.strategy.generate_signal(small_data, {})


if __name__ == '__main__':
    unittest.main()