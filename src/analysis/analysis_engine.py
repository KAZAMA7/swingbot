"""
Analysis Engine

Coordinates technical indicator calculations and manages analysis workflow.
"""

import pandas as pd
import logging
from typing import Dict, List, Any

from .rsi_calculator import RSICalculator
from .bollinger_bands_calculator import BollingerBandsCalculator
from .ema_calculator import EMACalculator
from ..models.exceptions import IndicatorError


class AnalysisEngine:
    """Coordinates technical analysis calculations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize analysis engine.
        
        Args:
            config: Configuration dictionary with indicator parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize calculators
        self.calculators = {
            'rsi': RSICalculator(),
            'bollinger_bands': BollingerBandsCalculator(),
            'ema': EMACalculator()
        }
        
        self.logger.info("Analysis engine initialized with calculators: %s", list(self.calculators.keys()))
    
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform complete technical analysis for a symbol.
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with calculated indicators
            
        Raises:
            IndicatorError: If analysis fails
        """
        try:
            if data.empty:
                raise IndicatorError(f"No data provided for analysis of {symbol}")
            
            self.logger.debug(f"Starting analysis for {symbol} with {len(data)} data points")
            
            # Validate data structure
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise IndicatorError(f"Missing required columns: {missing_columns}")
            
            results = {}
            
            # Calculate RSI
            try:
                rsi_params = self.config.get('indicators', {}).get('rsi', {'period': 14})
                if self._has_sufficient_data(data, 'rsi', rsi_params):
                    results['rsi'] = self.calculators['rsi'].calculate(data, rsi_params)
                    self.logger.debug(f"RSI calculated for {symbol}")
                else:
                    self.logger.warning(f"Insufficient data for RSI calculation for {symbol}")
            except Exception as e:
                self.logger.error(f"RSI calculation failed for {symbol}: {e}")
            
            # Calculate Bollinger Bands
            try:
                bb_params = self.config.get('indicators', {}).get('bollinger_bands', {'period': 20, 'std_dev': 2})
                if self._has_sufficient_data(data, 'bollinger_bands', bb_params):
                    results['bollinger_bands'] = self.calculators['bollinger_bands'].calculate(data, bb_params)
                    self.logger.debug(f"Bollinger Bands calculated for {symbol}")
                else:
                    self.logger.warning(f"Insufficient data for Bollinger Bands calculation for {symbol}")
            except Exception as e:
                self.logger.error(f"Bollinger Bands calculation failed for {symbol}: {e}")
            
            # Calculate EMA
            try:
                ema_params = self.config.get('indicators', {}).get('ema', {'period': 20})
                if self._has_sufficient_data(data, 'ema', ema_params):
                    results['ema'] = self.calculators['ema'].calculate(data, ema_params)
                    self.logger.debug(f"EMA calculated for {symbol}")
                else:
                    self.logger.warning(f"Insufficient data for EMA calculation for {symbol}")
            except Exception as e:
                self.logger.error(f"EMA calculation failed for {symbol}: {e}")
            
            if not results:
                raise IndicatorError(f"No indicators could be calculated for {symbol}")
            
            self.logger.info(f"Analysis completed for {symbol}. Calculated indicators: {list(results.keys())}")
            return results
            
        except Exception as e:
            raise IndicatorError(f"Analysis failed for {symbol}: {e}")
    
    def _has_sufficient_data(self, data: pd.DataFrame, indicator_name: str, params: Dict) -> bool:
        """
        Check if there's sufficient data for indicator calculation.
        
        Args:
            data: DataFrame with price data
            indicator_name: Name of the indicator
            params: Indicator parameters
            
        Returns:
            True if sufficient data is available
        """
        try:
            calculator = self.calculators.get(indicator_name)
            if not calculator:
                return False
            
            required_periods = calculator.get_required_periods(params)
            return len(data) >= required_periods
            
        except Exception as e:
            self.logger.error(f"Error checking data sufficiency for {indicator_name}: {e}")
            return False
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data quality.
        
        Args:
            data: DataFrame to validate
            
        Returns:
            True if data is valid
        """
        try:
            if data.empty:
                return False
            
            # Check for required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                return False
            
            # Check for null values in critical columns
            if data[['Close']].isnull().any().any():
                return False
            
            # Check for negative prices
            if (data[['Open', 'High', 'Low', 'Close']] < 0).any().any():
                return False
            
            # Check for logical price relationships
            invalid_prices = (
                (data['High'] < data['Low']) |
                (data['High'] < data['Open']) |
                (data['High'] < data['Close']) |
                (data['Low'] > data['Open']) |
                (data['Low'] > data['Close'])
            )
            
            if invalid_prices.any():
                self.logger.warning(f"Found {invalid_prices.sum()} rows with invalid price relationships")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return False
    
    def get_analysis_summary(self, symbol: str, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate analysis summary with key metrics.
        
        Args:
            symbol: Stock symbol
            indicators: Dictionary of calculated indicators
            
        Returns:
            Dictionary with analysis summary
        """
        try:
            summary = {
                'symbol': symbol,
                'timestamp': pd.Timestamp.now(),
                'indicators_calculated': list(indicators.keys()),
                'analysis_quality': 'good' if len(indicators) >= 3 else 'limited'
            }
            
            # Add latest values for each indicator
            if 'rsi' in indicators:
                latest_rsi = indicators['rsi'].iloc[-1] if hasattr(indicators['rsi'], 'iloc') else indicators['rsi']
                summary['latest_rsi'] = float(latest_rsi)
                summary['rsi_signal'] = 'oversold' if latest_rsi < 30 else 'overbought' if latest_rsi > 70 else 'neutral'
            
            if 'bollinger_bands' in indicators:
                bb_data = indicators['bollinger_bands']
                if hasattr(bb_data, 'iloc'):
                    latest_bb = bb_data.iloc[-1]
                    summary['latest_bb_upper'] = float(latest_bb['upper_band'])
                    summary['latest_bb_lower'] = float(latest_bb['lower_band'])
                    summary['latest_bandwidth'] = float(latest_bb['bandwidth'])
            
            if 'ema' in indicators:
                latest_ema = indicators['ema'].iloc[-1] if hasattr(indicators['ema'], 'iloc') else indicators['ema']
                summary['latest_ema'] = float(latest_ema)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate analysis summary for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def batch_analyze(self, symbols_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """
        Perform analysis on multiple symbols.
        
        Args:
            symbols_data: Dictionary mapping symbols to their data
            
        Returns:
            Dictionary mapping symbols to their analysis results
        """
        results = {}
        
        for symbol, data in symbols_data.items():
            try:
                results[symbol] = self.analyze_symbol(symbol, data)
                self.logger.debug(f"Batch analysis completed for {symbol}")
            except Exception as e:
                self.logger.error(f"Batch analysis failed for {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        self.logger.info(f"Batch analysis completed for {len(symbols_data)} symbols")
        return results
    
    def get_required_data_periods(self) -> int:
        """
        Get the maximum number of periods required by all indicators.
        
        Returns:
            Maximum periods needed
        """
        max_periods = 0
        
        for indicator_name, calculator in self.calculators.items():
            try:
                indicator_config = self.config.get('indicators', {}).get(indicator_name, {})
                default_params = calculator.get_default_params()
                params = {**default_params, **indicator_config}
                
                required = calculator.get_required_periods(params)
                max_periods = max(max_periods, required)
                
            except Exception as e:
                self.logger.error(f"Error getting required periods for {indicator_name}: {e}")
        
        # Add buffer for better analysis
        return max_periods + 50
    
    def add_calculator(self, name: str, calculator):
        """
        Add a new indicator calculator.
        
        Args:
            name: Calculator name
            calculator: Calculator instance implementing IndicatorInterface
        """
        self.calculators[name] = calculator
        self.logger.info(f"Added calculator: {name}")
    
    def remove_calculator(self, name: str):
        """
        Remove an indicator calculator.
        
        Args:
            name: Calculator name to remove
        """
        if name in self.calculators:
            del self.calculators[name]
            self.logger.info(f"Removed calculator: {name}")
    
    def get_available_calculators(self) -> List[str]:
        """
        Get list of available calculators.
        
        Returns:
            List of calculator names
        """
        return list(self.calculators.keys())