"""
EMA Crossover Strategy

Implements EMA crossover trading strategy for detecting trend changes.
"""

import pandas as pd
import logging
from typing import Dict, List
from datetime import datetime

from src.interfaces.strategy import StrategyInterface
from src.models.data_models import Signal, SignalType
from src.models.exceptions import StrategyError
from src.analysis.ema_calculator import EMACalculator


class EMACrossoverStrategy(StrategyInterface):
    """EMA crossover strategy implementation."""
    
    def __init__(self, short_period: int = 50, long_period: int = 200, 
                 approach_threshold: float = 0.02):
        """
        Initialize EMA crossover strategy.
        
        Args:
            short_period: Short EMA period (default 50)
            long_period: Long EMA period (default 200)
            approach_threshold: Threshold for "approaching" signals (default 2%)
        """
        self.logger = logging.getLogger(__name__)
        self.strategy_name = "ema_crossover"
        self.short_period = short_period
        self.long_period = long_period
        self.approach_threshold = approach_threshold
        self.ema_calculator = EMACalculator()
        
        # Validate parameters
        if not self.validate_conditions({
            'short_period': short_period,
            'long_period': long_period,
            'approach_threshold': approach_threshold
        }):
            raise StrategyError("Invalid EMA crossover strategy parameters")
    
    def generate_signal(self, data: pd.DataFrame, indicators: Dict) -> 'Signal':
        """
        Generate trading signal based on EMA crossover rules.
        
        Strategy Rules:
        - BUY: Short EMA crosses above Long EMA (bullish crossover)
        - SELL: Short EMA crosses below Long EMA (bearish crossover)
        - WEAK_BUY/WEAK_SELL: EMAs are approaching crossover threshold
        
        Args:
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators (can be empty, will calculate EMAs)
            
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
            
            # Calculate EMA crossover signals
            crossover_data = self.ema_calculator.calculate_ema_crossover_signals(
                data, self.short_period, self.long_period, self.approach_threshold
            )
            
            # Get latest crossover information
            latest_signal = crossover_data['signals'].iloc[-1]
            latest_crossover_type = crossover_data['crossover_type'].iloc[-1]
            latest_strength = crossover_data['signal_strength'].iloc[-1]
            latest_short_ema = crossover_data['short_ema'].iloc[-1]
            latest_long_ema = crossover_data['long_ema'].iloc[-1]
            latest_convergence = crossover_data['ema_convergence'].iloc[-1]
            
            current_price = latest_data['Close']
            
            # Determine signal type based on crossover
            signal_type = SignalType.NO_SIGNAL
            confidence = 0.0
            
            if latest_crossover_type == 'bullish':
                signal_type = SignalType.BUY
                confidence = min(0.9, max(0.6, latest_strength))
            elif latest_crossover_type == 'bearish':
                signal_type = SignalType.SELL
                confidence = min(0.9, max(0.6, latest_strength))
            elif latest_crossover_type == 'approaching_bullish':
                signal_type = SignalType.BUY
                confidence = min(0.5, max(0.3, latest_strength))
            elif latest_crossover_type == 'approaching_bearish':
                signal_type = SignalType.SELL
                confidence = min(0.5, max(0.3, latest_strength))
            
            # Create signal object
            signal = Signal(
                symbol=symbol,
                timestamp=latest_timestamp if isinstance(latest_timestamp, datetime) else datetime.now(),
                signal_type=signal_type,
                confidence=confidence,
                indicators={
                    'short_ema': float(latest_short_ema),
                    'long_ema': float(latest_long_ema),
                    'ema_convergence_pct': float(latest_convergence),
                    'crossover_type': latest_crossover_type,
                    'current_price': float(current_price),
                    'short_period': self.short_period,
                    'long_period': self.long_period
                },
                strategy_name=self.strategy_name
            )
            
            self.logger.debug(f"Generated {signal_type.value} signal for {symbol} "
                            f"({latest_crossover_type}) with confidence {confidence:.2f}")
            return signal
            
        except Exception as e:
            raise StrategyError(f"EMA crossover signal generation failed: {e}")
    
    def validate_conditions(self, conditions: Dict) -> bool:
        """
        Validate strategy conditions/parameters.
        
        Args:
            conditions: Dictionary of strategy conditions
            
        Returns:
            True if conditions are valid, False otherwise
        """
        try:
            short_period = conditions.get('short_period', self.short_period)
            long_period = conditions.get('long_period', self.long_period)
            approach_threshold = conditions.get('approach_threshold', self.approach_threshold)
            
            # Validate EMA periods
            if not isinstance(short_period, int) or not isinstance(long_period, int):
                return False
            
            if short_period < 1 or long_period < 1:
                return False
            
            if short_period >= long_period:
                return False
            
            # Validate approach threshold
            if not isinstance(approach_threshold, (int, float)):
                return False
            
            if approach_threshold <= 0 or approach_threshold > 0.1:  # Max 10%
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_required_indicators(self) -> List[str]:
        """
        Get list of indicators required by this strategy.
        
        Returns:
            List of indicator names (EMAs are calculated internally)
        """
        return []  # EMAs are calculated internally
    
    def get_strategy_params(self) -> Dict:
        """
        Get strategy parameters and their default values.
        
        Returns:
            Dictionary of parameter names and default values
        """
        return {
            'short_period': 50,
            'long_period': 200,
            'approach_threshold': 0.02
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
            self.logger.error(f"EMA crossover backtest failed: {e}")
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
            
            # Calculate EMA crossover data
            crossover_data = self.ema_calculator.calculate_ema_crossover_signals(
                data, self.short_period, self.long_period, self.approach_threshold
            )
            
            # Get latest signal strength
            latest_strength = crossover_data['signal_strength'].iloc[-1]
            latest_crossover_type = crossover_data['crossover_type'].iloc[-1]
            
            # Adjust strength based on crossover type
            if latest_crossover_type in ['bullish', 'bearish']:
                return latest_strength
            elif latest_crossover_type in ['approaching_bullish', 'approaching_bearish']:
                return latest_strength * 0.7  # Reduce strength for approaching signals
            else:
                return 0.0
            
        except Exception as e:
            self.logger.error(f"EMA crossover signal strength calculation failed: {e}")
            return 0.0
    
    def detect_crossover_type(self, data: pd.DataFrame) -> str:
        """
        Detect the current crossover type for the latest data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Crossover type string
        """
        try:
            crossover_data = self.ema_calculator.calculate_ema_crossover_signals(
                data, self.short_period, self.long_period, self.approach_threshold
            )
            
            return crossover_data['crossover_type'].iloc[-1]
            
        except Exception as e:
            self.logger.error(f"Crossover type detection failed: {e}")
            return 'none'
    
    def get_ema_values(self, data: pd.DataFrame) -> Dict:
        """
        Get current EMA values and convergence information.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with EMA information
        """
        try:
            crossover_data = self.ema_calculator.calculate_ema_crossover_signals(
                data, self.short_period, self.long_period, self.approach_threshold
            )
            
            return {
                'short_ema': crossover_data['short_ema'].iloc[-1],
                'long_ema': crossover_data['long_ema'].iloc[-1],
                'convergence_pct': crossover_data['ema_convergence'].iloc[-1],
                'short_period': self.short_period,
                'long_period': self.long_period
            }
            
        except Exception as e:
            self.logger.error(f"EMA values retrieval failed: {e}")
            return {}
    
    def calculate_crossover_strength(self, short_ema: float, long_ema: float, 
                                   price: float) -> float:
        """
        Calculate signal strength based on EMA relationship and price action.
        
        Args:
            short_ema: Short EMA value
            long_ema: Long EMA value
            price: Current price
            
        Returns:
            Signal strength between 0 and 1
        """
        try:
            # Calculate EMA convergence
            convergence_pct = abs((short_ema - long_ema) / long_ema * 100)
            
            # Price confirmation factor
            if short_ema > long_ema:  # Bullish setup
                price_confirmation = 1.0 if price > short_ema else 0.5
            else:  # Bearish setup
                price_confirmation = 1.0 if price < short_ema else 0.5
            
            # EMA momentum factor (higher convergence = stronger signal)
            momentum_factor = min(1.0, convergence_pct / 5.0)  # Normalize to 5%
            
            # Combined strength
            strength = (price_confirmation + momentum_factor) / 2
            
            return min(1.0, max(0.0, strength))
            
        except Exception as e:
            self.logger.error(f"Crossover strength calculation failed: {e}")
            return 0.0