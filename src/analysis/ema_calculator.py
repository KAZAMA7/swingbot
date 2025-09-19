"""
EMA Calculator

Implements Exponential Moving Average calculation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict

from src.interfaces.indicator import IndicatorInterface
from src.models.exceptions import IndicatorError


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
    
    def calculate_ema_crossover_signals(self, data: pd.DataFrame, short_period: int = 50, 
                                      long_period: int = 200, approach_threshold: float = 0.02) -> Dict:
        """
        Calculate EMA crossover signals between two EMAs.
        
        Args:
            data: DataFrame with OHLCV data
            short_period: Short EMA period (default 50)
            long_period: Long EMA period (default 200)
            approach_threshold: Threshold for "approaching" signals as percentage (default 2%)
            
        Returns:
            Dictionary with EMA values, crossover signals, and signal strength
        """
        try:
            if short_period >= long_period:
                raise IndicatorError(f"Short period ({short_period}) must be less than long period ({long_period})")
            
            if 'Close' not in data.columns:
                raise IndicatorError("Data must contain 'Close' column for EMA crossover calculation")
            
            close_prices = data['Close']
            
            # Calculate EMAs
            short_ema = close_prices.ewm(span=short_period, adjust=False).mean()
            long_ema = close_prices.ewm(span=long_period, adjust=False).mean()
            
            # Calculate EMA convergence (percentage difference)
            ema_convergence = ((short_ema - long_ema) / long_ema * 100).fillna(0)
            
            # Detect crossovers
            short_above_long = (short_ema > long_ema).fillna(False)
            short_above_long_prev = short_above_long.shift(1).fillna(False)
            
            # Initialize signals
            signals = pd.Series(0, index=data.index)
            crossover_type = pd.Series('none', index=data.index)
            
            # Bullish crossover: short EMA crosses above long EMA
            bullish_crossover = (~short_above_long_prev) & short_above_long
            signals[bullish_crossover] = 1
            crossover_type[bullish_crossover] = 'bullish'
            
            # Bearish crossover: short EMA crosses below long EMA
            bearish_crossover = short_above_long_prev & (~short_above_long)
            signals[bearish_crossover] = -1
            crossover_type[bearish_crossover] = 'bearish'
            
            # Approaching crossover detection
            ema_distance_pct = abs(ema_convergence)
            approaching_mask = (ema_distance_pct <= approach_threshold * 100) & (signals == 0)
            
            # Determine approaching direction
            for i in range(len(data)):
                if approaching_mask.iloc[i]:
                    if ema_convergence.iloc[i] > 0:
                        crossover_type.iloc[i] = 'approaching_bearish'  # Short above but close
                    else:
                        crossover_type.iloc[i] = 'approaching_bullish'  # Short below but close
            
            # Calculate signal strength based on EMA convergence and price action
            signal_strength = self._calculate_crossover_strength(
                data, short_ema, long_ema, ema_convergence, crossover_type
            )
            
            return {
                'short_ema': short_ema,
                'long_ema': long_ema,
                'ema_convergence': ema_convergence,
                'signals': signals,
                'crossover_type': crossover_type,
                'signal_strength': signal_strength,
                'short_period': short_period,
                'long_period': long_period
            }
            
        except Exception as e:
            raise IndicatorError(f"EMA crossover calculation failed: {e}")
    
    def _calculate_crossover_strength(self, data: pd.DataFrame, short_ema: pd.Series, 
                                    long_ema: pd.Series, ema_convergence: pd.Series, 
                                    crossover_type: pd.Series) -> pd.Series:
        """
        Calculate signal strength for EMA crossovers.
        
        Args:
            data: DataFrame with OHLCV data
            short_ema: Short EMA series
            long_ema: Long EMA series
            ema_convergence: EMA convergence percentage series
            crossover_type: Crossover type series
            
        Returns:
            Series with signal strength values (0.0 to 1.0)
        """
        try:
            close_prices = data['Close']
            signal_strength = pd.Series(0.0, index=data.index)
            
            for i in range(len(data)):
                crossover = crossover_type.iloc[i]
                
                if crossover in ['bullish', 'bearish']:
                    # Strong signal for actual crossovers
                    # Factor in price position relative to EMAs
                    price = close_prices.iloc[i]
                    short_val = short_ema.iloc[i]
                    long_val = long_ema.iloc[i]
                    
                    if crossover == 'bullish':
                        # Bullish crossover strength
                        price_confirmation = 1.0 if price > short_val else 0.5
                        ema_momentum = min(1.0, abs(ema_convergence.iloc[i]) / 5.0)  # Normalize to 5%
                        signal_strength.iloc[i] = min(1.0, (price_confirmation + ema_momentum) / 2)
                    
                    elif crossover == 'bearish':
                        # Bearish crossover strength
                        price_confirmation = 1.0 if price < short_val else 0.5
                        ema_momentum = min(1.0, abs(ema_convergence.iloc[i]) / 5.0)
                        signal_strength.iloc[i] = min(1.0, (price_confirmation + ema_momentum) / 2)
                
                elif crossover in ['approaching_bullish', 'approaching_bearish']:
                    # Moderate signal for approaching crossovers
                    convergence_strength = 1.0 - (abs(ema_convergence.iloc[i]) / 2.0)  # Closer = stronger
                    signal_strength.iloc[i] = max(0.3, min(0.7, convergence_strength))
            
            return signal_strength
            
        except Exception as e:
            raise IndicatorError(f"Crossover strength calculation failed: {e}")
    
    def detect_ema_crossover_points(self, crossover_data: Dict) -> pd.DataFrame:
        """
        Extract crossover points with detailed information.
        
        Args:
            crossover_data: Dictionary from calculate_ema_crossover_signals()
            
        Returns:
            DataFrame with crossover point details
        """
        try:
            signals = crossover_data['signals']
            crossover_type = crossover_data['crossover_type']
            signal_strength = crossover_data['signal_strength']
            short_ema = crossover_data['short_ema']
            long_ema = crossover_data['long_ema']
            ema_convergence = crossover_data['ema_convergence']
            
            # Find all crossover points
            crossover_points = []
            
            for i in range(len(signals)):
                if crossover_type.iloc[i] != 'none':
                    crossover_points.append({
                        'timestamp': signals.index[i],
                        'crossover_type': crossover_type.iloc[i],
                        'signal': signals.iloc[i],
                        'signal_strength': signal_strength.iloc[i],
                        'short_ema_value': short_ema.iloc[i],
                        'long_ema_value': long_ema.iloc[i],
                        'ema_convergence_pct': ema_convergence.iloc[i],
                        'short_period': crossover_data['short_period'],
                        'long_period': crossover_data['long_period']
                    })
            
            return pd.DataFrame(crossover_points)
            
        except Exception as e:
            raise IndicatorError(f"Crossover point detection failed: {e}")