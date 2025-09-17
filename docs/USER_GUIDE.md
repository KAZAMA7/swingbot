# User Guide

## Getting Started

### Quick Start (Recommended)

The easiest way to get started is with the simple trading bot:

1. **Install Python dependencies:**
   ```bash
   pip install yfinance pandas numpy matplotlib pyyaml
   ```

2. **Run the simple bot:**
   ```bash
   python simple_trading_bot.py
   ```

3. **Check the results:**
   - View console output for real-time analysis
   - Check `signals.csv` for detailed results
   - Review `config.yaml` for customization options

### Full System Setup

For advanced features and customization:

1. **Install all dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test the installation:**
   ```bash
   python test_bot.py
   ```

3. **Run the full system:**
   ```bash
   python src/main.py --test
   ```

## Understanding the Output

### Console Output
```
Stock Trading Bot
========================================
2025-09-17 17:33:38 - INFO - Analyzing AAPL...
2025-09-17 17:33:38 - INFO - AAPL: NO_SIGNAL - Price: $238.15, RSI: 62.2
```

- **Symbol**: Stock ticker being analyzed
- **Signal**: BUY, SELL, or NO_SIGNAL
- **Price**: Current stock price
- **RSI**: Relative Strength Index value

### CSV Output (signals.csv)
| timestamp | symbol | signal_type | confidence | rsi | current_price |
|-----------|--------|-------------|------------|-----|---------------|
| 2025-09-17T17:33:38 | AAPL | NO_SIGNAL | 0.0 | 62.2 | 238.15 |

## Configuration Guide

### Basic Configuration (config.yaml)

```yaml
# Stocks to analyze
watchlist:
  - "AAPL"    # Apple Inc.
  - "GOOGL"   # Alphabet Inc.
  - "MSFT"    # Microsoft Corp.
  - "TSLA"    # Tesla Inc.
  - "NVDA"    # NVIDIA Corp.

# Technical indicator settings
indicators:
  rsi:
    period: 14        # 14-day RSI (standard)
  bollinger_bands:
    period: 20        # 20-day moving average
    std_dev: 2        # 2 standard deviations
  ema:
    period: 20        # 20-day exponential moving average

# Trading strategy parameters
strategy:
  swing_trading:
    rsi_oversold: 30    # Buy when RSI below 30
    rsi_overbought: 70  # Sell when RSI above 70
```

### Advanced Configuration

```yaml
# Data source settings
data_sources:
  yahoo_finance:
    enabled: true
    rate_limit: 5     # Requests per second

# Scheduling (for full system)
scheduling:
  update_interval: 300      # 5 minutes
  market_hours_only: true   # Only during market hours

# Output settings
output:
  csv_file: "signals.csv"
  database: "trading_data.db"
  charts_enabled: false
  output_dir: "output"

# Logging settings
logging:
  level: "INFO"
  file: "trading_bot.log"
  max_size_mb: 10
  backup_count: 5
```

## Trading Strategy Explained

### The Swing Trading Strategy

The bot uses a three-indicator approach for swing trading:

#### Buy Signal Requirements (ALL must be true):
1. **RSI < 30** - Stock is oversold
2. **Price < Bollinger Lower Band** - Price is compressed below normal range
3. **Price > EMA** - Overall trend is still upward

#### Sell Signal Requirements (ALL must be true):
1. **RSI > 70** - Stock is overbought  
2. **Price > Bollinger Upper Band** - Price is extended above normal range
3. **Price < EMA** - Overall trend is turning downward

#### Why This Works:
- **RSI** identifies momentum extremes
- **Bollinger Bands** identify price compression/extension
- **EMA** confirms the overall trend direction

### Signal Confidence

Each signal includes a confidence score (0.0 to 1.0):
- **0.8-1.0**: Very strong signal
- **0.6-0.8**: Strong signal  
- **0.4-0.6**: Moderate signal
- **0.0-0.4**: Weak signal

## Usage Scenarios

### Scenario 1: Daily Analysis

Run the bot once per day to get trading ideas:

```bash
python simple_trading_bot.py
```

Review the output and `signals.csv` file for potential trades.

### Scenario 2: Continuous Monitoring

Use the full system for automated monitoring:

```bash
python src/main.py  # Runs continuously with scheduling
```

### Scenario 3: Custom Watchlist

