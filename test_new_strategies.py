#!/usr/bin/env python3
"""
Test script for new EMA Crossover and SuperTrend strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

from src.strategies.ema_crossover_strategy import EMACrossoverStrategy
from src.strategies.supertrend_strategy import SuperTrendStrategy
from src.strategies.multi_strategy_scorer import MultiStrategyScorer
from src.notifications.email_service import EmailNotificationService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_data(periods=100):
    """Create realistic test data."""
    dates = pd.date_range(start='2023-01-01', periods=periods, freq='D')
    np.random.seed(42)
    
    # Generate trending price data
    prices = []
    price = 100.0
    for i in range(periods):
        # Create trend changes
        if i < periods // 3:
            change = np.random.normal(0.5, 1.5)  # Uptrend
        elif i < 2 * periods // 3:
            change = np.random.normal(-0.3, 1.2)  # Downtrend
        else:
            change = np.random.normal(0.2, 1.0)  # Recovery
        
        price += change
        prices.append(max(price, 1))
    
    return pd.DataFrame({
        'Open': [p * np.random.uniform(0.99, 1.01) for p in prices],
        'High': [p * np.random.uniform(1.01, 1.03) for p in prices],
        'Low': [p * np.random.uniform(0.97, 0.99) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, periods)
    }, index=dates)

def test_individual_strategies():
    """Test individual strategies."""
    logger.info("Testing individual strategies...")
    
    test_data = create_test_data(100)
    
    # Test EMA Crossover Strategy
    logger.info("Testing EMA Crossover Strategy...")
    ema_strategy = EMACrossoverStrategy(short_period=20, long_period=50)
    ema_signal = ema_strategy.generate_signal(test_data, {})
    
    logger.info(f"EMA Crossover - Signal: {ema_signal.signal_type.value}, "
               f"Confidence: {ema_signal.confidence:.2f}")
    
    # Get EMA values
    ema_values = ema_strategy.get_ema_values(test_data)
    logger.info(f"EMA Values - Short: {ema_values['short_ema']:.2f}, "
               f"Long: {ema_values['long_ema']:.2f}, "
               f"Convergence: {ema_values['convergence_pct']:.2f}%")
    
    # Test SuperTrend Strategy
    logger.info("Testing SuperTrend Strategy...")
    st_strategy = SuperTrendStrategy(atr_period=10, multiplier=3.0)
    st_signal = st_strategy.generate_signal(test_data, {})
    
    logger.info(f"SuperTrend - Signal: {st_signal.signal_type.value}, "
               f"Confidence: {st_signal.confidence:.2f}")
    
    # Get SuperTrend values
    st_values = st_strategy.get_supertrend_values(test_data)
    logger.info(f"SuperTrend Values - Value: {st_values['supertrend_value']:.2f}, "
               f"Trend: {st_values['trend_direction']}, "
               f"ATR: {st_values['atr_value']:.2f}")
    
    return ema_signal, st_signal

def test_multi_strategy_scoring():
    """Test multi-strategy scoring."""
    logger.info("Testing Multi-Strategy Scoring...")
    
    # Get individual signals
    ema_signal, st_signal = test_individual_strategies()
    
    # Test with different weights
    weights = {
        'ema_crossover': 1.5,
        'supertrend': 1.2
    }
    
    scorer = MultiStrategyScorer(weights)
    composite = scorer.calculate_composite_score([ema_signal, st_signal], 'TEST')
    
    logger.info(f"Composite Signal - Type: {composite.signal_type.value}, "
               f"Score: {composite.composite_score:.1f}, "
               f"Confidence: {composite.confidence:.2f}")
    
    # Get strategy breakdown
    breakdown = composite.get_signal_breakdown()
    logger.info("Strategy Breakdown:")
    for strategy, details in breakdown.items():
        logger.info(f"  {strategy}: Score={details['signal_score']:.1f}, "
                   f"Weight={details['weight']:.1f}, "
                   f"Contribution={details['weighted_contribution']:.1f}")
    
    return composite

def test_email_notifications():
    """Test email notification formatting."""
    logger.info("Testing Email Notifications...")
    
    # Get composite signal
    composite = test_multi_strategy_scoring()
    
    # Test email service (disabled)
    email_config = {
        'enabled': False,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'test@example.com',
        'password': 'dummy_password',
        'recipients': ['trader@example.com'],
        'use_tls': True,
        'send_on_strong_signals_only': True
    }
    
    email_service = EmailNotificationService(email_config)
    
    # Test email formatting
    subject, body = email_service.format_signal_email(composite, 'TEST')
    
    logger.info(f"Email Subject: {subject}")
    logger.info(f"Email Body Preview (first 200 chars):\n{body[:200]}...")
    
    return True

def main():
    """Main test function."""
    logger.info("🚀 Starting Enhanced Trading Strategies Test")
    
    try:
        # Test individual strategies
        test_individual_strategies()
        
        # Test multi-strategy scoring
        test_multi_strategy_scoring()
        
        # Test email notifications
        test_email_notifications()
        
        logger.info("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)