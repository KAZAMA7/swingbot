"""
Tests for Technical Indicators
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.analysis.rsi_calculator import RSICalculator
from src.analysis.bollinger_bands_calculator import BollingerBandsCalculator
from src.analysis.ema_calculator import EMACalculator
from src.analysis.supertrend_calculator import SuperTrendCalculator
from src.models.exceptions import IndicatorError


class TestIndicators(unittest.TestCase):
    """Test cases for technical indicators."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)  # For reproducible tests
        
        # Generate realistic price data
        prices = []
        price = 100.0
        for _ in range(100):
            change = np.random.normal(0, 2)  # Random walk with volatility
            price += change
            prices.append(max(price, 1))  # Ensure positive prices
        
        self.test_data = pd.DataFrame({
            'Open': [p * 0.99 for p in prices],
            'High': [p * 1.02 for p in prices],
            'Low': [p * 0.98 for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)
        
        self.rsi_calc = RSICalculator()
        self.bb_calc = BollingerBandsCalculator()
        self.ema_calc = EMACalculator()
        self.supertrend_calc = SuperTrendCalculator()
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        params = {'period': 14}
        rsi = self.rsi_calc.calculate(self.test_data, params)
        
        # RSI should be between 0 and 100
        self.assertTrue((rsi >= 0).all())
        self.assertTrue((rsi <= 100).all())
        
        # Should have values for most of the data
        self.assertGreater(len(rsi.dropna()), 80)
    
    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        small_data = self.test_data.head(5)
        params = {'period': 14}
        
        with self.assertRaises(IndicatorError):
            self.rsi_calc.calculate(small_data, params)
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation."""
        params = {'period': 20, 'std_dev': 2}
        bb = self.bb_calc.calculate(self.test_data, params)
        
        # Should have all required columns
        required_cols = ['upper_band', 'middle_band', 'lower_band', 'bandwidth', 'percent_b']
        for col in required_cols:
            self.assertIn(col, bb.columns)
        
        # Upper band should be above lower band
        valid_data = bb.dropna()
        self.assertTrue((valid_data['upper_band'] > valid_data['lower_band']).all())
        
        # Middle band should be between upper and lower
        self.assertTrue((valid_data['middle_band'] >= valid_data['lower_band']).all())
        self.assertTrue((valid_data['middle_band'] <= valid_data['upper_band']).all())
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        params = {'period': 20}
        ema = self.ema_calc.calculate(self.test_data, params)
        
        # EMA should have values for most data points
        self.assertGreater(len(ema.dropna()), 80)
        
        # EMA should be positive (since our prices are positive)
        self.assertTrue((ema.dropna() > 0).all())
    
    def test_ema_multiple_periods(self):
        """Test EMA with multiple periods."""
        periods = [10, 20, 50]
        emas = self.ema_calc.calculate_multiple_emas(self.test_data, periods)
        
        # Should have columns for each period
        for period in periods:
            self.assertIn(f'ema_{period}', emas.columns)
    
    def test_ema_crossover_signals(self):
        """Test EMA crossover signal calculation."""
        result = self.ema_calc.calculate_ema_crossover_signals(
            self.test_data, short_period=20, long_period=50, approach_threshold=0.02
        )
        
        # Should have all required keys
        required_keys = ['short_ema', 'long_ema', 'ema_convergence', 'signals', 
                        'crossover_type', 'signal_strength', 'short_period', 'long_period']
        for key in required_keys:
            self.assertIn(key, result)
        
        # Crossover types should be valid
        crossover_values = result['crossover_type'].unique()
        valid_types = ['none', 'bullish', 'bearish', 'approaching_bullish', 'approaching_bearish']
        for crossover_type in crossover_values:
            self.assertIn(crossover_type, valid_types)
        
        # Signal strength should be between 0 and 1
        strength_values = result['signal_strength']
        self.assertTrue((strength_values >= 0.0).all())
        self.assertTrue((strength_values <= 1.0).all())
    
    def test_ema_crossover_invalid_periods(self):
        """Test EMA crossover with invalid periods."""
        with self.assertRaises(IndicatorError):
            self.ema_calc.calculate_ema_crossover_signals(
                self.test_data, short_period=50, long_period=20  # Invalid: short >= long
            )
    
    def test_ema_crossover_points_detection(self):
        """Test EMA crossover points detection."""
        crossover_data = self.ema_calc.calculate_ema_crossover_signals(
            self.test_data, short_period=10, long_period=30
        )
        
        crossover_points = self.ema_calc.detect_ema_crossover_points(crossover_data)
        
        # Should be a DataFrame
        self.assertIsInstance(crossover_points, pd.DataFrame)
        
        # If there are crossover points, they should have the right columns
        if len(crossover_points) > 0:
            expected_cols = ['timestamp', 'crossover_type', 'signal', 'signal_strength',
                           'short_ema_value', 'long_ema_value', 'ema_convergence_pct',
                           'short_period', 'long_period']
            for col in expected_cols:
                self.assertIn(col, crossover_points.columns)
    
    def test_parameter_validation(self):
        """Test parameter validation for all indicators."""
        # Valid parameters
        self.assertTrue(self.rsi_calc.validate_params({'period': 14}))
        self.assertTrue(self.bb_calc.validate_params({'period': 20, 'std_dev': 2}))
        self.assertTrue(self.ema_calc.validate_params({'period': 20}))
        
        # Invalid parameters
        self.assertFalse(self.rsi_calc.validate_params({'period': 1}))
        self.assertFalse(self.bb_calc.validate_params({'period': 1, 'std_dev': 2}))
        self.assertFalse(self.ema_calc.validate_params({'period': 0}))
    
    def test_default_parameters(self):
        """Test default parameters."""
        rsi_defaults = self.rsi_calc.get_default_params()
        self.assertEqual(rsi_defaults['period'], 14)
        
        bb_defaults = self.bb_calc.get_default_params()
        self.assertEqual(bb_defaults['period'], 20)
        self.assertEqual(bb_defaults['std_dev'], 2)
        
        ema_defaults = self.ema_calc.get_default_params()
        self.assertEqual(ema_defaults['period'], 20)
        
        supertrend_defaults = self.supertrend_calc.get_default_params()
        self.assertEqual(supertrend_defaults['atr_period'], 10)
        self.assertEqual(supertrend_defaults['multiplier'], 3.0)
    
    def test_supertrend_calculation(self):
        """Test SuperTrend calculation."""
        params = {'atr_period': 10, 'multiplier': 3.0}
        supertrend = self.supertrend_calc.calculate(self.test_data, params)
        
        # SuperTrend should have values for most data points
        self.assertGreater(len(supertrend.dropna()), 80)
        
        # SuperTrend should be positive (since our prices are positive)
        self.assertTrue((supertrend.dropna() > 0).all())
    
    def test_supertrend_with_signals(self):
        """Test SuperTrend calculation with signals."""
        params = {'atr_period': 10, 'multiplier': 3.0}
        result = self.supertrend_calc.calculate_with_signals(self.test_data, params)
        
        # Should have all required keys
        required_keys = ['supertrend', 'trend_direction', 'signals', 'atr']
        for key in required_keys:
            self.assertIn(key, result)
        
        # Trend direction should be 'bullish' or 'bearish'
        trend_values = result['trend_direction'].dropna().unique()
        for trend in trend_values:
            self.assertIn(trend, ['bullish', 'bearish'])
        
        # Signals should be -1, 0, or 1
        signal_values = result['signals'].unique()
        for signal in signal_values:
            self.assertIn(signal, [-1, 0, 1])
    
    def test_supertrend_insufficient_data(self):
        """Test SuperTrend with insufficient data."""
        small_data = self.test_data.head(5)
        params = {'atr_period': 10, 'multiplier': 3.0}
        
        with self.assertRaises(IndicatorError):
            self.supertrend_calc.calculate(small_data, params)
    
    def test_supertrend_parameter_validation(self):
        """Test SuperTrend parameter validation."""
        # Valid parameters
        self.assertTrue(self.supertrend_calc.validate_params({'atr_period': 10, 'multiplier': 3.0}))
        
        # Invalid parameters
        self.assertFalse(self.supertrend_calc.validate_params({'atr_period': 0, 'multiplier': 3.0}))
        self.assertFalse(self.supertrend_calc.validate_params({'atr_period': 10, 'multiplier': 0}))
        self.assertFalse(self.supertrend_calc.validate_params({'atr_period': 10, 'multiplier': -1}))
    
    def test_supertrend_trend_changes(self):
        """Test SuperTrend trend change detection."""
        params = {'atr_period': 10, 'multiplier': 3.0}
        supertrend_data = self.supertrend_calc.calculate_with_signals(self.test_data, params)
        
        trend_changes = self.supertrend_calc.detect_trend_changes(supertrend_data)
        
        # Should be a DataFrame
        self.assertIsInstance(trend_changes, pd.DataFrame)
        
        # If there are trend changes, they should have the right columns
        if len(trend_changes) > 0:
            expected_cols = ['timestamp', 'signal_type', 'trend_direction', 'supertrend_value', 'signal_strength']
            for col in expected_cols:
                self.assertIn(col, trend_changes.columns)
    
    def test_supertrend_trend_strength(self):
        """Test SuperTrend trend strength calculation."""
        params = {'atr_period': 10, 'multiplier': 3.0}
        supertrend_data = self.supertrend_calc.calculate_with_signals(self.test_data, params)
        
        strength = self.supertrend_calc.get_current_trend_strength(self.test_data, supertrend_data)
        
        # Strength should be between 0 and 1
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)


if __name__ == '__main__':
    unittest.main()