"""
Technical Indicator Interface

Defines the contract for technical indicator implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict
from pandas import DataFrame, Series


class IndicatorInterface(ABC):
    """Abstract interface for technical indicator implementations."""
    
    @abstractmethod
    def calculate(self, data: DataFrame, params: Dict) -> Series:
        """
        Calculate the indicator values.
        
        Args:
            data: DataFrame with OHLCV data
            params: Dictionary of indicator parameters
            
        Returns:
            Series with calculated indicator values
            
        Raises:
            IndicatorError: If calculation fails
        """
        pass
    
    @abstractmethod
    def get_required_periods(self, params: Dict) -> int:
        """
        Get minimum number of periods required for calculation.
        
        Args:
            params: Dictionary of indicator parameters
            
        Returns:
            Minimum number of data points needed
        """
        pass
    
    @abstractmethod
    def validate_params(self, params: Dict) -> bool:
        """
        Validate indicator parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_default_params(self) -> Dict:
        """
        Get default parameters for the indicator.
        
        Returns:
            Dictionary of default parameter values
        """
        pass