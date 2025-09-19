#!/usr/bin/env python3
"""
Backtesting Engine for Enhanced Multi-Strategy NIFTY Trading Bot

Comprehensive backtesting framework to evaluate strategy performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class PositionType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    position_type: PositionType
    quantity: int
    entry_signal: str
    exit_signal: str
    pnl: float
    pnl_percent: float
    holding_days: int
    strategy_name: str
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary."""
        result = asdict(self)
        result['entry_date'] = self.entry_date.isoformat()
        result['exit_date'] = self.exit_date.isoformat()
        result['position_type'] = self.position_type.value
        return result


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    entry_date: datetime
    entry_price: float
    position_type: PositionType
    quantity: int
    entry_signal: str
    strategy_name: str
    
    def current_pnl(self, current_price: float) -> float:
        """Calculate current P&L."""
        if self.position_type == PositionType.LONG:
            return (current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - current_price) * self.quantity
    
    def current_pnl_percent(self, current_price: float) -> float:
        """Calculate current P&L percentage."""
        if self.position_type == PositionType.LONG:
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - current_price) / self.entry_price) * 100


@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    initial_capital: float = 1000000.0  # 10 Lakh INR
    position_size_percent: float = 5.0  # 5% per position
    max_positions: int = 20
    commission_percent: float = 0.1  # 0.1% commission
    slippage_percent: float = 0.05  # 0.05% slippage
    stop_loss_percent: float = 5.0  # 5% stop loss
    take_profit_percent: float = 15.0  # 15% take profit
    max_holding_days: int = 30  # Maximum holding period
    allow_short_selling: bool = False
    rebalance_frequency: str = "daily"  # daily, weekly, monthly
    
    # Risk management
    max_portfolio_drawdown: float = 20.0  # 20% max drawdown
    max_daily_loss: float = 2.0  # 2% max daily loss
    
    # Signal filtering
    min_signal_confidence: float = 0.3  # Minimum signal confidence
    min_composite_score: float = 30.0  # Minimum composite score


