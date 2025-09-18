"""
RSI Calculator

Implements Relative Strength Index calculation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict

from interfaces.indicator import IndicatorInterface
from models.exceptions import IndicatorError


class RSICalculator(IndicatorInterface):
    """RSI (Relative Strength Index) calculator."""
    
    def __init__(self):
        """Initialize RSI calculator."""
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, data: pd.DataFrame, params: Dict) -> pd.Series:
        """
        Calculate RSI values.
        
        Args:
            data: DataFrame with OHLCV data
            params: Dictionary with 'period' parameter
            
        Returns:
            Series with RSI values
            
        Raises:
            IndicatorError: If calculation fails
        """
        try:
            period = params.get('period', 14)
            
            if len(data) < period + 1:
                raise IndicatorError(f"Insufficient data for RSI calculation. Need at least {period + 1} periods, got {len(data)}")
            
            # Use 'Close' column for RSI calculation
            if 'Close' not in data.columns:
                raise IndicatorError("Data must contain 'Close' column for RSI calculation")
            
            close_prices = data['Close']
            
            # Calculate price changes
            delta = close_prices.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses using exponential moving average
            avg_gains = gains.ewm(span=period, adjust=False).mean()
            avg_losses = losses.ewm(span=period, adjust=False).mean()
            
            # Calculate RS (Relative Strength)
            rs = avg_gains / avg_losses
            
            # Calculate RSI
            rsi = 100 - (100 / (1 + rs))
            
            # Handle division by zero (when avg_losses is 0)
            rsi = rsi.fillna(100)
            
            self.logger.debug(f"Calculated RSI with period {period}")
            return rsi
            
        except Exception as e:
            raise IndicatorError(f"RSI calculation failed: {e}")
    
    def get_required_periods(self, params: Dict) -> int:
        """
        Get minimum number of periods required for calculation.
        
        Args:
            params: Dictionary with parameters
            
        Returns:
            Minimum number of data points needed
        """
        period = params.get('period', 14)
        return period + 1  # Need one extra period for the initial delta calculation
    
    def validate_params(self, params: Dict) -> bool:
        """
        Validate RSI parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            period = params.get('period', 14)
            
            if not isinstance(period, int):
                return False
            
            if period < 2 or period > 100:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_default_params(self) -> Dict:
        """
        Get default parameters for RSI.
        
        Returns:
            Dictionary of default parameter values
        """
        return {'period': 14}
    
    def get_signal_levels(self) -> Dict[str, float]:
        """
        Get common RSI signal levels.
        
        Returns:
            Dictionary with signal level names and values
        """
        return {
            'oversold': 30.0,
            'overbought': 70.0,
            'extreme_oversold': 20.0,
            'extreme_overbought': 80.0
        }