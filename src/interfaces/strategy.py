"""
Trading Strategy Interface

Defines the contract for trading strategy implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from pandas import DataFrame


class StrategyInterface(ABC):
    """Abstract interface for trading strategy implementations."""
    
    @abstractmethod
    def generate_signal(self, data: DataFrame, indicators: Dict) -> 'Signal':
        """
        Generate trading signal based on data and indicators.
        
        Args:
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            
        Returns:
            Signal object with trading recommendation
            
        Raises:
            StrategyError: If signal generation fails
        """
        pass
    
    @abstractmethod
    def validate_conditions(self, conditions: Dict) -> bool:
        """
        Validate strategy conditions/parameters.
        
        Args:
            conditions: Dictionary of strategy conditions
            
        Returns:
            True if conditions are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """
        Get list of indicators required by this strategy.
        
        Returns:
            List of indicator names
        """
        pass
    
    @abstractmethod
    def get_strategy_params(self) -> Dict:
        """
        Get strategy parameters and their default values.
        
        Returns:
            Dictionary of parameter names and default values
        """
        pass