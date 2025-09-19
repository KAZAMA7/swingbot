"""
Swing Trading Strategy

Implements swing trading strategy using RSI, Bollinger Bands, and EMA.
"""

import pandas as pd
import logging
from typing import Dict, List
from datetime import datetime

from src.interfaces.strategy import StrategyInterface
from src.models.data_models import Signal, SignalType
from src.models.exceptions import StrategyError


class SwingTradingStrategy(StrategyInterface):
    """Swing trading strategy implementation."""
    
    def __init__(self):
        """Initialize swing trading strategy."""
        self.logger = logging.getLogger(__name__)
        self.strategy_name = "swing_trading"
    
    def generate_signal(self, data: pd.DataFrame, indicators: Dict) -> 'Signal':
        """
        Generate trading signal based on swing trading rules.
        
        Strategy Rules:
        - BUY: RSI < oversold_threshold AND price < BB_lower AND price > EMA
        - SELL: RSI > overbought_threshold AND price > BB_upper AND price < EMA
        
        Args:
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            
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
            
            # Extract required indicators
            rsi_values = indicators.get('rsi')
            bb_data = indicators.get('bollinger_bands')
            ema_values = indicators.get('ema')
            
            if rsi_values is None or bb_data is None or ema_values is None:
                raise StrategyError("Missing required indicators: RSI, Bollinger Bands, or EMA")
            
            # Get latest indicator values
            latest_rsi = rsi_values.iloc[-1] if hasattr(rsi_values, 'iloc') else rsi_values
            latest_bb_upper = bb_data['upper_band'].iloc[-1] if hasattr(bb_data, 'iloc') else bb_data['upper_band']
            latest_bb_lower = bb_data['lower_band'].iloc[-1] if hasattr(bb_data, 'iloc') else bb_data['lower_band']
            latest_ema = ema_values.iloc[-1] if hasattr(ema_values, 'iloc') else ema_values
            
            current_price = latest_data['Close']
            
            # Get strategy parameters (with defaults)
            rsi_oversold = 30
            rsi_overbought = 70
            
            # Initialize signal components
            signal_type = SignalType.NO_SIGNAL
            confidence = 0.0
            
            # Check BUY conditions
            rsi_buy_condition = latest_rsi < rsi_oversold
            bb_buy_condition = current_price < latest_bb_lower
            ema_buy_condition = current_price > latest_ema
            
            # Check SELL conditions
            rsi_sell_condition = latest_rsi > rsi_overbought
            bb_sell_condition = current_price > latest_bb_upper
            ema_sell_condition = current_price < latest_ema
            
            # Generate BUY signal
            if rsi_buy_condition and bb_buy_condition and ema_buy_condition:
                signal_type = SignalType.BUY
                # Calculate confidence based on how strong the conditions are
                rsi_strength = (rsi_oversold - latest_rsi) / rsi_oversold
                bb_strength = (latest_bb_lower - current_price) / latest_bb_lower
                ema_strength = (current_price - latest_ema) / latest_ema
                confidence = min(0.9, max(0.5, (rsi_strength + bb_strength + ema_strength) / 3))
            
            # Generate SELL signal
            elif rsi_sell_condition and bb_sell_condition and ema_sell_condition:
                signal_type = SignalType.SELL
                # Calculate confidence based on how strong the conditions are
                rsi_strength = (latest_rsi - rsi_overbought) / (100 - rsi_overbought)
                bb_strength = (current_price - latest_bb_upper) / latest_bb_upper
                ema_strength = (latest_ema - current_price) / latest_ema
                confidence = min(0.9, max(0.5, (rsi_strength + bb_strength + ema_strength) / 3))
            
            # Create signal object
            signal = Signal(
                symbol=symbol,
                timestamp=latest_timestamp if isinstance(latest_timestamp, datetime) else datetime.now(),
                signal_type=signal_type,
                confidence=confidence,
                indicators={
                    'rsi': float(latest_rsi),
                    'bb_upper': float(latest_bb_upper),
                    'bb_lower': float(latest_bb_lower),
                    'ema': float(latest_ema),
                    'current_price': float(current_price)
                },
                strategy_name=self.strategy_name
            )
            
            self.logger.debug(f"Generated {signal_type.value} signal for {symbol} with confidence {confidence:.2f}")
            return signal
            
        except Exception as e:
            raise StrategyError(f"Signal generation failed: {e}")
    
    def validate_conditions(self, conditions: Dict) -> bool:
        """
        Validate strategy conditions/parameters.
        
        Args:
            conditions: Dictionary of strategy conditions
            
        Returns:
            True if conditions are valid, False otherwise
        """
        try:
            rsi_oversold = conditions.get('rsi_oversold', 30)
            rsi_overbought = conditions.get('rsi_overbought', 70)
            
            # Validate RSI thresholds
            if not isinstance(rsi_oversold, (int, float)) or not 0 <= rsi_oversold <= 100:
                return False
            
            if not isinstance(rsi_overbought, (int, float)) or not 0 <= rsi_overbought <= 100:
                return False
            
            if rsi_oversold >= rsi_overbought:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_required_indicators(self) -> List[str]:
        """
        Get list of indicators required by this strategy.
        
        Returns:
            List of indicator names
        """
        return ['rsi', 'bollinger_bands', 'ema']
    
    def get_strategy_params(self) -> Dict:
        """
        Get strategy parameters and their default values.
        
        Returns:
            Dictionary of parameter names and default values
        """
        return {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'rsi_period': 14,
            'bb_period': 20,
            'bb_std_dev': 2,
            'ema_period': 20
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
                'profitable': return_pct > 0
            }
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
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
            
            latest_data = data.iloc[-1]
            
            # Extract indicators
            rsi_values = indicators.get('rsi')
            bb_data = indicators.get('bollinger_bands')
            ema_values = indicators.get('ema')
            
            if rsi_values is None or bb_data is None or ema_values is None:
                return 0.0
            
            latest_rsi = rsi_values.iloc[-1]
            latest_bb_upper = bb_data['upper_band'].iloc[-1]
            latest_bb_lower = bb_data['lower_band'].iloc[-1]
            latest_ema = ema_values.iloc[-1]
            current_price = latest_data['Close']
            
            # Calculate how close we are to signal conditions
            rsi_buy_strength = max(0, (30 - latest_rsi) / 30) if latest_rsi < 50 else 0
            rsi_sell_strength = max(0, (latest_rsi - 70) / 30) if latest_rsi > 50 else 0
            
            bb_buy_strength = max(0, (latest_bb_lower - current_price) / latest_bb_lower) if current_price < latest_bb_lower else 0
            bb_sell_strength = max(0, (current_price - latest_bb_upper) / latest_bb_upper) if current_price > latest_bb_upper else 0
            
            ema_buy_strength = max(0, (current_price - latest_ema) / latest_ema) if current_price > latest_ema else 0
            ema_sell_strength = max(0, (latest_ema - current_price) / latest_ema) if current_price < latest_ema else 0
            
            # Return the maximum strength (either buy or sell)
            buy_strength = (rsi_buy_strength + bb_buy_strength + ema_buy_strength) / 3
            sell_strength = (rsi_sell_strength + bb_sell_strength + ema_sell_strength) / 3
            
            return max(buy_strength, sell_strength)
            
        except Exception as e:
            self.logger.error(f"Signal strength calculation failed: {e}")
            return 0.0