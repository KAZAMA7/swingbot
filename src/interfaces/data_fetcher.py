"""
Data Fetcher Interface

Defines the contract for data fetching implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from pandas import DataFrame


class DataFetcherInterface(ABC):
    """Abstract interface for data fetching implementations."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def fetch_historical_data(self, symbol: str, period: str) -> DataFrame:
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
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is supported.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_exchanges(self) -> List[str]:
        """
        Get list of supported exchanges.
        
        Returns:
            List of exchange codes
        """
        pass