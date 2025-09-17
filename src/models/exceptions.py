"""
Custom Exceptions

Application-specific exception classes.
"""


class TradingBotError(Exception):
    """Base exception for trading bot errors."""
    pass


class DataFetchError(TradingBotError):
    """Exception raised when data fetching fails."""
    pass


class IndicatorError(TradingBotError):
    """Exception raised when indicator calculation fails."""
    pass


class StrategyError(TradingBotError):
    """Exception raised when strategy execution fails."""
    pass


class ConfigurationError(TradingBotError):
    """Exception raised when configuration is invalid."""
    pass


class DatabaseError(TradingBotError):
    """Exception raised when database operations fail."""
    pass