"""
File Output Handler

Handles CSV and file-based output operations.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.models.data_models import Signal, OHLCV, IndicatorValue
from src.models.exceptions import TradingBotError


class FileOutputHandler:
    """Handles file-based output operations."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize file output handler.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"File output handler initialized: {self.output_dir}")
    
    def save_signals_csv(self, signals: List[Signal], filename: str = "signals.csv"):
        """
        Save signals to CSV file.
        
        Args:
            signals: List of Signal objects
            filename: Output filename
        """
        try:
            if not signals:
                self.logger.warning("No signals to save")
                return
            
            csv_path = self.output_dir / filename
            
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
                
                # Write signals
                for signal in signals:
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
            
            self.logger.info(f"Saved {len(signals)} signals to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save signals to CSV: {e}")
            raise TradingBotError(f"CSV save failed: {e}")
    
    def save_price_data_csv(self, price_data: List[OHLCV], filename: str = "price_data.csv"):
        """
        Save price data to CSV file.
        
        Args:
            price_data: List of OHLCV objects
            filename: Output filename
        """
        try:
            if not price_data:
                self.logger.warning("No price data to save")
                return
            
            csv_path = self.output_dir / filename
            
            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for data in price_data:
                    writer.writerow({
                        'timestamp': data.timestamp.isoformat(),
                        'symbol': data.symbol,
                        'open': data.open,
                        'high': data.high,
                        'low': data.low,
                        'close': data.close,
                        'volume': data.volume
                    })
            
            self.logger.info(f"Saved {len(price_data)} price records to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save price data to CSV: {e}")
            raise TradingBotError(f"Price data CSV save failed: {e}")
    
    def save_analysis_summary(self, summary: Dict[str, Any], filename: str = "analysis_summary.json"):
        """
        Save analysis summary to JSON file.
        
        Args:
            summary: Analysis summary dictionary
            filename: Output filename
        """
        try:
            json_path = self.output_dir / filename
            
            # Convert datetime objects to strings for JSON serialization
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(json_path, 'w') as jsonfile:
                json.dump(summary, jsonfile, indent=2, default=json_serializer)
            
            self.logger.info(f"Saved analysis summary to {json_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis summary: {e}")
            raise TradingBotError(f"Analysis summary save failed: {e}")
    
    def create_daily_report(self, signals: List[Signal], summary: Dict[str, Any]):
        """
        Create a daily trading report.
        
        Args:
            signals: List of signals generated today
            summary: Analysis summary
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            report_path = self.output_dir / f"daily_report_{today}.txt"
            
            with open(report_path, 'w') as f:
                f.write(f"Stock Trading Bot - Daily Report\n")
                f.write(f"Date: {today}\n")
                f.write("=" * 50 + "\n\n")
                
                # Summary section
                f.write("SUMMARY\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total symbols analyzed: {summary.get('symbols_analyzed', 0)}\n")
                f.write(f"Signals generated: {len(signals)}\n")
                f.write(f"Buy signals: {len([s for s in signals if s.signal_type.value == 'BUY'])}\n")
                f.write(f"Sell signals: {len([s for s in signals if s.signal_type.value == 'SELL'])}\n")
                f.write("\n")
                
                # Signals section
                if signals:
                    f.write("SIGNALS\n")
                    f.write("-" * 20 + "\n")
                    for signal in signals:
                        if signal.signal_type.value != 'NO_SIGNAL':
                            f.write(f"{signal.signal_type.value}: {signal.symbol} ")
                            f.write(f"(Confidence: {signal.confidence:.2f})\n")
                            f.write(f"  Price: ${signal.indicators.get('current_price', 'N/A')}\n")
                            f.write(f"  RSI: {signal.indicators.get('rsi', 'N/A'):.1f}\n")
                            f.write(f"  Strategy: {signal.strategy_name}\n")
                            f.write("\n")
                else:
                    f.write("No trading signals generated today.\n\n")
                
                # Footer
                f.write("=" * 50 + "\n")
                f.write("Generated by Stock Trading Bot\n")
            
            self.logger.info(f"Created daily report: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create daily report: {e}")
            raise TradingBotError(f"Daily report creation failed: {e}")
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """
        Clean up old output files.
        
        Args:
            days_to_keep: Number of days of files to keep
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            files_removed = 0
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    files_removed += 1
            
            if files_removed > 0:
                self.logger.info(f"Cleaned up {files_removed} old files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old files: {e}")
    
    def get_output_stats(self) -> Dict[str, Any]:
        """
        Get statistics about output files.
        
        Returns:
            Dictionary with file statistics
        """
        try:
            stats = {
                'output_directory': str(self.output_dir),
                'total_files': 0,
                'total_size_mb': 0,
                'file_types': {}
            }
            
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file():
                    stats['total_files'] += 1
                    file_size = file_path.stat().st_size
                    stats['total_size_mb'] += file_size / (1024 * 1024)
                    
                    ext = file_path.suffix.lower()
                    if ext not in stats['file_types']:
                        stats['file_types'][ext] = 0
                    stats['file_types'][ext] += 1
            
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get output stats: {e}")
            return {'error': str(e)}