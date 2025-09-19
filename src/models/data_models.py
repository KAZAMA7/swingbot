"""
Data Models

Core data structures for the trading bot.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class OHLCV:
    """Open, High, Low, Close, Volume data structure."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def __post_init__(self):
        """Validate data after initialization."""
        if self.high < self.low:
            raise ValueError("High price cannot be less than low price")
        if self.open < 0 or self.close < 0:
            raise ValueError("Prices cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")


@dataclass
class Signal:
    """Trading signal data structure."""
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    confidence: float
    indicators: Dict[str, float]
    strategy_name: str
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.strategy_name:
            raise ValueError("Strategy name cannot be empty")


@dataclass
class IndicatorValue:
    """Technical indicator value data structure."""
    symbol: str
    timestamp: datetime
    indicator_name: str
    value: float
    parameters: Dict
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.indicator_name:
            raise ValueError("Indicator name cannot be empty")


@dataclass
class CompositeSignal:
    """Composite signal from multiple strategies."""
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    composite_score: float  # -100 to +100
    confidence: float
    contributing_signals: list  # List[Signal]
    strategy_weights: Dict[str, float]
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not -100.0 <= self.composite_score <= 100.0:
            raise ValueError("Composite score must be between -100.0 and 100.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.contributing_signals:
            raise ValueError("Contributing signals cannot be empty")
    
    def get_signal_breakdown(self) -> Dict[str, float]:
        """Get breakdown of individual strategy contributions."""
        breakdown = {}
        total_weight = sum(self.strategy_weights.values())
        
        for signal in self.contributing_signals:
            strategy_name = signal.strategy_name
            weight = self.strategy_weights.get(strategy_name, 1.0)
            normalized_weight = weight / total_weight if total_weight > 0 else 0
            
            # Convert signal to score (-100 to +100)
            if signal.signal_type == SignalType.BUY:
                signal_score = signal.confidence * 100
            elif signal.signal_type == SignalType.SELL:
                signal_score = -signal.confidence * 100
            else:
                signal_score = 0
            
            breakdown[strategy_name] = {
                'signal_score': signal_score,
                'weight': weight,
                'weighted_contribution': signal_score * normalized_weight,
                'confidence': signal.confidence
            }
        
        return breakdown
    
    def get_strongest_signal(self) -> 'Signal':
        """Get the signal with highest confidence."""
        if not self.contributing_signals:
            return None
        
        return max(self.contributing_signals, key=lambda s: s.confidence)
    
    def get_strategy_count(self) -> int:
        """Get number of contributing strategies."""
        return len(set(signal.strategy_name for signal in self.contributing_signals))


@dataclass
class EMACrossoverSignal(Signal):
    """EMA crossover specific signal."""
    short_ema_period: int = 50
    long_ema_period: int = 200
    short_ema_value: float = 0.0
    long_ema_value: float = 0.0
    crossover_type: str = 'none'  # 'bullish', 'bearish', 'approaching'
    ema_convergence: float = 0.0  # Percentage difference between EMAs
    
    def __post_init__(self):
        """Validate data after initialization."""
        super().__post_init__()
        if self.short_ema_period >= self.long_ema_period:
            raise ValueError("Short EMA period must be less than long EMA period")
        if self.crossover_type not in ['none', 'bullish', 'bearish', 'approaching_bullish', 'approaching_bearish']:
            raise ValueError("Invalid crossover type")
    
    def get_ema_distance_pct(self) -> float:
        """Get percentage distance between EMAs."""
        if self.long_ema_value == 0:
            return 0.0
        return abs(self.ema_convergence)
    
    def is_approaching_crossover(self, threshold: float = 2.0) -> bool:
        """Check if EMAs are approaching crossover."""
        return self.get_ema_distance_pct() <= threshold


@dataclass
class SuperTrendSignal(Signal):
    """SuperTrend specific signal."""
    atr_period: int = 10
    multiplier: float = 3.0
    supertrend_value: float = 0.0
    trend_direction: str = 'bullish'  # 'bullish', 'bearish'
    trend_change: bool = False  # True if trend just changed
    trend_strength: float = 0.0  # 0.0 to 1.0
    
    def __post_init__(self):
        """Validate data after initialization."""
        super().__post_init__()
        if self.trend_direction not in ['bullish', 'bearish']:
            raise ValueError("Trend direction must be 'bullish' or 'bearish'")
        if not 0.0 <= self.trend_strength <= 1.0:
            raise ValueError("Trend strength must be between 0.0 and 1.0")
        if self.atr_period < 1:
            raise ValueError("ATR period must be positive")
        if self.multiplier <= 0:
            raise ValueError("Multiplier must be positive")
    
    def is_price_above_supertrend(self, current_price: float) -> bool:
        """Check if current price is above SuperTrend line."""
        return current_price > self.supertrend_value
    
    def get_distance_from_supertrend(self, current_price: float) -> float:
        """Get distance from SuperTrend as percentage."""
        if self.supertrend_value == 0:
            return 0.0
        return ((current_price - self.supertrend_value) / self.supertrend_value) * 100