@dataclass
class BacktestResults:
    """Backtesting results summary."""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    avg_holding_days: float
    trades: List[Trade]
    daily_returns: pd.Series
    equity_curve: pd.Series
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary."""
        result = asdict(self)
        result['start_date'] = self.start_date.isoformat()
        result['end_date'] = self.end_date.isoformat()
        result['trades'] = [trade.to_dict() for trade in self.trades]
        # Convert pandas series to JSON-serializable format
        result['daily_returns'] = {str(k): v for k, v in self.daily_returns.to_dict().items()}
        result['equity_curve'] = {str(k): v for k, v in self.equity_curve.to_dict().items()}
        return result


class BacktestEngine:
    """Main backtesting engine."""
    
    def __init__(self, config: BacktestConfig = None):
        """Initialize backtest engine."""
        self.config = config or BacktestConfig()
        self.reset()
    
    def reset(self):
        """Reset backtest state."""
        self.current_capital = self.config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_equity = []
        self.daily_dates = []
        self.peak_capital = self.config.initial_capital
        self.max_drawdown = 0.0
    
    def run_backtest(self, data_dict: Dict[str, pd.DataFrame], 
                    signal_generator_func, start_date: str = None, 
                    end_date: str = None) -> BacktestResults:
        """
        Run comprehensive backtest.
        
        Args:
            data_dict: Dictionary of symbol -> OHLCV data
            signal_generator_func: Function that generates signals for given data
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            
        Returns:
            BacktestResults object
        """
        logger.info("Starting backtest...")
        self.reset()
        
        # Prepare data
        all_dates = self._get_common_dates(data_dict, start_date, end_date)
        if len(all_dates) < 30:
            raise ValueError("Insufficient data for backtesting (need at least 30 days)")
        
        logger.info(f"Backtesting from {all_dates[0]} to {all_dates[-1]} ({len(all_dates)} days)")
        
        # Run day-by-day simulation
        for i, current_date in enumerate(all_dates):
            try:
                self._process_day(current_date, data_dict, signal_generator_func, i)
                
                # Record daily equity
                total_equity = self._calculate_total_equity(current_date, data_dict)
                self.daily_equity.append(total_equity)
                self.daily_dates.append(current_date)
                
                # Update max drawdown
                if total_equity > self.peak_capital:
                    self.peak_capital = total_equity
                
                current_drawdown = (self.peak_capital - total_equity) / self.peak_capital * 100
                self.max_drawdown = max(self.max_drawdown, current_drawdown)
                
                # Risk management - stop if max drawdown exceeded
                if current_drawdown > self.config.max_portfolio_drawdown:
                    logger.warning(f"Max drawdown exceeded on {current_date}, stopping backtest")
                    break
                    
            except Exception as e:
                logger.error(f"Error processing {current_date}: {e}")
                continue
        
        # Close all remaining positions
        self._close_all_positions(all_dates[-1], data_dict, "BACKTEST_END")
        
        # Calculate results
        results = self._calculate_results(all_dates[0], all_dates[-1])
        
        logger.info(f"Backtest completed: {results.total_return_percent:.2f}% return, "
                   f"{results.total_trades} trades, {results.win_rate:.1f}% win rate")
        
        return results
    
    def _get_common_dates(self, data_dict: Dict[str, pd.DataFrame], 
                         start_date: str = None, end_date: str = None) -> List[datetime]:
        """Get common trading dates across all symbols."""
        all_dates = None
        
        for symbol, data in data_dict.items():
            if data.empty:
                continue
                
            symbol_dates = set(data.index)
            if all_dates is None:
                all_dates = symbol_dates
            else:
                all_dates = all_dates.intersection(symbol_dates)
        
        if all_dates is None:
            return []
        
        # Convert to sorted list
        date_list = sorted(list(all_dates))
        
        # Apply date filters
        if start_date:
            start_dt = pd.to_datetime(start_date)
            # Make timezone aware if needed
            if date_list and hasattr(date_list[0], 'tz') and date_list[0].tz is not None:
                if start_dt.tz is None:
                    start_dt = start_dt.tz_localize(date_list[0].tz)
            date_list = [d for d in date_list if d >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            # Make timezone aware if needed
            if date_list and hasattr(date_list[0], 'tz') and date_list[0].tz is not None:
                if end_dt.tz is None:
                    end_dt = end_dt.tz_localize(date_list[0].tz)
            date_list = [d for d in date_list if d <= end_dt]
        
        return date_list
    
    def _process_day(self, current_date: datetime, data_dict: Dict[str, pd.DataFrame], 
                    signal_generator_func, day_index: int):
        """Process a single trading day."""
        # Skip first few days to allow indicators to stabilize
        if day_index < 50:
            return
        
        # Check existing positions for exits
        self._check_position_exits(current_date, data_dict)
        
        # Generate new signals
        if len(self.positions) < self.config.max_positions:
            self._check_new_entries(current_date, data_dict, signal_generator_func)
    
    def _check_position_exits(self, current_date: datetime, data_dict: Dict[str, pd.DataFrame]):
        """Check if any positions should be closed."""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            if symbol not in data_dict or current_date not in data_dict[symbol].index:
                continue
            
            current_price = data_dict[symbol].loc[current_date, 'Close']
            holding_days = (current_date - position.entry_date).days
            
            # Check stop loss
            pnl_percent = position.current_pnl_percent(current_price)
            if pnl_percent <= -self.config.stop_loss_percent:
                positions_to_close.append((symbol, current_price, "STOP_LOSS"))
                continue
            
            # Check take profit
            if pnl_percent >= self.config.take_profit_percent:
                positions_to_close.append((symbol, current_price, "TAKE_PROFIT"))
                continue
            
            # Check max holding period
            if holding_days >= self.config.max_holding_days:
                positions_to_close.append((symbol, current_price, "MAX_HOLDING"))
                continue
        
        # Close positions
        for symbol, exit_price, exit_reason in positions_to_close:
            self._close_position(symbol, current_date, exit_price, exit_reason)
    
    def _check_new_entries(self, current_date: datetime, data_dict: Dict[str, pd.DataFrame], 
                          signal_generator_func):
        """Check for new position entries."""
        for symbol, data in data_dict.items():
            if symbol in self.positions or current_date not in data.index:
                continue
            
            # Get historical data up to current date
            historical_data = data.loc[:current_date].copy()
            if len(historical_data) < 50:  # Need enough data for indicators
                continue
            
            try:
                # Generate signals
                signals = signal_generator_func(historical_data)
                if not signals:
                    continue
                
                # Check signal criteria
                composite_signal = signals.get('composite_signal', 'NO_SIGNAL')
                composite_score = signals.get('composite_score', 0)
                composite_confidence = signals.get('composite_confidence', 0)
                
                if (composite_signal in ['BUY', 'SELL'] and 
                    abs(composite_score) >= self.config.min_composite_score and
                    composite_confidence >= self.config.min_signal_confidence):
                    
                    current_price = historical_data['Close'].iloc[-1]
                    self._open_position(symbol, current_date, current_price, 
                                      composite_signal, "COMPOSITE")
                    
            except Exception as e:
                logger.debug(f"Error generating signals for {symbol} on {current_date}: {e}")
                continue
    
    def _open_position(self, symbol: str, entry_date: datetime, entry_price: float, 
                      signal: str, strategy_name: str):
        """Open a new position."""
        if len(self.positions) >= self.config.max_positions:
            return
        
        # Calculate position size
        position_value = self.current_capital * (self.config.position_size_percent / 100)
        quantity = int(position_value / entry_price)
        
        if quantity <= 0:
            return
        
        # Apply slippage and commission
        actual_entry_price = entry_price * (1 + self.config.slippage_percent / 100)
        commission = position_value * (self.config.commission_percent / 100)
        
        # Determine position type
        if signal == 'BUY':
            position_type = PositionType.LONG
        elif signal == 'SELL' and self.config.allow_short_selling:
            position_type = PositionType.SHORT
        else:
            return
        
        # Create position
        position = Position(
            symbol=symbol,
            entry_date=entry_date,
            entry_price=actual_entry_price,
            position_type=position_type,
            quantity=quantity,
            entry_signal=signal,
            strategy_name=strategy_name
        )
        
        self.positions[symbol] = position
        self.current_capital -= (position_value + commission)
        
        logger.debug(f"Opened {position_type.value} position: {symbol} @ ₹{actual_entry_price:.2f}")
    
    def _close_position(self, symbol: str, exit_date: datetime, exit_price: float, 
                       exit_reason: str):
        """Close an existing position."""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Apply slippage and commission
        actual_exit_price = exit_price * (1 - self.config.slippage_percent / 100)
        position_value = actual_exit_price * position.quantity
        commission = position_value * (self.config.commission_percent / 100)
        
        # Calculate P&L
        if position.position_type == PositionType.LONG:
            pnl = (actual_exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - actual_exit_price) * position.quantity
        
        pnl -= commission  # Subtract commission
        pnl_percent = (pnl / (position.entry_price * position.quantity)) * 100
        
        # Create trade record
        trade = Trade(
            symbol=symbol,
            entry_date=position.entry_date,
            exit_date=exit_date,
            entry_price=position.entry_price,
            exit_price=actual_exit_price,
            position_type=position.position_type,
            quantity=position.quantity,
            entry_signal=position.entry_signal,
            exit_signal=exit_reason,
            pnl=pnl,
            pnl_percent=pnl_percent,
            holding_days=(exit_date - position.entry_date).days,
            strategy_name=position.strategy_name
        )
        
        self.trades.append(trade)
        self.current_capital += (position_value - commission)
        
        # Remove position
        del self.positions[symbol]
        
        logger.debug(f"Closed {position.position_type.value} position: {symbol} @ ₹{actual_exit_price:.2f}, "
                    f"P&L: ₹{pnl:.2f} ({pnl_percent:.2f}%)")
    
    def _close_all_positions(self, exit_date: datetime, data_dict: Dict[str, pd.DataFrame], 
                           exit_reason: str):
        """Close all remaining positions."""
        symbols_to_close = list(self.positions.keys())
        
        for symbol in symbols_to_close:
            if symbol in data_dict and exit_date in data_dict[symbol].index:
                exit_price = data_dict[symbol].loc[exit_date, 'Close']
                self._close_position(symbol, exit_date, exit_price, exit_reason)
    
    def _calculate_total_equity(self, current_date: datetime, 
                              data_dict: Dict[str, pd.DataFrame]) -> float:
        """Calculate total portfolio equity."""
        total_equity = self.current_capital
        
        for symbol, position in self.positions.items():
            if symbol in data_dict and current_date in data_dict[symbol].index:
                current_price = data_dict[symbol].loc[current_date, 'Close']
                position_value = current_price * position.quantity
                total_equity += position_value
        
        return total_equity
    
    def _calculate_results(self, start_date: datetime, end_date: datetime) -> BacktestResults:
        """Calculate comprehensive backtest results."""
        # Basic metrics
        final_capital = self.daily_equity[-1] if self.daily_equity else self.config.initial_capital
        total_return = final_capital - self.config.initial_capital
        total_return_percent = (total_return / self.config.initial_capital) * 100
        
        # Time-based metrics
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = ((final_capital / self.config.initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = (len(winning_trades) / len(self.trades) * 100) if self.trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        avg_holding_days = np.mean([t.holding_days for t in self.trades]) if self.trades else 0
        
        # Risk metrics
        daily_returns = pd.Series(self.daily_equity).pct_change().dropna()
        equity_curve = pd.Series(self.daily_equity, index=self.daily_dates)
        
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        profit_factor = abs(sum([t.pnl for t in winning_trades]) / sum([t.pnl for t in losing_trades])) if losing_trades else float('inf')
        
        return BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            annualized_return=annualized_return,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_holding_days=avg_holding_days,
            trades=self.trades,
            daily_returns=daily_returns,
            equity_curve=equity_curve
        )
    
    def _calculate_sharpe_ratio(self, daily_returns: pd.Series, risk_free_rate: float = 0.06) -> float:
        """Calculate Sharpe ratio."""
        if daily_returns.empty or daily_returns.std() == 0:
            return 0.0
        
        excess_returns = daily_returns - (risk_free_rate / 252)  # Daily risk-free rate
        return (excess_returns.mean() / daily_returns.std()) * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, daily_returns: pd.Series, risk_free_rate: float = 0.06) -> float:
        """Calculate Sortino ratio."""
        if daily_returns.empty:
            return 0.0
        
        excess_returns = daily_returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf') if excess_returns.mean() > 0 else 0.0
        
        return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)


def save_backtest_results(results: BacktestResults, output_dir: str = "output/backtests") -> str:
    """Save backtest results to JSON file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"backtest_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results.to_dict(), f, indent=2, default=str)
    
    logger.info(f"Backtest results saved to {filename}")
    return str(filename)