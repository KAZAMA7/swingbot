"""
EMA Calculator

Implements Exponential Moving Average calculation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict

from ..interfaces.indicator import IndicatorInterface
from ..models.exceptions import IndicatorError


class EMACalculator(IndicatorInterface):
    """EMA (Exponential Moving Average) calculator."""
    
    def __init__(self):
        """Initialize EMA calculator."""
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, data: pd.DataFrame, params: Dict) -> pd.Series:
        """
        Calculate EMA values.
        
        Args:
            data: DataFrame with OHLCV data
            params: Dictionary with 'period' parameter
            
        Returns:
            Series with EMA values
            
        Raises:
            IndicatorError: If calculation fails
        """
        try:
            period = params.get('period', 20)
            
            if len(data) < period:
                raise IndicatorError(f"Insufficient data for EMA calculation. Need at least {period} periods, got {len(data)}")
            
            # Use 'Close' column for EMA calculation
            if 'Close' not in data.columns:
                raise IndicatorError("Data must contain 'Close' column for EMA calculation")
            
            close_prices = data['Close']
            
            # Calculate EMA using pandas ewm function
            ema = close_prices.ewm(span=period, adjust=False).mean()
            
            self.logger.debug(f"Calculated EMA with period {period}")
            return ema
            
        except Exception as e:
            raise IndicatorError(f"EMA calculation failed: {e}")
    
    def get_required_periods(self, params: Dict) -> int:
        """
        Get minimum number of periods required for calculation.
        
        Args:
            params: Dictionary with parameters
            
        Returns:
            Minimum number of data points needed
        """
        period = params.get('period', 20)
        return period
    
    def validate_params(self, params: Dict) -> bool:
        """
        Validate EMA parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            period = params.get('period', 20)
            
            if not isinstance(period, int):
                return False
            
            if period < 1 or period > 500:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_default_params(self) -> Dict:
        """
        Get default parameters for EMA.
        
        Returns:
            Dictionary of default parameter values
        """
        return {'period': 20}
    
    def calculate_multiple_emas(self, data: pd.DataFrame, periods: list) -> pd.DataFrame:
        """
        Calculate multiple EMAs with different periods.
        
        Args:
            data: DataFrame with OHLCV data
            periods: List of periods to calculate
            
        Returns:
            DataFrame with EMA columns for each period
        """
        try:
            if 'Close' not in data.columns:
                raise IndicatorError("Data must contain 'Close' column for EMA calculation")
            
            close_prices = data['Close']
            result = pd.DataFrame(index=data.index)
            
            for period in periods:
                if not isinstance(period, int) or period < 1:
                    self.logger.warning(f"Invalid EMA period: {period}, skipping")
                    continue
                
                ema = close_prices.ewm(span=period, adjust=False).mean()
                result[f'ema_{period}'] = ema
            
            self.logger.debug(f"Calculated EMAs for periods: {periods}")
            return result
            
        except Exception as e:
            raise IndicatorError(f"Multiple EMA calculation failed: {e}")
    
    def detect_crossovers(self, price_data: pd.Series, ema_data: pd.Series) -> pd.Series:
        """
        Detect price crossovers with EMA.
        
        Args:
            price_data: Price series (usually Close prices)
            ema_data: EMA series
            
        Returns:
            Series with crossover signals (1 for bullish crossover, -1 for bearish crossover, 0 for no signal)
        """
        try:
            # Calculate crossovers
            price_above_ema = price_data > ema_data
            price_above_ema_prev = price_above_ema.shift(1)
            
            # Initialize signals
            signals = pd.Series(0, index=price_data.index)
            
            # Bullish crossover: price crosses above EMA
            bullish_crossover = (~price_above_ema_prev) & price_above_ema
            signals[bullish_crossover] = 1
            
            # Bearish crossover: price crosses below EMA
            bearish_crossover = price_above_ema_prev & (~price_above_ema)
            signals[bearish_crossover] = -1
            
            return signals
            
        except Exception as e:
            raise IndicatorError(f"Crossover detection failed: {e}")
    
    def calculate_ema_slope(self, ema_data: pd.Series, periods: int = 5) -> pd.Series:
        """
        Calculate EMA slope to determine trend direction.
        
        Args:
            ema_data: EMA series
            periods: Number of periods to calculate slope over
            
        Returns:
            Series with EMA slope values
        """
        try:
            # Calculate percentage change over specified periods
            slope = ema_data.pct_change(periods) * 100
            
            return slope
            
        except Exception as e:
            raise IndicatorError(f"EMA slope calculation failed: {e}")