1. Edit `config.yaml`:
   ```yaml
   watchlist:
     - "YOUR_STOCK_1"
     - "YOUR_STOCK_2"
   ```

2. Run the analysis:
   ```bash
   python simple_trading_bot.py
   ```

### Scenario 4: Different Time Frames

Adjust indicator periods for different trading styles:

```yaml
# For day trading (shorter periods)
indicators:
  rsi:
    period: 7
  bollinger_bands:
    period: 10
  ema:
    period: 10

# For long-term investing (longer periods)
indicators:
  rsi:
    period: 21
  bollinger_bands:
    period: 50
  ema:
    period: 50
```

## Interpreting Results

### Strong Buy Signal Example
```
🚨 BUY signal for AAPL at $145.50
RSI: 25.3 (oversold)
Price below BB lower: $147.20
Price above EMA: $144.80
Confidence: 0.85
```

**Interpretation**: Apple is oversold (RSI 25.3), trading below its normal range (below Bollinger lower band), but still above the trend line (EMA). This suggests a potential bounce.

### Strong Sell Signal Example
```
🚨 SELL signal for TSLA at $890.25
RSI: 78.4 (overbought)
Price above BB upper: $885.60
Price below EMA: $895.40
Confidence: 0.92
```

**Interpretation**: Tesla is overbought (RSI 78.4), trading above its normal range, and starting to fall below the trend line. This suggests a potential pullback.

### No Signal Example
```
MSFT: NO_SIGNAL - Price: $380.15, RSI: 55.2
```

**Interpretation**: Microsoft is in a neutral state with no clear trading opportunity based on the current criteria.

## Best Practices

### 1. Risk Management
- Never risk more than 1-2% of your portfolio on a single trade
- Always use stop-loss orders
- Diversify across multiple positions

### 2. Signal Validation
- Look for confluence with other analysis methods
- Check overall market conditions
- Consider fundamental factors

### 3. Timing
- Avoid trading during low-volume periods
- Be cautious around earnings announcements
- Consider market opening/closing volatility

### 4. Record Keeping
- Keep track of all trades and outcomes
- Review the `signals.csv` file regularly
- Analyze which signals work best

## Troubleshooting

### Common Issues

#### "No data available for symbol"
- Check if the symbol is valid
- Verify internet connection
- Try a different symbol

#### "Connection test failed"
- Check internet connection
- Verify Yahoo Finance is accessible
- Try running again later

#### "Insufficient data for calculation"
- Symbol may be newly listed
- Try a longer time period
- Check if symbol is actively traded

### Getting Help

1. **Check the logs**: Look at `trading_bot.log` for detailed error messages
2. **Run tests**: Use `python test_bot.py` to verify installation
3. **Review configuration**: Ensure `config.yaml` is properly formatted
4. **Check dependencies**: Verify all required packages are installed

## Performance Tips

### Optimizing for Speed
- Reduce the watchlist size for faster analysis
- Increase `rate_limit` if your connection can handle it
- Use SSD storage for database operations

### Optimizing for Accuracy
- Use longer indicator periods for more stable signals
- Increase confidence thresholds
- Add more symbols for better diversification

### Resource Management
- Monitor memory usage with large watchlists
- Clean up old log files regularly
- Use the database cleanup features

## Advanced Features

### Custom Indicators
See the [Developer Guide](DEVELOPER_GUIDE.md) for adding custom technical indicators.

### Custom Strategies
Learn how to implement your own trading strategies in the Developer Guide.

### Backtesting
Use historical data to test strategy performance:

```python
# Example backtesting code
from src.strategies.swing_trading_strategy import SwingTradingStrategy

strategy = SwingTradingStrategy()
# Implement backtesting logic
```

## Legal and Risk Disclaimers

⚠️ **Important**: This software is for educational purposes only and does not constitute financial advice.

- **No Guarantees**: Past performance does not guarantee future results
- **Risk of Loss**: Trading involves substantial risk of financial loss
- **Do Your Research**: Always conduct your own analysis before trading
- **Professional Advice**: Consider consulting with a qualified financial advisor
- **No Liability**: The authors are not responsible for any trading losses

## Support and Community

- **Documentation**: Read the full [Developer Guide](DEVELOPER_GUIDE.md)
- **Issues**: Report bugs and request features on GitHub
- **Updates**: Check for new releases and improvements

Remember: The best trading system is one you understand and can use consistently!