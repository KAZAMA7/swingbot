"""
Yahoo Finance Data Fetcher

Implements data fetching from Yahoo Finance using yfinance library.
"""

import yfinance as yf
import pandas as pd
import logging
import time
from typing import Dict, List
from datetime import datetime, timedelta

from ..interfaces.data_fetcher import DataFetcherInterface
from ..models.data_models import OHLCV
from ..models.exceptions import DataFetchError


class YahooFinanceFetcher(DataFetcherInterface):
    """Yahoo Finance data fetcher implementation."""
    
    def __init__(self, rate_limit: int = 5):
        """
        Initialize Yahoo Finance fetcher.
        
        Args:
            rate_limit: Maximum requests per second
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)
        
        # Common exchanges supported by Yahoo Finance
        self.supported_exchanges = [
            'NYSE', 'NASDAQ', 'LSE', 'TSE', 'ASX', 'TSX', 'FRA', 'AMS', 'SWX'
        ]
    
    def _rate_limit_delay(self):
        """Implement rate limiting."""
        if self.rate_limit > 0:
            time_since_last = time.time() - self.last_request_time
            min_interval = 1.0 / self.rate_limit
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_current_data(self, symbols: List[str]) -> Dict[str, 'OHLCV']:
        """
        Fetch current market data for given symbols.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to OHLCV data
            
        Raises:
            DataFetchError: If data fetching fails
        """
        result = {}
        
        for symbol in symbols:
            try:
                self._rate_limit_delay()
                
                ticker = yf.Ticker(symbol)
                
                # Get current data (last trading day)
                hist = ticker.history(period="2d")  # Get 2 days to ensure we have recent data
                
                if hist.empty:
                    self.logger.warning(f"No data available for symbol {symbol}")
                    continue
                
                # Get the most recent trading day
                latest_data = hist.iloc[-1]
                latest_timestamp = hist.index[-1].to_pydatetime()
                
                ohlcv = OHLCV(
                    symbol=symbol,
                    timestamp=latest_timestamp,
                    open=float(latest_data['Open']),
                    high=float(latest_data['High']),
                    low=float(latest_data['Low']),
                    close=float(latest_data['Close']),
                    volume=int(latest_data['Volume'])
                )
                
                result[symbol] = ohlcv
                self.logger.debug(f"Fetched current data for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch current data for {symbol}: {e}")
                # Continue with other symbols instead of failing completely
                continue
        
        if not result:
            raise DataFetchError("Failed to fetch data for any symbols")
        
        return result
    
    def fetch_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        Fetch historical market data for a symbol.
        
        Args:
            symbol: Stock symbol to fetch
            period: Time period (e.g., "1y", "6mo", "200d")
            
        Returns:
            DataFrame with OHLCV data indexed by date
            
        Raises:
            DataFetchError: If data fetching fails
        """
        try:
            self._rate_limit_delay()
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                raise DataFetchError(f"No historical data available for {symbol}")
            
            # Ensure we have enough data points (at least 200 for technical analysis)
            if len(hist) < 50:
                self.logger.warning(f"Limited historical data for {symbol}: {len(hist)} days")
            
            self.logger.debug(f"Fetched {len(hist)} days of historical data for {symbol}")
            return hist
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch historical data for {symbol}: {e}")
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is supported.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            self._rate_limit_delay()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid info back
            if not info or 'symbol' not in info:
                return False
            
            # Try to get some recent data
            hist = ticker.history(period="5d")
            return not hist.empty
            
        except Exception as e:
            self.logger.debug(f"Symbol validation failed for {symbol}: {e}")
            return False
    
    def get_supported_exchanges(self) -> List[str]:
        """
        Get list of supported exchanges.
        
        Returns:
            List of exchange codes
        """
        return self.supported_exchanges.copy()
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """
        Get additional information about a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with symbol information
        """
        try:
            self._rate_limit_delay()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': info.get('symbol', symbol),
                'name': info.get('longName', 'Unknown'),
                'exchange': info.get('exchange', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return {'symbol': symbol, 'name': 'Unknown'}
    
    def fetch_ohlcv_list(self, symbol: str, period: str = "1y") -> List[OHLCV]:
        """
        Fetch historical data as list of OHLCV objects.
        
        Args:
            symbol: Stock symbol
            period: Time period
            
        Returns:
            List of OHLCV objects
        """
        try:
            hist_df = self.fetch_historical_data(symbol, period)
            
            ohlcv_list = []
            for timestamp, row in hist_df.iterrows():
                ohlcv = OHLCV(
                    symbol=symbol,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                ohlcv_list.append(ohlcv)
            
            return ohlcv_list
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch OHLCV list for {symbol}: {e}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Yahoo Finance.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Test with a well-known symbol
            test_symbol = "AAPL"
            ticker = yf.Ticker(test_symbol)
            hist = ticker.history(period="1d")
            
            return not hist.empty
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False