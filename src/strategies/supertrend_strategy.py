"""
SuperTrend Strategy

Implements SuperTrend trading strategy for trend identification and reversal detection.
"""

import pandas as pd
import logging
from typing import Dict, List
from datetime import datetime

from src.interfaces.strategy import StrategyInterface
from src.models.data_models import Signal, SignalType
from src.models.exceptions import StrategyError
from src.analysis.supertrend_calculator import SuperTrendCalculator


class SuperTrendStrategy(StrategyInterface):
    """SuperTrend strategy implementation."""
    
    def __init__(self, atr_period: int = 10, multiplier: float = 3.0):
        """
        Initialize SuperTrend strategy.
        
        Args:
            atr_period: ATR calculation period (default 10)
            multiplier: SuperTrend multiplier (default 3.0)
        """
        self.logger = logging.getLogger(__name__)
        self.strategy_name = "supertrend"
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.supertrend_calculator = SuperTrendCalculator()
        
        # Validate parameters
        if not self.validate_conditions({
            'atr_period': atr_period,
            'multiplier': multiplier
        }):
            raise StrategyError("Invalid SuperTrend strategy parameters")
    
    def generate_signal(self, data: pd.DataFrame, indicators: Dict) -> 'Signal':
        """
        Generate trading signal based on SuperTrend rules.
        
        Strategy Rules:
        - BUY: Price crosses above SuperTrend line (trend reversal to bullish)
        - SELL: Price crosses below SuperTrend line (trend reversal to bearish)
        - HOLD: Price continues in same trend direction
        
        Args:
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators (can be empty, will calculate SuperTrend)
            
        Returns:
            Signal object with trading recommendation
            
        Raises:
            StrategyError: If signal generation fails
        """
        try:
            if data.empty:
                raise StrategyError("No data provided for signal generation")
            
            # Get the latest data point
            latest_data = data.iloc[-1]
            latest_timestamp = data.index[-1]
            symbol = getattr(latest_data, 'symbol', 'UNKNOWN')
            
            # Calculate SuperTrend with signals
            supertrend_data = self.supertrend_calculator.calculate_with_signals(
                data, {'atr_period': self.atr_period, 'multiplier': self.multiplier}
            )
            
            # Get latest SuperTrend information
            latest_signal = supertrend_data['signals'].iloc[-1]
            latest_trend = supertrend_data['trend_direction'].iloc[-1]
            latest_supertrend = supertrend_data['supertrend'].iloc[-1]
            latest_atr = supertrend_data['atr'].iloc[-1]
            
            current_price = latest_data['Close']
            
            # Calculate trend strength
            trend_strength = self.supertrend_calculator.get_current_trend_strength(
                data, supertrend_data
            )
            
            # Determine signal type based on SuperTrend
            signal_type = SignalType.NO_SIGNAL
            confidence = 0.0
            
            if latest_signal == 1:  # Bullish reversal
                signal_type = SignalType.BUY
                confidence = min(0.9, max(0.6, trend_strength))
            elif latest_signal == -1:  # Bearish reversal
                signal_type = SignalType.SELL
                confidence = min(0.9, max(0.6, trend_strength))
            else:
                # No reversal, but check trend strength for continuation signals
                if latest_trend == 'bullish' and trend_strength > 0.7:
                    signal_type = SignalType.BUY
                    confidence = min(0.5, trend_strength * 0.7)
                elif latest_trend == 'bearish' and trend_strength > 0.7:
                    signal_type = SignalType.SELL
                    confidence = min(0.5, trend_strength * 0.7)
            
            # Create signal object
            signal = Signal(
                symbol=symbol,
                timestamp=latest_timestamp if isinstance(latest_timestamp, datetime) else datetime.now(),
                signal_type=signal_type,
                confidence=confidence,
                indicators={
                    'supertrend_value': float(latest_supertrend),
                    'trend_direction': latest_trend,
                    'trend_strength': float(trend_strength),
                    'atr_value': float(latest_atr),
                    'current_price': float(current_price),
                    'atr_period': self.atr_period,
                    'multiplier': self.multiplier,
                    'trend_reversal': bool(latest_signal != 0)
                },
                strategy_name=self.strategy_name
            )
            
            self.logger.debug(f"Generated {signal_type.value} signal for {symbol} "
                            f"(trend: {latest_trend}, strength: {trend_strength:.2f}) "
                            f"with confidence {confidence:.2f}")
            return signal
            
        except Exception as e:
            raise StrategyError(f"SuperTrend signal generation failed: {e}")
    
    def validate_conditions(self, conditions: Dict) -> bool:
        """
        Validate strategy conditions/parameters.
        
        Args:
            conditions: Dictionary of strategy conditions
            
        Returns:
            True if conditions are valid, False otherwise
        """
        try:
            atr_period = conditions.get('atr_period', self.atr_period)
            multiplier = conditions.get('multiplier', self.multiplier)
            
            # Validate ATR period
            if not isinstance(atr_period, int):
                return False
            
            if atr_period < 1 or atr_period > 100:
                return False
            
            # Validate multiplier
            if not isinstance(multiplier, (int, float)):
                return False
            
            if multiplier <= 0 or multiplier > 10:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_required_indicators(self) -> List[str]:
        """
        Get list of indicators required by this strategy.
        
        Returns:
            List of indicator names (SuperTrend is calculated internally)
        """
        return []  # SuperTrend is calculated internally
    
    def get_strategy_params(self) -> Dict:
        """
        Get strategy parameters and their default values.
        
        Returns:
            Dictionary of parameter names and default values
        """
        return {
            'atr_period': 10,
            'multiplier': 3.0
        }
    
    def backtest_signal(self, data: pd.DataFrame, indicators: Dict, 
                       entry_price: float, exit_price: float, 
                       signal_type: SignalType) -> Dict:
        """
        Backtest a signal to evaluate performance.
        
        Args:
            data: Historical price data
            indicators: Historical indicator data
            entry_price: Entry price for the trade
            exit_price: Exit price for the trade
            signal_type: Type of signal (BUY/SELL)
            
        Returns:
            Dictionary with backtest results
        """
        try:
            if signal_type == SignalType.BUY:
                return_pct = (exit_price - entry_price) / entry_price * 100
            elif signal_type == SignalType.SELL:
                return_pct = (entry_price - exit_price) / entry_price * 100
            else:
                return_pct = 0
            
            return {
                'return_percent': return_pct,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'signal_type': signal_type.value,
                'profitable': return_pct > 0,
                'strategy': self.strategy_name
            }
            
        except Exception as e:
            self.logger.error(f"SuperTrend backtest failed: {e}")
            return {'return_percent': 0, 'profitable': False}
    
    def get_signal_strength(self, data: pd.DataFrame, indicators: Dict) -> float:
        """
        Calculate signal strength without generating actual signal.
        
        Args:
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            
        Returns:
            Signal strength between 0 and 1
        """
        try:
            if data.empty:
                return 0.0
            
            # Calculate SuperTrend data
            supertrend_data = self.supertrend_calculator.calculate_with_signals(
                data, {'atr_period': self.atr_period, 'multiplier': self.multiplier}
            )
            
            # Get trend strength
            trend_strength = self.supertrend_calculator.get_current_trend_strength(
                data, supertrend_data
            )
            
            # Check for recent trend reversal
            latest_signal = supertrend_data['signals'].iloc[-1]
            if latest_signal != 0:
                return min(1.0, trend_strength + 0.3)  # Boost for reversal signals
            
            return trend_strength
            
        except Exception as e:
            self.logger.error(f"SuperTrend signal strength calculation failed: {e}")
            return 0.0
    
    def detect_trend_change(self, data: pd.DataFrame) -> Dict:
        """
        Detect trend changes and reversal points.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with trend change information
        """
        try:
            supertrend_data = self.supertrend_calculator.calculate_with_signals(
                data, {'atr_period': self.atr_period, 'multiplier': self.multiplier}
            )
            
            trend_changes = self.supertrend_calculator.detect_trend_changes(supertrend_data)
            
            # Get latest trend information
            latest_trend = supertrend_data['trend_direction'].iloc[-1]
            latest_signal = supertrend_data['signals'].iloc[-1]
            
            return {
                'current_trend': latest_trend,
                'trend_reversal': bool(latest_signal != 0),
                'reversal_type': 'bullish' if latest_signal == 1 else 'bearish' if latest_signal == -1 else 'none',
                'trend_changes': trend_changes
            }
            
        except Exception as e:
            self.logger.error(f"Trend change detection failed: {e}")
            return {'current_trend': 'unknown', 'trend_reversal': False}
    
    def get_supertrend_values(self, data: pd.DataFrame) -> Dict:
        """
        Get current SuperTrend values and trend information.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with SuperTrend information
        """
        try:
            supertrend_data = self.supertrend_calculator.calculate_with_signals(
                data, {'atr_period': self.atr_period, 'multiplier': self.multiplier}
            )
            
            return {
                'supertrend_value': supertrend_data['supertrend'].iloc[-1],
                'trend_direction': supertrend_data['trend_direction'].iloc[-1],
                'atr_value': supertrend_data['atr'].iloc[-1],
                'atr_period': self.atr_period,
                'multiplier': self.multiplier
            }
            
        except Exception as e:
            self.logger.error(f"SuperTrend values retrieval failed: {e}")
            return {}
    
    def is_price_above_supertrend(self, data: pd.DataFrame) -> bool:
        """
        Check if current price is above SuperTrend line.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            True if price is above SuperTrend, False otherwise
        """
        try:
            if data.empty:
                return False
            
            supertrend_data = self.supertrend_calculator.calculate_with_signals(
                data, {'atr_period': self.atr_period, 'multiplier': self.multiplier}
            )
            
            current_price = data['Close'].iloc[-1]
            current_supertrend = supertrend_data['supertrend'].iloc[-1]
            
            return current_price > current_supertrend
            
        except Exception as e:
            self.logger.error(f"Price vs SuperTrend comparison failed: {e}")
            return False
    
    def calculate_trend_strength_score(self, data: pd.DataFrame) -> float:
        """
        Calculate a comprehensive trend strength score.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Trend strength score between -1 (strong bearish) and 1 (strong bullish)
        """
        try:
            supertrend_data = self.supertrend_calculator.calculate_with_signals(
                data, {'atr_period': self.atr_period, 'multiplier': self.multiplier}
            )
            
            current_price = data['Close'].iloc[-1]
            current_supertrend = supertrend_data['supertrend'].iloc[-1]
            current_atr = supertrend_data['atr'].iloc[-1]
            current_trend = supertrend_data['trend_direction'].iloc[-1]
            
            # Calculate distance from SuperTrend as percentage of ATR
            distance = (current_price - current_supertrend) / current_atr
            
            # Normalize to -1 to 1 scale
            strength_score = max(-1.0, min(1.0, distance / 2.0))
            
            # Apply trend direction
            if current_trend == 'bearish':
                strength_score = -abs(strength_score)
            else:
                strength_score = abs(strength_score)
            
            return strength_score
            
        except Exception as e:
            self.logger.error(f"Trend strength score calculation failed: {e}")
            return 0.0