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


if __name__ == '__main__':
    unittest.main()