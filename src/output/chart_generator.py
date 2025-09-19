"""
Chart Generator

Creates matplotlib charts for technical analysis visualization.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.data_models import Signal, SignalType
from src.models.exceptions import TradingBotError


class ChartGenerator:
    """Generates technical analysis charts."""
    
    def __init__(self, output_dir: str = "output/charts"):
        """
        Initialize chart generator.
        
        Args:
            output_dir: Directory for chart files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style
        plt.style.use('default')
        
        self.logger.info(f"Chart generator initialized: {self.output_dir}")
    
    def create_technical_analysis_chart(self, symbol: str, data: pd.DataFrame, 
                                      indicators: Dict[str, Any], 
                                      signals: Optional[list] = None,
                                      filename: Optional[str] = None) -> str:
        """
        Create a comprehensive technical analysis chart.
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            signals: List of signals to plot
            filename: Optional custom filename
            
        Returns:
            Path to saved chart file
        """
        try:
            if data.empty:
                raise TradingBotError("No data provided for chart generation")
            
            # Create figure with subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), 
                                               gridspec_kw={'height_ratios': [3, 1, 1]})
            
            # Main price chart with indicators
            self._plot_price_and_indicators(ax1, symbol, data, indicators, signals)
            
            # RSI subplot
            self._plot_rsi(ax2, data, indicators)
            
            # Volume subplot
            self._plot_volume(ax3, data)
            
            # Format and save
            plt.tight_layout()
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{symbol}_analysis_{timestamp}.png"
            
            chart_path = self.output_dir / filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Created technical analysis chart: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create technical analysis chart: {e}")
            raise TradingBotError(f"Chart generation failed: {e}")
    
    def _plot_price_and_indicators(self, ax, symbol: str, data: pd.DataFrame, 
                                 indicators: Dict[str, Any], signals: Optional[list]):
        """Plot price data with technical indicators."""
        # Plot price
        ax.plot(data.index, data['Close'], label='Close Price', color='black', linewidth=1.5)
        
        # Plot EMA if available
        if 'ema' in indicators:
            ema_data = indicators['ema']
            ax.plot(data.index, ema_data, label='EMA(20)', color='blue', linewidth=1)
        
        # Plot Bollinger Bands if available
        if 'bollinger_bands' in indicators:
            bb_data = indicators['bollinger_bands']
            if hasattr(bb_data, 'columns'):
                ax.plot(data.index, bb_data['upper_band'], label='BB Upper', 
                       color='red', linestyle='--', alpha=0.7)
                ax.plot(data.index, bb_data['middle_band'], label='BB Middle', 
                       color='orange', linestyle='--', alpha=0.7)
                ax.plot(data.index, bb_data['lower_band'], label='BB Lower', 
                       color='green', linestyle='--', alpha=0.7)
                
                # Fill between bands
                ax.fill_between(data.index, bb_data['upper_band'], bb_data['lower_band'], 
                               alpha=0.1, color='gray')
        
        # Plot signals if provided
        if signals:
            for signal in signals:
                if signal.signal_type == SignalType.BUY:
                    ax.scatter(signal.timestamp, signal.indicators.get('current_price', 0), 
                             color='green', marker='^', s=100, label='Buy Signal', zorder=5)
                elif signal.signal_type == SignalType.SELL:
                    ax.scatter(signal.timestamp, signal.indicators.get('current_price', 0), 
                             color='red', marker='v', s=100, label='Sell Signal', zorder=5)
        
        ax.set_title(f'{symbol} - Technical Analysis', fontsize=14, fontweight='bold')
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_rsi(self, ax, data: pd.DataFrame, indicators: Dict[str, Any]):
        """Plot RSI indicator."""
        if 'rsi' in indicators:
            rsi_data = indicators['rsi']
            ax.plot(data.index, rsi_data, label='RSI(14)', color='purple', linewidth=1.5)
            
            # Add overbought/oversold lines
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought (70)')
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold (30)')
            ax.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
            
            # Fill overbought/oversold areas
            ax.fill_between(data.index, 70, 100, alpha=0.1, color='red')
            ax.fill_between(data.index, 0, 30, alpha=0.1, color='green')
            
            ax.set_ylabel('RSI', fontsize=12)
            ax.set_ylim(0, 100)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'RSI data not available', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=12)
    
    def _plot_volume(self, ax, data: pd.DataFrame):
        """Plot volume data."""
        if 'Volume' in data.columns:
            # Color bars based on price movement
            colors = ['green' if close >= open_price else 'red' 
                     for close, open_price in zip(data['Close'], data['Open'])]
            
            ax.bar(data.index, data['Volume'], color=colors, alpha=0.7, width=0.8)
            ax.set_ylabel('Volume', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Format volume numbers
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
        else:
            ax.text(0.5, 0.5, 'Volume data not available', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=12)
    
    def create_signals_summary_chart(self, signals: list, filename: str = "signals_summary.png"):
        """
        Create a summary chart of all signals.
        
        Args:
            signals: List of Signal objects
            filename: Output filename
            
        Returns:
            Path to saved chart file
        """
        try:
            if not signals:
                self.logger.warning("No signals to plot")
                return None
            
            # Prepare data
            signal_data = []
            for signal in signals:
                if signal.signal_type != SignalType.NO_SIGNAL:
                    signal_data.append({
                        'symbol': signal.symbol,
                        'timestamp': signal.timestamp,
                        'signal_type': signal.signal_type.value,
                        'confidence': signal.confidence,
                        'price': signal.indicators.get('current_price', 0)
                    })
            
            if not signal_data:
                self.logger.warning("No actionable signals to plot")
                return None
            
            df = pd.DataFrame(signal_data)
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Signal count by symbol
            signal_counts = df['symbol'].value_counts()
            ax1.bar(signal_counts.index, signal_counts.values, color='steelblue', alpha=0.7)
            ax1.set_title('Trading Signals by Symbol', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Number of Signals')
            ax1.grid(True, alpha=0.3)
            
            # Signal confidence distribution
            buy_signals = df[df['signal_type'] == 'BUY']['confidence']
            sell_signals = df[df['signal_type'] == 'SELL']['confidence']
            
            ax2.hist(buy_signals, bins=10, alpha=0.7, label='Buy Signals', color='green')
            ax2.hist(sell_signals, bins=10, alpha=0.7, label='Sell Signals', color='red')
            ax2.set_title('Signal Confidence Distribution', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Confidence Level')
            ax2.set_ylabel('Frequency')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            chart_path = self.output_dir / filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Created signals summary chart: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create signals summary chart: {e}")
            raise TradingBotError(f"Signals summary chart generation failed: {e}")
    
    def create_performance_chart(self, performance_data: Dict[str, Any], 
                               filename: str = "performance.png"):
        """
        Create a performance tracking chart.
        
        Args:
            performance_data: Dictionary with performance metrics
            filename: Output filename
            
        Returns:
            Path to saved chart file
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Signal accuracy over time (if available)
            if 'accuracy_over_time' in performance_data:
                accuracy_data = performance_data['accuracy_over_time']
                ax1.plot(accuracy_data['dates'], accuracy_data['accuracy'], 
                        marker='o', linewidth=2, color='blue')
                ax1.set_title('Signal Accuracy Over Time')
                ax1.set_ylabel('Accuracy (%)')
                ax1.grid(True, alpha=0.3)
            
            # Win/Loss ratio
            if 'win_loss_ratio' in performance_data:
                wins = performance_data['win_loss_ratio']['wins']
                losses = performance_data['win_loss_ratio']['losses']
                ax2.pie([wins, losses], labels=['Wins', 'Losses'], 
                       colors=['green', 'red'], autopct='%1.1f%%')
                ax2.set_title('Win/Loss Ratio')
            
            # Signal distribution by type
            if 'signal_distribution' in performance_data:
                signal_dist = performance_data['signal_distribution']
                ax3.bar(signal_dist.keys(), signal_dist.values(), 
                       color=['green', 'red', 'gray'], alpha=0.7)
                ax3.set_title('Signal Distribution')
                ax3.set_ylabel('Count')
            
            # Average confidence by signal type
            if 'avg_confidence' in performance_data:
                conf_data = performance_data['avg_confidence']
                ax4.bar(conf_data.keys(), conf_data.values(), 
                       color=['green', 'red'], alpha=0.7)
                ax4.set_title('Average Confidence by Signal Type')
                ax4.set_ylabel('Confidence')
                ax4.set_ylim(0, 1)
            
            plt.tight_layout()
            
            chart_path = self.output_dir / filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Created performance chart: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create performance chart: {e}")
            raise TradingBotError(f"Performance chart generation failed: {e}")
    
    def cleanup_old_charts(self, days_to_keep: int = 7):
        """
        Clean up old chart files.
        
        Args:
            days_to_keep: Number of days of charts to keep
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            files_removed = 0
            for file_path in self.output_dir.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    files_removed += 1
            
            if files_removed > 0:
                self.logger.info(f"Cleaned up {files_removed} old chart files")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old charts: {e}")