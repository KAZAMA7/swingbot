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
    
    def fetch_historical_data(self, symbol: str, period: str = "max", fallback_periods: List[str] = None) -> pd.DataFrame:
        """
        Fetch historical market data for a symbol with fallback periods.
        
        Args:
            symbol: Stock symbol to fetch
            period: Primary time period (e.g., "max", "10y", "1y", "6mo")
            fallback_periods: List of fallback periods to try if primary fails
            
        Returns:
            DataFrame with OHLCV data indexed by date
            
        Raises:
            DataFetchError: If data fetching fails for all periods
        """
        if fallback_periods is None:
            fallback_periods = ["max", "10y", "5y", "2y", "1y", "6mo"]
        
        # Ensure primary period is first in the list
        periods_to_try = [period] + [p for p in fallback_periods if p != period]
        
        last_error = None
        for attempt_period in periods_to_try:
            try:
                self._rate_limit_delay()
                
                ticker = yf.Ticker(symbol)
                self.logger.debug(f"Attempting to fetch {attempt_period} data for {symbol}")
                hist = ticker.history(period=attempt_period)
                
                if not hist.empty and len(hist) >= 50:  # Minimum threshold for analysis
                    # Log data range information
                    start_date = hist.index.min().strftime('%Y-%m-%d')
                    end_date = hist.index.max().strftime('%Y-%m-%d')
                    years_span = (hist.index.max() - hist.index.min()).days / 365.25
                    
                    self.logger.debug(f"Successfully fetched {len(hist)} days of data for {symbol} "
                                    f"from {start_date} to {end_date} ({years_span:.1f} years) [Period: {attempt_period}]")
                    
                    # Warn if data span is limited
                    if years_span < 1.0:
                        self.logger.warning(f"Limited historical data for {symbol}: {years_span:.1f} years")
                    
                    return hist
                else:
                    self.logger.debug(f"Insufficient data with {attempt_period} for {symbol}: {len(hist) if not hist.empty else 0} days")
                    
            except Exception as e:
                last_error = e
                self.logger.debug(f"Failed to fetch {attempt_period} data for {symbol}: {e}")
                continue
        
        # If we get here, all periods failed
        raise DataFetchError(f"Failed to fetch historical data for {symbol} with any period. Last error: {last_error}")
    
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
    
    def fetch_ohlcv_list(self, symbol: str, period: str = "max") -> List[OHLCV]:
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