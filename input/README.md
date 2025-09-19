# Input Configuration Files

This directory contains configuration files for the Enhanced Multi-Strategy NIFTY Trading Bot.

## Configuration Files

### `config_nifty50.yaml`
Configuration optimized for NIFTY 50 analysis:
- 50 symbols (top companies by market cap)
- Shorter timeout (60 seconds per symbol)
- Optimized for quick analysis

### `config_nifty100.yaml`
Configuration optimized for NIFTY 100 analysis:
- 100 symbols (broader market coverage)
- Moderate timeout (90 seconds per symbol)
- Balanced performance and coverage

### `config_nifty500.yaml`
Configuration optimized for NIFTY 500 analysis:
- 500 symbols (comprehensive market coverage)
- Longer timeout (120 seconds per symbol)
- Maximum market coverage

### `config_enhanced_multi_strategy.yaml`
Default configuration file with standard settings.

## Configuration Sections

Each configuration file contains:

- **Data Fetching**: Historical data retrieval settings
- **Strategies**: EMA Crossover, SuperTrend, and Legacy strategy settings
- **Multi-Strategy**: Composite scoring thresholds and weights
- **Email Notifications**: SMTP settings for alerts
- **Output**: Directory structure for results
- **Indicators**: Technical indicator parameters
- **Market**: Index-specific settings

## Usage

The bot automatically selects the appropriate configuration based on the `--size` parameter:

```bash
# Uses config_nifty50.yaml
./enhanced-multi-strategy-nifty-bot --size nifty50

# Uses config_nifty100.yaml  
./enhanced-multi-strategy-nifty-bot --size nifty100

# Uses config_nifty500.yaml
./enhanced-multi-strategy-nifty-bot --size nifty500

# Use custom config
./enhanced-multi-strategy-nifty-bot --config input/my_custom_config.yaml
```

## Customization

You can create custom configuration files by copying and modifying any of the existing files. Key parameters to adjust:

- **Strategy weights**: Adjust the importance of each strategy
- **Thresholds**: Modify buy/sell signal thresholds
- **Timeouts**: Adjust based on your system performance
- **Email settings**: Configure SMTP for notifications