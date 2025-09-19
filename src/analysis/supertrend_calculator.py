"""
SuperTrend Calculator

Implements SuperTrend indicator calculation using ATR (Average True Range).
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple

from src.interfaces.indicator import IndicatorInterface
from src.models.exceptions import IndicatorError


class SuperTrendCalculator(IndicatorInterface):
    """SuperTrend indicator calculator."""
    
    def __init__(self):
        """Initialize SuperTrend calculator."""
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, data: pd.DataFrame, params: Dict) -> pd.Series:
        """
        Calculate SuperTrend values.
        
        Args:
            data: DataFrame with OHLCV data (must contain High, Low, Close)
            params: Dictionary with 'atr_period' and 'multiplier' parameters
            
        Returns:
            Series with SuperTrend values
            
        Raises:
            IndicatorError: If calculation fails
        """
        try:
            atr_period = params.get('atr_period', 10)
            multiplier = params.get('multiplier', 3.0)
            
            if len(data) < atr_period + 1:
                raise IndicatorError(f"Insufficient data for SuperTrend calculation. Need at least {atr_period + 1} periods, got {len(data)}")
            
            # Validate required columns
            required_columns = ['High', 'Low', 'Close']
            for col in required_columns:
                if col not in data.columns:
                    raise IndicatorError(f"Data must contain '{col}' column for SuperTrend calculation")
            
            # Calculate ATR (Average True Range)
            atr = self._calculate_atr(data, atr_period)
            
            # Calculate SuperTrend
            supertrend = self._calculate_supertrend_values(data, atr, multiplier)
            
            self.logger.debug(f"Calculated SuperTrend with ATR period {atr_period} and multiplier {multiplier}")
            return supertrend
            
        except Exception as e:
            raise IndicatorError(f"SuperTrend calculation failed: {e}")
    
    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range (ATR).
        
        Args:
            data: DataFrame with High, Low, Close columns
            period: ATR calculation period
            
        Returns:
            Series with ATR values
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        prev_close = close.shift(1)
        
        # Calculate True Range components
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        # True Range is the maximum of the three components
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR using exponential moving average
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def _calculate_supertrend_values(self, data: pd.DataFrame, atr: pd.Series, multiplier: float) -> pd.Series:
        """
        Calculate SuperTrend values using ATR.
        
        Args:
            data: DataFrame with High, Low, Close columns
            atr: ATR series
            multiplier: SuperTrend multiplier
            
        Returns:
            Series with SuperTrend values
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # Calculate basic upper and lower bands
        hl_avg = (high + low) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize SuperTrend series
        supertrend = pd.Series(index=data.index, dtype=float)
        trend_direction = pd.Series(index=data.index, dtype=int)  # 1 for up, -1 for down
        
        # Set initial values
        supertrend.iloc[0] = lower_band.iloc[0]
        trend_direction.iloc[0] = 1
        
        # Calculate SuperTrend values
        for i in range(1, len(data)):
            # Current values
            curr_close = close.iloc[i]
            curr_upper = upper_band.iloc[i]
            curr_lower = lower_band.iloc[i]
            prev_close = close.iloc[i-1]
            prev_supertrend = supertrend.iloc[i-1]
            prev_trend = trend_direction.iloc[i-1]
            
            # Adjust bands based on previous values
            if curr_upper < upper_band.iloc[i-1] or prev_close > upper_band.iloc[i-1]:
                final_upper = curr_upper
            else:
                final_upper = upper_band.iloc[i-1]
            
            if curr_lower > lower_band.iloc[i-1] or prev_close < lower_band.iloc[i-1]:
                final_lower = curr_lower
            else:
                final_lower = lower_band.iloc[i-1]
            
            # Determine trend direction and SuperTrend value
            if prev_trend == 1:  # Previous trend was up
                if curr_close <= final_lower:
                    # Trend changes to down
                    supertrend.iloc[i] = final_upper
                    trend_direction.iloc[i] = -1
                else:
                    # Trend continues up
                    supertrend.iloc[i] = final_lower
                    trend_direction.iloc[i] = 1
            else:  # Previous trend was down
                if curr_close >= final_upper:
                    # Trend changes to up
                    supertrend.iloc[i] = final_lower
                    trend_direction.iloc[i] = 1
                else:
                    # Trend continues down
                    supertrend.iloc[i] = final_upper
                    trend_direction.iloc[i] = -1
        
        return supertrend
    
    def calculate_with_signals(self, data: pd.DataFrame, params: Dict) -> Dict:
        """
        Calculate SuperTrend with trend direction and signals.
        
        Args:
            data: DataFrame with OHLCV data
            params: Dictionary with SuperTrend parameters
            
        Returns:
            Dictionary with 'supertrend', 'trend_direction', 'signals', and 'atr'
        """
        try:
            atr_period = params.get('atr_period', 10)
            multiplier = params.get('multiplier', 3.0)
            
            # Calculate ATR
            atr = self._calculate_atr(data, atr_period)
            
            # Calculate SuperTrend
            supertrend = self._calculate_supertrend_values(data, atr, multiplier)
            
            # Determine trend direction
            close = data['Close']
            trend_direction = pd.Series(index=data.index, dtype=str)
            
            for i in range(len(data)):
                if close.iloc[i] > supertrend.iloc[i]:
                    trend_direction.iloc[i] = 'bullish'
                else:
                    trend_direction.iloc[i] = 'bearish'
            
            # Generate signals (trend changes)
            signals = pd.Series(0, index=data.index)
            prev_trend = None
            
            for i in range(len(data)):
                curr_trend = trend_direction.iloc[i]
                if prev_trend is not None and prev_trend != curr_trend:
                    if curr_trend == 'bullish':
                        signals.iloc[i] = 1  # Buy signal
                    else:
                        signals.iloc[i] = -1  # Sell signal
                prev_trend = curr_trend
            
            return {
                'supertrend': supertrend,
                'trend_direction': trend_direction,
                'signals': signals,
                'atr': atr
            }
            
        except Exception as e:
            raise IndicatorError(f"SuperTrend calculation with signals failed: {e}")
    
    def get_required_periods(self, params: Dict) -> int:
        """
        Get minimum number of periods required for calculation.
        
        Args:
            params: Dictionary with parameters
            
        Returns:
            Minimum number of data points needed
        """
        atr_period = params.get('atr_period', 10)
        return atr_period + 1  # Need one extra period for ATR calculation
    
    def validate_params(self, params: Dict) -> bool:
        """
        Validate SuperTrend parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            atr_period = params.get('atr_period', 10)
            multiplier = params.get('multiplier', 3.0)
            
            # Validate ATR period
            if not isinstance(atr_period, int) or atr_period < 1 or atr_period > 100:
                return False
            
            # Validate multiplier
            if not isinstance(multiplier, (int, float)) or multiplier <= 0 or multiplier > 10:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_default_params(self) -> Dict:
        """
        Get default parameters for SuperTrend.
        
        Returns:
            Dictionary of default parameter values
        """
        return {
            'atr_period': 10,
            'multiplier': 3.0
        }
    
    def detect_trend_changes(self, supertrend_data: Dict) -> pd.DataFrame:
        """
        Detect trend changes and reversal points.
        
        Args:
            supertrend_data: Dictionary from calculate_with_signals()
            
        Returns:
            DataFrame with trend change information
        """
        try:
            trend_direction = supertrend_data['trend_direction']
            signals = supertrend_data['signals']
            supertrend = supertrend_data['supertrend']
            
            # Create DataFrame with trend change details
            changes = []
            
            for i in range(len(signals)):
                if signals.iloc[i] != 0:
                    changes.append({
                        'timestamp': signals.index[i],
                        'signal_type': 'buy' if signals.iloc[i] == 1 else 'sell',
                        'trend_direction': trend_direction.iloc[i],
                        'supertrend_value': supertrend.iloc[i],
                        'signal_strength': abs(signals.iloc[i])
                    })
            
            return pd.DataFrame(changes)
            
        except Exception as e:
            raise IndicatorError(f"Trend change detection failed: {e}")
    
    def get_current_trend_strength(self, data: pd.DataFrame, supertrend_data: Dict) -> float:
        """
        Calculate current trend strength based on price distance from SuperTrend.
        
        Args:
            data: DataFrame with OHLCV data
            supertrend_data: Dictionary from calculate_with_signals()
            
        Returns:
            Trend strength value (0.0 to 1.0)
        """
        try:
            if len(data) == 0:
                return 0.0
            
            current_price = data['Close'].iloc[-1]
            current_supertrend = supertrend_data['supertrend'].iloc[-1]
            current_atr = supertrend_data['atr'].iloc[-1]
            
            # Calculate distance from SuperTrend as percentage of ATR
            distance = abs(current_price - current_supertrend)
            strength = min(1.0, distance / (current_atr * 2))  # Normalize to 0-1
            
            return strength
            
        except Exception as e:
            self.logger.error(f"Trend strength calculation failed: {e}")
            return 0.0