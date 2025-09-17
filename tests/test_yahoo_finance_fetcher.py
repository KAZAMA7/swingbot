"""
Tests for Yahoo Finance Fetcher
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

from src.data.yahoo_finance_fetcher import YahooFinanceFetcher
from src.models.exceptions import DataFetchError


class TestYahooFinanceFetcher(unittest.TestCase):
    """Test cases for YahooFinanceFetcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = YahooFinanceFetcher(rate_limit=10)  # Higher rate limit for tests
    
    @patch('src.data.yahoo_finance_fetcher.yf.Ticker')
    def test_fetch_current_data_success(self, mock_ticker):
        """Test successful current data fetching."""
        # Mock yfinance response
        mock_hist = pd.DataFrame({
            'Open': [150.0],
            'High': [155.0],
            'Low': [149.0],
            'Close': [154.0],
            'Volume': [1000000]
        }, index=[datetime(2023, 1, 1)])
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # Test fetch
        result = self.fetcher.fetch_current_data(['AAPL'])
        
        self.assertIn('AAPL', result)
        self.assertEqual(result['AAPL'].close, 154.0)
        self.assertEqual(result['AAPL'].volume, 1000000)
    
    @patch('src.data.yahoo_finance_fetcher.yf.Ticker')
    def test_fetch_current_data_no_data(self, mock_ticker):
        """Test handling of no data available."""
        # Mock empty response
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        # Should raise DataFetchError when no data for any symbol
        with self.assertRaises(DataFetchError):
            self.fetcher.fetch_current_data(['INVALID'])
    
    @patch('src.data.yahoo_finance_fetcher.yf.Ticker')
    def test_validate_symbol_valid(self, mock_ticker):
        """Test symbol validation for valid symbol."""
        # Mock valid symbol response
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'symbol': 'AAPL'}
        mock_ticker_instance.history.return_value = pd.DataFrame({
            'Close': [150.0]
        }, index=[datetime(2023, 1, 1)])
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.fetcher.validate_symbol('AAPL')
        self.assertTrue(result)
    
    @patch('src.data.yahoo_finance_fetcher.yf.Ticker')
    def test_validate_symbol_invalid(self, mock_ticker):
        """Test symbol validation for invalid symbol."""
        # Mock invalid symbol response
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {}
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.fetcher.validate_symbol('INVALID')
        self.assertFalse(result)
    
    def test_get_supported_exchanges(self):
        """Test getting supported exchanges."""
        exchanges = self.fetcher.get_supported_exchanges()
        
        self.assertIsInstance(exchanges, list)
        self.assertIn('NYSE', exchanges)
        self.assertIn('NASDAQ', exchanges)


if __name__ == '__main__':
    unittest.main()