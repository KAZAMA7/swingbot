#!/usr/bin/env python3
"""
Chart Generation Module for Enhanced Multi-Strategy NIFTY Trading Bot

Generates comprehensive charts for trading signals and technical analysis.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import logging

# Set matplotlib backend for headless environments
import matplotlib
matplotlib.use('Agg')

# Configure seaborn style
sns.set_style("whitegrid")
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    # Fallback for older matplotlib versions
    plt.style.use('seaborn')

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate comprehensive trading charts with signals and indicators."""
    
    def __init__(self, output_dir: str = "output/charts"):
        """Initialize chart generator with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Chart configuration
        self.figsize = (16, 12)
        self.dpi = 100
        self.colors = {
            'price': '#2E86AB',
            'ema_short': '#A23B72',
            'ema_long': '#F18F01',
            'supertrend_up': '#43AA8B',
            'supertrend_down': '#F8961E',
            'buy_signal': '#06D6A0',
            'sell_signal': '#F72585',
            'volume': '#6C757D',
            'rsi': '#8E44AD',
            'macd': '#E67E22',
            'bb_upper': '#3498DB',
            'bb_lower': '#3498DB',
            'bb_middle': '#95A5A6'
        }
    
    def generate_comprehensive_chart(self, symbol: str, data: pd.DataFrame, 
                                   signals: Dict, strategies: Dict = None,
                                   save_path: Optional[str] = None) -> str:
        """
        Generate comprehensive chart with price, indicators, and signals.
        
        Args:
            symbol: Stock symbol
            data: OHLCV data with indicators
            signals: Dictionary containing signal information
            strategies: Dictionary of strategy signals
            save_path: Optional custom save path
            
        Returns:
            Path to saved chart
        """
        try:
            # Create figure with subplots
            fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
            gs = fig.add_gridspec(4, 2, height_ratios=[3, 1, 1, 1], hspace=0.3, wspace=0.2)
            
            # Main price chart
            ax_price = fig.add_subplot(gs[0, :])
            self._plot_price_and_indicators(ax_price, symbol, data, signals, strategies)
            
            # Volume chart
            ax_volume = fig.add_subplot(gs[1, :], sharex=ax_price)
            self._plot_volume(ax_volume, data)
            
            # RSI chart
            ax_rsi = fig.add_subplot(gs[2, 0], sharex=ax_price)
            self._plot_rsi(ax_rsi, data)
            
            # MACD chart
            ax_macd = fig.add_subplot(gs[2, 1], sharex=ax_price)
            self._plot_macd(ax_macd, data)
            
            # Strategy performance chart
            ax_strategy = fig.add_subplot(gs[3, :])
            self._plot_strategy_signals(ax_strategy, data, strategies)
            
            # Format x-axis for all subplots
            self._format_date_axis(ax_price)
            plt.setp(ax_price.get_xticklabels(), visible=False)
            plt.setp(ax_volume.get_xticklabels(), visible=False)
            plt.setp(ax_rsi.get_xticklabels(), visible=False)
            plt.setp(ax_macd.get_xticklabels(), visible=False)
            
            # Add title and metadata
            self._add_chart_metadata(fig, symbol, data, signals)
            
            # Save chart
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.output_dir / f"{symbol}_{timestamp}_comprehensive.png"
            
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            logger.info(f"Chart saved: {save_path}")
            return str(save_path)
            
        except Exception as e:
            logger.error(f"Error generating chart for {symbol}: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def _plot_price_and_indicators(self, ax, symbol: str, data: pd.DataFrame, 
                                 signals: Dict, strategies: Dict = None):
        """Plot price, EMAs, SuperTrend, and Bollinger Bands."""
        # Plot candlestick-style price
        self._plot_candlesticks(ax, data)
        
        # Plot EMAs
        if 'EMA_50' in data.columns and 'EMA_200' in data.columns:
            ax.plot(data.index, data['EMA_50'], color=self.colors['ema_short'], 
                   linewidth=2, label='EMA 50', alpha=0.8)
            ax.plot(data.index, data['EMA_200'], color=self.colors['ema_long'], 
                   linewidth=2, label='EMA 200', alpha=0.8)
        
        # Plot SuperTrend
        if 'SuperTrend' in data.columns and 'SuperTrend_Direction' in data.columns:
            self._plot_supertrend(ax, data)
        
        # Plot Bollinger Bands
        if all(col in data.columns for col in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
            self._plot_bollinger_bands(ax, data)
        
        # Plot signals
        self._plot_trading_signals(ax, data, signals, strategies)
        
        ax.set_title(f"{symbol} - Price Action & Technical Indicators", fontsize=14, fontweight='bold')
        ax.set_ylabel("Price (₹)", fontsize=12)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
    
    def _plot_candlesticks(self, ax, data: pd.DataFrame):
        """Plot candlestick chart."""
        # Simple line chart for now (can be enhanced to proper candlesticks)
        ax.plot(data.index, data['Close'], color=self.colors['price'], 
               linewidth=1.5, label='Close Price')
        
        # Add high/low shadows
        for i in range(0, len(data), max(1, len(data) // 200)):  # Sample points for performance
            ax.plot([data.index[i], data.index[i]], 
                   [data['Low'].iloc[i], data['High'].iloc[i]], 
                   color=self.colors['price'], alpha=0.3, linewidth=0.5)
    
    def _plot_supertrend(self, ax, data: pd.DataFrame):
        """Plot SuperTrend indicator."""
        # Plot SuperTrend line with color coding
        bullish_mask = data['SuperTrend_Direction'] == 1
        bearish_mask = data['SuperTrend_Direction'] == -1
        
        if bullish_mask.any():
            ax.plot(data.index[bullish_mask], data['SuperTrend'][bullish_mask], 
                   color=self.colors['supertrend_up'], linewidth=2, 
                   label='SuperTrend (Bullish)', alpha=0.8)
        
        if bearish_mask.any():
            ax.plot(data.index[bearish_mask], data['SuperTrend'][bearish_mask], 
                   color=self.colors['supertrend_down'], linewidth=2, 
                   label='SuperTrend (Bearish)', alpha=0.8)
    
    def _plot_bollinger_bands(self, ax, data: pd.DataFrame):
        """Plot Bollinger Bands."""
        ax.plot(data.index, data['BB_Upper'], color=self.colors['bb_upper'], 
               linewidth=1, alpha=0.6, linestyle='--', label='BB Upper')
        ax.plot(data.index, data['BB_Lower'], color=self.colors['bb_lower'], 
               linewidth=1, alpha=0.6, linestyle='--', label='BB Lower')
        ax.plot(data.index, data['BB_Middle'], color=self.colors['bb_middle'], 
               linewidth=1, alpha=0.5, label='BB Middle')
        
        # Fill between bands
        ax.fill_between(data.index, data['BB_Upper'], data['BB_Lower'], 
                       alpha=0.1, color=self.colors['bb_upper'])
    
    def _plot_trading_signals(self, ax, data: pd.DataFrame, signals: Dict, strategies: Dict = None):
        """Plot trading signals on price chart."""
        # Plot composite signals
        if 'composite_signal' in signals and signals['composite_signal'] != 'NO_SIGNAL':
            signal_type = signals['composite_signal']
            latest_price = data['Close'].iloc[-1]
            latest_date = data.index[-1]
            
            if signal_type == 'BUY':
                ax.scatter(latest_date, latest_price, color=self.colors['buy_signal'], 
                          s=200, marker='^', label='BUY Signal', zorder=5, edgecolor='white', linewidth=2)
            elif signal_type == 'SELL':
                ax.scatter(latest_date, latest_price, color=self.colors['sell_signal'], 
                          s=200, marker='v', label='SELL Signal', zorder=5, edgecolor='white', linewidth=2)
        
        # Plot strategy-specific signals
        if strategies:
            self._plot_strategy_specific_signals(ax, data, strategies)
    
    def _plot_strategy_specific_signals(self, ax, data: pd.DataFrame, strategies: Dict):
        """Plot individual strategy signals."""
        latest_price = data['Close'].iloc[-1]
        latest_date = data.index[-1]
        
        # Offset signals vertically to avoid overlap
        price_offset = latest_price * 0.02
        
        for i, (strategy_name, strategy_data) in enumerate(strategies.items()):
            if strategy_data['signal'] != 'NO_SIGNAL':
                offset = price_offset * (i + 1)
                
                if strategy_data['signal'] == 'BUY':
                    ax.scatter(latest_date, latest_price + offset, 
                             color=self.colors['buy_signal'], s=100, marker='o', 
                             alpha=0.7, label=f'{strategy_name} BUY')
                elif strategy_data['signal'] == 'SELL':
                    ax.scatter(latest_date, latest_price - offset, 
                             color=self.colors['sell_signal'], s=100, marker='o', 
                             alpha=0.7, label=f'{strategy_name} SELL')
    
    def _plot_volume(self, ax, data: pd.DataFrame):
        """Plot volume chart."""
        if 'Volume' in data.columns:
            ax.bar(data.index, data['Volume'], color=self.colors['volume'], 
                  alpha=0.6, width=1)
            ax.set_ylabel("Volume", fontsize=12)
            ax.set_title("Volume", fontsize=12, fontweight='bold')
            
            # Add volume moving average
            if len(data) > 20:
                volume_ma = data['Volume'].rolling(window=20).mean()
                ax.plot(data.index, volume_ma, color='red', linewidth=1, 
                       alpha=0.8, label='Volume MA(20)')
                ax.legend(fontsize=10)
    
    def _plot_rsi(self, ax, data: pd.DataFrame):
        """Plot RSI indicator."""
        if 'RSI_14' in data.columns:
            ax.plot(data.index, data['RSI_14'], color=self.colors['rsi'], 
                   linewidth=2, label='RSI(14)')
            
            # Add overbought/oversold lines
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought')
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold')
            ax.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
            
            ax.set_ylabel("RSI", fontsize=12)
            ax.set_title("RSI (14)", fontsize=12, fontweight='bold')
            ax.set_ylim(0, 100)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
    
    def _plot_macd(self, ax, data: pd.DataFrame):
        """Plot MACD indicator."""
        if all(col in data.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
            ax.plot(data.index, data['MACD'], color=self.colors['macd'], 
                   linewidth=2, label='MACD')
            ax.plot(data.index, data['MACD_Signal'], color='red', 
                   linewidth=1, label='Signal')
            
            # Plot histogram
            colors = ['green' if x >= 0 else 'red' for x in data['MACD_Histogram']]
            ax.bar(data.index, data['MACD_Histogram'], color=colors, 
                  alpha=0.6, width=1, label='Histogram')
            
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax.set_ylabel("MACD", fontsize=12)
            ax.set_title("MACD", fontsize=12, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
    
    def _plot_strategy_signals(self, ax, data: pd.DataFrame, strategies: Dict = None):
        """Plot strategy performance over time."""
        if not strategies:
            ax.text(0.5, 0.5, 'No Strategy Data Available', 
                   transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title("Strategy Signals", fontsize=12, fontweight='bold')
            return
        
        # Create a simple bar chart of strategy confidences
        strategy_names = list(strategies.keys())
        confidences = [strategies[name]['confidence'] for name in strategy_names]
        signals = [strategies[name]['signal'] for name in strategy_names]
        
        colors = [self.colors['buy_signal'] if sig == 'BUY' 
                 else self.colors['sell_signal'] if sig == 'SELL' 
                 else 'gray' for sig in signals]
        
        bars = ax.bar(strategy_names, confidences, color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar, conf, sig in zip(bars, confidences, signals):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{conf:.1%}\n{sig}', ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel("Confidence", fontsize=12)
        ax.set_title("Strategy Signals & Confidence", fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3, axis='y')
    
    def _format_date_axis(self, ax):
        """Format date axis for better readability."""
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _add_chart_metadata(self, fig, symbol: str, data: pd.DataFrame, signals: Dict):
        """Add metadata and summary information to chart."""
        # Add main title
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[-2] if len(data) > 1 else 0
        price_change_pct = (price_change / data['Close'].iloc[-2] * 100) if len(data) > 1 else 0
        
        title = f"{symbol} - Technical Analysis Dashboard"
        subtitle = f"Price: ₹{latest_price:.2f} ({price_change:+.2f}, {price_change_pct:+.2f}%)"
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        fig.text(0.5, 0.95, subtitle, ha='center', fontsize=12)
        
        # Add signal summary
        composite_signal = signals.get('composite_signal', 'NO_SIGNAL')
        composite_score = signals.get('composite_score', 0)
        
        signal_text = f"Composite Signal: {composite_signal} (Score: {composite_score:.1f})"
        fig.text(0.5, 0.92, signal_text, ha='center', fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fig.text(0.99, 0.01, f"Generated: {timestamp}", ha='right', va='bottom', 
                fontsize=8, alpha=0.7)
    
    def generate_portfolio_summary_chart(self, results: List[Dict], 
                                       save_path: Optional[str] = None) -> str:
        """Generate portfolio-level summary chart."""
        try:
            if not results:
                return None
            
            # Create figure
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # Signal distribution
            signals = [r['composite_signal'] for r in results]
            signal_counts = pd.Series(signals).value_counts()
            
            ax1.pie(signal_counts.values, labels=signal_counts.index, autopct='%1.1f%%',
                   colors=[self.colors['buy_signal'] if 'BUY' in label 
                          else self.colors['sell_signal'] if 'SELL' in label 
                          else 'gray' for label in signal_counts.index])
            ax1.set_title("Signal Distribution", fontsize=14, fontweight='bold')
            
            # Score distribution
            scores = [r['composite_score'] for r in results if r['composite_score'] != 0]
            if scores:
                ax2.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7)
                ax2.set_xlabel("Composite Score")
                ax2.set_ylabel("Frequency")
                ax2.set_title("Score Distribution", fontsize=14, fontweight='bold')
            
            # Top signals
            buy_signals = [r for r in results if r['composite_signal'] == 'BUY']
            sell_signals = [r for r in results if r['composite_signal'] == 'SELL']
            
            if buy_signals:
                top_buys = sorted(buy_signals, key=lambda x: x['composite_score'], reverse=True)[:10]
                symbols = [r['symbol'].replace('.NS', '') for r in top_buys]
                scores = [r['composite_score'] for r in top_buys]
                
                ax3.barh(symbols, scores, color=self.colors['buy_signal'], alpha=0.7)
                ax3.set_xlabel("Composite Score")
                ax3.set_title("Top BUY Signals", fontsize=14, fontweight='bold')
            
            if sell_signals:
                top_sells = sorted(sell_signals, key=lambda x: x['composite_score'])[:10]
                symbols = [r['symbol'].replace('.NS', '') for r in top_sells]
                scores = [r['composite_score'] for r in top_sells]
                
                ax4.barh(symbols, scores, color=self.colors['sell_signal'], alpha=0.7)
                ax4.set_xlabel("Composite Score")
                ax4.set_title("Top SELL Signals", fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            # Save chart
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.output_dir / f"portfolio_summary_{timestamp}.png"
            
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Portfolio summary chart saved: {save_path}")
            return str(save_path)
            
        except Exception as e:
            logger.error(f"Error generating portfolio summary chart: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None


def create_chart_for_symbol(symbol: str, data: pd.DataFrame, signals: Dict, 
                          strategies: Dict = None, output_dir: str = "output/charts") -> str:
    """
    Convenience function to create a chart for a single symbol.
    
    Args:
        symbol: Stock symbol
        data: OHLCV data with indicators
        signals: Signal information
        strategies: Strategy-specific signals
        output_dir: Output directory for charts
        
    Returns:
        Path to saved chart
    """
    chart_gen = ChartGenerator(output_dir)
    return chart_gen.generate_comprehensive_chart(symbol, data, signals, strategies)