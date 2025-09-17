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