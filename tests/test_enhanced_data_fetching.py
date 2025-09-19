#!/usr/bin/env python3
"""
Comprehensive tests for enhanced data fetching functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_nifty_trading_bot import (
    analyze_symbol_enhanced, 
    load_config, 
    validate_config, 
    get_default_config
)


class TestEnhancedDataFetching(unittest.TestCase):
    """Test enhanced data fetching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.test_symbol = "RELIANCE.NS"
        
        # Create sample historical data
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
        self.sample_data = pd.DataFrame({
            'Open': np.random.uniform(2000, 2500, len(dates)),
            'High': np.random.uniform(2100, 2600, len(dates)),
            'Low': np.random.uniform(1900, 2400, len(dates)),
            'Close': np.random.uniform(2000, 2500, len(dates)),
            'Volume': np.random.uniform(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Sample configuration
        self.sample_config = {
            'data_fetching': {
                'max_data_period': 'max',
                'fallback_periods': ['max', '10y', '5y', '2y', '1y', '6mo'],
                'min_data_threshold': 200,
                'timeout_per_symbol': 60,
                'show_data_summary': True
            }
        }
    
    @patch('enhanced_nifty_trading_bot.yf.Ticker')
    def test_analyze_symbol_with_max_period(self, mock_ticker):
        """Test analyzing symbol with maximum period data."""
        # Mock yfinance ticker
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = self.sample_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Test analysis
        result = analyze_symbol_enhanced(
            self.test_symbol, 
            self.logger, 
            config=self.sample_config
        )
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], self.test_symbol)
        self.assertIn('data_start_date', result)
        self.assertIn('data_end_date', result)
        self.assertIn('data_years', result)
        self.assertIn('data_period_used', result)
        
        # Verify data range calculation
        self.assertGreater(result['data_years'], 3.0)  # Should be about 4 years
        self.assertEqual(result['data_period_used'], 'max')
    
    @patch('enhanced_nifty_trading_bot.yf.Ticker')
    def test_fallback_period_logic(self, mock_ticker):
        """Test fallback period logic when max fails."""
        mock_ticker_instance = Mock()
        
        # Mock max period failing, 5y succeeding
        def mock_history(period):
            if period == 'max':
                raise Exception("Max period failed")
            elif period == '10y':
                return pd.DataFrame()  # Empty data
            elif period == '5y':
                return self.sample_data
            else:
                return pd.DataFrame()
        
        mock_ticker_instance.history.side_effect = mock_history
        mock_ticker.return_value = mock_ticker_instance
        
        result = analyze_symbol_enhanced(
            self.test_symbol, 
            self.logger, 
            config=self.sample_config
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['data_period_used'], '5y')
    
    @patch('enhanced_nifty_trading_bot.yf.Ticker')
    def test_insufficient_data_handling(self, mock_ticker):
        """Test handling of insufficient data."""
        # Create data with less than minimum threshold
        small_data = self.sample_data.head(50)  # Only 50 days
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = small_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = analyze_symbol_enhanced(
            self.test_symbol, 
            self.logger, 
            config=self.sample_config
        )
        
        # Should return None due to insufficient data
        self.assertIsNone(result)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid config
        valid_config = {
            'data_fetching': {
                'max_data_period': 'max',
                'fallback_periods': ['max', '5y', '1y'],
                'min_data_threshold': 100,
                'timeout_per_symbol': 30
            }
        }
        
        validated = validate_config(valid_config)
        self.assertEqual(validated['data_fetching']['max_data_period'], 'max')
        self.assertEqual(validated['data_fetching']['min_data_threshold'], 100)
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        # Test empty config
        empty_config = {}
        validated = validate_config(empty_config)
        
        self.assertIn('data_fetching', validated)
        self.assertEqual(validated['data_fetching']['max_data_period'], 'max')
        self.assertIsInstance(validated['data_fetching']['fallback_periods'], list)
        self.assertGreater(validated['data_fetching']['min_data_threshold'], 0)
    
    def test_invalid_config_handling(self):
        """Test handling of invalid configuration values."""
        invalid_config = {
            'data_fetching': {
                'fallback_periods': 'not_a_list',  # Should be list
                'min_data_threshold': -100,  # Should be positive
                'timeout_per_symbol': 'invalid'  # Should be number
            }
        }
        
        validated = validate_config(invalid_config)
        
        # Should use defaults for invalid values
        self.assertIsInstance(validated['data_fetching']['fallback_periods'], list)
        self.assertGreater(validated['data_fetching']['min_data_threshold'], 0)
        self.assertIsInstance(validated['data_fetching']['timeout_per_symbol'], (int, float))
    
    def test_get_default_config(self):
        """Test default configuration generation."""
        default_config = get_default_config()
        
        self.assertIn('data_fetching', default_config)
        self.assertIn('data_sources', default_config)
        
        data_config = default_config['data_fetching']
        self.assertEqual(data_config['max_data_period'], 'max')
        self.assertIn('max', data_config['fallback_periods'])
        self.assertGreater(data_config['min_data_threshold'], 0)
    
    @patch('enhanced_nifty_trading_bot.yf.Ticker')
    def test_data_quality_warnings(self, mock_ticker):
        """Test data quality warnings for limited historical data."""
        # Create data with less than 1 year
        short_data = pd.DataFrame({
            'Open': [2000, 2100, 2050],
            'High': [2100, 2200, 2150],
            'Low': [1950, 2000, 1980],
            'Close': [2050, 2150, 2100],
            'Volume': [1000000, 1200000, 1100000]
        }, index=pd.date_range(start='2024-01-01', periods=3, freq='D'))
        
        # Pad to meet minimum threshold
        dates = pd.date_range(start='2023-06-01', end='2024-01-01', freq='D')
        padded_data = pd.DataFrame({
            'Open': np.random.uniform(2000, 2100, len(dates)),
            'High': np.random.uniform(2100, 2200, len(dates)),
            'Low': np.random.uniform(1900, 2000, len(dates)),
            'Close': np.random.uniform(2000, 2100, len(dates)),
            'Volume': np.random.uniform(1000000, 2000000, len(dates))
        }, index=dates)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = padded_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = analyze_symbol_enhanced(
            self.test_symbol, 
            self.logger, 
            config=self.sample_config
        )
        
        # Should still return result but with warning logged
        self.assertIsNotNone(result)
        self.assertLess(result['data_years'], 1.0)
        
        # Verify warning was logged
        warning_calls = [call for call in self.logger.warning.call_args_list 
                        if 'Limited historical data' in str(call)]
        self.assertGreater(len(warning_calls), 0)


class TestPeriodFallbackLogic(unittest.TestCase):
    """Test period fallback logic specifically."""
    
    def setUp(self):
        self.logger = Mock()
        self.test_symbol = "TCS.NS"
    
    @patch('enhanced_nifty_trading_bot.yf.Ticker')
    def test_all_periods_fail(self, mock_ticker):
        """Test when all periods fail to fetch data."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = Exception("Network error")
        mock_ticker.return_value = mock_ticker_instance
        
        config = {
            'data_fetching': {
                'fallback_periods': ['max', '5y', '1y'],
                'min_data_threshold': 200
            }
        }
        
        result = analyze_symbol_enhanced(self.test_symbol, self.logger, config=config)
        self.assertIsNone(result)
    
    @patch('enhanced_nifty_trading_bot.yf.Ticker')
    def test_period_priority_order(self, mock_ticker):
        """Test that periods are tried in correct order."""
        mock_ticker_instance = Mock()
        
        # Track which periods were called
        called_periods = []
        
        def track_history_calls(period):
            called_periods.append(period)
            if period == '2y':
                # Return data on third attempt
                dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='D')
                return pd.DataFrame({
                    'Close': np.random.uniform(1000, 1100, len(dates))
                }, index=dates)
            else:
                raise Exception(f"Failed for {period}")
        
        mock_ticker_instance.history.side_effect = track_history_calls
        mock_ticker.return_value = mock_ticker_instance
        
        config = {
            'data_fetching': {
                'fallback_periods': ['max', '10y', '2y', '1y'],
                'min_data_threshold': 200
            }
        }
        
        result = analyze_symbol_enhanced(self.test_symbol, self.logger, config=config)
        
        # Should have tried periods in order and succeeded on '2y'
        self.assertEqual(called_periods, ['max', '10y', '2y'])
        self.assertIsNotNone(result)
        self.assertEqual(result['data_period_used'], '2y')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)