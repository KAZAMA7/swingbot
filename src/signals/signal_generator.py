"""
Signal Generator

Generates trading signals using strategies and manages signal persistence.
"""

import pandas as pd
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from ..strategies.swing_trading_strategy import SwingTradingStrategy
from ..models.data_models import Signal, SignalType
from ..models.exceptions import StrategyError


class SignalGenerator:
    """Generates and manages trading signals."""
    
    def __init__(self, config: Dict[str, Any] = None, db_manager=None):
        """
        Initialize signal generator.
        
        Args:
            config: Configuration dictionary
            db_manager: Database manager instance
        """
        self.config = config or {}
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategies
        self.strategies = {
            'swing_trading': SwingTradingStrategy()
        }
        
        # Setup output paths
        output_config = self.config.get('output', {})
        self.csv_file = output_config.get('csv_file', 'signals.csv')
        self.output_dir = Path(output_config.get('output_dir', 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Signal generator initialized")
    
    def generate_signal(self, symbol: str, data: pd.DataFrame, 
                       indicators: Dict[str, Any], strategy_name: str = 'swing_trading') -> Signal:
        """
        Generate trading signal for a symbol.
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            strategy_name: Name of strategy to use
            
        Returns:
            Generated Signal object
            
        Raises:
            StrategyError: If signal generation fails
        """
        try:
            strategy = self.strategies.get(strategy_name)
            if not strategy:
                raise StrategyError(f"Strategy '{strategy_name}' not found")
            
            # Add symbol to data if not present
            if hasattr(data.iloc[-1], 'symbol'):
                pass  # Symbol already in data
            else:
                # Add symbol as attribute to the latest row
                data = data.copy()
                data.loc[data.index[-1], 'symbol'] = symbol
            
            signal = strategy.generate_signal(data, indicators)
            
            # Ensure signal has correct symbol
            if signal.symbol == 'UNKNOWN':
                signal.symbol = symbol
            
            self.logger.debug(f"Generated {signal.signal_type.value} signal for {symbol}")
            return signal
            
        except Exception as e:
            raise StrategyError(f"Signal generation failed for {symbol}: {e}")
    
    def process_symbol(self, symbol: str, data: pd.DataFrame, 
                      indicators: Dict[str, Any]) -> Signal:
        """
        Process a symbol and generate signal with persistence.
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            
        Returns:
            Generated Signal object
        """
        try:
            # Generate signal
            signal = self.generate_signal(symbol, data, indicators)
            
            # Persist signal
            self._persist_signal(signal)
            
            # Log signal
            self._log_signal(signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Failed to process symbol {symbol}: {e}")
            # Return a NO_SIGNAL in case of error
            return Signal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal_type=SignalType.NO_SIGNAL,
                confidence=0.0,
                indicators={},
                strategy_name='error'
            )
    
    def _persist_signal(self, signal: Signal):
        """
        Persist signal to database and CSV file.
        
        Args:
            signal: Signal to persist
        """
        try:
            # Save to database if available
            if self.db_manager:
                self.db_manager.store_signal(signal)
            
            # Save to CSV file
            self._save_to_csv(signal)
            
        except Exception as e:
            self.logger.error(f"Failed to persist signal: {e}")
    
    def _save_to_csv(self, signal: Signal):
        """
        Save signal to CSV file.
        
        Args:
            signal: Signal to save
        """
        try:
            csv_path = self.output_dir / self.csv_file
            
            # Check if file exists to determine if we need headers
            file_exists = csv_path.exists()
            
            with open(csv_path, 'a', newline='') as csvfile:
                fieldnames = [
                    'timestamp', 'symbol', 'signal_type', 'confidence', 
                    'strategy_name', 'rsi', 'bb_upper', 'bb_lower', 
                    'ema', 'current_price'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Prepare row data
                row_data = {
                    'timestamp': signal.timestamp.isoformat(),
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type.value,
                    'confidence': signal.confidence,
                    'strategy_name': signal.strategy_name
                }
                
                # Add indicator values
                indicators = signal.indicators
                row_data.update({
                    'rsi': indicators.get('rsi', ''),
                    'bb_upper': indicators.get('bb_upper', ''),
                    'bb_lower': indicators.get('bb_lower', ''),
                    'ema': indicators.get('ema', ''),
                    'current_price': indicators.get('current_price', '')
                })
                
                writer.writerow(row_data)
            
            self.logger.debug(f"Signal saved to CSV: {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save signal to CSV: {e}")
    
    def _log_signal(self, signal: Signal):
        """
        Log signal information.
        
        Args:
            signal: Signal to log
        """
        if signal.signal_type != SignalType.NO_SIGNAL:
            self.logger.info(
                f"SIGNAL: {signal.signal_type.value} {signal.symbol} "
                f"(confidence: {signal.confidence:.2f}) - "
                f"RSI: {signal.indicators.get('rsi', 'N/A'):.1f}, "
                f"Price: {signal.indicators.get('current_price', 'N/A'):.2f}"
            )
    
    def batch_process(self, symbols_data: Dict[str, pd.DataFrame], 
                     symbols_indicators: Dict[str, Dict[str, Any]]) -> Dict[str, Signal]:
        """
        Process multiple symbols and generate signals.
        
        Args:
            symbols_data: Dictionary mapping symbols to their data
            symbols_indicators: Dictionary mapping symbols to their indicators
            
        Returns:
            Dictionary mapping symbols to their signals
        """
        results = {}
        
        for symbol in symbols_data.keys():
            try:
                data = symbols_data[symbol]
                indicators = symbols_indicators.get(symbol, {})
                
                if not indicators:
                    self.logger.warning(f"No indicators available for {symbol}, skipping")
                    continue
                
                signal = self.process_symbol(symbol, data, indicators)
                results[symbol] = signal
                
            except Exception as e:
                self.logger.error(f"Batch processing failed for {symbol}: {e}")
        
        self.logger.info(f"Batch processed {len(results)} symbols")
        return results
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """
        Get summary of available strategies.
        
        Returns:
            Dictionary with strategy information
        """
        summary = {}
        
        for name, strategy in self.strategies.items():
            try:
                summary[name] = {
                    'required_indicators': strategy.get_required_indicators(),
                    'parameters': strategy.get_strategy_params()
                }
            except Exception as e:
                self.logger.error(f"Failed to get summary for strategy {name}: {e}")
                summary[name] = {'error': str(e)}
        
        return summary
    
    def add_strategy(self, name: str, strategy):
        """
        Add a new trading strategy.
        
        Args:
            name: Strategy name
            strategy: Strategy instance implementing StrategyInterface
        """
        self.strategies[name] = strategy
        self.logger.info(f"Added strategy: {name}")
    
    def get_recent_signals(self, symbol: str = None, limit: int = 10) -> List[Signal]:
        """
        Get recent signals from database.
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum number of signals to return
            
        Returns:
            List of recent signals
        """
        try:
            if self.db_manager:
                return self.db_manager.get_latest_signals(symbol, limit)
            else:
                self.logger.warning("No database manager available for retrieving signals")
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve recent signals: {e}")
            return []
    
    def get_signal_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get signal statistics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with signal statistics
        """
        try:
            if not self.db_manager:
                return {'error': 'No database manager available'}
            
            # This would require additional database queries
            # For now, return basic structure
            return {
                'period_days': days,
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'no_signals': 0,
                'average_confidence': 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get signal statistics: {e}")
            return {'error': str(e)}