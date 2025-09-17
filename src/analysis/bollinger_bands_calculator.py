"""
Bollinger Bands Calculator

Implements Bollinger Bands calculation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict

from ..interfaces.indicator import IndicatorInterface
from ..models.exceptions import IndicatorError


class BollingerBandsCalculator(IndicatorInterface):
    """Bollinger Bands calculator."""
    
    def __init__(self):
        """Initialize Bollinger Bands calculator."""
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, data: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Calculate Bollinger Bands values.
        
        Args:
            data: DataFrame with OHLCV data
            params: Dictionary with 'period' and 'std_dev' parameters
            
        Returns:
            DataFrame with upper_band, middle_band, lower_band, and bandwidth columns
            
        Raises:
            IndicatorError: If calculation fails
        """
        try:
            period = params.get('period', 20)
            std_dev = params.get('std_dev', 2)
            
            if len(data) < period:
                raise IndicatorError(f"Insufficient data for Bollinger Bands calculation. Need at least {period} periods, got {len(data)}")
            
            # Use 'Close' column for Bollinger Bands calculation
            if 'Close' not in data.columns:
                raise IndicatorError("Data must contain 'Close' column for Bollinger Bands calculation")
            
            close_prices = data['Close']
            
            # Calculate middle band (Simple Moving Average)
            middle_band = close_prices.rolling(window=period).mean()
            
            # Calculate standard deviation
            rolling_std = close_prices.rolling(window=period).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (rolling_std * std_dev)
            lower_band = middle_band - (rolling_std * std_dev)
            
            # Calculate bandwidth (volatility measure)
            bandwidth = (upper_band - lower_band) / middle_band * 100
            
            # Calculate %B (position within bands)
            percent_b = (close_prices - lower_band) / (upper_band - lower_band)
            
            # Create result DataFrame
            result = pd.DataFrame({
                'upper_band': upper_band,
                'middle_band': middle_band,
                'lower_band': lower_band,
                'bandwidth': bandwidth,
                'percent_b': percent_b
            }, index=data.index)
            
            self.logger.debug(f"Calculated Bollinger Bands with period {period}, std_dev {std_dev}")
            return result
            
        except Exception as e:
            raise IndicatorError(f"Bollinger Bands calculation failed: {e}")
    
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
        Validate Bollinger Bands parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            period = params.get('period', 20)
            std_dev = params.get('std_dev', 2)
            
            if not isinstance(period, int):
                return False
            
            if period < 2 or period > 200:
                return False
            
            if not isinstance(std_dev, (int, float)):
                return False
            
            if std_dev <= 0 or std_dev > 5:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_default_params(self) -> Dict:
        """
        Get default parameters for Bollinger Bands.
        
        Returns:
            Dictionary of default parameter values
        """
        return {
            'period': 20,
            'std_dev': 2
        }
    
    def detect_squeeze(self, bb_data: pd.DataFrame, threshold: float = 10.0) -> pd.Series:
        """
        Detect Bollinger Band squeeze (low volatility periods).
        
        Args:
            bb_data: DataFrame with Bollinger Bands data
            threshold: Bandwidth threshold for squeeze detection
            
        Returns:
            Boolean Series indicating squeeze periods
        """
        try:
            if 'bandwidth' not in bb_data.columns:
                raise IndicatorError("Bollinger Bands data must contain 'bandwidth' column")
            
            # Calculate rolling minimum of bandwidth over last 20 periods
            min_bandwidth = bb_data['bandwidth'].rolling(window=20).min()
            
            # Squeeze occurs when current bandwidth is near the minimum
            squeeze = bb_data['bandwidth'] <= (min_bandwidth * 1.1)
            
            return squeeze
            
        except Exception as e:
            raise IndicatorError(f"Squeeze detection failed: {e}")
    
    def get_breakout_signals(self, data: pd.DataFrame, bb_data: pd.DataFrame) -> pd.Series:
        """
        Generate breakout signals based on price crossing bands.
        
        Args:
            data: Original OHLCV data
            bb_data: Bollinger Bands data
            
        Returns:
            Series with breakout signals (1 for upper breakout, -1 for lower breakout, 0 for no signal)
        """
        try:
            if 'Close' not in data.columns:
                raise IndicatorError("Data must contain 'Close' column")
            
            close_prices = data['Close']
            upper_band = bb_data['upper_band']
            lower_band = bb_data['lower_band']
            
            # Initialize signals
            signals = pd.Series(0, index=data.index)
            
            # Upper breakout: price closes above upper band
            upper_breakout = close_prices > upper_band
            signals[upper_breakout] = 1
            
            # Lower breakout: price closes below lower band
            lower_breakout = close_prices < lower_band
            signals[lower_breakout] = -1
            
            return signals
            
        except Exception as e:
            raise IndicatorError(f"Breakout signal generation failed: {e}")